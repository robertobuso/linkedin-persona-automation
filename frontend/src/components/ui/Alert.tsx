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
