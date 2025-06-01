import React from 'react'
import { Card } from './Card'
import { CpuChipIcon as BrainIcon } from '@heroicons/react/24/outline'

interface LoadingPageProps {
  message?: string
  submessage?: string
}

export function FullPageLoading() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-ai-purple-500 to-ml-green-500 rounded-xl flex items-center justify-center mx-auto mb-4 ai-thinking">
          <BrainIcon className="h-8 w-8 text-white" />
        </div>
        <div className="loading-dots">
          <div></div>
          <div></div>
          <div></div>
        </div>
      </div>
    </div>
  )
}

export function LoadingPage({ message = "Loading...", submessage }: LoadingPageProps) {
  return (
    <div className="flex items-center justify-center min-h-96">
      <div className="text-center">
        <div className="w-12 h-12 bg-gradient-to-r from-ai-purple-500 to-ml-green-500 rounded-lg flex items-center justify-center mx-auto mb-4 ai-thinking">
          <BrainIcon className="h-6 w-6 text-white" />
        </div>
        <h3 className="text-lg font-medium text-neural-700 mb-2">{message}</h3>
        {submessage && (
          <p className="text-gray-600 text-sm mb-4">{submessage}</p>
        )}
        <div className="loading-dots justify-center">
          <div className="bg-ai-purple-500"></div>
          <div className="bg-ml-green-500"></div>
          <div className="bg-prediction-500"></div>
        </div>
      </div>
    </div>
  )
}

export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Card className="animate-pulse">
      <div className="p-6 space-y-4">
        <div className="flex justify-between items-start">
          <div className="space-y-2 flex-1">
            <Skeleton width="75%" height={16} />
            <Skeleton width="50%" height={12} />
          </div>
          <Skeleton width={64} height={24} />
        </div>
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} height={12} />
        ))}
        <div className="flex justify-between">
          <Skeleton width="25%" height={12} />
          <Skeleton width={80} height={32} />
        </div>
      </div>
    </Card>
  )
}

export function LoadingDots({ 
  size = 'default',
  color = 'current' 
}: { 
  size?: 'sm' | 'default' | 'lg'
  color?: 'current' | 'ai' | 'primary' | 'secondary'
}) {
  // Configurable sizes and colors
  return (
    <div className="loading-dots">
      <div className={dotClasses}></div>
      <div className={dotClasses}></div>
      <div className={dotClasses}></div>
    </div>
  )
}
export function Skeleton({ 
  className = '',
  width,
  height,
  variant = 'default'
}: {
  className?: string
  width?: string | number
  height?: string | number
  variant?: 'default' | 'rounded' | 'circle' | 'text'
}) {
  // Flexible skeleton with variants and custom sizing
}

export function ListSkeleton({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: items }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  )
}