import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type ContentSource } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useContentSources() {
  return useQuery({
    queryKey: ['content-sources'],
    queryFn: () => api.getContentSources(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  })
}

export function useCreateContentSource() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: {
      name: string
      source_type: string
      url?: string
      description?: string
      is_active?: boolean
      check_frequency_hours?: number
    }) => api.createContentSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
      notify.success('Content source created successfully')
    },
    onError: (error: any) => {
      notify.error('Failed to create content source', error.message)
    }
  })
}

export function useUpdateContentSource() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string, data: Partial<ContentSource> }) => 
      api.updateContentSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
      notify.success('Content source updated successfully')
    },
    onError: (error: any) => {
      notify.error('Failed to update content source', error.message)
    }
  })
}

export function useDeleteContentSource() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: string) => api.deleteContentSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
      notify.success('Content source deleted successfully')
    },
    onError: (error: any) => {
      notify.error('Failed to delete content source', error.message)
    }
  })
}

export function useValidateFeedUrl() {
  return useMutation({
    mutationFn: (url: string) => api.validateFeedUrl(url),
    onError: (error: any) => {
      notify.error('Failed to validate feed URL', error.message)
    }
  })
}
