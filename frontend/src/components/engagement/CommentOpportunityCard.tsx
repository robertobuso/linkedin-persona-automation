import React, { useState } from 'react'
import { 
  ChatBubbleLeftIcon, 
  LinkIcon, 
  ClockIcon, 
  UserIcon,
  SparklesIcon,
  CheckIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { EngagementOpportunity } from '@/lib/api'
import { useEngagementStore } from '@/stores/engagementStore'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'

interface CommentOpportunityCardProps {
  opportunity: EngagementOpportunity
}

export function CommentOpportunityCard({ opportunity }: CommentOpportunityCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [customComment, setCustomComment] = useState('')
  const { createComment, isLoading } = useEngagementStore()

  const handleEngage = async (useCustomComment: boolean = false) => {
    try {
      await createComment({
        opportunity_id: opportunity.id,
        comment_text: useCustomComment ? customComment : opportunity.suggested_comment
      })
      notify.success('Comment posted successfully!')
    } catch (error) {
      notify.error('Failed to post comment')
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive'
      case 'high': return 'warning'
      case 'medium': return 'secondary'
      default: return 'neutral'
    }
  }

  return (
    <Card hover="lift" className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <UserIcon className="h-5 w-5 text-neural-600" />
              <h3 className="font-semibold text-neural-700">{opportunity.target_author}</h3>
              <Badge variant={getPriorityColor(opportunity.priority)} size="sm">
                {opportunity.priority}
              </Badge>
              {opportunity.relevance_score && (
                <Badge variant="ai" size="sm">
                  {opportunity.relevance_score}% match
                </Badge>
              )}
            </div>
            
            <p className="text-gray-600 line-clamp-3">
              {opportunity.target_content}
            </p>
          </div>
        </div>

        {/* AI Analysis */}
        {opportunity.ai_analysis && (
          <div className="bg-ai-purple-50 rounded-lg p-4 border border-ai-purple-200">
            <div className="flex items-center space-x-2 mb-2">
              <SparklesIcon className="h-4 w-4 text-ai-purple-600" />
              <span className="font-medium text-ai-purple-700">AI Analysis</span>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              {opportunity.engagement_reason}
            </p>
            {opportunity.ai_analysis.confidence_score && (
              <ConfidenceIndicator
                score={opportunity.ai_analysis.confidence_score}
                label="Success Probability"
                size="sm"
              />
            )}
          </div>
        )}

        {/* Suggested Comment */}
        {opportunity.suggested_comment && (
          <div className="bg-ml-green-50 rounded-lg p-4 border border-ml-green-200">
            <div className="flex items-center space-x-2 mb-2">
              <ChatBubbleLeftIcon className="h-4 w-4 text-ml-green-600" />
              <span className="font-medium text-ml-green-700">Suggested Comment</span>
            </div>
            <p className="text-sm text-gray-700">
              "{opportunity.suggested_comment}"
            </p>
          </div>
        )}

        {/* Custom Comment Input */}
        {isExpanded && (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Custom Comment (Optional)
            </label>
            <textarea
              value={customComment}
              onChange={(e) => setCustomComment(e.target.value)}
              placeholder="Write your own comment..."
              className="w-full p-3 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
              rows={3}
            />
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <ClockIcon className="h-4 w-4" />
            <span>{formatDistanceToNow(new Date(opportunity.created_at), { addSuffix: true })}</span>
          </div>
          {opportunity.context_tags && opportunity.context_tags.length > 0 && (
            <div className="flex items-center space-x-1">
              <span>Tags:</span>
              <span>{opportunity.context_tags.join(', ')}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="ai"
              onClick={() => handleEngage(false)}
              loading={isLoading}
              leftIcon={<ChatBubbleLeftIcon className="h-4 w-4" />}
            >
              Use AI Comment
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Simple' : 'Custom'}
            </Button>

            {isExpanded && customComment && (
              <Button
                size="sm"
                variant="default"
                onClick={() => handleEngage(true)}
                loading={isLoading}
                leftIcon={<CheckIcon className="h-4 w-4" />}
              >
                Post Custom
              </Button>
            )}
          </div>

          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => window.open(opportunity.target_url, '_blank')}
              leftIcon={<LinkIcon className="h-4 w-4" />}
            >
              View Post
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
