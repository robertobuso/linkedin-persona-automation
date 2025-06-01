import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'
import { PostDraft, api } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { CalendarIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline'

interface PublishDraftModalProps {
  draft: PostDraft
  isOpen: boolean
  onClose: () => void
}

export function PublishDraftModal({ draft, isOpen, onClose }: PublishDraftModalProps) {
  const [publishMode, setPublishMode] = useState<'now' | 'schedule'>('now')
  const [scheduledTime, setScheduledTime] = useState('')
  
  const queryClient = useQueryClient()

  const publishMutation = useMutation({
    mutationFn: (scheduledFor?: string) => api.publishDraft(draft.id, scheduledFor),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      
      if (publishMode === 'now') {
        notify.success('Post published successfully!', result.linkedin_post_url)
      } else {
        notify.success('Post scheduled successfully!')
      }
      
      onClose()
    },
    onError: (error: any) => {
      notify.error('Publishing failed', error.message)
    }
  })

  const handlePublish = () => {
    const scheduledFor = publishMode === 'schedule' ? scheduledTime : undefined
    publishMutation.mutate(scheduledFor)
  }

  const getMinDateTime = () => {
    const now = new Date()
    now.setMinutes(now.getMinutes() + 5) // Minimum 5 minutes from now
    return now.toISOString().slice(0, 16)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Publish to LinkedIn"
      size="lg"
    >
      <div className="space-y-6">
        <Card variant="intelligence" padding="sm">
          <div className="p-4">
            <h4 className="font-medium text-neural-700 mb-2">Draft Preview</h4>
            <div className="text-sm text-gray-600 line-clamp-3">
              {draft.content}
            </div>
            {draft.hashtags.length > 0 && (
              <div className="mt-2 text-xs text-ai-purple-600">
                {draft.hashtags.join(' ')}
              </div>
            )}
          </div>
        </Card>

        <div className="space-y-4">
          <h4 className="font-medium text-neural-700">Publishing Options</h4>
          
          <div className="space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="radio"
                value="now"
                checked={publishMode === 'now'}
                onChange={(e) => setPublishMode(e.target.value as 'now')}
                className="text-ai-purple-600 focus:ring-ai-purple-500"
              />
              <PaperAirplaneIcon className="h-5 w-5 text-ml-green-500" />
              <div>
                <div className="font-medium">Publish Now</div>
                <div className="text-sm text-gray-600">
                  Post immediately to your LinkedIn profile
                </div>
              </div>
            </label>

            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="radio"
                value="schedule"
                checked={publishMode === 'schedule'}
                onChange={(e) => setPublishMode(e.target.value as 'schedule')}
                className="text-ai-purple-600 focus:ring-ai-purple-500 mt-1"
              />
              <CalendarIcon className="h-5 w-5 text-prediction-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium mb-2">Schedule for Later</div>
                {publishMode === 'schedule' && (
                  <Input
                    type="datetime-local"
                    value={scheduledTime}
                    onChange={(e) => setScheduledTime(e.target.value)}
                    min={getMinDateTime()}
                    className="w-full"
                  />
                )}
                <div className="text-sm text-gray-600 mt-1">
                  Schedule for optimal engagement time
                </div>
              </div>
            </label>
          </div>
        </div>

        <div className="bg-neutral-50 p-4 rounded-lg">
          <h5 className="font-medium text-neutral-700 mb-2">Publishing Tips</h5>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Best times to post: 8-10 AM and 12-2 PM on weekdays</li>
            <li>• Include a clear call-to-action in your post</li>
            <li>• Engage with comments within the first hour</li>
            <li>• Use 3-5 relevant hashtags for maximum reach</li>
          </ul>
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
            onClick={handlePublish}
            loading={publishMutation.isPending}
            disabled={publishMode === 'schedule' && !scheduledTime}
            leftIcon={publishMode === 'now' ? 
              <PaperAirplaneIcon className="h-4 w-4" /> : 
              <CalendarIcon className="h-4 w-4" />
            }
          >
            {publishMode === 'now' ? 'Publish Now' : 'Schedule Post'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}