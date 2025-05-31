import React from 'react'
import { CpuChipIcon as BrainIcon } from '@heroicons/react/24/outline'
import { useUIStore } from '@/stores/uiStore'
import { LoadingDots } from '@/components/ui/LoadingStates'

export function AIStatusIndicator() {
  const { aiThinking, aiMessage } = useUIStore()

  if (!aiThinking) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-40">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 max-w-sm">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <BrainIcon className="h-6 w-6 text-ai-purple-600" />
            <div className="absolute inset-0 animate-ping">
              <BrainIcon className="h-6 w-6 text-ai-purple-400 opacity-50" />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="font-medium text-neural-700">AI Processing</div>
            <div className="text-sm text-gray-600">
              {aiMessage || 'Working on your request...'}
            </div>
            <div className="mt-2">
              <LoadingDots className="text-ai-purple-500" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
