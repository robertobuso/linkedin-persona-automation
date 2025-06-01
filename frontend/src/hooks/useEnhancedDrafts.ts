import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type PostDraft } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useRegenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, options }: { 
      draftId: string
      options: { style?: string; preserve_hashtags?: boolean }
    }) => api.regenerateDraft(draftId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      notify.success('Draft regenerated successfully!')
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
      notify.success(`Generated ${drafts.length} new drafts!`)
    },
    onError: (error: any) => {
      notify.error('Batch generation failed', error.message)
    }
  })
}