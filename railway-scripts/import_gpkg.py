"""
Import railway data from GPKG file(s) into railway_segments and stations tables.

Enhanced importer — computes length_km in Python and infers `usage` from segment
length: <1.5 km → spur, 1.5–5 km → branch, ≥5 km → main.  High-speed segments
always get usage='main' regardless of length.

Skips urban rail: subway, monorail, light_rail, tram.

Usage: .venv/bin/python import_gpkg.py <gpkg_file_or_dir> [--stations-only] [--segments-only] [--clear-old]
  --stations-only   Only import stations (skip segments)
  --segments-only   Only import segments (skip stations)
  --clear-old       Clear old grid-based data before import
"""
import math
import sqlite3
import sys
import psycopg2
from pathlib import Path
from datetime import datetime
from shapely import wkb

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "railwaymap", "user": "railway", "password": "railway123",
}

GPKG_MAGIC = b'\x47\x50'

# ---- Length thresholds for usage inference ----
SPUR_MAX_KM = 1.5
BRANCH_MAX_KM = 5.0


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def find_wkb_offset(blob: bytes) -> int | None:
    """Find the WKB start offset within a GPKG geometry blob."""
    for off in range(4, min(len(blob), 80)):
        endian_byte = blob[off]
        if endian_byte not in (0x00, 0x01):
            continue
        if off + 5 > len(blob):
            continue
        byteorder = 'little' if endian_byte == 0x01 else 'big'
        geom_type = int.from_bytes(blob[off+1:off+5], byteorder)
        if 1 <= geom_type <= 7:
            return off
    return None


def haversine_km(coords) -> float:
    """Compute length in km from (lng, lat) coordinate sequence (Haversine)."""
    total = 0.0
    for i in range(1, len(coords)):
        lon1, lat1 = math.radians(coords[i-1][0]), math.radians(coords[i-1][1])
        lon2, lat2 = math.radians(coords[i][0]), math.radians(coords[i][1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2
             + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2)
        total += 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return total


def parse_gpkg_geom(blob: bytes) -> tuple[str, float] | None:
    """Parse GPKG geometry blob → (wkt, length_km)."""
    if not blob or len(blob) < 10:
        return None
    if blob[:2] != GPKG_MAGIC:
        return None
    wkb_offset = find_wkb_offset(blob)
    if wkb_offset is None:
        return None
    try:
        geom = wkb.loads(blob[wkb_offset:])
        coords = list(geom.coords)
        length = haversine_km(coords)
        return (geom.wkt, length)
    except Exception:
        return None


def classify(fclass: str, name: str, length_km: float) -> tuple[str, str] | None:
    """
    Classify a railway segment → (category, usage) or None to skip.

    category: high_speed | conventional | other_rail
    usage:    main | branch | spur
    """
    fclass = (fclass or '').lower()
    name = name or ''

    # Skip urban rail — incomplete/fragmented data
    if fclass in ('subway', 'monorail', 'light_rail', 'tram'):
        return None

    # Narrow gauge / minor → always other_rail + spur
    if fclass in ('narrow_gauge', 'miniature_railway', 'funicular'):
        return ('other_rail', 'spur')

    # ---- Category ----
    if any(kw in name for kw in ('高铁', '高速', '客专', '城际')):
        category = 'high_speed'
    else:
        category = 'conventional'

    # ---- Usage ----
    if category == 'high_speed':
        usage = 'main'
    elif length_km < SPUR_MAX_KM:
        usage = 'spur'
    elif length_km < BRANCH_MAX_KM:
        usage = 'branch'
    else:
        usage = 'main'

    return (category, usage)


def parse_gpkg_point(blob: bytes) -> str | None:
    """Parse GPKG point geometry blob → WKT POINT string."""
    if not blob or len(blob) < 10:
        return None
    if blob[:2] != GPKG_MAGIC:
        return None
    wkb_offset = find_wkb_offset(blob)
    if wkb_offset is None:
        return None
    try:
        geom = wkb.loads(blob[wkb_offset:])
        return geom.wkt
    except Exception:
        return None


def classify_station(name: str, province: str) -> str:
    """
    Classify a station → category string.
    Returns one of: major_hub, major_passenger, medium_passenger, small_passenger
    """
    name = name or ''

    # Major hub indicators (terminal stations in provincial capitals)
    hub_keywords = ['枢纽', '总站', '中心站']
    if any(kw in name for kw in hub_keywords):
        return 'major_hub'

    # Major passenger indicators
    major_keywords = ['站', '北站', '南站', '东站', '西站']
    is_major_city_keyword = any(kw in name for kw in major_keywords)

    # Medium/small based on name patterns
    if '站' in name:
        if any(kw in name for kw in ['北', '南', '东', '西']):
            return 'major_passenger'
        return 'medium_passenger'

    return 'small_passenger'


def import_stations_from_gpkg(path, conn, cur, source_label: str) -> tuple[int, int, int]:
    """
    Import railway stations from a GPKG file.
    Returns (station_count, halt_count, skip_count).
    """
    if not path.exists():
        log(f"  FILE NOT FOUND: {path}")
        return (0, 0, 0)

    gpkg = sqlite3.connect(str(path))
    gc = gpkg.cursor()

    gc.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='gis_osm_transport_free'"
    )
    if not gc.fetchone():
        log(f"  No gis_osm_transport_free in {path.name}")
        gpkg.close()
        return (0, 0, 0)

    gc.execute(
        "SELECT fid, geom, osm_id, code, fclass, name "
        "FROM gis_osm_transport_free "
        "WHERE fclass IN ('railway_station', 'railway_halt')"
    )
    rows = gc.fetchall()
    total = len(rows)
    if total == 0:
        gpkg.close()
        return (0, 0, 0)

    log(f"  {path.name}: {total} station points")

    station_count = 0
    halt_count = 0
    skip_count = 0
    batch: list[tuple] = []

    for fid, geom_blob, osm_id, code, fclass, name in rows:
        if not name:
            skip_count += 1
            continue

        name = name.strip()[:200]
        wkt = parse_gpkg_point(geom_blob)
        if not wkt:
            skip_count += 1
            continue

        is_halt = (fclass == 'railway_halt')
        category = 'small_passenger' if is_halt else classify_station(name, '')

        batch.append((
            osm_id,
            name,
            category,
            'gpkg:' + source_label,
            wkt,
            True,    # passenger
        ))

        if is_halt:
            halt_count += 1
        else:
            station_count += 1

    if batch:
        cur.executemany("""
            INSERT INTO stations
            (osm_id, name, category, source_grid, data_quality, geom, passenger, freight)
            VALUES (%s, %s, %s, %s, 'gpkg',
                    ST_GeomFromText(%s, 4326),
                    %s, FALSE)
            ON CONFLICT (osm_id, source_grid) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                geom = EXCLUDED.geom,
                passenger = EXCLUDED.passenger,
                updated_at = NOW()
        """, batch)

    gpkg.close()
    return (station_count, halt_count, skip_count)


