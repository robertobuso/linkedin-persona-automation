import React, { useState, useEffect } from 'react'
import { useContentStore } from '@/stores/contentStore'
import { ContentViewToggle } from '@/components/content/ContentViewToggle'
import { ContentIntelligenceFilters } from '@/components/content/ContentIntelligenceFilters'
import { ContentIntelligenceCard } from '@/components/content/ContentIntelligenceCard'
import { DailyArticleSummary } from '@/components/dashboard/DailyArticleSummary'
import { Button } from '@/components/ui/Button'
import { CpuChipIcon as BrainIcon } from '@heroicons/react/24/outline'
import { LoadingPage, CardSkeleton } from '@/components/ui/LoadingStates'
import { notify } from '@/stores/uiStore'

export default function ContentIntelligence() {
  const {
    allContent,
    viewMode,
    isLoading,
    error,
    setViewMode,
    runAIContentSelection,
    fetchContentByMode,
    clearError
  } = useContentStore()

  useEffect(() => {
    fetchContentByMode(viewMode)
  }, [fetchContentByMode, viewMode])

  useEffect(() => {
    if (error) {
      notify.error('Content Loading Error', error)
      clearError()
    }
  }, [error, clearError])

  const handleAISelection = async () => {
    try {
      await runAIContentSelection()
      notify.success('AI content selection completed successfully')
    } catch (error) {
      notify.error('AI Selection Failed', 'Unable to run AI content selection')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Content Intelligence</h1>
          <p className="text-gray-600 mt-1">
            AI-powered content discovery and selection
          </p>
        </div>
        <div className="flex space-x-2">
          <ContentViewToggle value={viewMode} onChange={setViewMode} />
          <Button onClick={handleAISelection} variant="ai" leftIcon={<BrainIcon className="h-4 w-4" />}>
            Run AI Selection
          </Button>
        </div>
      </div>

      {/* Daily Article Summary - only show for AI-selected view */}
      {viewMode === 'ai-selected' && <DailyArticleSummary />}

      {/* Content Filters */}
      <ContentIntelligenceFilters />

      {/* Content Grid */}
      <div className="space-y-6">
        {isLoading ? (
          <div className="space-y-6">
            {[1, 2, 3, 4].map(i => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : allContent.length === 0 ? (
          <div className="text-center py-12">
            <BrainIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No content found</h3>
            <p className="text-gray-600 mb-6">
              {viewMode === 'ai-selected' 
                ? 'No AI-selected content available. Try running AI selection.' 
                : 'No content matches your current filters.'}
            </p>
            {viewMode === 'ai-selected' && (
              <Button onClick={handleAISelection} variant="ai">
                Run AI Selection
              </Button>
            )}
          </div>
        ) : (
          allContent.map(item => (
            <ContentIntelligenceCard 
              key={item.id} 
              content={item}
              viewMode={viewMode}
            />
          ))
        )}
      </div>
    </div>
  )
}
