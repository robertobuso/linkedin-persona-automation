# Missing UI and Layout Components

## Base UI Components

### `src/components/ui/index.ts` - UI Components Export
```typescript
export { Button, buttonVariants } from './Button'
export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './Card'
export { Badge, badgeVariants } from './Badge'
export { Input } from './Input'
export { Modal, ConfirmModal } from './Modal'
export { 
  Spinner, 
  LoadingDots, 
  Skeleton, 
  CardSkeleton, 
  TableSkeleton, 
  LoadingPage, 
  AILoading, 
  FullPageLoading 
} from './LoadingStates'
export { Select } from './Select'
export { Switch } from './Switch'
export { Textarea } from './Textarea'
export { Tooltip } from './Tooltip'
export { Dropdown } from './Dropdown'
export { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs'
export { Progress } from './Progress'
export { Avatar } from './Avatar'
export { Alert, AlertDescription, AlertTitle } from './Alert'
```

### `src/components/ui/Select.tsx` - Select Component
```typescript
import React from 'react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: Array<{ value: string; label: string; disabled?: boolean }>
  placeholder?: string
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, placeholder, ...props }, ref) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            className={cn(
              'flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white',
              'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              'appearance-none pr-8',
              error && 'border-red-500 focus:ring-red-500',
              className
            )}
            ref={ref}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option 
                key={option.value} 
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          <ChevronDownIcon className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 pointer-events-none" />
        </div>
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export { Select }
```

### `src/components/ui/Switch.tsx` - Switch Component
```typescript
import React from 'react'
import { Switch as HeadlessSwitch } from '@headlessui/react'
import { cn } from '@/utils/cn'

interface SwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Switch({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md',
  className
}: SwitchProps) {
  const sizeClasses = {
    sm: 'h-4 w-8',
    md: 'h-6 w-11',
    lg: 'h-8 w-14'
  }

  const thumbSizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4', 
    lg: 'h-6 w-6'
  }

  const translateClasses = {
    sm: checked ? 'translate-x-4' : 'translate-x-1',
    md: checked ? 'translate-x-6' : 'translate-x-1',
    lg: checked ? 'translate-x-8' : 'translate-x-1'
  }

  if (label || description) {
    return (
      <div className={cn('flex items-start space-x-3', className)}>
        <HeadlessSwitch
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          className={cn(
            'relative inline-flex items-center rounded-full transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
            sizeClasses[size],
            checked ? 'bg-neural-600' : 'bg-gray-200',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <span
            className={cn(
              'inline-block transform rounded-full bg-white transition-transform',
              thumbSizeClasses[size],
              translateClasses[size]
            )}
          />
        </HeadlessSwitch>
        
        <div className="flex-1">
          {label && (
            <label className="text-sm font-medium text-gray-900">
              {label}
            </label>
          )}
          {description && (
            <p className="text-sm text-gray-500">{description}</p>
          )}
        </div>
      </div>
    )
  }

  return (
    <HeadlessSwitch
      checked={checked}
      onChange={onChange}
      disabled={disabled}
      className={cn(
        'relative inline-flex items-center rounded-full transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
        sizeClasses[size],
        checked ? 'bg-neural-600' : 'bg-gray-200',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <span
        className={cn(
          'inline-block transform rounded-full bg-white transition-transform',
          thumbSizeClasses[size],
          translateClasses[size]
        )}
      />
    </HeadlessSwitch>
  )
}
```

### `src/components/ui/Textarea.tsx` - Textarea Component  
```typescript
import React from 'react'
import { cn } from '@/utils/cn'

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, ...props }, ref) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            {label}
          </label>
        )}
        <textarea
          className={cn(
            'flex min-h-[80px] w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white',
            'placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural-500 focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50 resize-none',
            error && 'border-red-500 focus-visible:ring-red-500',
            className
          )}
          ref={ref}
          {...props}
        />
        {helperText && !error && (
          <p className="text-sm text-gray-500">{helperText}</p>
        )}
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

export { Textarea }
```

### `src/components/ui/Tooltip.tsx` - Tooltip Component
```typescript
import React, { useState } from 'react'
import { cn } from '@/utils/cn'

interface TooltipProps {
  children: React.ReactNode
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
}

export function Tooltip({ children, content, position = 'top', className }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  }

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-900',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900',
    left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-900',
    right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-900'
  }

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div 
          className={cn(
            'absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded whitespace-nowrap',
            positionClasses[position],
            className
          )}
        >
          {content}
          <div 
            className={cn(
              'absolute w-0 h-0 border-4',
              arrowClasses[position]
            )}
          />
        </div>
      )}
    </div>
  )
}
```

