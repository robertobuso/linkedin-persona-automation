import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { EnhancedDraftEditor } from '@/components/creation/EnhancedDraftEditor'
import { BatchOperationsPanel } from '@/components/creation/BatchOperationsPanel'
import { DraftsWorkshop } from '@/components/creation/DraftsWorkshop'
import { LoadingPage } from '@/components/ui/LoadingStates'
import { Card } from '@/components/ui/Card'
import { notify } from '@/stores/uiStore'

export default function CreationStudio() {
  const [selectedDraft, setSelectedDraft] = useState(null)

  const { data: drafts = [], isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return <LoadingPage message="Loading your creation studio..." />
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-neural-700">Creation Studio</h1>
        <p className="text-gray-600 mt-2">
          Create, edit, and publish AI-generated LinkedIn content
        </p>
      </div>

      {/* Batch Operations */}
      <BatchOperationsPanel />

      {/* Drafts Workshop */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
        <div className="xl:col-span-3">
          <DraftsWorkshop 
            drafts={drafts} 
            onSelectDraft={setSelectedDraft}
            selectedDraft={selectedDraft}
          />
        </div>
        
        <div className="xl:col-span-1">
          {selectedDraft ? (
            <EnhancedDraftEditor 
              draft={selectedDraft}
              onUpdate={setSelectedDraft}
            />
          ) : (
            <Card className="p-6 text-center">
              <p className="text-gray-500">Select a draft to edit with enhanced features</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}