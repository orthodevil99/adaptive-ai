import { apiRequest } from './client';
import type {
  AssistantRequest,
  AssistantResponse,
  BackendAnalysis,
  FeedbackRequest,
  SessionSummary,
  UserPreferences,
} from './types';

export const endpoints = {
  getProjectInfo: () => apiRequest<Record<string, unknown>>('/'),
  getHealth: () => apiRequest<Record<string, unknown>>('/health'),
  getModelHealth: () => apiRequest<Record<string, unknown>>('/health/model'),

  analyze: (body: AssistantRequest) =>
    apiRequest<BackendAnalysis>('/api/v1/assistant/analyze', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  respond: (body: AssistantRequest) =>
    apiRequest<AssistantResponse>('/api/v1/assistant/respond', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  submitFeedback: (body: FeedbackRequest) =>
    apiRequest<{ status: string; interaction_id: string; rating: number; adaptation: string }>(
      '/api/v1/assistant/feedback',
      { method: 'POST', body: JSON.stringify(body) }
    ),

  listUserSessions: (userId: string) =>
    apiRequest<{ user_id: string; sessions: SessionSummary[] }>(
      `/api/v1/users/${encodeURIComponent(userId)}/sessions`
    ),

  getSession: (sessionId: string, userId: string) =>
    apiRequest<{ session_id: string; messages: Array<Record<string, unknown>> }>(
      `/api/v1/sessions/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(userId)}`
    ),

  deleteSession: (sessionId: string, userId: string) =>
    apiRequest<{ status: string; session_id: string }>(
      `/api/v1/sessions/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(userId)}`,
      { method: 'DELETE' }
    ),

  getPreferences: (userId: string) =>
    apiRequest<{ user_id: string; preferences: UserPreferences }>(
      `/api/v1/preferences/${encodeURIComponent(userId)}`
    ),

  updatePreferences: (userId: string, prefs: UserPreferences) =>
    apiRequest<{ user_id: string; preferences: UserPreferences }>(
      `/api/v1/preferences/${encodeURIComponent(userId)}`,
      { method: 'PUT', body: JSON.stringify(prefs) }
    ),

  resetPreferences: (userId: string) =>
    apiRequest<{ status: string; user_id: string }>(
      `/api/v1/preferences/${encodeURIComponent(userId)}`,
      { method: 'DELETE' }
    ),

  getAnalyticsSummary: () => apiRequest<Record<string, unknown>>('/api/v1/analytics/summary'),
};
