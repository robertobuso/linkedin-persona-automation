import React, { useState } from 'react'
import { 
  DocumentTextIcon, 
  PlusIcon,
  FunnelIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EnhancedDraftCard } from './EnhancedDraftCard'
import { useDrafts, useBatchGenerateDrafts } from '@/hooks/useEnhancedDrafts'
import { DraftWithContent } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function CreationStudio() {
  const [selectedDraft, setSelectedDraft] = useState<DraftWithContent | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  
  const { data: drafts = [], isLoading, error } = useDrafts()
  const { mutateAsync: batchGenerate, isLoading: isBatchGenerating } = useBatchGenerateDrafts()

  const handleBatchGenerate = async () => {
    try {
      const newDrafts = await batchGenerate({
        max_posts: 5,
        min_relevance_score: 75,
        style: 'professional'
      })
      
      notify.success(`Generated ${newDrafts.length} new drafts!`)
    } catch (error) {
      notify.error('Failed to generate drafts')
    }
  }

  const filteredDrafts = statusFilter === 'all' 
    ? drafts 
    : drafts.filter(draft => draft.status === statusFilter)

  const statusCounts = drafts.reduce((acc, draft) => {
    acc[draft.status] = (acc[draft.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neural-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="text-center py-12">
        <p className="text-red-600">Failed to load drafts</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </Card>
    )
  }

  if (drafts.length === 0) {
    return (
      <Card className="text-center py-12">
        <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No drafts yet</h3>
        <p className="text-gray-600 mb-6">
          Generate some content drafts to get started
        </p>
        <Button 
          variant="ai" 
          onClick={handleBatchGenerate}
          loading={isBatchGenerating}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Generate Drafts
        </Button>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neural-700">Creation Studio</h1>
          <p className="text-gray-600">Manage and refine your content drafts</p>
        </div>
        
        <div className="flex space-x-3">
          <Button 
            variant="outline"
            onClick={handleBatchGenerate}
            loading={isBatchGenerating}
            leftIcon={<PlusIcon className="h-4 w-4" />}
          >
            Generate More
          </Button>
        </div>
      </div>

      {/* Status Filter */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <FunnelIcon className="h-5 w-5 text-gray-500" />
            <span className="font-medium text-gray-700">Filter by status:</span>
            
            <div className="flex space-x-2">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  statusFilter === 'all'
                    ? 'bg-neural-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All ({drafts.length})
              </button>
              
              {Object.entries(statusCounts).map(([status, count]) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    statusFilter === status
                      ? 'bg-neural-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {status} ({count})
                </button>
              ))}
            </div>
          </div>
          
          <Badge variant="secondary">
            {filteredDrafts.length} draft{filteredDrafts.length !== 1 ? 's' : ''}
          </Badge>
        </div>
      </Card>

      {/* Drafts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredDrafts.map((draft) => (
          <EnhancedDraftCard
            key={draft.id}
            draft={draft}
            isSelected={selectedDraft?.id === draft.id}
            onSelect={() => setSelectedDraft(draft)}
            showFullContent={true}
          />
        ))}
      </div>

      {filteredDrafts.length === 0 && statusFilter !== 'all' && (
        <Card className="text-center py-12">
          <p className="text-gray-600">No drafts with status "{statusFilter}"</p>
          <Button 
            variant="outline" 
            onClick={() => setStatusFilter('all')}
            className="mt-4"
          >
            Show All Drafts
          </Button>
        </Card>
      )}
    </div>
  )
}
