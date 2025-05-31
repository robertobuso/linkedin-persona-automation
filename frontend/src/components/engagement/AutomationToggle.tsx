import React from 'react'
import { Switch } from '@headlessui/react'
import { BoltIcon } from '@heroicons/react/24/outline'
import { Badge } from '@/components/ui/Badge'
import { useEngagementStore } from '@/stores/engagementStore'
import { cn } from '@/utils/cn'

export function AutomationToggle() {
  const { automationEnabled, toggleAutomation } = useEngagementStore()

  return (
    <div className="flex items-center space-x-3">
      <BoltIcon className="h-5 w-5 text-neural-600" />
      <span className="text-sm font-medium text-gray-700">Auto Engagement</span>
      <Switch
        checked={automationEnabled}
        onChange={toggleAutomation}
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
          automationEnabled ? 'bg-ml-green-500' : 'bg-gray-200'
        )}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            automationEnabled ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </Switch>
      <Badge variant={automationEnabled ? 'success' : 'secondary'} size="sm">
        {automationEnabled ? 'ON' : 'OFF'}
      </Badge>
    </div>
  )
}
