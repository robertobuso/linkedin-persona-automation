import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { PersonaMetrics } from '@/lib/api'
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline'

interface PersonaInsightsProps {
  metrics?: PersonaMetrics
}

export function PersonaInsights({ metrics }: PersonaInsightsProps) {
  const insights = [
    {
      title: "Authority Building",
      description: "Your thought leadership content performs 23% better than industry posts",
      trend: "up" as const,
      confidence: 0.87
    },
    {
      title: "Engagement Peak",
      description: "Tuesday 10 AM posts receive 40% more engagement",
      trend: "up" as const,
      confidence: 0.92
    },
    {
      title: "Content Mix",
      description: "Technical deep-dives generate highest-quality discussions",
      trend: "neutral" as const,
      confidence: 0.78
    },
    {
      title: "Network Growth",
      description: "Consistent posting increased your network reach by 15%",
      trend: "up" as const,
      confidence: 0.84
    }
  ]

  const recommendations = [
    "Focus on thought leadership content during peak hours",
    "Increase technical content frequency by 20%",
    "Engage more with comments to boost algorithmic reach",
    "Consider LinkedIn Live sessions for authority building"
  ]

  return (
    <Card>
      <div className="p-6 space-y-6">
        <h3 className="text-lg font-semibold text-neural-700">AI Insights</h3>
        
        {/* Key Insights */}
        <div className="space-y-4">
          {insights.map((insight, index) => (
            <div key={index} className="border-l-4 border-ai-purple-500 pl-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{insight.title}</h4>
                {insight.trend === 'up' ? (
                  <ArrowTrendingUpIcon className="h-4 w-4 text-ml-green-500" />
                ) : insight.trend === 'down' ? (
                  <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
                ) : null}
              </div>
              <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
              <ConfidenceIndicator
                score={insight.confidence}
                label="Confidence"
                size="sm"
              />
            </div>
          ))}
        </div>

        {/* Recommendations */}
        <div className="pt-4 border-t border-gray-100">
          <h4 className="font-medium text-gray-900 mb-3">AI Recommendations</h4>
          <div className="space-y-2">
            {recommendations.map((rec, index) => (
              <div key={index} className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 bg-ai-purple-500 rounded-full mt-2 flex-shrink-0" />
                <p className="text-sm text-gray-600">{rec}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Overall Score */}
        <div className="pt-4 border-t border-gray-100">
          <div className="text-center">
            <div className="text-3xl font-bold text-neural-600 mb-2">
              {metrics?.authority_score || 87}
            </div>
            <div className="text-sm text-gray-600 mb-2">Overall Persona Score</div>
            <Badge variant="ai" size="sm">Top 15% in your industry</Badge>
          </div>
        </div>
      </div>
    </Card>
  )
}