import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card } from '@/components/ui/Card'

interface EngagementTrendsProps {
  data?: {
    posting_frequency: 'increasing' | 'decreasing' | 'stable'
    engagement_trend: 'improving' | 'declining' | 'stable'
    best_performing_time: string
    top_content_types: string[]
  }
}

export function EngagementTrends({ data }: EngagementTrendsProps) {
  const trendData = [
    { name: 'Mon', engagement: 65 },
    { name: 'Tue', engagement: 78 },
    { name: 'Wed', engagement: 90 },
    { name: 'Thu', engagement: 81 },
    { name: 'Fri', engagement: 56 },
    { name: 'Sat', engagement: 45 },
    { name: 'Sun', engagement: 38 },
  ]

  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-6">Weekly Engagement Trends</h3>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="name" 
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis 
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Bar 
                dataKey="engagement" 
                fill="#10B981" 
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {data && (
          <div className="mt-6 pt-4 border-t border-gray-100">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Best Time:</span>
                <span className="font-medium text-gray-900 ml-2">{data.best_performing_time}</span>
              </div>
              <div>
                <span className="text-gray-600">Trend:</span>
                <span className={`font-medium ml-2 ${
                  data.engagement_trend === 'improving' ? 'text-ml-green-600' : 
                  data.engagement_trend === 'declining' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {data.engagement_trend}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
