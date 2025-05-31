import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ArrowTrendingUpIcon, EyeIcon, HeartIcon } from '@heroicons/react/24/outline'

export function ContentPerformance() {
  const topPosts = [
    {
      id: 1,
      content: "Excited to share insights about AI in content marketing...",
      engagement: { likes: 245, comments: 32, shares: 18, views: 1200 },
      performance_score: 92,
      published_at: "2024-01-15"
    },
    {
      id: 2,
      content: "The future of LinkedIn automation is here...",
      engagement: { likes: 189, comments: 28, shares: 15, views: 980 },
      performance_score: 87,
      published_at: "2024-01-18"
    },
    {
      id: 3,
      content: "Key takeaways from the latest industry report...",
      engagement: { likes: 156, comments: 22, shares: 12, views: 850 },
      performance_score: 79,
      published_at: "2024-01-20"
    }
  ]

  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-6">Top Performing Content</h3>
        
        <div className="space-y-4">
          {topPosts.map((post, index) => (
            <div key={post.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <p className="text-gray-700 line-clamp-2 mb-2">
                    {post.content}
                  </p>
                  <p className="text-xs text-gray-500">
                    Published {new Date(post.published_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="success" size="sm">
                    #{index + 1}
                  </Badge>
                  <Badge variant="ai" size="sm">
                    {post.performance_score}% score
                  </Badge>
                </div>
              </div>
              
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="flex items-center space-x-1">
                  <HeartIcon className="h-4 w-4 text-red-500" />
                  <span>{post.engagement.likes}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <ArrowTrendingUpIcon className="h-4 w-4 text-blue-500" />
                  <span>{post.engagement.comments}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />
                  <span>{post.engagement.shares}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <EyeIcon className="h-4 w-4 text-purple-500" />
                  <span>{post.engagement.views}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
