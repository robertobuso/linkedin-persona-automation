import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useLinkedInStatus() {
  return useQuery({
    queryKey: ['linkedin-status'],
    queryFn: () => api.getLinkedInStatus(),
    refetchInterval: 60 * 1000, // Check every minute
  })
}

export function useConnectLinkedIn() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.connectLinkedIn(),
    onSuccess: () => {
      // Status will be updated when the OAuth window closes
      notify.info('Complete LinkedIn authorization in the popup window')
    },
    onError: (error: any) => {
      notify.error('Failed to initiate LinkedIn connection', error.message)
    }
  })
}

export function useDisconnectLinkedIn() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.disconnectLinkedIn(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['linkedin-status'] })
      notify.success('LinkedIn disconnected successfully')
    },
    onError: (error: any) => {
      notify.error('Failed to disconnect LinkedIn', error.message)
    }
  })
}

