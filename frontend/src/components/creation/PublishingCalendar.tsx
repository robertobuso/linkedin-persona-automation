import React, { useState } from 'react'
import { Calendar, dateFnsLocalizer } from 'react-big-calendar'
import { format, parse, startOfWeek, getDay } from 'date-fns'
import { enUS } from 'date-fns/locale'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { CalendarIcon, PlusIcon } from '@heroicons/react/24/outline'
import 'react-big-calendar/lib/css/react-big-calendar.css'

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales: {
    'en-US': enUS,
  },
})

export function PublishingCalendar() {
  const [view, setView] = useState<'month' | 'week' | 'day'>('month')
  const [date, setDate] = useState(new Date())

  // Mock events - replace with real data
  const events = [
    {
      id: 1,
      title: 'AI Article Draft',
      start: new Date(2024, 1, 15, 10, 0),
      end: new Date(2024, 1, 15, 10, 30),
      status: 'scheduled'
    },
    {
      id: 2,
      title: 'Industry Insights Post',
      start: new Date(2024, 1, 17, 14, 0),
      end: new Date(2024, 1, 17, 14, 30),
      status: 'draft'
    },
    {
      id: 3,
      title: 'Weekly Roundup',
      start: new Date(2024, 1, 20, 9, 0),
      end: new Date(2024, 1, 20, 9, 30),
      status: 'published'
    }
  ]

  const eventStyleGetter = (event: any) => {
    let backgroundColor = '#3174ad'
    
    switch (event.status) {
      case 'scheduled':
        backgroundColor = '#10B981'
        break
      case 'draft':
        backgroundColor = '#F59E0B'
        break
      case 'published':
        backgroundColor = '#6B7280'
        break
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block'
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Calendar Header */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
              <CalendarIcon className="h-5 w-5" />
              <span>Publishing Calendar</span>
            </h3>
            <div className="flex items-center space-x-3">
              <div className="flex space-x-2">
                <Badge variant="success" size="sm">Scheduled</Badge>
                <Badge variant="warning" size="sm">Draft</Badge>
                <Badge variant="secondary" size="sm">Published</Badge>
              </div>
              <Button 
                variant="ai" 
                size="sm"
                leftIcon={<PlusIcon className="h-4 w-4" />}
              >
                Schedule Post
              </Button>
            </div>
          </div>

          {/* Calendar */}
          <div className="h-96">
            <Calendar
              localizer={localizer}
              events={events}
              startAccessor="start"
              endAccessor="end"
              views={['month', 'week', 'day']}
              view={view}
              onView={(newView) => setView(newView)}
              date={date}
              onNavigate={(newDate) => setDate(newDate)}
              eventPropGetter={eventStyleGetter}
              style={{ height: '100%' }}
              toolbar={true}
            />
          </div>
        </div>
      </Card>

      {/* Upcoming Posts */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-neural-700 mb-4">Upcoming Posts</h3>
          <div className="space-y-3">
            {events
              .filter(event => event.start > new Date())
              .map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900">{event.title}</h4>
                    <p className="text-sm text-gray-600">
                      {format(event.start, 'MMM d, yyyy \'at\' h:mm a')}
                    </p>
                  </div>
                  <Badge variant="success" size="sm">
                    {event.status}
                  </Badge>
                </div>
              ))}
          </div>
        </div>
      </Card>
    </div>
  )
}
