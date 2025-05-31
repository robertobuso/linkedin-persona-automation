import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

const cardVariants = cva(
  'rounded-xl border shadow-sm transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'bg-white border-gray-200',
        intelligence: 'bg-gradient-to-br from-white to-neural-50 border border-neural-200 ring-1 ring-neural-100',
        ai: 'bg-gradient-to-br from-ai-purple-50 to-ml-green-50 border border-ai-purple-200',
        prediction: 'bg-gradient-to-br from-prediction-50 to-white border border-prediction-200',
        success: 'bg-gradient-to-br from-ml-green-50 to-white border border-ml-green-200',
        elevated: 'bg-white border-gray-200 shadow-lg',
        glass: 'bg-white/80 backdrop-blur-sm border border-white/20',
      },
      padding: {
        none: 'p-0',
        sm: 'p-4',
        default: 'p-6',
        lg: 'p-8',
      },
      hover: {
        none: '',
        lift: 'hover:shadow-md hover:-translate-y-1',
        glow: 'hover:shadow-lg hover:shadow-neural-500/20',
        scale: 'hover:scale-105',
      }
    },
    defaultVariants: {
      variant: 'default',
      padding: 'default',
      hover: 'none',
    },
  }
)

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  intelligence?: boolean
  glowing?: boolean
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, hover, intelligence, glowing, children, ...props }, ref) => {
    const finalVariant = intelligence ? 'intelligence' : variant
    
    return (
      <div
        ref={ref}
        className={cn(
          cardVariants({ variant: finalVariant, padding, hover }),
          glowing && 'animate-glow',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
)
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-lg font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
)
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-gray-600', className)}
      {...props}
    />
  )
)
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
)
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center p-6 pt-0', className)}
      {...props}
    />
  )
)
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }