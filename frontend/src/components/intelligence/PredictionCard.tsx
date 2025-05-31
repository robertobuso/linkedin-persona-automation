import React from 'react'
import { ArrowTrendingUpIcon, EyeIcon, HeartIcon, ChatBubbleLeftIcon, ShareIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from './ConfidenceIndicator'
import { EngagementPrediction } from '@/lib/api'

interface PredictionCardProps {
  prediction: EngagementPrediction
  compact?: boolean
  className?: string
}

export function PredictionCard({ prediction, compact = false, className }: PredictionCardProps) {
  const metrics = [
    {
      icon: HeartIcon,
      label: 'Likes',
      value: prediction.predicted_likes,
      color: 'text-red-500'
    },
    {
      icon: ChatBubbleLeftIcon,
      label: 'Comments',
      value: prediction.predicted_comments,
      color: 'text-blue-500'
    },
    {
      icon: ShareIcon,
      label: 'Shares',
      value: prediction.predicted_shares,
      color: 'text-green-500'
    },
    {
      icon: EyeIcon,
      label: 'Views',
      value: prediction.predicted_views,
      color: 'text-purple-500'
    }
  ]

  return (
    <Card intelligence className={className}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ArrowTrendingUpIcon className="h-5 w-5 text-neural-600" />
            <h4 className="font-semibold text-neural-700">Engagement Prediction</h4>
          </div>
          <Badge variant="ai" size="sm">
            {prediction.model_type}
          </Badge>
        </div>
        
        {/* Engagement Rate */}
        <div className="text-center py-2">
          <div className="text-3xl font-bold text-neural-600">
            {(prediction.predicted_engagement_rate * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Expected Engagement Rate</div>
        </div>

        {/* Metrics Grid */}
        {!compact && (
          <div className="grid grid-cols-2 gap-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-center">
                <div className="flex items-center justify-center mb-1">
                  <metric.icon className={cn('h-4 w-4', metric.color)} />
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {metric.value.toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">{metric.label}</div>
              </div>
            ))}
          </div>
        )}
        
        {/* Confidence */}
        <div className={cn(compact ? 'pt-2' : 'pt-4', 'border-t border-gray-100')}>
          <ConfidenceIndicator 
            score={prediction.confidence}
            label="Prediction Confidence"
            size="sm"
          />
        </div>

        {/* Model info */}
        {!compact && (
          <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
            <div className="flex justify-between">
              <span>Model: {prediction.model_type}</span>
              <span>Predicted: {new Date(prediction.predicted_at).toLocaleDateString()}</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
