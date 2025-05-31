import React from 'react'
import { Transition } from '@headlessui/react'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  InformationCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline'
import { useNotifications } from '@/stores/uiStore'
import { cn } from '@/utils/cn'

export function NotificationCenter() {
  const { notifications, removeNotification } = useNotifications()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <Transition
          key={notification.id}
          show={true}
          enter="transform ease-out duration-300 transition"
          enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
          enterTo="translate-y-0 opacity-100 sm:translate-x-0"
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <NotificationItem
            notification={notification}
            onDismiss={() => removeNotification(notification.id)}
          />
        </Transition>
      ))}
    </div>
  )
}

function NotificationItem({ 
  notification, 
  onDismiss 
}: { 
  notification: any
  onDismiss: () => void 
}) {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }

  const colors = {
    success: 'bg-ml-green-50 border-ml-green-200 text-ml-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-prediction-50 border-prediction-200 text-prediction-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  }

  const iconColors = {
    success: 'text-ml-green-500',
    error: 'text-red-500',
    warning: 'text-prediction-500',
    info: 'text-blue-500',
  }

  const Icon = icons[notification.type]

  return (
    <div className={cn(
      'rounded-lg border p-4 shadow-lg backdrop-blur-sm',
      colors[notification.type]
    )}>
      <div className="flex items-start">
        <Icon className={cn('h-5 w-5 mt-0.5 mr-3', iconColors[notification.type])} />
        <div className="flex-1 min-w-0">
          <h4 className="font-medium">{notification.title}</h4>
          {notification.message && (
            <p className="mt-1 text-sm opacity-90">{notification.message}</p>
          )}
          {notification.action && (
            <button
              onClick={notification.action.onClick}
              className="mt-2 text-sm font-medium underline hover:no-underline"
            >
              {notification.action.label}
            </button>
          )}
        </div>
        <button
          onClick={onDismiss}
          className="ml-2 flex-shrink-0 hover:opacity-70"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