def import_gpkg(path: Path, conn, cur, source_label: str) -> tuple[int, int, int]:
    """Import a single GPKG file. Returns (rail_count, skip_geom, skip_urban)."""
    if not path.exists():
        log(f"  FILE NOT FOUND: {path}")
        return (0, 0, 0)

    gpkg = sqlite3.connect(str(path))
    gc = gpkg.cursor()

    gc.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='gis_osm_railways_free'"
    )
    if not gc.fetchone():
        log(f"  No gis_osm_railways_free in {path.name}")
        gpkg.close()
        return (0, 0, 0)

    gc.execute('SELECT COUNT(*) FROM gis_osm_railways_free')
    total = gc.fetchone()[0]
    log(f"  {path.name}: {total} features")

    gc.execute(
        'SELECT fid, geom, osm_id, code, fclass, name, layer, bridge, tunnel '
        'FROM gis_osm_railways_free'
    )

    rail_count = 0
    skip_geom = 0
    skip_urban = 0
    batch: list[tuple] = []

    for fid, geom_blob, osm_id, code, fclass, name, layer, bridge, tunnel in gc:
        parsed = parse_gpkg_geom(geom_blob)
        if not parsed:
            skip_geom += 1
            continue
        wkt, length_km = parsed

        result = classify(fclass, name or '', length_km)
        if result is None:
            skip_urban += 1
            continue
        category, usage = result

        railway_val = fclass if fclass else 'rail'
        layer_int = int(layer) if layer is not None else 0
        bridge_bool = bridge == 'T' or bridge == 1
        tunnel_bool = tunnel == 'T' or tunnel == 1

        batch.append((
            osm_id,
            (name or '')[:300],
            railway_val,
            category,
            usage,
            f'gpkg:{source_label}',
            wkt,
            length_km,
            bridge_bool,
            tunnel_bool,
            layer_int,
        ))
        rail_count += 1

    # Batch insert with pre-computed length_km
    cur.executemany("""
        INSERT INTO railway_segments
        (osm_id, name, railway, category, usage, source_grid, data_quality, geom,
         electrified, gauge, max_speed, track_count, length_km,
         bridge, tunnel, layer)
        VALUES (%s, %s, %s, %s, %s, %s, 'gpkg',
                ST_GeomFromText(%s, 4326),
                NULL, 1435, NULL, 1, %s,
                %s, %s, %s)
        ON CONFLICT (osm_id, source_grid) DO UPDATE SET
            name = EXCLUDED.name,
            railway = EXCLUDED.railway,
            category = EXCLUDED.category,
            usage = EXCLUDED.usage,
            geom = EXCLUDED.geom,
            length_km = EXCLUDED.length_km,
            bridge = EXCLUDED.bridge,
            tunnel = EXCLUDED.tunnel,
            layer = EXCLUDED.layer
    """, batch)

    gpkg.close()
    return (rail_count, skip_geom, skip_urban)


