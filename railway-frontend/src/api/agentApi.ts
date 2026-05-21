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
}

export const agentApi = {
  chat(req: AgentChatRequest) {
    return apiClient.post<unknown, AgentChatResponse>('/agent/chat', req)
  },
}
