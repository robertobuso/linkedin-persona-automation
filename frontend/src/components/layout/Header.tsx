import React from 'react'
import { Menu, Transition } from '@headlessui/react'
import { 
  Bars3Icon,
  BellIcon,
  CogIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { useNotifications, notify } from '@/stores/uiStore'
import { cn } from '@/utils/cn'

export function Header() {
  const { toggleSidebar, sidebarCollapsed } = useUIStore()
  const { user, logout } = useAuthStore()
  const { notifications } = useNotifications()

  const unreadCount = notifications.filter(n => !n.read).length

  const handleLogout = async () => {
    try {
      logout()
      notify.success('Logged out successfully')
    } catch (error) {
      notify.error('Logout failed')
    }
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          {/* Sidebar toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="lg:hidden"
          >
            <Bars3Icon className="h-5 w-5" />
          </Button>

          {/* Breadcrumb or page title */}
          <div className="hidden lg:block">
            <h1 className="text-lg font-semibold text-gray-900">
              AI-Powered LinkedIn Automation
            </h1>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* AI Status indicator */}
          <AIQuickStatus />

          {/* Notifications */}
          <NotificationDropdown unreadCount={unreadCount} />

          {/* User menu */}
          <UserDropdown user={user} onLogout={handleLogout} />
        </div>
      </div>
    </header>
  )
}

function AIQuickStatus() {
  const { aiThinking, aiMessage } = useUIStore()

  if (!aiThinking) {
    return (
      <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500">
        <div className="w-2 h-2 bg-ml-green-500 rounded-full"></div>
        <span>AI Ready</span>
      </div>
    )
  }

  return (
    <div className="hidden md:flex items-center space-x-2 text-sm">
      <div className="w-2 h-2 bg-ai-purple-500 rounded-full animate-pulse"></div>
      <span className="text-ai-purple-600">
        {aiMessage || 'AI Processing...'}
      </span>
    </div>
  )
}

function NotificationDropdown({ unreadCount }: { unreadCount: number }) {
  const { notifications, removeNotification } = useNotifications()

  return (
    <Menu as="div" className="relative">
      <Menu.Button as={Button} variant="ghost" size="icon" className="relative">
        <BellIcon className="h-5 w-5" />
        {unreadCount > 0 && (
          <Badge 
            variant="destructive" 
            size="sm"
            className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
      </Menu.Button>

      <Transition
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 focus:outline-none z-50">
          <div className="p-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <p className="text-sm text-gray-500">{unreadCount} unread</p>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <BellIcon className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>No notifications</p>
              </div>
            ) : (
              notifications.slice(0, 5).map((notification) => (
                <Menu.Item key={notification.id}>
                  <div className="p-4 hover:bg-gray-50 border-b border-gray-100 last:border-b-0">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="font-medium text-sm text-gray-900">
                          {notification.title}
                        </p>
                        {notification.message && (
                          <p className="text-sm text-gray-600 mt-1">
                            {notification.message}
                          </p>
                        )}
                        <p className="text-xs text-gray-400 mt-2">
                          Just now
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeNotification(notification.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        ×
                      </Button>
                    </div>
                  </div>
                </Menu.Item>
              ))
            )}
          </div>

          {notifications.length > 0 && (
            <div className="p-4 border-t border-gray-100">
              <Button variant="ghost" size="sm" className="w-full">
                View all notifications
              </Button>
            </div>
          )}
        </Menu.Items>
      </Transition>
    </Menu>
  )
}

function UserDropdown({ 
  user, 
  onLogout 
}: { 
  user: any
  onLogout: () => void 
}) {
  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center space-x-2 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-neural-500">
        <Avatar
          fallback={user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
          size="md"
        />
        <div className="hidden md:block text-left">
          <p className="font-medium text-gray-700">
            {user?.full_name || 'User'}
          </p>
          <p className="text-xs text-gray-500">{user?.email}</p>
        </div>
        <ChevronDownIcon className="h-4 w-4 text-gray-400" />
      </Menu.Button>

      <Transition
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 focus:outline-none z-50">
          <div className="p-4 border-b border-gray-100">
            <p className="font-medium text-gray-900">{user?.full_name || 'User'}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>

          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  className={cn(
                    'flex items-center w-full px-4 py-2 text-sm text-left',
                    active ? 'bg-gray-50 text-gray-900' : 'text-gray-700'
                  )}
                >
                  <UserCircleIcon className="h-4 w-4 mr-3" />
                  Profile
                </button>
              )}
            </Menu.Item>

            <Menu.Item>
              {({ active }) => (
                <button
                  className={cn(
                    'flex items-center w-full px-4 py-2 text-sm text-left',
                    active ? 'bg-gray-50 text-gray-900' : 'text-gray-700'
                  )}
                >
                  <CogIcon className="h-4 w-4 mr-3" />
                  Settings
                </button>
              )}
            </Menu.Item>
          </div>

          <div className="py-1 border-t border-gray-100">
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={onLogout}
                  className={cn(
                    'flex items-center w-full px-4 py-2 text-sm text-left',
                    active ? 'bg-gray-50 text-red-600' : 'text-red-600'
                  )}
                >
                  <ArrowRightOnRectangleIcon className="h-4 w-4 mr-3" />
                  Sign out
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  )
}
