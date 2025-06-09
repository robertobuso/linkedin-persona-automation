import React, { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { EnhancedDraftCard } from '@/components/creation/EnhancedDraftCard'
import { BatchOperationsPanel } from '@/components/creation/BatchOperationsPanel'
import { LoadingPage } from '@/components/ui/LoadingStates'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { FunnelIcon, PlusIcon } from '@heroicons/react/24/outline'
import { useBatchGenerateDrafts } from '@/hooks/useDrafts'
import { notify } from '@/stores/uiStore'

export default function CreationStudio() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const queryClient = useQueryClient()
  
  const { data: drafts = [], isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
    refetchInterval: 30 * 1000,
  })

  const { mutateAsync: batchGenerate, isLoading: isBatchGenerating } = useBatchGenerateDrafts()

  // Sort drafts by creation date (newest first)
  const sortedDrafts = [...drafts].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  const filteredDrafts = statusFilter === 'all' 
    ? sortedDrafts 
    : sortedDrafts.filter(draft => draft.status === statusFilter)

  const statusCounts = drafts.reduce((acc, draft) => {
    acc[draft.status] = (acc[draft.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const handleBatchGenerate = async () => {
    try {
      const newDrafts = await batchGenerate({
        max_posts: 5,
        min_relevance_score: 75,
        style: 'professional_thought_leader'
      })
      
      notify.success(`Generated ${newDrafts.length} new drafts!`)
      
      // Refresh data and show newest drafts
      await queryClient.invalidateQueries({ queryKey: ['drafts'] })
      setStatusFilter('all') // Show all to see new drafts
    } catch (error) {
      notify.error('Failed to generate drafts')
    }
  }

  if (isLoading) {
    return <LoadingPage message="Loading your creation studio..." />
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Creation Studio</h1>
          <p className="text-gray-600 mt-2">
            Create, edit, and publish AI-generated LinkedIn content
          </p>
        </div>
        
        <Button 
          variant="ai"
          onClick={handleBatchGenerate}
          loading={isBatchGenerating}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Generate New Drafts
        </Button>
      </div>

      {/* Batch Operations */}
      <BatchOperationsPanel />

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