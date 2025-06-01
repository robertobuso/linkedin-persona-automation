import React from 'react'
import { Card } from '@/components/ui/Card'
import { CpuChipIcon as BrainIcon } from '@heroicons/react/24/outline'

interface AIThinkingIndicatorProps {
  message?: string
  compact?: boolean
}

export function AIThinkingIndicator({ 
  message = "AI is thinking...", 
  compact = false 
}: AIThinkingIndicatorProps) {
  if (compact) {
    return (
      <div className="flex items-center space-x-2 text-ai-purple-600">
        <BrainIcon className="h-4 w-4 ai-thinking" />
        <span className="text-sm">{message}</span>
        <div className="loading-dots">
          <div className="bg-ai-purple-500"></div>
          <div className="bg-ml-green-500"></div>
          <div className="bg-prediction-500"></div>
        </div>
      </div>
    )
  }

  return (
    <Card variant="ai">
      <div className="p-4">
        <div className="flex items-center space-x-3">
          <BrainIcon className="h-6 w-6 text-ai-purple-600 ai-thinking" />
          <div className="flex-1">
            <p className="text-sm font-medium text-ai-purple-700">{message}</p>
            <div className="loading-dots mt-2">
              <div className="bg-ai-purple-500"></div>
              <div className="bg-ml-green-500"></div>
              <div className="bg-prediction-500"></div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}