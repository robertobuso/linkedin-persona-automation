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
