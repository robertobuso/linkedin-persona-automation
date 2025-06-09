import React, { useState } from 'react'
import { 
  XMarkIcon, 
  ArrowPathIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface RegenerateModalProps {
  isOpen: boolean
  onClose: () => void
  onRegenerate: (toneStyle: string, preserveHashtags: boolean) => void
  isLoading?: boolean
  currentHashtags?: string[]
}

export function RegenerateModal({ 
  isOpen, 
  onClose, 
  onRegenerate, 
  isLoading = false,
  currentHashtags = []
}: RegenerateModalProps) {
  const [selectedTone, setSelectedTone] = useState('professional')
  const [preserveHashtags, setPreserveHashtags] = useState(false)

  const toneOptions = [
    {
      value: 'professional',
      label: 'Professional',
      description: 'Formal, business-focused tone',
      icon: '💼'
    },
    {
      value: 'conversational', 
      label: 'Conversational',
      description: 'Friendly, approachable tone',
      icon: '💬'
    },
    {
      value: 'storytelling',
      label: 'Storytelling', 
      description: 'Narrative-driven, engaging tone',
      icon: '📖'
    },
    {
      value: 'humorous',
      label: 'Humorous',
      description: 'Light-hearted, entertaining tone', 
      icon: '😄'
    },
    {
      value: 'professional_thought_leader',
      label: 'Thought Leadership',
      description: 'Expert insights and industry analysis',
      icon: '🧠'
    },
    {
      value: 'educational',
      label: 'Educational', 
      description: 'Teaching and instructional content',
      icon: '📚'
    },
    {
      value: 'engagement_optimized',
      label: 'Engagement Optimized',
      description: 'Designed to maximize interaction',
      icon: '🎯'
    }
  ]

  const handleRegenerate = () => {
    onRegenerate(selectedTone, preserveHashtags)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <ArrowPathIcon className="h-5 w-5 text-neural-600" />
              <h2 className="text-lg font-semibold text-neural-700">
                Regenerate Draft
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isLoading}
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Tone Selection */}
          <div className="space-y-4 mb-6">
            <label className="block text-sm font-medium text-gray-700">
              Choose Tone Style
            </label>
            
            <div className="space-y-3">
              {toneOptions.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedTone === option.value
                      ? 'border-neural-500 bg-neural-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="tone"
                    value={option.value}
                    checked={selectedTone === option.value}
                    onChange={(e) => setSelectedTone(e.target.value)}
                    className="mt-1"
                    disabled={isLoading}
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{option.icon}</span>
                      <span className="font-medium text-gray-900">
                        {option.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {option.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Hashtag Preservation */}
          {currentHashtags.length > 0 && (
            <div className="mb-6">
              <label className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  checked={preserveHashtags}
                  onChange={(e) => setPreserveHashtags(e.target.checked)}
                  className="mt-1"
                  disabled={isLoading}
                />
                <div>
                  <span className="block text-sm font-medium text-gray-700">
                    Preserve current hashtags
                  </span>
                  <p className="text-sm text-gray-600 mt-1">
                    Keep existing hashtags: {currentHashtags.join(' ')}
                  </p>
                </div>
              </label>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-3">
            <Button
              onClick={handleRegenerate}
              loading={isLoading}
              variant="ai"
              leftIcon={<SparklesIcon className="h-4 w-4" />}
              className="flex-1"
            >
              Regenerate Draft
            </Button>
            <Button
              onClick={onClose}
              variant="outline"
              disabled={isLoading}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
