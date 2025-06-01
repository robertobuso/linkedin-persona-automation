import React, { useState } from 'react'
import { 
  ExternalLinkIcon, 
  SparklesIcon, 
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ContentItem } from '@/lib/api'
import { useGenerateDraft } from '@/hooks/useEnhancedDrafts'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'
import { useRouter } from 'next/router'

interface ContentCardProps {
  content: ContentItem & { draft_generated?: boolean }
  viewMode: string
}

export function ContentCard({ content, viewMode }: ContentCardProps) {
  const router = useRouter()
  const { mutateAsync: generateDraft, isLoading } = useGenerateDraft()
  const [toneStyle, setToneStyle] = useState<string>('professional')

  const handleGenerateDraft = async () => {
    if (content.draft_generated) {
      notify.warning('Draft already generated for this content')
      return
    }

    try {
      const newDraft = await generateDraft({
        content_item_id: content.id,
        tone_style: toneStyle
      })
      
      notify.success('Draft generated successfully!')
      
      // Redirect to the new draft page
      router.push(`/drafts/${newDraft.id}`)
      
    } catch (error: any) {
      if (error.status === 409) {
        notify.warning('Draft already generated for this content')
      } else {
        notify.error('Failed to generate draft')
      }
    }
  }

  const handleReadOriginal = () => {
    window.open(content.url, '_blank', 'noopener,noreferrer')
  }

  return (
    <Card hover="lift" className="relative">
      {content.ai_analysis?.llm_selected && (
        <div className="absolute top-4 right-4 z-10">
          <Badge variant="ai" icon={<SparklesIcon className="h-3 w-3" />}>
            AI Selected
          </Badge>
        </div>
      )}

      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="pr-20">
          <h3 className="text-lg font-semibold text-neural-700 mb-2 line-clamp-2">
            {content.title}
          </h3>
          <p className="text-gray-600 line-clamp-3">
            {content.content.substring(0, 200)}...
          </p>
        </div>

        {/* Content Metadata */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <span className="font-medium">{content.source_name}</span>
            <div className="flex items-center space-x-1">
              <ClockIcon className="h-4 w-4" />
              <span>{formatDistanceToNow(new Date(content.published_at), { addSuffix: true })}</span>
            </div>
            {content.relevance_score && (
              <div className="flex items-center space-x-1 text-ml-green-600">
                <span className="font-medium">{content.relevance_score}% relevant</span>
              </div>
            )}
          </div>
        </div>

        {/* Tags */}
        {content.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {content.tags.slice(0, 6).map(tag => (
              <Badge key={tag} variant="neutral" size="sm">
                {tag}
              </Badge>
            ))}
            {content.tags.length > 6 && (
              <Badge variant="outline" size="sm">
                +{content.tags.length - 6} more
              </Badge>
            )}
          </div>
        )}

        {/* Tone Style Selector (only show when generating) */}
        {!content.draft_generated && !isLoading && (
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Tone:</label>
            <select
              value={toneStyle}
              onChange={(e) => setToneStyle(e.target.value)}
              className="text-sm border border-gray-200 rounded px-2 py-1"
            >
              <option value="professional">Professional</option>
              <option value="conversational">Conversational</option>
              <option value="storytelling">Storytelling</option>
              <option value="humorous">Humorous</option>
            </select>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            {content.draft_generated ? (
              <Badge 
                variant="success" 
                icon={<CheckCircleIcon className="h-4 w-4" />}
                className="px-3 py-2"
              >
                DRAFT GENERATED
              </Badge>
            ) : (
              <Button
                size="sm"
                onClick={handleGenerateDraft}
                loading={isLoading}
                variant="ai"
                leftIcon={<SparklesIcon className="h-4 w-4" />}
              >
                Generate Draft
              </Button>
            )}
            
            <Button 
              size="sm" 
              variant="outline"
              onClick={handleReadOriginal}
              leftIcon={<ExternalLinkIcon className="h-4 w-4" />}
            >
              Read Original
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
