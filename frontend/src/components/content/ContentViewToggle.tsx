import React from 'react'
import { Tab } from '@headlessui/react'
import { CpuChipIcon as BrainIcon, NewspaperIcon, ArrowTrendingUpIcon, ViewColumnsIcon } from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

interface ContentViewToggleProps {
  value: 'ai-selected' | 'fresh' | 'trending' | 'all'
  onChange: (value: 'ai-selected' | 'fresh' | 'trending' | 'all') => void
}

export function ContentViewToggle({ value, onChange }: ContentViewToggleProps) {
  const views = [
    {
      key: 'ai-selected' as const,
      label: 'AI Selected',
      icon: BrainIcon,
      description: 'Content selected by AI'
    },
    {
      key: 'fresh' as const,
      label: 'Fresh',
      icon: NewspaperIcon,
      description: 'Recently published'
    },
    {
      key: 'trending' as const,
      label: 'Trending',
      icon: ArrowTrendingUpIcon,
      description: 'Popular content'
    },
    {
      key: 'all' as const,
      label: 'All',
      icon: ViewColumnsIcon,
      description: 'All available content'
    }
  ]

  const selectedIndex = views.findIndex(view => view.key === value)

  return (
    <Tab.Group selectedIndex={selectedIndex} onChange={(index) => onChange(views[index].key)}>
      <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 p-1">
        {views.map((view) => (
          <Tab
            key={view.key}
            className={({ selected }) =>
              cn(
                'flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-medium transition-all',
                'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
                selected
                  ? 'bg-white text-neural-700 shadow'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              )
            }
          >
            <view.icon className="h-4 w-4" />
            <span>{view.label}</span>
          </Tab>
        ))}
      </Tab.List>
    </Tab.Group>
  )
}