### `src/components/ui/Progress.tsx` - Progress Component
```typescript
import React from 'react'
import { cn } from '@/utils/cn'

interface ProgressProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'error'
  showValue?: boolean
  className?: string
}

export function Progress({ 
  value, 
  max = 100, 
  size = 'md', 
  variant = 'default',
  showValue = false,
  className 
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const variantClasses = {
    default: 'bg-neural-500',
    success: 'bg-ml-green-500',
    warning: 'bg-prediction-500',
    error: 'bg-red-500'
  }

  return (
    <div className={cn('w-full', className)}>
      <div className={cn(
        'w-full bg-gray-200 rounded-full overflow-hidden',
        sizeClasses[size]
      )}>
        <div
          className={cn(
            'h-full transition-all duration-300 ease-in-out',
            variantClasses[variant]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showValue && (
        <div className="flex justify-between text-sm text-gray-600 mt-1">
          <span>{value}</span>
          <span>{max}</span>
        </div>
      )}
    </div>
  )
}
```

### `src/components/ui/Avatar.tsx` - Avatar Component
```typescript
import React from 'react'
import { cn } from '@/utils/cn'

interface AvatarProps {
  src?: string
  alt?: string
  fallback?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

export function Avatar({ src, alt, fallback, size = 'md', className }: AvatarProps) {
  const sizeClasses = {
    sm: 'h-6 w-6 text-xs',
    md: 'h-8 w-8 text-sm',
    lg: 'h-12 w-12 text-base',
    xl: 'h-16 w-16 text-lg'
  }

  if (src) {
    return (
      <img
        src={src}
        alt={alt || 'Avatar'}
        className={cn(
          'rounded-full object-cover',
          sizeClasses[size],
          className
        )}
      />
    )
  }

  return (
    <div
      className={cn(
        'bg-gradient-to-r from-ai-purple-500 to-ml-green-500 rounded-full flex items-center justify-center text-white font-medium',
        sizeClasses[size],
        className
      )}
    >
      {fallback || '?'}
    </div>
  )
}
```

### `src/components/ui/Alert.tsx` - Alert Component
```typescript
import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon, 
  XCircleIcon 
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

const alertVariants = cva(
  'relative w-full rounded-lg border p-4',
  {
    variants: {
      variant: {
        default: 'bg-blue-50 text-blue-900 border-blue-200',
        destructive: 'bg-red-50 text-red-900 border-red-200',
        warning: 'bg-prediction-50 text-prediction-900 border-prediction-200',
        success: 'bg-ml-green-50 text-ml-green-900 border-ml-green-200',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  icon?: boolean
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant, icon = true, children, ...props }, ref) => {
    const icons = {
      default: InformationCircleIcon,
      destructive: XCircleIcon,
      warning: ExclamationTriangleIcon,
      success: CheckCircleIcon,
    }

    const Icon = icons[variant || 'default']

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(alertVariants({ variant }), className)}
        {...props}
      >
        <div className="flex">
          {icon && (
            <div className="flex-shrink-0">
              <Icon className="h-5 w-5" />
            </div>
          )}
          <div className={cn('flex-1', icon && 'ml-3')}>
            {children}
          </div>
        </div>
      </div>
    )
  }
)

Alert.displayName = 'Alert'

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn('mb-1 font-medium leading-none tracking-tight', className)}
    {...props}
  />
))
AlertTitle.displayName = 'AlertTitle'

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('text-sm opacity-90', className)}
    {...props}
  />
))
AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertTitle, AlertDescription }
```

### `src/components/ui/Tabs.tsx` - Tabs Component
```typescript
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
```

### `src/components/ui/Dropdown.tsx` - Dropdown Component
```typescript
import React from 'react'
import { Menu, Transition } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

interface DropdownProps {
  trigger: React.ReactNode
  children: React.ReactNode
  align?: 'left' | 'right'
  className?: string
}

interface DropdownItemProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
}

export function Dropdown({ trigger, children, align = 'left', className }: DropdownProps) {
  return (
    <Menu as="div" className={cn('relative inline-block text-left', className)}>
      <Menu.Button as="div">
        {trigger}
      </Menu.Button>

      <Transition
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className={cn(
          'absolute z-50 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none',
          align === 'right' ? 'right-0' : 'left-0'
        )}>
          <div className="py-1">
            {children}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  )
}

export function DropdownItem({ children, onClick, disabled, className }: DropdownItemProps) {
  return (
    <Menu.Item disabled={disabled}>
      {({ active }) => (
        <button
          onClick={onClick}
          className={cn(
            'block w-full px-4 py-2 text-left text-sm',
            active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
            disabled && 'opacity-50 cursor-not-allowed',
            className
          )}
        >
          {children}
        </button>
      )}
    </Menu.Item>
  )
}
```

