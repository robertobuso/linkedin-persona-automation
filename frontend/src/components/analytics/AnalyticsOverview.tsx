import React from 'react'
import { 
  ArrowTrendingUpIcon, 
 ArrowTrendingDownIcon, 
  EyeIcon, 
  HeartIcon,
  ChatBubbleLeftIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PersonaMetrics } from '@/lib/api'

interface AnalyticsOverviewProps {
  metrics?: PersonaMetrics
}

export function AnalyticsOverview({ metrics }: AnalyticsOverviewProps) {
  const overviewStats = [
    {
      title: 'Authority Score',
      value: metrics?.authority_score || 0,
      change: '+5',
      trend: 'up' as const,
      icon: ArrowTrendingUpIcon,
      color: 'text-ml-green-600',
      bgColor: 'bg-ml-green-100'
    },
    {
      title: 'Engagement Rate',
      value: `${((metrics?.engagement_trend || 0) * 100).toFixed(1)}%`,
      change: '+2.3%',
      trend: 'up' as const,
      icon: HeartIcon,
      color: 'text-red-500',
      bgColor: 'bg-red-100'
    },
    {
      title: 'Content Quality',
      value: Math.round(metrics?.content_quality_avg || 0),
      change: '+8',
      trend: 'up' as const,
      icon: EyeIcon,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Network Growth',
      value: `${((metrics?.network_growth || 0) * 100).toFixed(1)}%`,
      change: '+12%',
      trend: 'up' as const,
      icon: UserGroupIcon,
      color: 'text-purple-500',
      bgColor: 'bg-purple-100'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {overviewStats.map((stat) => (
        <Card key={stat.title} hover="lift">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                <div className="flex items-center mt-2">
                  {stat.trend === 'up' ? (
                    <ArrowTrendingUpIcon className="h-4 w-4 text-ml-green-500 mr-1" />
                  ) : (
                    <ArrowArrowTrendingDownIcon className="h-4 w-4 text-red-500 mr-1" />
                  )}
                  <span className={`text-sm ${stat.trend === 'up' ? 'text-ml-green-600' : 'text-red-600'}`}>
                    {stat.change}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">vs last period</span>
                </div>
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
