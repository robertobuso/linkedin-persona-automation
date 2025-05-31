import React, { useState } from 'react'
import { usePersonaMetrics } from '@/hooks/useAIRecommendations'
import { AnalyticsOverview } from '@/components/analytics/AnalyticsOverview'
import { PerformanceChart } from '@/components/analytics/PerformanceChart'
import { ContentPerformance } from '@/components/analytics/ContentPerformance'
import { EngagementTrends } from '@/components/analytics/EngagementTrends'
import { PersonaInsights } from '@/components/analytics/PersonaInsights'
import { TimePeriodSelector } from '@/components/analytics/TimePeriodSelector'
import { LoadingPage } from '@/components/ui/LoadingStates'

export default function PersonaAnalytics() {
  const [timePeriod, setTimePeriod] = useState(30)
  const { data: metrics, isLoading } = usePersonaMetrics(timePeriod)

  if (isLoading) {
    return <LoadingPage message="Loading analytics data..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Persona Analytics</h1>
          <p className="text-gray-600 mt-1">
            Deep insights into your LinkedIn presence and performance
          </p>
        </div>
        <TimePeriodSelector value={timePeriod} onChange={setTimePeriod} />
      </div>

      {/* Overview Cards */}
      <AnalyticsOverview metrics={metrics} />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceChart data={metrics?.engagement_history} />
        <EngagementTrends data={metrics?.trends} />
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ContentPerformance />
        </div>
        <div>
          <PersonaInsights metrics={metrics} />
        </div>
      </div>
    </div>
  )
}