## Layout Components

### `src/components/layout/index.ts` - Layout Components Export
```typescript
export { AppLayout, AuthLayout, EmptyLayout } from './AppLayout'
export { Header } from './Header'
export { Sidebar } from './Sidebar'
export { NotificationCenter } from './NotificationCenter'
export { AIStatusIndicator } from './AIStatusIndicator'
```

### `src/components/layout/Header.tsx` - Complete Header Component
```typescript
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
```

### `src/components/layout/Sidebar.tsx` - Complete Sidebar Component
```typescript
import React from 'react'
import { NavLink } from 'react-router-dom'
import { 
  HomeIcon,
  BrainIcon,
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
```

### `src/components/layout/NotificationCenter.tsx` - Complete Notification System
```typescript
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
```

### `src/components/layout/AIStatusIndicator.tsx` - AI Status Display
```typescript
import React from 'react'
import { BrainIcon } from '@heroicons/react/24/outline'
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
```

# Missing Core Files

## `src/utils/cn.ts` - ClassName Utility
```typescript
import { type ClassValue, clsx } from "clsx"

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}
```

## `src/stores/uiStore.ts` - UI State Management
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  read?: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

interface UIState {
  // Navigation
  sidebarOpen: boolean
  activeTab: string
  sidebarCollapsed: boolean
  
  // Notifications
  notifications: Notification[]
  
  // Modals
  activeModal: string | null
  modalData: any
  
  // Loading states
  globalLoading: boolean
  loadingStates: Record<string, boolean>
  
  // Theme and preferences
  theme: 'light' | 'dark' | 'system'
  
  // AI Features
  aiThinking: boolean
  aiMessage: string | null
}

interface UIActions {
  // Navigation
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  toggleSidebarCollapsed: () => void
  setActiveTab: (tab: string) => void
  
  // Notifications
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  
  // Modals
  openModal: (modalId: string, data?: any) => void
  closeModal: () => void
  
  // Loading states
  setGlobalLoading: (loading: boolean) => void
  setLoadingState: (key: string, loading: boolean) => void
  
  // Theme
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  
  // AI Features
  setAIThinking: (thinking: boolean, message?: string) => void
  clearAIState: () => void
}

type UIStore = UIState & UIActions

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // Initial state
      sidebarOpen: true,
      activeTab: 'dashboard',
      sidebarCollapsed: false,
      notifications: [],
      activeModal: null,
      modalData: null,
      globalLoading: false,
      loadingStates: {},
      theme: 'system',
      aiThinking: false,
      aiMessage: null,

      // Actions
      setSidebarOpen: (open) => {
        set({ sidebarOpen: open })
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }))
      },

      toggleSidebarCollapsed: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
      },

      setActiveTab: (tab) => {
        set({ activeTab: tab })
      },

      addNotification: (notification) => {
        const id = Math.random().toString(36).substr(2, 9)
        const newNotification: Notification = {
          id,
          duration: 5000, // Default 5 seconds
          read: false,
          ...notification,
        }

        set((state) => ({
          notifications: [...state.notifications, newNotification],
        }))

        // Auto-remove after duration
        if (newNotification.duration && newNotification.duration > 0) {
          setTimeout(() => {
            get().removeNotification(id)
          }, newNotification.duration)
        }

        return id
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }))
      },

      clearNotifications: () => {
        set({ notifications: [] })
      },

      openModal: (modalId, data) => {
        set({ activeModal: modalId, modalData: data })
      },

      closeModal: () => {
        set({ activeModal: null, modalData: null })
      },

      setGlobalLoading: (loading) => {
        set({ globalLoading: loading })
      },

      setLoadingState: (key, loading) => {
        set((state) => ({
          loadingStates: {
            ...state.loadingStates,
            [key]: loading,
          },
        }))
      },

      setTheme: (theme) => {
        set({ theme })
      },

      setAIThinking: (thinking, message) => {
        set({ aiThinking: thinking, aiMessage: message || null })
      },

      clearAIState: () => {
        set({ aiThinking: false, aiMessage: null })
      },
    }),
    {
      name: 'ui-preferences',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
)

// Helper hooks
export const useNotifications = () => {
  const { notifications, addNotification, removeNotification, clearNotifications } = useUIStore()
  return { notifications, addNotification, removeNotification, clearNotifications }
}

export const useModal = () => {
  const { activeModal, modalData, openModal, closeModal } = useUIStore()
  return { activeModal, modalData, openModal, closeModal }
}

