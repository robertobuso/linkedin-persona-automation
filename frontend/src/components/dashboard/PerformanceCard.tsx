import React from 'react'
import { ArrowTrendingUpIcon,ArrowTrendingDownIcon, MinusIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/LoadingStates'

interface PerformanceCardProps {
  title: string
  metric?: any
  type: 'prediction' | 'pipeline' | 'growth'
  loading?: boolean
}

export function PerformanceCard({ title, metric, type, loading }: PerformanceCardProps) {
  if (loading) {
    return (
      <Card>
        <div className="space-y-4">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-full" />
        </div>
      </Card>
    )
  }

  const renderMetric = () => {
    switch (type) {
      case 'prediction':
        return (
          <div className="space-y-2">
            <div className="text-3xl font-bold text-neural-600">
              {metric?.engagement_rate ? `${(metric.engagement_rate * 100).toFixed(1)}%` : '8.2%'}
            </div>
            <div className="text-sm text-gray-600">Expected next post engagement</div>
            <div className="flex items-center space-x-1 text-ml-green-600">
              <ArrowTrendingUpIcon className="h-4 w-4" />
              <span className="text-sm">+2.1% vs average</span>
            </div>
          </div>
        )
      
      case 'pipeline':
        return (
          <div className="space-y-2">
            <div className="text-3xl font-bold text-neural-600">
              {metric?.ready_drafts || 3}
            </div>
            <div className="text-sm text-gray-600">Ready to publish</div>
            <div className="flex items-center space-x-1 text-prediction-600">
              <MinusIcon className="h-4 w-4" />
              <span className="text-sm">2 in review</span>
            </div>
          </div>
        )
      
      case 'growth':
        return (
          <div className="space-y-2">
            <div className="text-3xl font-bold text-neural-600">
              {metric?.authority_score || 87}
            </div>
            <div className="text-sm text-gray-600">Authority Score</div>
            <div className="flex items-center space-x-1 text-ml-green-600">
              <ArrowTrendingUpIcon className="h-4 w-4" />
              <span className="text-sm">+5 this week</span>
            </div>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <Card hover="lift" className="p-6">
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {renderMetric()}
      </div>
    </Card>
  )
}
