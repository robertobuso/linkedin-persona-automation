import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, DraftWithContent } from '@/lib/api'
import { notify } from '@/stores/uiStore'

// Get all drafts
export function useDrafts() {
  return useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getAllUserDrafts(),
    refetchInterval: 30 * 1000,
    refetchOnWindowFocus: true,
  })
}

// Generate new draft from content
export function useGenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ content_item_id, tone_style }: { 
      content_item_id: string
      tone_style: string 
    }) => api.generateDraftFromContent(content_item_id, tone_style),
    onSuccess: (newDraft) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
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

// Regenerate existing draft
export function useRegenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, options }: { 
      draftId: string
      options: { tone_style: string; preserve_hashtags?: boolean }
    }) => api.regenerateDraft(draftId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    },
    onError: (error: any) => {
      notify.error('Failed to regenerate draft', error.message)
    }
  })
}

// Batch generate drafts
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

// Update draft
export function useUpdateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, data }: { draftId: string, data: any }) => 
      api.updateDraft(draftId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    }
  })
}

// Publish draft
export function usePublishDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, scheduledFor }: { draftId: string, scheduledFor?: string }) => 
      api.publishDraft(draftId, scheduledFor),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      notify.success('Draft published successfully!')
    },
    onError: (error: any) => {
      notify.error('Publishing Failed', error.message || 'Failed to publish draft')
    }
  })
}

// Delete draft
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

// Get tone styles
export function useToneStyles() {
  return useQuery({
    queryKey: ['tone-styles'],
    queryFn: () => api.getToneStyles(),
    staleTime: 5 * 60 * 1000,
  })
}