def main():
    args = sys.argv[1:]
    stations_only = '--stations-only' in args
    segments_only = '--segments-only' in args
    clear_old = '--clear-old' in args

    # Filter out flags to get the target path
    target_args = [a for a in args if not a.startswith('--')]
    target = Path(target_args[0]) if target_args else Path('..')
    log(f"=== GPKG Import: {target} ===")
    log(f"stations_only={stations_only}, segments_only={segments_only}, clear_old={clear_old}")
    if not segments_only:
        log(f"usage thresholds: spur <{SPUR_MAX_KM}km ≤ branch <{BRANCH_MAX_KM}km ≤ main")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Clear old grid-based data if requested
    if clear_old and not segments_only:
        cur.execute("DELETE FROM stations WHERE source_grid LIKE 'r%'")
        log(f"  Cleared {cur.rowcount} old grid-based stations")
    if clear_old and not stations_only:
        cur.execute("DELETE FROM railway_segments WHERE data_quality = 'osm' AND source_grid LIKE 'r%'")
        log(f"  Cleared {cur.rowcount} old grid-based segments")
    conn.commit()

    files = []
    if target.is_file() and target.suffix == '.gpkg':
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob('*.gpkg'))
    else:
        log(f"ERROR: {target} is not a gpkg file or directory")
        sys.exit(1)

    total_rail = 0
    total_skip_geom = 0
    total_skip_urban = 0
    total_stations = 0
    total_halts = 0
    total_station_skip = 0

    for f in files:
        source_label = f.stem

        # Import segments (unless stations-only)
        if not stations_only:
            rail, skip_g, skip_u = import_gpkg(f, conn, cur, source_label)
            total_rail += rail
            total_skip_geom += skip_g
            total_skip_urban += skip_u

        # Import stations (unless segments-only)
        if not segments_only:
            st, ha, sk = import_stations_from_gpkg(f, conn, cur, source_label)
            total_stations += st
            total_halts += ha
            total_station_skip += sk

        conn.commit()

        parts = []
        if not stations_only:
            parts.append(f"{rail} rails")
        if not segments_only:
            parts.append(f"{st} stations, {ha} halts")
        log(f"  → {', '.join(parts)}")

    conn.commit()

    if not stations_only:
        cur.execute("SELECT COUNT(*) FROM railway_segments")
        db_seg = cur.fetchone()[0]
    else:
        db_seg = 0

    cur.execute("SELECT COUNT(*) FROM stations")
    db_st = cur.fetchone()[0]
    conn.close()

    log(f"=== DONE: {len(files)} files ===")
    if not stations_only:
        log(f"  rail imported: {total_rail}")
        log(f"  geom-skip:     {total_skip_geom}")
        log(f"  urban-skip:    {total_skip_urban}")
        log(f"  DB segments:   {db_seg}")
    if not segments_only:
        log(f"  stations:      {total_stations}")
        log(f"  halts:         {total_halts}")
        log(f"  station-skip:  {total_station_skip}")
    log(f"  DB stations:   {db_st}")


if __name__ == '__main__':
    main()
