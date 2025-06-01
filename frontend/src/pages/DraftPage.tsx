import React from 'react'
import { useRouter } from 'next/router'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { EnhancedDraftCard } from '@/components/creation/EnhancedDraftCard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

export function DraftPage() {
  const router = useRouter()
  const { draftId } = router.query

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => api.getDraft(draftId as string),
    enabled: !!draftId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neural-600"></div>
      </div>
    )
  }

  if (error || !draft) {
    return (
      <Card className="text-center py-12">
        <p className="text-red-600 mb-4">Draft not found</p>
        <Button variant="outline" onClick={() => router.push('/creation')}>
          Back to Creation Studio
        </Button>
      </Card>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          onClick={() => router.push('/creation')}
          leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
        >
          Back to Studio
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-neural-700">
            {draft.title || 'Draft Preview'}
          </h1>
          <p className="text-gray-600">Review and edit your draft</p>
        </div>
      </div>

      {/* Draft Card */}
      <div className="max-w-2xl">
        <EnhancedDraftCard
          draft={draft}
          showFullContent={true}
        />
      </div>
    </div>
  )
}
