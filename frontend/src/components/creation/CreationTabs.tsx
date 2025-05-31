import React from 'react'
import { Tab } from '@headlessui/react'
import { 
  SparklesIcon, 
  DocumentTextIcon, 
  CalendarIcon 
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

interface CreationTabsProps {
  value: 'recommendations' | 'drafts' | 'calendar'
  onChange: (value: 'recommendations' | 'drafts' | 'calendar') => void
}

export function CreationTabs({ value, onChange }: CreationTabsProps) {
  const tabs = [
    {
      key: 'recommendations' as const,
      label: 'Recommendations',
      icon: SparklesIcon,
      description: 'AI-powered draft recommendations'
    },
    {
      key: 'drafts' as const,
      label: 'Drafts',
      icon: DocumentTextIcon,
      description: 'Your content drafts'
    },
    {
      key: 'calendar' as const,
      label: 'Calendar',
      icon: CalendarIcon,
      description: 'Publishing schedule'
    }
  ]

  const selectedIndex = tabs.findIndex(tab => tab.key === value)

  return (
    <Tab.Group selectedIndex={selectedIndex} onChange={(index) => onChange(tabs[index].key)}>
      <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 p-1">
        {tabs.map((tab) => (
          <Tab
            key={tab.key}
            className={({ selected }) =>
              cn(
                'flex items-center space-x-2 rounded-md px-4 py-2 text-sm font-medium transition-all',
                'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
                selected
                  ? 'bg-white text-neural-700 shadow'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              )
            }
          >
            <tab.icon className="h-4 w-4" />
            <span>{tab.label}</span>
          </Tab>
        ))}
      </Tab.List>
    </Tab.Group>
  )
}