export const useLoadingState = (key: string) => {
  const { loadingStates, setLoadingState } = useUIStore()
  return {
    isLoading: loadingStates[key] || false,
    setLoading: (loading: boolean) => setLoadingState(key, loading),
  }
}

// Notification helpers
export const notify = {
  success: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'success', title, message })
  },
  error: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'error', title, message, duration: 8000 })
  },
  warning: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'warning', title, message })
  },
  info: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'info', title, message })
  },
}
```

## `src/stores/authStore.ts` - Authentication Store (if also missing)
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api, type User } from '@/lib/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; full_name?: string }) => Promise<void>
  logout: () => void
  clearError: () => void
  checkAuth: () => Promise<void>
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email, password) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await api.login(email, password)
          const { access_token, user } = response
          
          localStorage.setItem('token', access_token)
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Login failed',
            isAuthenticated: false,
          })
          throw error
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await api.register(data)
          const { access_token, user } = response
          
          localStorage.setItem('token', access_token)
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Registration failed',
            isAuthenticated: false,
          })
          throw error
        }
      },

      logout: () => {
        localStorage.removeItem('token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },

      clearError: () => {
        set({ error: null })
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token')
        
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        try {
          const user = await api.getCurrentUser()
          set({
            user,
            token,
            isAuthenticated: true,
          })
        } catch (error) {
          localStorage.removeItem('token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
)
```

## `src/stores/engagementStore.ts` - Engagement Store (if missing)
```typescript
import { create } from 'zustand'
import { api, type EngagementOpportunity } from '@/lib/api'

interface EngagementStats {
  total_opportunities: number
  completion_rate: number
  status_breakdown: Record<string, number>
  type_breakdown: Record<string, number>
  period_days: number
  generated_at: string
}

interface EngagementState {
  // Opportunity data
  commentQueue: EngagementOpportunity[]
  highPriorityOpportunities: EngagementOpportunity[]
  allOpportunities: EngagementOpportunity[]
  
  // Stats
  engagementStats: EngagementStats | null
  
  // Settings
  automationEnabled: boolean
  
  // UI state
  isLoading: boolean
  error: string | null
  selectedOpportunity: EngagementOpportunity | null
}

interface EngagementActions {
  // Data fetching
  fetchCommentOpportunities: (params?: {
    limit?: number
    priority?: string
    status?: string
  }) => Promise<void>
  fetchHighPriorityOpportunities: () => Promise<void>
  fetchEngagementStats: (days?: number) => Promise<void>
  
  // Opportunity management
  createComment: (data: {
    opportunity_id: string
    comment_text?: string
  }) => Promise<void>
  discoverNewPosts: (maxPosts?: number) => Promise<void>
  
  // Queue management
  updateQueue: (opportunities: EngagementOpportunity[]) => void
  removeFromQueue: (opportunityId: string) => void
  addToQueue: (opportunity: EngagementOpportunity) => void
  
  // Settings
  toggleAutomation: () => void
  setAutomationEnabled: (enabled: boolean) => void
  
  // UI state
  setSelectedOpportunity: (opportunity: EngagementOpportunity | null) => void
  clearError: () => void
  
  // Refresh
  refreshEngagementData: () => Promise<void>
}

type EngagementStore = EngagementState & EngagementActions

export const useEngagementStore = create<EngagementStore>((set, get) => ({
  // Initial state
  commentQueue: [],
  highPriorityOpportunities: [],
  allOpportunities: [],
  engagementStats: null,
  automationEnabled: false,
  isLoading: false,
  error: null,
  selectedOpportunity: null,

  // Actions
  fetchCommentOpportunities: async (params) => {
    set({ isLoading: true, error: null })
    
    try {
      const opportunities = await api.getCommentOpportunities(params)
      
      set({
        commentQueue: opportunities,
        allOpportunities: opportunities,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to fetch comment opportunities',
      })
    }
  },

  fetchHighPriorityOpportunities: async () => {
    try {
      const opportunities = await api.getCommentOpportunities({
        priority: 'high',
        limit: 10,
      })
      
      set({ highPriorityOpportunities: opportunities })
    } catch (error: any) {
      console.error('Failed to fetch high priority opportunities:', error)
    }
  },

  fetchEngagementStats: async (days = 30) => {
    try {
      const stats = await api.getEngagementStats(days)
      set({ engagementStats: stats })
    } catch (error: any) {
      console.error('Failed to fetch engagement stats:', error)
    }
  },

  createComment: async (data) => {
    set({ isLoading: true, error: null })
    
    try {
      const result = await api.createComment(data)
      
      // Remove the opportunity from queue after successful comment
      set((state) => ({
        commentQueue: state.commentQueue.filter(
          (opp) => opp.id !== data.opportunity_id
        ),
        allOpportunities: state.allOpportunities.filter(
          (opp) => opp.id !== data.opportunity_id
        ),
        isLoading: false,
      }))
      
      return result
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to create comment',
      })
      throw error
    }
  },

  discoverNewPosts: async (maxPosts = 50) => {
    set({ isLoading: true, error: null })
    
    try {
      await api.discoverCommentPosts(maxPosts)
      
      // Refresh opportunities after discovery
      await get().fetchCommentOpportunities()
      
      set({ isLoading: false })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to discover new posts',
      })
      throw error
    }
  },

  updateQueue: (opportunities) => {
    set({ commentQueue: opportunities })
  },

  removeFromQueue: (opportunityId) => {
    set((state) => ({
      commentQueue: state.commentQueue.filter((opp) => opp.id !== opportunityId),
      allOpportunities: state.allOpportunities.filter((opp) => opp.id !== opportunityId),
    }))
  },

  addToQueue: (opportunity) => {
    set((state) => ({
      commentQueue: [opportunity, ...state.commentQueue],
      allOpportunities: [opportunity, ...state.allOpportunities],
    }))
  },

  toggleAutomation: () => {
    set((state) => ({ automationEnabled: !state.automationEnabled }))
  },

  setAutomationEnabled: (enabled) => {
    set({ automationEnabled: enabled })
  },

  setSelectedOpportunity: (opportunity) => {
    set({ selectedOpportunity: opportunity })
  },

  clearError: () => {
    set({ error: null })
  },

  refreshEngagementData: async () => {
    await Promise.all([
      get().fetchCommentOpportunities(),
      get().fetchHighPriorityOpportunities(),
      get().fetchEngagementStats(),
    ])
  },
}))

// Helper hooks
export const useEngagementQueue = () => {
  const { commentQueue, isLoading, error } = useEngagementStore()
  return { commentQueue, isLoading, error }
}

export const useHighPriorityOpportunities = () => {
  const { highPriorityOpportunities } = useEngagementStore()
  return highPriorityOpportunities
}
```

