import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useDrafts() {
  return useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
    refetchInterval: 10 * 60 * 1000, // Refresh every 10 minutes
  })
}

export function useGenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (contentId: string) => api.generateDraft(contentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['draft-recommendations'] })
    },
    onError: (error: any) => {
      notify.error('Generation Failed', error.message || 'Failed to generate draft')
    }
  })
}

export function useUpdateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, data }: { draftId: string, data: any }) => 
      api.updateDraft(draftId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['draft-recommendations'] })
    }
  })
}

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
