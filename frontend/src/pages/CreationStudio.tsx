import React, { useState } from 'react'
import { useDraftRecommendations, useDrafts } from '@/hooks/useAIRecommendations'
import { CreationTabs } from '@/components/creation/CreationTabs'
import { DraftRecommendationsView } from '@/components/creation/DraftRecommendationsView'
import { DraftsWorkshop } from '@/components/creation/DraftsWorkshop'
import { PublishingCalendar } from '@/components/creation/PublishingCalendar'
import { Button } from '@/components/ui/Button'
import { SparklesIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline'
import { LoadingPage } from '@/components/ui/LoadingStates'
import { notify } from '@/stores/uiStore'

export default function CreationStudio() {
  const [activeTab, setActiveTab] = useState<'recommendations' | 'drafts' | 'calendar'>('recommendations')
  const { data: recommendations, isLoading: recommendationsLoading } = useDraftRecommendations()
  const { data: drafts, isLoading: draftsLoading } = useDrafts()

  const handleBatchGenerate = async () => {
    try {
      // This would trigger batch generation on the backend
      notify.success('Batch generation started')
    } catch (error) {
      notify.error('Batch generation failed')
    }
  }

  if (recommendationsLoading && activeTab === 'recommendations') {
    return <LoadingPage message="Loading AI recommendations..." />
  }

  if (draftsLoading && activeTab === 'drafts') {
    return <LoadingPage message="Loading your drafts..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Creation Studio</h1>
          <p className="text-gray-600 mt-1">
            AI-powered content creation and optimization
          </p>
        </div>
        <div className="flex space-x-2">
          <CreationTabs value={activeTab} onChange={setActiveTab} />
          <Button 
            onClick={handleBatchGenerate}
            variant="ai"
            leftIcon={<SparklesIcon className="h-4 w-4" />}
          >
            Batch Generate
          </Button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'recommendations' && (
        <DraftRecommendationsView recommendations={recommendations || []} />
      )}

      {activeTab === 'drafts' && (
        <DraftsWorkshop drafts={drafts || []} />
      )}

      {activeTab === 'calendar' && (
        <PublishingCalendar />
      )}
    </div>
  )
}