## `src/lib/api.ts` - API Client (if missing the basic types)
```typescript
// Basic User interface for auth store
export interface User {
  id: string
  email: string
  full_name?: string
  linkedin_profile_url?: string
  is_active: boolean
  preferences?: Record<string, any>
  created_at: string
  updated_at: string
}

// Basic EngagementOpportunity interface
export interface EngagementOpportunity {
  id: string
  target_id: string
  target_content: string
  target_author: string
  target_url?: string
  engagement_type: 'comment' | 'like' | 'share'
  priority: 'urgent' | 'high' | 'medium' | 'low'
  status: 'pending' | 'scheduled' | 'completed' | 'failed' | 'skipped'
  relevance_score?: number
  context_tags?: string[]
  engagement_reason?: string
  suggested_comment?: string
  ai_analysis?: {
    confidence_score?: number
    optimal_timing?: string
    success_probability?: number
  }
  created_at: string
  scheduled_for?: string
  completed_at?: string
}

// Basic API client class for auth
class APIClient {
  private baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token')
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    return response.json()
  }

  // Authentication
  async login(email: string, password: string) {
    return this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(data: { email: string; password: string; full_name?: string }) {
    return this.request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getCurrentUser() {
    return this.request<User>('/auth/me')
  }

  // Engagement (basic methods to prevent errors)
  async getCommentOpportunities(params?: any) {
    return this.request<EngagementOpportunity[]>('/engagement/comment-opportunities')
  }

  async discoverCommentPosts(maxPosts: number) {
    return this.request('/engagement/discover-posts', { method: 'POST' })
  }

  async createComment(data: any) {
    return this.request('/engagement/comment', { method: 'POST', body: JSON.stringify(data) })
  }

  async getEngagementStats(days: number) {
    return this.request(`/engagement/stats?period_days=${days}`)
  }

  // Placeholder methods to prevent errors
  async getDailyArticleSummary() {
    return this.request('/content/daily-summary')
  }
}

export const api = new APIClient()
```

## Quick File Summary:

**Create these files:**

1. **`src/utils/cn.ts`** - ClassName utility function
2. **`src/stores/uiStore.ts`** - UI state management with notifications
3. **`src/stores/authStore.ts`** - Authentication state management  
4. **`src/stores/engagementStore.ts`** - Engagement features state
5. **`src/lib/api.ts`** - Basic API client (if missing)

After adding these files, your app should start working! Try:

```bash
cd frontend
npm run dev
```