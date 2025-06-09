import React from 'react'
import { useAIRecommendations, usePersonaMetrics, useTodaysContent, useEngagementQueue } from '@/hooks/useAIRecommendations'
import { IntelligenceBrief } from '@/components/dashboard/IntelligenceBrief'
import { PerformanceCard } from '@/components/dashboard/PerformanceCard'
import { QuickActionsPanel } from '@/components/dashboard/QuickActionsPanel'
import { TodaysContentIntelligence } from '@/components/dashboard/TodaysContentIntelligence'
import { EngagementOpportunities } from '@/components/dashboard/EngagementOpportunities'
import { RecommendedDraft } from '@/components/dashboard/RecommendedDraft'
import { DailyArticleSummary } from '@/components/dashboard/DailyArticleSummary'
import { LoadingPage } from '@/components/ui/LoadingStates'

export default function Dashboard() {
  const { data: aiRecommendations, isLoading: recommendationsLoading } = useAIRecommendations()
  const { data: personaMetrics, isLoading: metricsLoading } = usePersonaMetrics()
  const { data: todaysContent, isLoading: contentLoading } = useTodaysContent()
  const { data: engagementQueue, isLoading: engagementLoading } = useEngagementQueue()

  if (recommendationsLoading || metricsLoading) {
    return <LoadingPage message="Loading your AI intelligence dashboard..." />
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-neural-700">AI Intelligence Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Your personalized LinkedIn automation command center
        </p>
      </div>

      {/* Hero Intelligence Brief */}
      <IntelligenceBrief 
        recommendations={aiRecommendations || []}
        metrics={personaMetrics}
      />
      
      {/* Performance Intelligence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PerformanceCard
          title="Engagement Prediction"
          metric={personaMetrics?.next_post_prediction}
          type="prediction"
          loading={metricsLoading}
        />
        <PerformanceCard
          title="Content Pipeline"
          metric={todaysContent?.pipeline_status}
          type="pipeline"
          loading={contentLoading}
        />
        <PerformanceCard
          title="Persona Growth"
          metric={personaMetrics?.growth_metrics}
          type="growth"
          loading={metricsLoading}
        />
      </div>

      {/* Quick Intelligence Actions */}
      <QuickActionsPanel />

      {/* Today's Priorities */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <TodaysContentIntelligence content={todaysContent} loading={contentLoading} />
          <EngagementOpportunities opportunities={engagementQueue} loading={engagementLoading} />
          <RecommendedDraft />
        </div>

      {/* Daily Article Summary */}
      <DailyArticleSummary />
    </div>
  )
}
