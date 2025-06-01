import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  PaperAirplaneIcon,
  ArrowPathIcon,
  CalendarIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { PostDraft, api } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { ToneStyleSelector } from './ToneStyleSelector'
import { PublishDraftModal } from './PublishDraftModal'
import { RegenerateDraftModal } from './RegenerateDraftModal'

interface EnhancedDraftEditorProps {
  draft: PostDraft
  onUpdate: (draft: PostDraft) => void
}

export function EnhancedDraftEditor({ draft, onUpdate }: EnhancedDraftEditorProps) {
  const [editedContent, setEditedContent] = useState(draft.content)
  const [editedHashtags, setEditedHashtags] = useState(draft.hashtags.join(' '))
  const [showPublishModal, setShowPublishModal] = useState(false)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)
  const [showToneSelector, setShowToneSelector] = useState(false)

  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: (data: { content: string; hashtags: string[] }) => 
      api.updateDraft(draft.id, data),
    onSuccess: (updatedDraft) => {
      onUpdate(updatedDraft)
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      notify.success('Draft updated successfully!')
    },
    onError: (error: any) => {
      notify.error('Failed to update draft', error.message)
    }
  })

  const handleSave = () => {
    const hashtags = editedHashtags.split(' ').filter(tag => tag.trim())
    updateMutation.mutate({
      content: editedContent,
      hashtags
    })
  }

  const hasChanges = editedContent !== draft.content || 
    editedHashtags !== draft.hashtags.join(' ')

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success'
      case 'scheduled': return 'default'
      case 'published': return 'ml-green'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-neural-700">
                Edit Draft
              </h3>
              <Badge variant={getStatusColor(draft.status)} size="sm">
                {draft.status}
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowToneSelector(true)}
                leftIcon={<AdjustmentsHorizontalIcon className="h-4 w-4" />}
              >
                Tone
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRegenerateModal(true)}
                leftIcon={<ArrowPathIcon className="h-4 w-4" />}
              >
                Regenerate
              </Button>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content
              </label>
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="w-full h-48 px-3 py-2 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
                placeholder="Write your LinkedIn post..."
              />
              <div className="text-xs text-gray-500 mt-1">
                {editedContent.length} characters
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hashtags
              </label>
              <input
                type="text"
                value={editedHashtags}
                onChange={(e) => setEditedHashtags(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
                placeholder="#hashtag1 #hashtag2"
              />
              <div className="text-xs text-gray-500 mt-1">
                {editedHashtags.split(' ').filter(tag => tag.trim()).length} hashtags
              </div>
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={handleSave}
                variant={hasChanges ? "ai" : "secondary"}
                size="sm"
                className="flex-1"
                loading={updateMutation.isPending}
                disabled={!hasChanges}
              >
                {hasChanges ? 'Save Changes' : 'No Changes'}
              </Button>
              
              {draft.status === 'ready' && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowPublishModal(true)}
                    leftIcon={<CalendarIcon className="h-4 w-4" />}
                  >
                    Schedule
                  </Button>
                  <Button
                    variant="success"
                    size="sm"
                    onClick={() => setShowPublishModal(true)}
                    leftIcon={<PaperAirplaneIcon className="h-4 w-4" />}
                  >
                    Publish
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Modals */}
      <ToneStyleSelector
        isOpen={showToneSelector}
        onClose={() => setShowToneSelector(false)}
        currentContent={editedContent}
        onToneApplied={(newContent) => {
          setEditedContent(newContent)
          setShowToneSelector(false)
        }}
      />

      <PublishDraftModal
        draft={draft}
        isOpen={showPublishModal}
        onClose={() => setShowPublishModal(false)}
      />

      <RegenerateDraftModal
        draft={draft}
        isOpen={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        onRegenerated={(newDraft) => {
          onUpdate(newDraft)
          setEditedContent(newDraft.content)
          setEditedHashtags(newDraft.hashtags.join(' '))
        }}
      />
    </div>
  )
}