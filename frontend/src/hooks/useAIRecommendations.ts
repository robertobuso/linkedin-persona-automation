import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useAIRecommendations() {
  return useQuery({
    queryKey: ['ai-recommendations'],
    queryFn: () => api.getAIRecommendations({
      includeConfidence: true,
      includeReasoning: true,
      limit: 10
    }),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider fresh for 2 minutes
  })
}

export function usePersonaMetrics(days: number = 30) {
  return useQuery({
    queryKey: ['persona-metrics', days],
    queryFn: () => api.getPersonaMetrics(days),
    refetchInterval: 15 * 60 * 1000, // Refresh every 15 minutes
  })
}

export function useDraftRecommendations() {
  return useQuery({
    queryKey: ['draft-recommendations'],
    queryFn: () => api.getDraftRecommendations(),
    refetchInterval: 10 * 60 * 1000, // Refresh every 10 minutes
  })
}

export function useEngagementPrediction(draftId: string) {
  return useQuery({
    queryKey: ['engagement-prediction', draftId],
    queryFn: () => api.getEngagementPrediction(draftId),
    enabled: !!draftId,
    staleTime: 10 * 60 * 1000, // Predictions valid for 10 minutes
  })
}

export function useTodaysContent() {
  return useQuery({
    queryKey: ['todays-content'],
    queryFn: () => api.getContentByMode('ai-selected'),
    refetchInterval: 30 * 60 * 1000, // Refresh every 30 minutes
  })
}

export function useEngagementQueue() {
  return useQuery({
    queryKey: ['engagement-queue'],
    queryFn: () => api.getCommentOpportunities({
      limit: 20,
      status: 'pending'
    }),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  })
}

export function useDrafts() {
  return useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
    refetchInterval: 10 * 60 * 1000,
  })
}
