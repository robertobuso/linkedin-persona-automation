import React from 'react'
import { Tab } from '@headlessui/react'
import { cn } from '@/utils/cn'

interface TabsProps {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
}

interface TabsTriggerProps {
  value: string
  children: React.ReactNode
  className?: string
}

interface TabsContentProps {
  value: string
  children: React.ReactNode
  className?: string
}

export function Tabs({ children, className }: TabsProps) {
  return (
    <Tab.Group as="div" className={cn('w-full', className)}>
      {children}
    </Tab.Group>
  )
}

export function TabsList({ children, className }: TabsListProps) {
  return (
    <Tab.List className={cn(
      'inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500',
      className
    )}>
      {children}
    </Tab.List>
  )
}

export function TabsTrigger({ children, className }: TabsTriggerProps) {
  return (
    <Tab className={({ selected }) =>
      cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural-500 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        selected
          ? 'bg-white text-gray-950 shadow-sm'
          : 'hover:bg-gray-50 hover:text-gray-900',
        className
      )
    }>
      {children}
    </Tab>
  )
}

export function TabsContent({ children, className }: TabsContentProps) {
  return (
    <Tab.Panel className={cn(
      'mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural-500 focus-visible:ring-offset-2',
      className
    )}>
      {children}
    </Tab.Panel>
  )
}
