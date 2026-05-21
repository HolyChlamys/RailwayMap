/** Station type classification — matches backend category field */
export type StationType =
  | 'major_hub'
  | 'major_passenger'
  | 'medium_passenger'
  | 'small_passenger'
  | 'small_non_passenger'
  | 'large_yard'
  | 'medium_yard'
  | 'major_freight'
  | 'freight_yard'
  | 'signal_station'
  | 'emu_depot'
  | 'other_facility'

/** A single timetable entry for a train at a station */
export interface TimetableEntry {
  trainNo: string
  trainType: string
  departStation: string
  arriveStation: string
  arriveTime?: string
  departTime?: string
}

/** Core station entity — aligned with backend StationSearchResult DTO */
export interface Station {
  id: number
  name: string
  city: string
  province?: string
  category: StationType
  lon: number
  lat: number
  /** Train numbers passing through this station (populated by detail API) */
  routes?: string[]
  /** Preloaded timetable — all trains with arrive/depart times at this station */
  timetable?: TimetableEntry[]
  /** Annual passenger volume (ten-thousands), for heatmap */
  passengerVolume?: number
}

/** Station type display label mapping */
export const STATION_TYPE_LABELS: Record<StationType, string> = {
  major_hub: '重要枢纽站',
  major_passenger: '主要车站',
  medium_passenger: '中等车站',
  small_passenger: '小型车站',
  small_non_passenger: '小型站(无客运)',
  large_yard: '大型编组站',
  medium_yard: '中小编组站',
  major_freight: '重要货运站',
  freight_yard: '铁路货场',
  signal_station: '线路所',
  emu_depot: '动车整备场',
  other_facility: '其他设施',
}

/** Station search result (subset of Station for dropdown) */
export interface StationSearchResult {
  id: number
  name: string
  city: string
  province?: string
  category: StationType
  lon: number
  lat: number
}

/** City aggregation for search */
export interface CityResult {
  city: string
  stationCount: number
}

/** Map raw API response to Station */
export function mapToStation(raw: Record<string, any>): Station {
  return {
    id: raw.id as number,
    name: raw.name ?? '',
    city: raw.city ?? '',
    province: raw.province ?? undefined,
    category: (raw.category as StationType) ?? 'small_passenger',
    lon: raw.lon ?? 0,
    lat: raw.lat ?? 0,
    routes: raw.routes ?? raw.passingTrains ?? undefined,
    timetable: raw.timetable ?? undefined,
    passengerVolume: raw.passengerVolume ?? undefined,
  }
}

/** Map raw API response to StationSearchResult */
export function mapToSearchResult(raw: Record<string, any>): StationSearchResult {
  return {
    id: raw.id as number,
    name: raw.name ?? '',
    city: raw.city ?? '',
    province: raw.province ?? undefined,
    category: (raw.category as StationType) ?? 'small_passenger',
    lon: raw.lon ?? 0,
    lat: raw.lat ?? 0,
  }
}
