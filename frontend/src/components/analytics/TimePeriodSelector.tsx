import React from 'react'
import { Badge } from '@/components/ui/Badge'

interface TimePeriodSelectorProps {
  value: number
  onChange: (days: number) => void
}

export function TimePeriodSelector({ value, onChange }: TimePeriodSelectorProps) {
  const periods = [
    { days: 7, label: '7 Days' },
    { days: 30, label: '30 Days' },
    { days: 90, label: '90 Days' },
    { days: 365, label: '1 Year' }
  ]

  return (
    <div className="flex space-x-2">
      {periods.map((period) => (
        <Badge
          key={period.days}
          variant={value === period.days ? 'default' : 'outline'}
          className="cursor-pointer hover:bg-gray-50"
          onClick={() => onChange(period.days)}
        >
          {period.label}
        </Badge>
      ))}
    </div>
  )
}
