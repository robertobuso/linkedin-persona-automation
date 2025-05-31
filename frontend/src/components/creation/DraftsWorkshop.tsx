import React, { useState } from 'react'
import { 
  DocumentTextIcon, 
  PencilIcon, 
  TrashIcon,
  PaperAirplaneIcon,
  CalendarIcon 
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { PostDraft } from '@/lib/api'
import { useUpdateDraft, usePublishDraft } from '@/hooks/useDrafts'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'

interface DraftsWorkshopProps {
  drafts: PostDraft[]
}

export function DraftsWorkshop({ drafts }: DraftsWorkshopProps) {
  const [selectedDraft, setSelectedDraft] = useState<PostDraft | null>(null)
  
  if (drafts.length === 0) {
    return (
      <Card className="text-center py-12">
        <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No drafts yet</h3>
        <p className="text-gray-600 mb-6">
          Generate some content drafts to get started
        </p>
        <Button variant="ai">
          Generate Drafts
        </Button>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Drafts List */}
      <div className="lg:col-span-2 space-y-4">
        {drafts.map((draft) => (
          <DraftCard 
            key={draft.id}
            draft={draft}
            isSelected={selectedDraft?.id === draft.id}
            onSelect={() => setSelectedDraft(draft)}
          />
        ))}
      </div>

      {/* Draft Editor */}
      <div className="lg:col-span-1">
        {selectedDraft ? (
          <DraftEditor 
            draft={selectedDraft}
            onUpdate={(updatedDraft) => setSelectedDraft(updatedDraft)}
          />
        ) : (
          <Card className="p-6 text-center">
            <PencilIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Select a draft to edit</p>
          </Card>
        )}
      </div>
    </div>
  )
}

function DraftCard({ 
  draft, 
  isSelected, 
  onSelect 
}: { 
  draft: PostDraft
  isSelected: boolean
  onSelect: () => void 
}) {
  const { mutateAsync: publishDraft } = usePublishDraft()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success'
      case 'scheduled': return 'default'
      case 'published': return 'ml-green'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const handlePublish = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await publishDraft({ draftId: draft.id })
    } catch (error) {
      // Error handled by hook
    }
  }

  return (
    <Card 
      hover="lift"
      className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-neural-500' : ''}`}
      onClick={onSelect}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="font-semibold text-neural-700 mb-2 line-clamp-1">
              {draft.title || 'Untitled Draft'}
            </h3>
            <p className="text-gray-600 text-sm line-clamp-2">
              {draft.content.substring(0, 150)}...
            </p>
          </div>
          <Badge variant={getStatusColor(draft.status)} size="sm">
            {draft.status}
          </Badge>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{formatDistanceToNow(new Date(draft.created_at), { addSuffix: true })}</span>
            {draft.hashtags.length > 0 && (
              <>
                <span>•</span>
                <span>{draft.hashtags.length} hashtags</span>
              </>
            )}
          </div>

          {draft.status === 'ready' && (
            <Button
              size="sm"
              variant="ai"
              onClick={handlePublish}
              leftIcon={<PaperAirplaneIcon className="h-3 w-3" />}
            >
              Publish
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}

function DraftEditor({ 
  draft, 
  onUpdate 
}: { 
  draft: PostDraft
  onUpdate: (draft: PostDraft) => void 
}) {
  const [editedContent, setEditedContent] = useState(draft.content)
  const [editedHashtags, setEditedHashtags] = useState(draft.hashtags.join(' '))
  const { mutateAsync: updateDraft } = useUpdateDraft()

  const handleSave = async () => {
    try {
      const hashtags = editedHashtags.split(' ').filter(tag => tag.trim())
      const updatedDraft = await updateDraft({
        draftId: draft.id,
        data: {
          content: editedContent,
          hashtags
        }
      })
      onUpdate(updatedDraft)
      notify.success('Draft updated successfully!')
    } catch (error) {
      notify.error('Failed to update draft')
    }
  }

  return (
    <Card className="sticky top-6">
      <div className="p-6">
        <h3 className="font-semibold text-neural-700 mb-4">Edit Draft</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content
            </label>
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full h-32 px-3 py-2 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
              placeholder="Write your LinkedIn post..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hashtags
            </label>
            <input
              type="text"
              value={editedHashtags}
              onChange={(e) => setEditedHashtags(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
              placeholder="#hashtag1 #hashtag2"
            />
          </div>

          <div className="flex space-x-2">
            <Button
              onClick={handleSave}
              variant="ai"
              size="sm"
              className="flex-1"
            >
              Save Changes
            </Button>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<CalendarIcon className="h-4 w-4" />}
            >
              Schedule
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
