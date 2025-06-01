import React from 'react'
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline'
import { Badge } from '@/components/ui/Badge'

interface StatusIndicatorProps {
  status: 'active' | 'inactive' | 'pending' | 'error' | 'success' | 'warning'
  label?: string
  showIcon?: boolean
  size?: 'sm' | 'default' | 'lg'
}

export function StatusIndicator({ status, label, showIcon = true, size = 'default' }: StatusIndicatorProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'active':
      case 'success':
        return {
          icon: CheckCircleIcon,
          variant: 'success' as const,
          text: label || 'Active'
        }
      case 'inactive':
        return {
          icon: XCircleIcon,
          variant: 'secondary' as const,
          text: label || 'Inactive'
        }
      case 'pending':
        return {
          icon: ClockIcon,
          variant: 'warning' as const,
          text: label || 'Pending'
        }
      case 'error':
        return {
          icon: XCircleIcon,
          variant: 'destructive' as const,
          text: label || 'Error'
        }
      case 'warning':
        return {
          icon: ExclamationTriangleIcon,
          variant: 'warning' as const,
          text: label || 'Warning'
        }
      default:
        return {
          icon: ClockIcon,
          variant: 'secondary' as const,
          text: label || 'Unknown'
        }
    }
  }

  const config = getStatusConfig(status)
  const Icon = config.icon

  return (
    <Badge variant={config.variant} size={size}>
      {showIcon && <Icon className="h-3 w-3 mr-1" />}
      {config.text}
    </Badge>
  )
}