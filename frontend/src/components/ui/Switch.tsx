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
