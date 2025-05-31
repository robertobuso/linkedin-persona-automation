import React, { useState } from 'react'
import { MagnifyingGlassIcon, FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useContentStore } from '@/stores/contentStore'

export function ContentIntelligenceFilters() {
  const { searchQuery, selectedCategories, setSearchQuery, setSelectedCategories } = useContentStore()
  const [showFilters, setShowFilters] = useState(false)

  const availableCategories = [
    'Technology', 'Business', 'Innovation', 'Leadership', 'Marketing',
    'AI & ML', 'Startups', 'Industry News', 'Career Advice', 'Productivity'
  ]

  const handleCategoryToggle = (category: string) => {
    const newCategories = selectedCategories.includes(category)
      ? selectedCategories.filter(c => c !== category)
      : [...selectedCategories, category]
    setSelectedCategories(newCategories)
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedCategories([])
  }

  const hasActiveFilters = searchQuery || selectedCategories.length > 0

  return (
    <Card>
      <div className="p-4 space-y-4">
        {/* Search and Filter Toggle */}
        <div className="flex space-x-3">
          <div className="flex-1">
            <Input
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
            />
          </div>
          <Button
            variant={showFilters ? "default" : "outline"}
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<FunnelIcon className="h-4 w-4" />}
          >
            Filters
          </Button>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              onClick={clearFilters}
              leftIcon={<XMarkIcon className="h-4 w-4" />}
            >
              Clear
            </Button>
          )}
        </div>

        {/* Active Filters */}
        {selectedCategories.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {selectedCategories.map((category) => (
              <Badge
                key={category}
                variant="secondary"
                className="cursor-pointer hover:bg-gray-200"
                onClick={() => handleCategoryToggle(category)}
              >
                {category}
                <XMarkIcon className="h-3 w-3 ml-1" />
              </Badge>
            ))}
          </div>
        )}

        {/* Expanded Filters */}
        {showFilters && (
          <div className="pt-4 border-t border-gray-100">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Categories</h4>
              <div className="flex flex-wrap gap-2">
                {availableCategories.map((category) => (
                  <Badge
                    key={category}
                    variant={selectedCategories.includes(category) ? "default" : "outline"}
                    className="cursor-pointer hover:bg-neural-50"
                    onClick={() => handleCategoryToggle(category)}
                  >
                    {category}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
