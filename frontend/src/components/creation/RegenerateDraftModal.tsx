import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { PostDraft, api } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { ArrowPathIcon } from '@heroicons/react/24/outline'

interface RegenerateDraftModalProps {
  draft: PostDraft
  isOpen: boolean
  onClose: () => void
  onRegenerated: (newDraft: PostDraft) => void
}

const styleOptions = [
  { id: 'professional_thought_leader', name: 'Professional Thought Leader' },
  { id: 'storytelling', name: 'Storytelling' },
  { id: 'educational', name: 'Educational' },
  { id: 'thought_provoking', name: 'Thought Provoking' },
  { id: 'casual_conversational', name: 'Casual Conversational' },
  { id: 'data_driven', name: 'Data-Driven' }
]

export function RegenerateDraftModal({ 
  draft, 
  isOpen, 
  onClose, 
  onRegenerated 
}: RegenerateDraftModalProps) {
  const [selectedStyle, setSelectedStyle] = useState('professional_thought_leader')
  const [preserveHashtags, setPreserveHashtags] = useState(true)

  const regenerateMutation = useMutation({
    mutationFn: (options: { style: string; preserve_hashtags: boolean }) => 
      api.regenerateDraft(draft.id, options),
    onSuccess: (newDraft) => {
      onRegenerated(newDraft)
      notify.success('Draft regenerated successfully!')
      onClose()
    },
    onError: (error: any) => {
      notify.error('Failed to regenerate draft', error.message)
    }
  })

  const handleRegenerate = () => {
    regenerateMutation.mutate({
      style: selectedStyle,
      preserve_hashtags: preserveHashtags
    })
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Regenerate Draft"
      size="lg"
    >
      <div className="space-y-6">
        <Card variant="intelligence" padding="sm">
          <div className="p-4">
            <h4 className="font-medium text-neural-700 mb-2">Current Draft</h4>
            <div className="text-sm text-gray-600 line-clamp-3">
              {draft.content}
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Regenerate with Style
            </label>
            <select
              value={selectedStyle}
              onChange={(e) => setSelectedStyle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
            >
              {styleOptions.map((style) => (
                <option key={style.id} value={style.id}>
                  {style.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="preserve-hashtags"
              checked={preserveHashtags}
              onChange={(e) => setPreserveHashtags(e.target.checked)}
              className="h-4 w-4 text-ai-purple-600 focus:ring-ai-purple-500 border-gray-300 rounded"
            />
            <label htmlFor="preserve-hashtags" className="ml-2 block text-sm text-gray-900">
              Preserve existing hashtags
            </label>
          </div>
        </div>

        <div className="bg-prediction-50 p-4 rounded-lg">
          <h5 className="font-medium text-prediction-700 mb-2">⚡ AI Regeneration</h5>
          <p className="text-sm text-prediction-600">
            The AI will rewrite your draft using the selected style while maintaining the core message and insights.
            This usually takes 10-15 seconds.
          </p>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            variant="outline"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            variant="ai"
            onClick={handleRegenerate}
            loading={regenerateMutation.isPending}
            leftIcon={<ArrowPathIcon className="h-4 w-4" />}
          >
            Regenerate Draft
          </Button>
        </div>
      </div>
    </Modal>
  )
}
