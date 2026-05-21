/** A GeoJSON LineString coordinate array [lng, lat][] */
export type LineStringCoords = [number, number][]

/** A segment within a route plan — either a train ride or a transfer */
export interface RouteSegment {
  /** Train number (null for transfer/wait segments) */
  trainNo: string | null
  from: string
  to: string
  depart: string   // "HH:MM"
  arrive: string   // "HH:MM"
  /** Coordinates for this segment (null for transfer) */
  coordinates: LineStringCoords | null
}

/** A complete route plan (may contain multiple segments) */
export interface RoutePlan {
  id: string
  label: string           // "方案一"
  segments: RouteSegment[]
  totalDurationMin: number
  transfers: number
  /** Color from the route palette for map rendering */
  color: string
}

/** Constraints for route planning */
export interface RouteConstraint {
  origin: string
  destination: string
  waypoints?: string[]          // forced transfer stations
  preferTrainTypes?: string[]   // ['G', 'D']
  avoidStations?: string[]
  minTransferTimeMin?: number
  maxTransfers?: number
  departAfter?: string          // "HH:MM"
  arriveBefore?: string         // "HH:MM"
}

/** Route palette — 6 equidistant HSL colors */
export const ROUTE_PALETTE = [
  'var(--route-1)',
  'var(--route-2)',
  'var(--route-3)',
  'var(--route-4)',
  'var(--route-5)',
  'var(--route-6)',
] as const
