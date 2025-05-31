import React from 'react'
import { 
  ChatBubbleLeftIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useEngagementStore } from '@/stores/engagementStore'
import { Skeleton } from '@/components/ui/LoadingStates'

export function EngagementOverview() {
  const { engagementStats, isLoading } = useEngagementStore()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map(i => (
          <Card key={i}>
            <div className="p-6 space-y-2">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-8 w-3/4" />
              <Skeleton className="h-4 w-full" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  const stats = [
    {
      title: 'Total Opportunities',
      value: engagementStats?.total_opportunities || 0,
      icon: ChatBubbleLeftIcon,
      color: 'text-neural-600',
      bgColor: 'bg-neural-100'
    },
    {
      title: 'Completion Rate',
      value: `${Math.round((engagementStats?.completion_rate || 0) * 100)}%`,
      icon: CheckCircleIcon,
      color: 'text-ml-green-600',
      bgColor: 'bg-ml-green-100'
    },
    {
      title: 'Pending Actions',
      value: engagementStats?.status_breakdown?.pending || 0,
      icon: ClockIcon,
      color: 'text-prediction-600',
      bgColor: 'bg-prediction-100'
    },
    {
      title: 'High Priority',
      value: engagementStats?.status_breakdown?.high || 0,
      icon: ExclamationTriangleIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-100'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {stats.map((stat) => (
        <Card key={stat.title} hover="lift">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
