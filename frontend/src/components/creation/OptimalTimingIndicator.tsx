import React from 'react'
import { ClockIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'

interface OptimalTimingIndicatorProps {
  timing: {
    recommended_time: string
    expected_engagement: number
    confidence: number
    reasoning: string
  }
}

export function OptimalTimingIndicator({ timing }: OptimalTimingIndicatorProps) {
  const recommendedDate = new Date(timing.recommended_time)
  
  return (
    <Card variant="prediction" className="p-4">
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <ClockIcon className="h-4 w-4 text-prediction-600" />
          <span className="font-medium text-prediction-700">Optimal Timing</span>
          <Badge variant="prediction" size="sm">
            <ArrowTrendingUpIcon className="h-3 w-3 mr-1" />
            {Math.round(timing.expected_engagement * 100)}% engagement
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-lg font-semibold text-prediction-700">
              {recommendedDate.toLocaleDateString()}
            </div>
            <div className="text-sm text-gray-600">
              {recommendedDate.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          </div>
          <div className="text-right">
            <ConfidenceIndicator
              score={timing.confidence}
              label="Confidence"
              size="sm"
            />
          </div>
        </div>

        <p className="text-xs text-gray-600 leading-relaxed">
          {timing.reasoning}
        </p>
      </div>
    </Card>
  )
}
