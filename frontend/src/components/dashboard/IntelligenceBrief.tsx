import React from 'react'
import { CpuChipIcon as BrainIcon, ChartBarIcon, ClockIcon, ChartPieIcon as TargetIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { AIRecommendation, PersonaMetrics } from '@/lib/api'

interface IntelligenceBriefProps {
  recommendations: AIRecommendation[]
  metrics?: PersonaMetrics
}

export function IntelligenceBrief({ recommendations, metrics }: IntelligenceBriefProps) {
  const topRecommendation = recommendations?.[0]
  
  return (
    <Card intelligence className="relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-neural-100 to-ml-green-100 rounded-full opacity-50 transform translate-x-16 -translate-y-16" />
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-ai-purple-100 to-prediction-100 rounded-full opacity-30 transform -translate-x-12 translate-y-12" />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-neural-700 flex items-center space-x-2">
            <BrainIcon className="h-8 w-8 text-ai-purple-600" />
            <span>Today's Intelligence Brief</span>
          </h2>
          <ConfidenceIndicator 
            score={topRecommendation?.confidence || 0.8}
            label="Overall Confidence"
            size="lg"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <IntelligenceMetric
            icon={BrainIcon}
            label="AI-Selected Content"
            value="3 articles"
            change="+2 from yesterday"
            trend="up"
          />
          <IntelligenceMetric
            icon={ChartBarIcon}
            label="Engagement Opportunities"
            value="5 high-value"
            change="2 urgent priority"
            trend="neutral"
          />
          <IntelligenceMetric
            icon={ClockIcon}
            label="Optimal Window"
            value="Today 10:15 AM"
            change="87% success rate"
            trend="up"
          />
          <IntelligenceMetric
            icon={TargetIcon}
            label="Persona Focus"
            value="Thought Leadership"
            change={`Authority: ${metrics?.authority_score || 87}/100`}
            trend="up"
          />
        </div>

        {/* Top Recommendation */}
        {topRecommendation && (
          <div className="mt-6 p-4 bg-gradient-to-r from-ai-purple-50 to-ml-green-50 rounded-lg border border-ai-purple-200">
            <h3 className="font-semibold text-neural-700 mb-2">Priority Recommendation</h3>
            <p className="text-gray-600 text-sm">{topRecommendation.reasoning}</p>
          </div>
        )}
      </div>
    </Card>
  )
}

interface IntelligenceMetricProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  change: string
  trend?: 'up' | 'down' | 'neutral'
}

function IntelligenceMetric({ icon: Icon, label, value, change, trend = 'neutral' }: IntelligenceMetricProps) {
  const trendColors = {
    up: 'text-ml-green-600',
    down: 'text-red-500',
    neutral: 'text-gray-500'
  }

  return (
    <div className="text-center space-y-2">
      <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm border border-gray-200">
        <Icon className="h-6 w-6 text-neural-600" />
      </div>
      <div>
        <div className="text-lg font-bold text-neural-700">{value}</div>
        <div className="text-sm text-gray-600">{label}</div>
        <div className={`text-xs ${trendColors[trend]}`}>{change}</div>
      </div>
    </div>
  )
}
