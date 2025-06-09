import React from 'react'
import { PaperAirplaneIcon, PencilIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

export function RecommendedDraft() {
  const navigate = useNavigate()
  
  const { data: drafts = [] } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  })

  // Get the most recent ready draft
  const recommendedDraft = drafts
    .filter(draft => draft.status === 'ready')
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]

  if (!recommendedDraft) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-4">Recommended Draft</h3>
        <p className="text-gray-500">No drafts ready for publishing</p>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-neural-700">Recommended Draft</h3>
        <Badge variant="success">Ready to Publish</Badge>
      </div>
      
      <div className="space-y-4">
        <div>
          <h4 className="font-medium text-gray-900 mb-2">
            {recommendedDraft.title || 'AI Generated Post'}
          </h4>
          <p className="text-gray-600 line-clamp-3">
            {recommendedDraft.content.substring(0, 150)}...
          </p>
        </div>
        
        <div className="flex space-x-2">
          <Button
            variant="ai"
            size="sm"
            leftIcon={<PaperAirplaneIcon className="h-4 w-4" />}
            onClick={() => {
              // Handle publish logic here
            }}
          >
            Publish Now
          </Button>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<PencilIcon className="h-4 w-4" />}
            onClick={() => navigate('/creation')}
          >
            Edit Draft
          </Button>
        </div>
      </div>
    </Card>
  )
}