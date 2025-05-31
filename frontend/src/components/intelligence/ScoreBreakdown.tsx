import React from 'react'
import { ContentScore } from '@/lib/api'
import { ConfidenceIndicator } from './ConfidenceIndicator'

interface ScoreBreakdownProps {
  scores: ContentScore
  className?: string
}

export function ScoreBreakdown({ scores, className }: ScoreBreakdownProps) {
  const scoreItems = [
    {
      label: 'Relevance',
      value: scores.relevance_score,
      description: 'How relevant this content is to your audience'
    },
    {
      label: 'Source Credibility',
      value: scores.source_credibility,
      description: 'Trustworthiness and authority of the source'
    },
    {
      label: 'Timeliness',
      value: scores.timeliness_score,
      description: 'How current and timely this content is'
    },
    {
      label: 'Engagement Potential',
      value: scores.engagement_potential,
      description: 'Likelihood to generate engagement'
    }
  ]

  return (
    <div className={className}>
      <div className="space-y-3">
        {/* Overall Score */}
        <div className="flex items-center justify-between p-3 bg-neural-50 rounded-lg">
          <span className="font-semibold text-neural-700">Overall Score</span>
          <span className="text-xl font-bold text-neural-600">
            {Math.round(scores.composite_score)}/100
          </span>
        </div>

        {/* Individual Scores */}
        <div className="space-y-2">
          {scoreItems.map((item) => (
            <div key={item.label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.label}</span>
                <span className="font-medium text-gray-900">
                  {Math.round(item.value)}/100
                </span>
              </div>
              <ConfidenceIndicator
                score={item.value / 100}
                showPercentage={false}
                size="sm"
              />
            </div>
          ))}
        </div>

        {/* Confidence */}
        <div className="pt-2 border-t border-gray-100">
          <ConfidenceIndicator
            score={scores.confidence}
            label="Score Confidence"
            size="sm"
          />
        </div>
      </div>
    </div>
  )
}
