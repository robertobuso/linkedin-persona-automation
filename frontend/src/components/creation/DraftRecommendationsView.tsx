import React from 'react'
import { PaperAirplaneIcon, PencilIcon, ClockIcon } from '@heroicons/react/24/outline'
import { DraftRecommendationCard } from './DraftRecommendationCard'
import { RecommendationCategory } from './RecommendationCategory'
import { ScoredRecommendation } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

interface DraftRecommendationsViewProps {
  recommendations: ScoredRecommendation[]
}

export function DraftRecommendationsView({ recommendations }: DraftRecommendationsViewProps) {
  const categorizedRecommendations = {
    post_now: recommendations.filter(r => r.action === 'post_now'),
    review_and_edit: recommendations.filter(r => r.action === 'review_and_edit'),
    schedule_later: recommendations.filter(r => r.action === 'schedule_later'),
    skip: recommendations.filter(r => r.action === 'skip')
  }

  if (recommendations.length === 0) {
    return (
      <Card className="text-center py-12">
        <PaperAirplaneIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations available</h3>
        <p className="text-gray-600 mb-6">
          Create some drafts first to get AI-powered recommendations
        </p>
        <Button variant="ai">
          Generate New Drafts
        </Button>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Recommendation Categories Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <RecommendationCategory
          title="Ready to Publish"
          count={categorizedRecommendations.post_now.length}
          color="ml-green"
          icon={PaperAirplaneIcon}
          description="High-scoring drafts ready for immediate publishing"
        />
        <RecommendationCategory
          title="Needs Review"
          count={categorizedRecommendations.review_and_edit.length}
          color="prediction"
          icon={PencilIcon}
          description="Good content that could benefit from editing"
        />
        <RecommendationCategory
          title="Schedule Later"
          count={categorizedRecommendations.schedule_later.length}
          color="neural"
          icon={ClockIcon}
          description="Quality content to schedule for optimal timing"
        />
        <RecommendationCategory
          title="Skip for Now"
          count={categorizedRecommendations.skip.length}
          color="secondary"
          icon={ClockIcon}
          description="Content that may not align with current strategy"
        />
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neural-700">AI Recommendations</h3>
        {recommendations.map(recommendation => (
          <DraftRecommendationCard 
            key={recommendation.draft_id}
            recommendation={recommendation}
          />
        ))}
      </div>
    </div>
  )
}
