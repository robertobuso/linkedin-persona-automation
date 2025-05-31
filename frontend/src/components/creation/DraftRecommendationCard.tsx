import React from 'react'
import { 
  PaperAirplaneIcon, 
  PencilIcon, 
  ClockIcon, 
  XMarkIcon,
  CogIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { ScoreBreakdown } from '@/components/intelligence/ScoreBreakdown'
import { PredictionCard } from '@/components/intelligence/PredictionCard'
import { ReasoningPanel } from './ReasoningPanel'
import { OptimalTimingIndicator } from './OptimalTimingIndicator'
import { ActionButton } from './ActionButton'
import { ScoredRecommendation } from '@/lib/api'

interface DraftRecommendationCardProps {
  recommendation: ScoredRecommendation
}

export function DraftRecommendationCard({ recommendation }: DraftRecommendationCardProps) {
  const actionConfig = getActionConfig(recommendation.action)
  
  return (
    <Card hover="lift" className="p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-4">
          {/* Header */}
          <div className="flex items-center space-x-3">
            <Badge 
              variant={actionConfig.variant}
              icon={<actionConfig.icon className="h-3 w-3" />}
              size="lg"
            >
              {actionConfig.label}
            </Badge>
            <div className="text-2xl font-bold text-neural-600">
              {Math.round(recommendation.score * 100)}%
            </div>
            <ConfidenceIndicator
              score={recommendation.score}
              label="Recommendation Score"
              size="sm"
            />
          </div>

          {/* Content Preview */}
          <div>
            <h3 className="text-lg font-semibold text-neural-700 mb-2">
              {recommendation.draft?.title || 'Draft Content'}
            </h3>
            <p className="text-gray-600 line-clamp-3">
              {recommendation.draft?.content.substring(0, 200)}...
            </p>
          </div>

          {/* Score Breakdown */}
          <ScoreBreakdown scores={recommendation.content_score} />

          {/* Optimal Timing */}
          {recommendation.optimal_timing && (
            <OptimalTimingIndicator timing={recommendation.optimal_timing} />
          )}

          {/* AI Reasoning */}
          <ReasoningPanel reasoning={recommendation.reasoning} />
        </div>

        {/* Actions */}
        <div className="ml-6 space-y-2">
          <ActionButton 
            action={recommendation.action}
            draftId={recommendation.draft_id}
          />
          <Button 
            size="sm" 
            variant="ghost"
            leftIcon={<CogIcon className="h-4 w-4" />}
          >
            Edit
          </Button>
        </div>
      </div>

      {/* Predicted Performance */}
      {recommendation.estimated_performance && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <PredictionCard 
            prediction={recommendation.estimated_performance}
            compact
          />
        </div>
      )}
    </Card>
  )
}

function getActionConfig(action: string) {
  const configs = {
    post_now: {
      icon: PaperAirplaneIcon,
      label: 'Post Now',
      variant: 'success' as const
    },
    review_and_edit: {
      icon: PencilIcon,
      label: 'Review & Edit',
      variant: 'warning' as const
    },
    schedule_later: {
      icon: ClockIcon,
      label: 'Schedule Later',
      variant: 'default' as const
    },
    skip: {
      icon: XMarkIcon,
      label: 'Skip',
      variant: 'secondary' as const
    }
  }

  return configs[action as keyof typeof configs] || configs.skip
}
