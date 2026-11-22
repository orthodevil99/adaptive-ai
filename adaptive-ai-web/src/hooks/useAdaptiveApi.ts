import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { endpoints } from '../api/endpoints';
import type { AssistantRequest, FeedbackRequest, UserPreferences } from '../api/types';

export const useProjectInfo = () =>
  useQuery({ queryKey: ['projectInfo'], queryFn: endpoints.getProjectInfo, staleTime: 60_000 });

export const useHealth = () =>
  useQuery({ queryKey: ['health'], queryFn: endpoints.getHealth, refetchInterval: 15_000 });

export const useModelHealth = () =>
  useQuery({ queryKey: ['modelHealth'], queryFn: endpoints.getModelHealth, refetchInterval: 20_000 });

export const useAnalyticsSummary = () =>
  useQuery({ queryKey: ['analyticsSummary'], queryFn: endpoints.getAnalyticsSummary });

export const useUserSessions = (userId: string) =>
  useQuery({
    queryKey: ['sessions', userId],
    queryFn: () => endpoints.listUserSessions(userId),
  });

export const useSession = (sessionId: string, userId: string) =>
  useQuery({
    queryKey: ['session', sessionId, userId],
    queryFn: () => endpoints.getSession(sessionId, userId),
    retry: false,
  });

export const useDeleteSession = (userId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => endpoints.deleteSession(sessionId, userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sessions', userId] });
    },
  });
};

export const usePreferences = (userId: string) =>
  useQuery({
    queryKey: ['preferences', userId],
    queryFn: () => endpoints.getPreferences(userId),
  });

export const useUpdatePreferences = (userId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (prefs: UserPreferences) => endpoints.updatePreferences(userId, prefs),
    onSuccess: (data) => {
      qc.setQueryData(['preferences', userId], data);
    },
  });
};

export const useResetPreferences = (userId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => endpoints.resetPreferences(userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['preferences', userId] });
    },
  });
};

export const useAnalyze = () =>
  useMutation({
    mutationFn: (req: AssistantRequest) => endpoints.analyze(req),
  });

export const useRespond = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: AssistantRequest) => endpoints.respond(req),
    onSuccess: (data, vars) => {
      if (vars.user_id) {
        qc.invalidateQueries({ queryKey: ['sessions', vars.user_id] });
      }
      if (data.session_id && vars.user_id) {
        qc.invalidateQueries({ queryKey: ['session', data.session_id, vars.user_id] });
      }
    },
  });
};

export const useFeedback = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: FeedbackRequest) => endpoints.submitFeedback(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['analyticsSummary'] });
    },
  });
};
