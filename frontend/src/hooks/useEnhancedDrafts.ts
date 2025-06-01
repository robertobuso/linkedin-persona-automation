import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type DraftWithContent } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useDrafts() {
  return useQuery({
    queryKey: ['drafts', 'all'],
    queryFn: () => api.getAllUserDrafts(),
    refetchInterval: 30 * 1000, // Refresh every 30 seconds for real-time updates
    refetchOnWindowFocus: true,
  })
}

export function useGenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ content_item_id, tone_style }: { 
      content_item_id: string
      tone_style: string 
    }) => api.generateDraftFromContent(content_item_id, tone_style),
    onSuccess: (newDraft) => {
      // Update drafts list immediately
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      // Also update content list to show draft_generated status
      queryClient.invalidateQueries({ queryKey: ['content'] })
      
      return newDraft
    },
    onError: (error: any) => {
      if (error.status === 409) {
        notify.warning('Draft already generated for this content')
      } else {
        notify.error('Generation Failed', error.message || 'Failed to generate draft')
      }
    }
  })
}

export function useRegenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, options }: { 
      draftId: string
      options: { tone_style?: string; preserve_hashtags?: boolean }
    }) => api.regenerateDraft(draftId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    },
    onError: (error: any) => {
      notify.error('Failed to regenerate draft', error.message)
    }
  })
}

export function useBatchGenerateDrafts() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (options: {
      max_posts?: number
      min_relevance_score?: number
      style?: string
    }) => api.batchGenerateDrafts(options),
    onSuccess: (drafts) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['content'] })
    },
    onError: (error: any) => {
      notify.error('Batch generation failed', error.message)
    }
  })
}

export function useDeleteDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (draftId: string) => api.deleteDraft(draftId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    },
    onError: (error: any) => {
      notify.error('Failed to delete draft', error.message)
    }
  })
}

export function useToneStyles() {
  return useQuery({
    queryKey: ['tone-styles'],
    queryFn: () => api.getToneStyles(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
