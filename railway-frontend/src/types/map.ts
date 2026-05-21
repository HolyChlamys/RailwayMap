/** Map viewport state (for Pinia store — NOT the MapLibre instance) */
export interface MapViewport {
  center: [number, number]  // [lng, lat]
  zoom: number
  bearing: number
  pitch: number
}

/** Layer visibility state */
export interface LayerVisibility {
  /** Station layers by type */
  stations: Record<string, boolean>
  /** Railway line layers by category — keys match backend RailwayCategory codes */
  lines: Record<string, boolean>
}

/** Entry animation phase for staggered reveal */
export type MapEntryPhase = 'idle' | 'background' | 'lines' | 'stations' | 'ui' | 'complete'

/** Map style mode */
export type MapStyleMode = 'light' | 'dark' | 'satellite'
