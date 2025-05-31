import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, CpuChipIcon as BrainIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from './ConfidenceIndicator'
import { cn } from '@/utils/cn'

interface AIAnalysisPanelProps {
  reasoning: string
  score?: number
  category?: string
  confidence?: number
  className?: string
  defaultExpanded?: boolean
}

export function AIAnalysisPanel({
  reasoning,
  score,
  category,
  confidence,
  className,
  defaultExpanded = false
}: AIAnalysisPanelProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <Card variant="ai" className={cn('transition-all duration-200', className)}>
      <div className="space-y-3">
        {/* Header */}
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center space-x-2">
            <BrainIcon className="h-4 w-4 text-ai-purple-600" />
            <span className="font-medium text-neural-700">AI Analysis</span>
            {category && (
              <Badge variant="ai" size="sm">
                {category}
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {score && (
              <span className="text-sm font-semibold text-neural-600">
                {Math.round(score)}%
              </span>
            )}
            {isExpanded ? (
              <ChevronDownIcon className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </div>

        {/* Content */}
        {isExpanded && (
          <div className="space-y-3 pt-2 border-t border-ai-purple-100">
            {/* Reasoning */}
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">AI Reasoning:</h5>
              <p className="text-sm text-gray-600 leading-relaxed">
                {reasoning}
              </p>
            </div>

            {/* Confidence indicator */}
            {confidence && (
              <div className="pt-2">
                <ConfidenceIndicator 
                  score={confidence}
                  label="Analysis Confidence"
                  size="sm"
                />
              </div>
            )}

            {/* Additional metrics */}
            {score && (
              <div className="flex items-center justify-between text-sm pt-2 border-t border-ai-purple-100">
                <span className="text-gray-600">Relevance Score:</span>
                <span className="font-medium text-neural-700">{Math.round(score)}%</span>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
