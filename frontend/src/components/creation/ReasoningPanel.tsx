import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, CpuChipIcon as BrainIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'

interface ReasoningPanelProps {
  reasoning: string
  className?: string
}

export function ReasoningPanel({ reasoning, className }: ReasoningPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <Card variant="ai" className={className}>
      <div className="p-4">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center space-x-2">
            <BrainIcon className="h-4 w-4 text-ai-purple-600" />
            <span className="font-medium text-neural-700">AI Reasoning</span>
          </div>
          {isExpanded ? (
            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRightIcon className="h-4 w-4 text-gray-400" />
          )}
        </div>

        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-ai-purple-100">
            <p className="text-sm text-gray-700 leading-relaxed">
              {reasoning}
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
