import React from 'react'
import { ChatBubbleLeftIcon, ClockIcon, FireIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/LoadingStates'
import { EngagementOpportunity } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

interface EngagementOpportunitiesProps {
  opportunities?: EngagementOpportunity[]
  loading?: boolean
}

export function EngagementOpportunities({ opportunities = [], loading }: EngagementOpportunitiesProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <Card>
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/2" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    )
  }

  const highPriorityOpps = opportunities.filter(opp => 
    opp.priority === 'urgent' || opp.priority === 'high'
  )

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
            <ChatBubbleLeftIcon className="h-5 w-5" />
            <span>Engagement Opportunities</span>
          </h3>
          <Badge variant="prediction">
            {highPriorityOpps.length} High Priority
          </Badge>
        </div>

        {opportunities.length === 0 ? (
          <div className="text-center py-8">
            <ChatBubbleLeftIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No engagement opportunities found</p>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => navigate('/engagement')}
            >
              Discover Opportunities
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {opportunities.slice(0, 3).map((opportunity) => (
              <OpportunityPreview key={opportunity.id} opportunity={opportunity} />
            ))}
            
            <div className="pt-4 border-t border-gray-100">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => navigate('/engagement')}
              >
                View All Opportunities ({opportunities.length})
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

function OpportunityPreview({ opportunity }: { opportunity: EngagementOpportunity }) {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive'
      case 'high': return 'warning'
      case 'medium': return 'secondary'
      default: return 'neutral'
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 line-clamp-1">
              {opportunity.target_author}
            </h4>
            <p className="text-sm text-gray-600 line-clamp-2 mt-1">
              {opportunity.target_content.substring(0, 100)}...
            </p>
          </div>
          <Badge variant={getPriorityColor(opportunity.priority)} size="sm">
            {opportunity.priority}
          </Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <FireIcon className="h-3 w-3" />
            <span>{opportunity.relevance_score || 0}% match</span>
            <span>•</span>
            <ClockIcon className="h-3 w-3" />
            <span>2h ago</span>
          </div>
          
          <Button size="sm" variant="outline">
            Engage
          </Button>
        </div>
      </div>
    </div>
  )
}
