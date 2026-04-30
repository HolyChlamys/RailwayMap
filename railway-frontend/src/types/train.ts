export interface TrainSearchResult {
  trainNo: string
  trainType: string
  departStation: string
  arriveStation: string
  departTime: string
  arriveTime: string
  durationMin: number
}

export interface TrainRouteDetail {
  trainNo: string
  trainType: string
  departStation: string
  arriveStation: string
  departTime: string
  arriveTime: string
  durationMin: number
  stops: TrainStopInfo[]
  segmentsGeoJson: object | null
  fares: FareInfo[]
}

export interface TrainStopInfo {
  seq: number
  stationName: string
  stationId: number
  lon: number
  lat: number
  arriveTime: string
  departTime: string
  stayMin: number
}

export interface FareInfo {
  fromStation: string
  toStation: string
  priceSecond: number
  priceFirst: number
  priceBusiness: number
  priceSoftSleeperDown: number
  priceHardSleeperDown: number
  priceHardSeat: number
}
