import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface PerformanceChartProps {
  data?: Array<{
    date: string
    likes: number
    comments: number
    shares: number
    views: number
  }>
}

export function PerformanceChart({ data = [] }: PerformanceChartProps) {
  const chartData = data.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }))

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700">Engagement Performance</h3>
          <div className="flex space-x-2">
            <Badge variant="success" size="sm">Likes</Badge>
            <Badge variant="ai" size="sm">Comments</Badge>
            <Badge variant="warning" size="sm">Shares</Badge>
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
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
              <Line 
                type="monotone" 
                dataKey="likes" 
                stroke="#10B981" 
                strokeWidth={3}
                dot={{ fill: '#10B981', strokeWidth: 2 }}
              />
              <Line 
                type="monotone" 
                dataKey="comments" 
                stroke="#a855f7" 
                strokeWidth={3}
                dot={{ fill: '#a855f7', strokeWidth: 2 }}
              />
              <Line 
                type="monotone" 
                dataKey="shares" 
                stroke="#F59E0B" 
                strokeWidth={3}
                dot={{ fill: '#F59E0B', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  )
}
