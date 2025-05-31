import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface RecommendationCategoryProps {
  title: string
  count: number
  color: 'ml-green' | 'prediction' | 'neural' | 'secondary'
  icon: React.ComponentType<{ className?: string }>
  description: string
}

export function RecommendationCategory({ 
  title, 
  count, 
  color, 
  icon: Icon, 
  description 
}: RecommendationCategoryProps) {
  const colorClasses = {
    'ml-green': 'from-ml-green-50 to-ml-green-100 border-ml-green-200 text-ml-green-700',
    'prediction': 'from-prediction-50 to-prediction-100 border-prediction-200 text-prediction-700',
    'neural': 'from-neural-50 to-neural-100 border-neural-200 text-neural-700',
    'secondary': 'from-gray-50 to-gray-100 border-gray-200 text-gray-700'
  }

  const badgeVariants = {
    'ml-green': 'ml-green' as const,
    'prediction': 'prediction' as const,
    'neural': 'default' as const,
    'secondary': 'secondary' as const
  }

  return (
    <Card 
      className={`bg-gradient-to-br ${colorClasses[color]} border`}
      hover="lift"
    >
      <div className="p-6 text-center space-y-4">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm">
          <Icon className="h-6 w-6" />
        </div>
        
        <div className="space-y-2">
          <h3 className="font-semibold">{title}</h3>
          <Badge variant={badgeVariants[color]} size="lg">
            {count} drafts
          </Badge>
          <p className="text-xs opacity-80 leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </Card>
  )
}
