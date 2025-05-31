import React from 'react'
import { 
  CpuChipIcon as BrainIcon, 
  LinkIcon, 
  ClockIcon, 
  ArrowTrendingUpIcon,
  SparklesIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { AIAnalysisPanel } from '@/components/intelligence/AIAnalysisPanel'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { ContentItem } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { useGenerateDraft } from '@/hooks/useDrafts'
import { notify } from '@/stores/uiStore'

interface ContentIntelligenceCardProps {
  content: ContentItem
  viewMode: string
}

export function ContentIntelligenceCard({ content, viewMode }: ContentIntelligenceCardProps) {
  const { mutateAsync: generateDraft, isLoading } = useGenerateDraft()
  const isAISelected = content.ai_analysis?.llm_selected

  const handleGenerateDraft = async () => {
    try {
      await generateDraft(content.id)
      notify.success('Draft generated successfully!')
    } catch (error) {
      notify.error('Failed to generate draft')
    }
  }

  const handleReadOriginal = () => {
    window.open(content.url, '_blank', 'noopener,noreferrer')
  }

  return (
    <Card hover="lift" className="relative">
      {isAISelected && (
        <div className="absolute top-4 right-4 z-10">
          <Badge variant="ai" icon={<BrainIcon className="h-3 w-3" />}>
            AI Selected
          </Badge>
        </div>
      )}

      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="pr-20"> {/* Account for the badge */}
          <h3 className="text-lg font-semibold text-neural-700 mb-2 line-clamp-2">
            {content.title}
          </h3>
          <p className="text-gray-600 line-clamp-3">
            {content.content.substring(0, 200)}...
          </p>
        </div>

        {/* AI Analysis Panel */}
        {isAISelected && content.ai_analysis && (
          <AIAnalysisPanel
            reasoning={content.ai_analysis.selection_reason || 'Selected by AI for high relevance'}
            score={content.relevance_score}
            category={content.ai_analysis.topic_category}
            confidence={content.relevance_score ? content.relevance_score / 100 : undefined}
          />
        )}

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
                <ArrowTrendingUpIcon className="h-4 w-4" />
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

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            <Button
              size="sm"
              onClick={handleGenerateDraft}
              loading={isLoading}
              variant="ai"
              leftIcon={<SparklesIcon className="h-4 w-4" />}
            >
              Generate Draft
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={handleReadOriginal}
              leftIcon={<LinkIcon className="h-4 w-4" />}
            >
              Read Original
            </Button>
          </div>
          
          {isAISelected && content.relevance_score && (
            <ConfidenceIndicator 
              score={content.relevance_score / 100}
              size="sm"
              showPercentage={false}
              label=""
            />
          )}
        </div>
      </div>
    </Card>
  )
}
