import React from 'react'
import { 
  CpuChipIcon as BrainIcon, 
  PlusIcon, 
  PlayIcon, 
  MagnifyingGlassIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { useContentStore } from '@/stores/contentStore'
import { useEngagementStore } from '@/stores/engagementStore'
import { notify } from '@/stores/uiStore'
import { useNavigate } from 'react-router-dom'

export function QuickActionsPanel() {
  const navigate = useNavigate()
  const { runAIContentSelection } = useContentStore()
  const { discoverNewPosts } = useEngagementStore()

  const handleAISelection = async () => {
    try {
      await runAIContentSelection()
      notify.success('AI content selection completed')
    } catch (error) {
      notify.error('Failed to run AI selection')
    }
  }

  const handleDiscoverPosts = async () => {
    try {
      await discoverNewPosts()
      notify.success('New engagement opportunities discovered')
    } catch (error) {
      notify.error('Failed to discover new posts')
    }
  }

  const actions = [
    {
      icon: BrainIcon,
      label: 'Run AI Selection',
      description: 'Analyze and select today\'s best content',
      onClick: handleAISelection,
      variant: 'ai' as const
    },
    {
      icon: PlusIcon,
      label: 'Create Draft',
      description: 'Generate new LinkedIn post',
      onClick: () => navigate('/creation'),
      variant: 'default' as const
    },
    {
      icon: MagnifyingGlassIcon,
      label: 'Discover Posts',
      description: 'Find new engagement opportunities',
      onClick: handleDiscoverPosts,
      variant: 'secondary' as const
    },
    {
      icon: ChartBarIcon,
      label: 'View Analytics',
      description: 'See your performance insights',
      onClick: () => navigate('/analytics'),
      variant: 'outline' as const
    }
  ]

  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {actions.map((action) => (
            <Button
              key={action.label}
              variant={action.variant}
              className="h-auto p-4 flex flex-col items-center space-y-2 text-center"
              onClick={action.onClick}
            >
              <action.icon className="h-6 w-6" />
              <div>
                <div className="font-medium">{action.label}</div>
                <div className="text-xs opacity-80">{action.description}</div>
              </div>
            </Button>
          ))}
        </div>
      </div>
    </Card>
  )
}
