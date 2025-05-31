import React from 'react'
import { cn } from '@/utils/cn'

interface ConfidenceIndicatorProps {
  score: number // 0-1
  label?: string
  size?: 'sm' | 'md' | 'lg'
  showPercentage?: boolean
  className?: string
}

export function ConfidenceIndicator({
  score,
  label = "Confidence",
  size = "md",
  showPercentage = true,
  className
}: ConfidenceIndicatorProps) {
  const percentage = Math.round(score * 100)
  
  const getColorClass = () => {
    if (score >= 0.8) return 'bg-ml-green-500'
    if (score >= 0.6) return 'bg-prediction-500'
    if (score >= 0.4) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-1.5 text-xs'
      case 'lg':
        return 'h-3 text-base'
      default:
        return 'h-2 text-sm'
    }
  }
  
  return (
    <div className={cn('flex items-center space-x-2', className)}>
      {label && (
        <span className={cn('text-gray-600 font-medium', getSizeClasses().split(' ')[1])}>
          {label}:
        </span>
      )}
      <div className="flex-1 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={cn(
            'rounded-full transition-all duration-500 ease-out',
            getColorClass(),
            getSizeClasses().split(' ')[0]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showPercentage && (
        <span className={cn('font-medium text-gray-900', getSizeClasses().split(' ')[1])}>
          {percentage}%
        </span>
      )}
    </div>
  )
}
