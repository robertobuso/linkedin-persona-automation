import React, { useState } from 'react'
import { 
  PaperAirplaneIcon, 
  PencilIcon, 
  ArrowPathIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { DraftWithContent } from '@/lib/api'
import { useUpdateDraft, usePublishDraft, useDeleteDraft } from '@/hooks/useDrafts'
import { useRegenerateDraft } from '@/hooks/useEnhancedDrafts'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'
import { RegenerateModal } from './RegenerateModal'

interface EnhancedDraftCardProps {
  draft: DraftWithContent
  isSelected?: boolean
  onSelect?: () => void
  showFullContent?: boolean
}

export function EnhancedDraftCard({ 
  draft, 
  isSelected = false, 
  onSelect,
  showFullContent = false 
}: EnhancedDraftCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)
  
  const { mutateAsync: publishDraft, isLoading: isPublishing } = usePublishDraft()
  const { mutateAsync: regenerateDraft, isLoading: isRegenerating } = useRegenerateDraft()
  const { mutateAsync: deleteDraft, isLoading: isDeleting } = useDeleteDraft()

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
      notify.success('Draft published successfully!')
    } catch (error) {
      notify.error('Failed to publish draft')
    }
  }

  const handleRegenerate = async (toneStyle: string, preserveHashtags: boolean) => {
    try {
      await regenerateDraft({
        draftId: draft.id,
        options: {
          tone_style: toneStyle,
          preserve_hashtags: preserveHashtags
        }
      })
      notify.success('Draft regenerated successfully! 👌')
      setShowRegenerateModal(false)
    } catch (error) {
      notify.error('Failed to regenerate draft')
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this draft?')) {
      try {
        await deleteDraft(draft.id)
        notify.success('Draft deleted successfully')
      } catch (error) {
        notify.error('Failed to delete draft')
      }
    }
  }

  const shouldTruncateContent = !showFullContent && !isExpanded && draft.content.length > 400
  const displayContent = shouldTruncateContent 
    ? draft.content.substring(0, 400) + '...'
    : draft.content

  return (
    <>
      <Card 
        hover="lift"
        className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-neural-500' : ''}`}
        onClick={onSelect}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="font-semibold text-neural-700 mb-2 line-clamp-1">
                {draft.title || 'Untitled Draft'}
              </h3>
              <Badge variant={getStatusColor(draft.status)} size="sm">
                {draft.status}
              </Badge>
            </div>
          </div>

          {/* Content with Show More/Less */}
          <div className="mb-4">
            <div 
              className={`text-gray-700 whitespace-pre-wrap ${shouldTruncateContent ? 'max-h-[400px] overflow-hidden' : ''}`}
            >
              {displayContent}
            </div>
            
            {!showFullContent && draft.content.length > 400 && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setIsExpanded(!isExpanded)
              }}
              className="mt-2 text-sm text-neural-600 hover:text-neural-800 flex items-center space-x-1"
            >
              {isExpanded ? (
                <>
                  <EyeSlashIcon className="h-4 w-4" />
                  <span>Show less</span>
                </>
              ) : (
                <>
                  <EyeIcon className="h-4 w-4" />
                  <span>Show more</span>
                </>
              )}
            </button>
          )}
          </div>

          {/* Hashtags */}
          {draft.hashtags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {draft.hashtags.map((hashtag, index) => (
                <Badge key={index} variant="outline" size="sm">
                  {hashtag.startsWith('#') ? hashtag : `#${hashtag}`}
                </Badge>
              ))}
            </div>
          )}

          {/* Metadata */}
          <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
            <span>{formatDistanceToNow(new Date(draft.created_at), { addSuffix: true })}</span>
            {draft.generation_metadata?.word_count_validated && (
              <span>{draft.generation_metadata.word_count_validated} words</span>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <div className="flex space-x-2">
              {draft.status === 'ready' && (
                <Button
                  size="sm"
                  variant="ai"
                  onClick={handlePublish}
                  loading={isPublishing}
                  leftIcon={<PaperAirplaneIcon className="h-3 w-3" />}
                >
                  Publish
                </Button>
              )}
              
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowRegenerateModal(true)
                }}
                loading={isRegenerating}
                leftIcon={<ArrowPathIcon className="h-3 w-3" />}
              >
                Regenerate
              </Button>
            </div>

            <div className="flex space-x-1">
              <Button
                size="sm"
                variant="ghost"
                leftIcon={<CalendarIcon className="h-4 w-4" />}
              >
                Schedule
              </Button>
              
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDelete}
                loading={isDeleting}
                leftIcon={<TrashIcon className="h-4 w-4" />}
                className="text-red-600 hover:text-red-700"
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Regenerate Modal */}
      <RegenerateModal
        isOpen={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        onRegenerate={handleRegenerate}
        isLoading={isRegenerating}
        currentHashtags={draft.hashtags}
      />
    </>
  )
}
