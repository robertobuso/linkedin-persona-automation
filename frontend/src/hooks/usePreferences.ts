import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type ContentPreferences } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useUserPreferences() {
  return useQuery({
    queryKey: ['user-preferences'],
    queryFn: () => api.getUserPreferences(),
    retry: false, // Don't retry if user has no preferences yet
  })
}

export function useSaveQuickPreferences() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: {
      jobRole: string
      industry: string
      interests: string[]
      customPrompt: string
      relevanceThreshold: number
      maxArticlesPerDay: number
    }) => api.saveQuickPreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] })
      queryClient.invalidateQueries({ queryKey: ['content'] }) // Refresh content with new preferences
      notify.success('Preferences saved successfully!')
    },
    onError: (error: any) => {
      notify.error('Failed to save preferences', error.message)
    }
  })
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: Partial<ContentPreferences>) => api.updatePreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] })
      queryClient.invalidateQueries({ queryKey: ['content'] })
      notify.success('Preferences updated successfully!')
    },
    onError: (error: any) => {
      notify.error('Failed to update preferences', error.message)
    }
  })
}