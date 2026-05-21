import apiClient from './client'
import type { AgentInstruction } from '../types/agent'

export interface AgentChatRequest {
  session_id?: string
  message: string
}

export interface AgentChatResponse {
  session_id: string
  text: string
  instructions: AgentInstruction[]
  suggestions: string[]
  station?: Record<string, unknown> | null
  routes?: Record<string, unknown>[] | null
}

export const agentApi = {
  chat(req: AgentChatRequest) {
    return apiClient.post<unknown, AgentChatResponse>('/agent/chat', req)
  },
}
