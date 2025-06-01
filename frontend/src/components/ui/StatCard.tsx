import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface StatCardProps {
  title: string
  value: string | number
  change?: {
    value: number
    type: 'increase' | 'decrease' | 'neutral'
    period?: string
  }
  icon?: React.ComponentType<{ className?: string }>
  variant?: 'default' | 'intelligence' | 'ai' | 'prediction'
  loading?: boolean
}

export function StatCard({ 
  title, 
  value, 
  change, 
  icon: Icon, 
  variant = 'default',
  loading = false 
}: StatCardProps) {
  if (loading) {
    return (
      <Card variant={variant} className="animate-pulse">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2 flex-1">
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
            {Icon && <div className="h-8 w-8 bg-gray-200 rounded"></div>}
          </div>
          {change && <div className="h-4 bg-gray-200 rounded w-1/3 mt-2"></div>}
        </div>
      </Card>
    )
  }

  const getChangeColor = (type: string) => {
    switch (type) {
      case 'increase': return 'text-ml-green-600'
      case 'decrease': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'increase': return '↗'
      case 'decrease': return '↘'
      default: return '→'
    }
  }

  return (
    <Card variant={variant} hover="glow">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-neural-700 mt-1">{value}</p>
          </div>
          {Icon && (
            <div className="flex-shrink-0">
              <Icon className="h-8 w-8 text-ai-purple-500" />
            </div>
          )}
        </div>
        
        {change && (
          <div className="mt-4">
            <span className={`text-sm font-medium ${getChangeColor(change.type)}`}>
              {getChangeIcon(change.type)} {Math.abs(change.value)}%
            </span>
            {change.period && (
              <span className="text-xs text-gray-500 ml-1">
                vs {change.period}
              </span>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
