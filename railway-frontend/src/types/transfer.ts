export interface TransferRequest {
  from: string
  to: string
  date: string
  maxTransfers: number
  preference: 'least_time' | 'least_transfer' | 'night_train' | 'least_price'
  maxResults: number
}

export interface TransferResult {
  id: string
  totalTimeMin: number
  totalPriceYuan: number
  transferCount: number
  score: number
  segments: TransferSegment[]
}

export interface TransferSegment {
  trainNo: string
  trainType: string
  fromStation: string
  toStation: string
  departTime: string
  arriveTime: string
  durationMin: number
  price: {
    second: number
    first: number
    business: number
    softSleeperDown: number
    hardSleeperDown: number
    hardSeat: number
  }
}
