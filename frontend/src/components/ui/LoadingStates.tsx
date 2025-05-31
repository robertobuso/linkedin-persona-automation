import React from 'react'
import { cn } from '@/utils/cn'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-8 w-8',
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-current border-t-transparent',
        sizeClasses[size],
        className
      )}
    />
  )
}

interface LoadingDotsProps {
  className?: string
}

export function LoadingDots({ className }: LoadingDotsProps) {
  return (
    <div className={cn('flex space-x-1', className)}>
      <div className="h-2 w-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
      <div className="h-2 w-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
      <div className="h-2 w-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
    </div>
  )
}

interface SkeletonProps {
  className?: string
  children?: React.ReactNode
}

export function Skeleton({ className, children, ...props }: SkeletonProps) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-gray-200', className)}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-center space-x-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-[200px]" />
          <Skeleton className="h-4 w-[150px]" />
        </div>
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  )
}

interface LoadingPageProps {
  message?: string
}

export function LoadingPage({ message = 'Loading...' }: LoadingPageProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-96 space-y-4">
      <div className="relative">
        <Spinner size="lg" className="text-neural-500" />
        <div className="absolute inset-0 animate-ping">
          <Spinner size="lg" className="text-neural-300" />
        </div>
      </div>
      <p className="text-gray-600 font-medium">{message}</p>
    </div>
  )
}

interface AILoadingProps {
  message?: string
}

export function AILoading({ message = 'AI is thinking...' }: AILoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <div className="relative">
        <div className="h-12 w-12 rounded-full bg-gradient-to-r from-ai-purple-500 to-ml-green-500 animate-pulse" />
        <div className="absolute inset-0 h-12 w-12 rounded-full bg-gradient-to-r from-ai-purple-500 to-ml-green-500 animate-ping opacity-50" />
      </div>
      <div className="text-center space-y-2">
        <p className="text-neural-700 font-medium">{message}</p>
        <LoadingDots className="text-neural-500" />
      </div>
    </div>
  )
}

export function FullPageLoading() {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="text-center space-y-4">
        <div className="relative mx-auto">
          <Spinner size="lg" className="text-neural-500" />
          <div className="absolute inset-0 animate-ping">
            <Spinner size="lg" className="text-neural-300" />
          </div>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-neural-700">Loading Application</h3>
          <p className="text-gray-600">Please wait while we set things up...</p>
        </div>
      </div>
    </div>
  )
}