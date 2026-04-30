export interface MapViewState {
  center: [number, number]
  zoom: number
  bearing: number
  pitch: number
}

export interface LayerVisibility {
  railways: boolean
  stations: boolean
  [category: string]: boolean
}
