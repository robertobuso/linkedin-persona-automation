import React from 'react'
import { NavLink } from 'react-router-dom'
import { 
  HomeIcon,
  CpuChipIcon as BrainIcon,
  DocumentTextIcon,
  ChatBubbleLeftIcon,
  ChartBarIcon,
  CogIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useUIStore } from '@/stores/uiStore'
import { useEngagementStore } from '@/stores/engagementStore'
import { cn } from '@/utils/cn'

export function Sidebar() {
  const { sidebarOpen, sidebarCollapsed, setSidebarOpen, toggleSidebarCollapsed } = useUIStore()
  const { commentQueue } = useEngagementStore()

  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
      description: 'AI Intelligence Overview'
    },
    {
      name: 'Content',
      href: '/content',
      icon: BrainIcon,
      description: 'Content Intelligence'
    },
    {
      name: 'Creation',
      href: '/creation',
      icon: DocumentTextIcon,
      description: 'Creation Studio'
    },
    {
      name: 'Engagement',
      href: '/engagement',
      icon: ChatBubbleLeftIcon,
      description: 'Engagement Hub',
      badge: commentQueue.filter(opp => opp.priority === 'urgent' || opp.priority === 'high').length
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
      description: 'Persona Analytics'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: CogIcon,
      description: 'AI Configuration'
    }
  ]

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-gray-200 transition-all duration-300',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        sidebarCollapsed ? 'lg:w-16' : 'lg:w-64',
        'w-64'
      )}>
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-ai-purple-500 to-ml-green-500 rounded-lg flex items-center justify-center">
                <BrainIcon className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-neural-700">AI LinkedIn</h1>
                <p className="text-xs text-gray-500">Automation Platform</p>
              </div>
            </div>
          )}
          
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebarCollapsed}
            className="hidden lg:flex"
          >
            {sidebarCollapsed ? (
              <ChevronRightIcon className="h-4 w-4" />
            ) : (
              <ChevronLeftIcon className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigationItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors group',
                  isActive
                    ? 'bg-neural-100 text-neural-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )
              }
              title={sidebarCollapsed ? item.name : undefined}
            >
              <item.icon 
                className={cn(
                  'flex-shrink-0 h-5 w-5',
                  sidebarCollapsed ? 'mx-auto' : 'mr-3'
                )} 
              />
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1">{item.name}</span>
                  {item.badge && item.badge > 0 && (
                    <Badge variant="destructive" size="sm">
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 text-center">
              Powered by Advanced AI
            </div>
          </div>
        )}
      </div>
    </>
  )
}
