import apiClient from './client'
import type { RoutePlan, RouteConstraint } from '../types/route'

export const routePlanApi = {
  plan(constraint: RouteConstraint) {
    return apiClient.post<RoutePlan[]>('/plan', constraint)
  },
}
