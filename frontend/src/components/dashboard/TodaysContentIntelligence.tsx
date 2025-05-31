import React from 'react'
import { NewspaperIcon, ClockIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/LoadingStates'
import { ContentItem } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

interface TodaysContentIntelligenceProps {
  content?: ContentItem[]
  loading?: boolean
}

export function TodaysContentIntelligence({ content = [], loading }: TodaysContentIntelligenceProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <Card>
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/2" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    )
  }

  const aiSelectedContent = content.filter(item => item.ai_analysis?.llm_selected)

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
            <NewspaperIcon className="h-5 w-5" />
            <span>Today's Content Intelligence</span>
          </h3>
          <Badge variant="ai">
            {aiSelectedContent.length} AI Selected
          </Badge>
        </div>

        {aiSelectedContent.length === 0 ? (
          <div className="text-center py-8">
            <NewspaperIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No AI-selected content for today</p>
            <Button 
              variant="ai" 
              size="sm"
              onClick={() => navigate('/content')}
            >
              Browse Content
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {aiSelectedContent.slice(0, 3).map((item) => (
              <ContentPreview key={item.id} content={item} />
            ))}
            
            <div className="pt-4 border-t border-gray-100">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => navigate('/content')}
              >
                View All Content ({aiSelectedContent.length})
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

function ContentPreview({ content }: { content: ContentItem }) {
  const navigate = useNavigate()

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="space-y-2">
        <h4 className="font-medium text-gray-900 line-clamp-2">
          {content.title}
        </h4>
        <p className="text-sm text-gray-600 line-clamp-2">
          {content.content.substring(0, 120)}...
        </p>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{content.source_name}</span>
            <span>•</span>
            <div className="flex items-center space-x-1">
              <ArrowTrendingUpIcon className="h-3 w-3" />
              <span>{content.relevance_score || 0}% relevant</span>
            </div>
          </div>
          
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => navigate('/content')}
          >
            Generate Draft
          </Button>
        </div>
      </div>
    </div>
  )
}
