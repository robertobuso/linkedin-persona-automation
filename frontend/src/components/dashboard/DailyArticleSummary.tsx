import React from 'react'
import { DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useDailyArticleSummary } from '@/stores/contentStore'
import { Skeleton } from '@/components/ui/LoadingStates'
import { useNavigate } from 'react-router-dom'

export function DailyArticleSummary() {
  const { data: summary, isLoading } = useDailyArticleSummary()
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <Card>
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </Card>
    )
  }

  if (!summary) {
    return null
  }

  return (
    <Card intelligence>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
            <DocumentTextIcon className="h-5 w-5" />
            <span>Daily Article Summary</span>
          </h3>
          <div className="flex items-center space-x-2">
            <Badge variant="ai" size="sm">
              <SparklesIcon className="h-3 w-3 mr-1" />
              AI Generated
            </Badge>
            <Badge variant="neutral" size="sm">
              {new Date(summary.date).toLocaleDateString()}
            </Badge>
          </div>
        </div>

        <div className="space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-neural-50 rounded-lg">
            <div className="text-center">
              <div className="text-xl font-bold text-neural-600">
                {summary.total_articles}
              </div>
              <div className="text-sm text-gray-600">Total Articles</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-ml-green-600">
                {summary.ai_selected_count}
              </div>
              <div className="text-sm text-gray-600">AI Selected</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-prediction-600">
                {Math.round(summary.selection_metadata.avg_relevance_score)}%
              </div>
              <div className="text-sm text-gray-600">Avg Relevance</div>
            </div>
          </div>

          {/* AI Summary */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2">AI Summary</h4>
            <p className="text-gray-700 leading-relaxed">
              {summary.summary_text}
            </p>
          </div>

          {/* Top categories */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Top Categories</h4>
            <div className="flex flex-wrap gap-2">
              {summary.selection_metadata.top_categories.map((category) => (
                <Badge key={category} variant="neutral" size="sm">
                  {category}
                </Badge>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex space-x-3 pt-4 border-t border-gray-100">
            <Button 
              variant="ai" 
              size="sm"
              onClick={() => navigate('/content')}
            >
              View Selected Content
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => navigate('/creation')}
            >
              Generate Drafts
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
