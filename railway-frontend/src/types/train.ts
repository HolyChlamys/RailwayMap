/** Train type letter (G = high-speed, D = EMU, Z = express, etc.) */
export type TrainType = 'G' | 'D' | 'Z' | 'T' | 'K' | 'C' | 'S' | 'L' | 'Y'

/** A single stop in a train's schedule */
export interface TrainStop {
  station: string
  arrive: string   // "HH:MM" or "-" for origin
  depart: string   // "HH:MM" or "-" for terminus
  /** Minutes stopped at this station (0 for origin/terminus) */
  dwellMinutes: number
}

/** Core train entity — aligned with backend TrainSearchResult / TrainRouteDetail DTO */
export interface Train {
  no: string
  type: TrainType
  from: string
  to: string
  departTime: string   // "HH:MM" or "HH:MM:SS"
  arriveTime: string   // "HH:MM" or "HH:MM:SS"
  durationMin: number
  stops?: TrainStop[]
}

/** Map raw API search result to Train */
export function mapToTrain(raw: Record<string, any>): Train {
  return {
    no: raw.trainNo ?? '',
    type: (raw.trainType ?? 'K') as TrainType,
    from: raw.departStation ?? '',
    to: raw.arriveStation ?? '',
    departTime: typeof raw.departTime === 'string' ? raw.departTime.substring(0, 5) : '',
    arriveTime: typeof raw.arriveTime === 'string' ? raw.arriveTime.substring(0, 5) : '',
    durationMin: raw.durationMin ?? 0,
  }
}

/** Compute minutes between two "HH:MM" or "HH:MM:SS" time strings, handling overnight trains */
function timeDiffMinutes(a: string, b: string): number {
  const toMin = (t: string) => {
    const parts = t.split(':')
    return parseInt(parts[0]) * 60 + parseInt(parts[1])
  }
  try {
    let diff = toMin(b) - toMin(a)
    if (diff < 0) diff += 24 * 60 // overnight train
    return diff
  } catch { return 0 }
}

/** Map raw train route detail to Train with stops */
export function mapToTrainDetail(raw: Record<string, any>): Train {
  const departTime = typeof raw.departTime === 'string' ? raw.departTime.substring(0, 5) : ''
  const arriveTime = typeof raw.arriveTime === 'string' ? raw.arriveTime.substring(0, 5) : ''
  const durationMin = raw.durationMin
    || (departTime && arriveTime ? timeDiffMinutes(departTime, arriveTime) : 0)
    || (raw.stops?.length > 1 ? timeDiffMinutes(raw.stops[0].departTime ?? raw.stops[0].arriveTime, raw.stops[raw.stops.length - 1].arriveTime ?? raw.stops[raw.stops.length - 1].departTime) : 0)
  return {
    no: raw.trainNo ?? '',
    type: (raw.trainType ?? 'K') as TrainType,
    from: raw.departStation ?? '',
    to: raw.arriveStation ?? '',
    departTime,
    arriveTime,
    durationMin,
    stops: (raw.stops ?? []).map((s: any) => ({
      station: s.stationName ?? '',
      arrive: typeof s.arriveTime === 'string' ? s.arriveTime.substring(0, 5) : '-',
      depart: typeof s.departTime === 'string' ? s.departTime.substring(0, 5) : '-',
      dwellMinutes: s.stayMin ?? 0,
    })),
  }
}

/** Train type display info */
export interface TrainTypeInfo {
  letter: TrainType
  label: string
  color: string
  speedKmh: number
}

export const TRAIN_TYPE_INFO: Record<TrainType, TrainTypeInfo> = {
  G: { letter: 'G', label: '高速动车', color: 'var(--signal-red)', speedKmh: 350 },
  D: { letter: 'D', label: '动车组', color: 'var(--signal-amber)', speedKmh: 250 },
  Z: { letter: 'Z', label: '直达特快', color: 'var(--signal-blue)', speedKmh: 160 },
  T: { letter: 'T', label: '特快', color: 'var(--signal-blue)', speedKmh: 140 },
  K: { letter: 'K', label: '快速', color: 'var(--signal-blue)', speedKmh: 120 },
  C: { letter: 'C', label: '城际', color: 'var(--signal-green)', speedKmh: 200 },
  S: { letter: 'S', label: '市郊', color: 'var(--signal-green)', speedKmh: 120 },
  L: { letter: 'L', label: '临客', color: 'var(--text-tertiary)', speedKmh: 100 },
  Y: { letter: 'Y', label: '旅游', color: 'var(--signal-caution)', speedKmh: 120 },
}
