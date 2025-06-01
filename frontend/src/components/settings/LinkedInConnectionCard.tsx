import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  LinkIcon,
  UserCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { api, type LinkedInStatus } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { formatDistanceToNow } from 'date-fns'

export function LinkedInConnectionCard() {
  const [isConnecting, setIsConnecting] = useState(false)
  const queryClient = useQueryClient()

  const { data: status, isLoading } = useQuery({
    queryKey: ['linkedin-status'],
    queryFn: () => api.getLinkedInStatus(),
    refetchInterval: 30 * 1000, // Check every 30 seconds
  })

  const disconnectMutation = useMutation({
    mutationFn: () => api.disconnectLinkedIn(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['linkedin-status'] })
      notify.success('LinkedIn disconnected successfully')
    },
    onError: (error: any) => {
      notify.error('Failed to disconnect LinkedIn', error.message)
    }
  })

  const handleConnect = async () => {
    try {
      setIsConnecting(true)
      const response = await api.connectLinkedIn()
      
      // Open LinkedIn OAuth in new window
      const authWindow = window.open(
        response.authorization_url,
        'linkedin-auth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      )

      // Poll for window closure (user completed auth)
      const pollForCompletion = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(pollForCompletion)
          setIsConnecting(false)
          
          // Refresh status after auth completion
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ['linkedin-status'] })
          }, 1000)
        }
      }, 1000)

    } catch (error: any) {
      setIsConnecting(false)
      notify.error('Failed to connect LinkedIn', error.message)
    }
  }

  const handleDisconnect = () => {
    disconnectMutation.mutate()
  }

  if (isLoading) {
    return (
      <Card>
        <div className="p-6">
          <div className="animate-pulse flex items-center space-x-4">
            <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              {status?.profile?.picture ? (
                <img
                  src={status.profile.picture}
                  alt="LinkedIn Profile"
                  className="h-12 w-12 rounded-full"
                />
              ) : (
                <UserCircleIcon className="h-12 w-12 text-gray-400" />
              )}
              
              {status?.connected && (
                <CheckCircleIcon className="h-5 w-5 text-ml-green-500 absolute -bottom-1 -right-1 bg-white rounded-full" />
              )}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-semibold text-neural-700">
                  LinkedIn Connection
                </h3>
                <Badge 
                  variant={status?.connected ? 'success' : 'secondary'}
                  size="sm"
                >
                  {status?.connected ? 'Connected' : 'Not Connected'}
                </Badge>
              </div>
              
              {status?.connected ? (
                <div className="text-sm text-gray-600">
                  <p className="font-medium">{status.profile?.name || 'LinkedIn User'}</p>
                  {status.profile?.email && (
                    <p className="text-xs">{status.profile.email}</p>
                  )}
                  {status.token_expires_at && (
                    <p className="text-xs text-gray-500">
                      Token expires {formatDistanceToNow(new Date(status.token_expires_at), { addSuffix: true })}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-600">
                  Connect your LinkedIn account to enable publishing and engagement features
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {status?.connected ? (
              <Button
                variant="outline"
                onClick={handleDisconnect}
                loading={disconnectMutation.isPending}
                leftIcon={<ExclamationTriangleIcon className="h-4 w-4" />}
              >
                Disconnect
              </Button>
            ) : (
              <Button
                variant="ai"
                onClick={handleConnect}
                loading={isConnecting}
                leftIcon={<LinkIcon className="h-4 w-4" />}
              >
                Connect LinkedIn
              </Button>
            )}
          </div>
        </div>

        {!status?.connected && (
          <div className="mt-4 p-4 bg-neural-50 rounded-lg">
            <h4 className="text-sm font-medium text-neural-700 mb-2">
              Why connect LinkedIn?
            </h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Publish AI-generated posts directly to your profile</li>
              <li>• Engage with relevant content automatically</li>
              <li>• Track performance metrics and analytics</li>
              <li>• Schedule posts for optimal engagement times</li>
            </ul>
          </div>
        )}
      </div>
    </Card>
  )
}