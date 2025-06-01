import React from 'react'

interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  showValue?: boolean
  variant?: 'default' | 'ai' | 'success' | 'warning' | 'destructive'
  size?: 'sm' | 'default' | 'lg'
}

export function ProgressBar({ 
  value, 
  max = 100, 
  label, 
  showValue = true, 
  variant = 'default',
  size = 'default' 
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100)
  
  const getVariantClasses = (variant: string) => {
    switch (variant) {
      case 'ai':
        return 'bg-gradient-to-r from-ai-purple-500 to-ml-green-500'
      case 'success':
        return 'bg-ml-green-500'
      case 'warning':
        return 'bg-prediction-500'
      case 'destructive':
        return 'bg-red-500'
      default:
        return 'bg-neural-500'
    }
  }
  
  const getSizeClasses = (size: string) => {
    switch (size) {
      case 'sm': return 'h-1'
      case 'lg': return 'h-3'
      default: return 'h-2'
    }
  }

  return (
    <div className="space-y-1">
      {(label || showValue) && (
        <div className="flex justify-between items-center">
          {label && <span className="text-sm text-gray-700">{label}</span>}
          {showValue && (
            <span className="text-sm text-gray-600">
              {value}/{max} ({Math.round(percentage)}%)
            </span>
          )}
        </div>
      )}
      
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${getSizeClasses(size)}`}>
        <div
          className={`${getSizeClasses(size)} ${getVariantClasses(variant)} transition-all duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}