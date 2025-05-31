import React from 'react'
import { PaperAirplaneIcon, PencilIcon, ClockIcon, CalendarIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { usePublishDraft } from '@/hooks/useDrafts'
import { useModal } from '@/stores/uiStore'
import { notify } from '@/stores/uiStore'

interface ActionButtonProps {
  action: 'post_now' | 'schedule_later' | 'review_and_edit' | 'skip'
  draftId: string
}

export function ActionButton({ action, draftId }: ActionButtonProps) {
  const { mutateAsync: publishDraft, isLoading } = usePublishDraft()
  const { openModal } = useModal()

  const handleAction = async () => {
    switch (action) {
      case 'post_now':
        try {
          await publishDraft({ draftId })
          notify.success('Draft published successfully!')
        } catch (error) {
          notify.error('Failed to publish draft')
        }
        break
        
      case 'schedule_later':
        openModal('schedule-draft', { draftId })
        break
        
      case 'review_and_edit':
        openModal('edit-draft', { draftId })
        break
        
      case 'skip':
        notify.info('Draft marked as skipped')
        break
    }
  }

  const getButtonConfig = () => {
    switch (action) {
      case 'post_now':
        return {
          icon: PaperAirplaneIcon,
          label: 'Post Now',
          variant: 'ai' as const
        }
      case 'schedule_later':
        return {
          icon: CalendarIcon,
          label: 'Schedule',
          variant: 'default' as const
        }
      case 'review_and_edit':
        return {
          icon: PencilIcon,
          label: 'Edit',
          variant: 'outline' as const
        }
      case 'skip':
        return {
          icon: ClockIcon,
          label: 'Skip',
          variant: 'ghost' as const
        }
    }
  }

  const config = getButtonConfig()

  return (
    <Button
      variant={config.variant}
      size="sm"
      onClick={handleAction}
      loading={isLoading}
      leftIcon={<config.icon className="h-4 w-4" />}
    >
      {config.label}
    </Button>
  )
}
