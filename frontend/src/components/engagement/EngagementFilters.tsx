import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface EngagementFiltersProps {
  priority: string
  status: string
  onPriorityChange: (priority: string) => void
  onStatusChange: (status: string) => void
}

export function EngagementFilters({
  priority,
  status,
  onPriorityChange,
  onStatusChange
}: EngagementFiltersProps) {
  const priorities = [
    { value: '', label: 'All Priorities' },
    { value: 'urgent', label: 'Urgent', color: 'destructive' as const },
    { value: 'high', label: 'High', color: 'warning' as const },
    { value: 'medium', label: 'Medium', color: 'secondary' as const },
    { value: 'low', label: 'Low', color: 'neutral' as const }
  ]

  const statuses = [
    { value: '', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'scheduled', label: 'Scheduled' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' }
  ]

  return (
    <Card>
      <div className="p-4 space-y-4">
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Filter by Priority</h4>
          <div className="flex flex-wrap gap-2">
            {priorities.map((p) => (
              <Badge
                key={p.value}
                variant={priority === p.value ? (p.color || 'default') : 'outline'}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => onPriorityChange(p.value)}
              >
                {p.label}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-3">Filter by Status</h4>
          <div className="flex flex-wrap gap-2">
            {statuses.map((s) => (
              <Badge
                key={s.value}
                variant={status === s.value ? 'default' : 'outline'}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => onStatusChange(s.value)}
              >
                {s.label}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </Card>
  )
}
