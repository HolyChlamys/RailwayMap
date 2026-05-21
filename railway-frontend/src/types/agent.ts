import type { RoutePlan } from './route'

/** Chat message role */
export type MessageRole = 'user' | 'agent'

/** Structured content within an agent message */
export interface AgentMessageContent {
  /** Plain text body */
  text: string
  /** Optional route plans embedded in the message */
  routePlans?: RoutePlan[]
  /** Optional station reference */
  stationId?: string
  /** Optional train reference */
  trainNo?: string
  /** Optional city reference */
  city?: string
  /** Frontend instructions for map/panel actions */
  instructions?: AgentInstruction[]
  /** Follow-up suggestion chips */
  suggestions?: string[]
}

/** A single chat message */
export interface ChatMessage {
  id: string
  role: MessageRole
  content: AgentMessageContent
  timestamp: Date
}

/** Agent panel open/close state */
export type AgentPanelState = 'closed' | 'open'

/** Quick-chip suggestion */
export interface QuickSuggestion {
  label: string
  prompt: string
}

/** Frontend instruction dispatched from agent response */
export interface AgentInstruction {
  action: 'flyToStation' | 'highlightTrain' | 'highlightRoutes' | 'highlightIsochrone'
    | 'openPanel' | 'openModal' | 'clearHighlights'
  [key: string]: unknown
}

export interface FlyToStationInstruction extends AgentInstruction {
  action: 'flyToStation'
  stationId: string
}

export interface HighlightTrainInstruction extends AgentInstruction {
  action: 'highlightTrain'
  trainNo: string
}

export interface HighlightRoutesInstruction extends AgentInstruction {
  action: 'highlightRoutes'
  routeIds: string[]
}

export interface HighlightIsochroneInstruction extends AgentInstruction {
  action: 'highlightIsochrone'
  stationId: string
}

export interface OpenPanelInstruction extends AgentInstruction {
  action: 'openPanel'
  panel: 'station' | 'train' | 'routePlan'
}

export interface OpenModalInstruction extends AgentInstruction {
  action: 'openModal'
  modal: 'timetable'
  stationId: string
}
