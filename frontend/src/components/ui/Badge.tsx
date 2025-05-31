import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-neural-100 text-neural-800 hover:bg-neural-200',
        secondary: 'border-transparent bg-gray-100 text-gray-800 hover:bg-gray-200',
        destructive: 'border-transparent bg-red-100 text-red-800 hover:bg-red-200',
        outline: 'text-gray-700 border-gray-200',
        success: 'border-transparent bg-ml-green-100 text-ml-green-800 hover:bg-ml-green-200',
        warning: 'border-transparent bg-prediction-100 text-prediction-800 hover:bg-prediction-200',
        ai: 'border-transparent bg-gradient-to-r from-ai-purple-100 to-ml-green-100 text-neural-800',
        'ml-green': 'border-transparent bg-ml-green-100 text-ml-green-800 hover:bg-ml-green-200',
        neutral: 'border-transparent bg-gray-100 text-gray-700 hover:bg-gray-200',
        prediction: 'border-transparent bg-prediction-100 text-prediction-800 hover:bg-prediction-200',
      },
      size: {
        default: 'px-2.5 py-0.5 text-xs',
        sm: 'px-2 py-0.5 text-xs',
        lg: 'px-3 py-1 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode
}

function Badge({ className, variant, size, icon, children, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </div>
  )
}

export { Badge, badgeVariants }