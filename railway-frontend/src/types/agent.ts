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
