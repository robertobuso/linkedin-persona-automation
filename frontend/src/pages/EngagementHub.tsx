import React, { useState, useEffect } from 'react'
import { useEngagementStore } from '@/stores/engagementStore'
import { EngagementOverview } from '@/components/engagement/EngagementOverview'
import { CommentOpportunityCard } from '@/components/engagement/CommentOpportunityCard'
import { EngagementFilters } from '@/components/engagement/EngagementFilters'
import { AutomationToggle } from '@/components/engagement/AutomationToggle'
import { Button } from '@/components/ui/Button'
import { MagnifyingGlassIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline'
import { LoadingPage, CardSkeleton } from '@/components/ui/LoadingStates'
import { notify } from '@/stores/uiStore'

export default function EngagementHub() {
  const [filterPriority, setFilterPriority] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('pending')
  
  const {
    commentQueue,
    isLoading,
    error,
    fetchCommentOpportunities,
    discoverNewPosts,
    clearError
  } = useEngagementStore()

  useEffect(() => {
    fetchCommentOpportunities({
      priority: filterPriority || undefined,
      status: filterStatus || undefined,
      limit: 50
    })
  }, [fetchCommentOpportunities, filterPriority, filterStatus])

  useEffect(() => {
    if (error) {
      notify.error('Engagement Error', error)
      clearError()
    }
  }, [error, clearError])

  const handleDiscoverPosts = async () => {
    try {
      await discoverNewPosts(50)
      notify.success('New engagement opportunities discovered!')
    } catch (error) {
      notify.error('Discovery failed')
    }
  }

  if (isLoading && commentQueue.length === 0) {
    return <LoadingPage message="Loading engagement opportunities..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Engagement Hub</h1>
          <p className="text-gray-600 mt-1">
            Manage your LinkedIn engagement opportunities
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <AutomationToggle />
          <Button 
            onClick={handleDiscoverPosts}
            variant="secondary"
            leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
          >
            Discover Posts
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <EngagementOverview />

      {/* Filters */}
      <EngagementFilters
        priority={filterPriority}
        status={filterStatus}
        onPriorityChange={setFilterPriority}
        onStatusChange={setFilterStatus}
      />

      {/* Opportunities List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : commentQueue.length === 0 ? (
          <div className="text-center py-12">
            <ChatBubbleLeftIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No opportunities found</h3>
            <p className="text-gray-600 mb-6">
              Try discovering new posts or adjusting your filters
            </p>
            <Button onClick={handleDiscoverPosts} variant="ai">
              Discover Opportunities
            </Button>
          </div>
        ) : (
          commentQueue.map(opportunity => (
            <CommentOpportunityCard 
              key={opportunity.id}
              opportunity={opportunity}
            />
          ))
        )}
      </div>
    </div>
  )
}
