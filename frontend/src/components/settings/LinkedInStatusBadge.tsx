import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/lib/api'

export function LinkedInStatusBadge() {
  const { data: status } = useQuery({
    queryKey: ['linkedin-status'],
    queryFn: () => api.getLinkedInStatus(),
    refetchInterval: 60 * 1000, // Check every minute
  })

  if (!status) return null

  return (
    <Badge 
      variant={status.connected ? 'success' : 'secondary'}
      size="sm"
    >
      LinkedIn {status.connected ? 'Connected' : 'Disconnected'}
    </Badge>
  )
}