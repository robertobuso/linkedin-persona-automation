import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { api } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'

interface AddSourceModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AddSourceModal({ isOpen, onClose }: AddSourceModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    description: '',
    check_frequency_hours: 24,
  })
  const [validationResult, setValidationResult] = useState<any>(null)
  const [isValidating, setIsValidating] = useState(false)

  const queryClient = useQueryClient()

  const validateMutation = useMutation({
    mutationFn: (url: string) => api.validateFeedUrl(url),
    onSuccess: (result) => {
      setValidationResult(result)
      if (result.valid && result.title && !formData.name) {
        setFormData(prev => ({ ...prev, name: result.title }))
      }
    },
    onError: () => {
      setValidationResult({ valid: false, error: 'Failed to validate URL' })
    }
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.createContentSource({
      ...data,
      source_type: 'rss_feed',
      is_active: true,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
      notify.success('Content source added successfully')
      onClose()
      resetForm()
    },
    onError: (error: any) => {
      notify.error('Failed to add source', error.message)
    }
  })

  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      description: '',
      check_frequency_hours: 24,
    })
    setValidationResult(null)
  }

  const handleUrlBlur = () => {
    if (formData.url && !validationResult) {
      validateMutation.mutate(formData.url)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validationResult?.valid) {
      notify.error('Please validate the RSS feed URL first')
      return
    }
    createMutation.mutate(formData)
  }

  const handleClose = () => {
    onClose()
    resetForm()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add Content Source"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="RSS Feed URL"
          type="url"
          value={formData.url}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, url: e.target.value }))
            setValidationResult(null)
          }}
          onBlur={handleUrlBlur}
          placeholder="https://example.com/feed.xml"
          required
        />

        {validationResult && (
          <div className={`p-3 rounded-lg flex items-center space-x-2 ${
            validationResult.valid 
              ? 'bg-ml-green-50 text-ml-green-700' 
              : 'bg-red-50 text-red-700'
          }`}>
            {validationResult.valid ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <XCircleIcon className="h-5 w-5" />
            )}
            <div className="flex-1">
              {validationResult.valid ? (
                <div>
                  <p className="font-medium">Valid RSS feed!</p>
                  {validationResult.title && (
                    <p className="text-sm">Title: {validationResult.title}</p>
                  )}
                  {validationResult.entry_count && (
                    <p className="text-sm">{validationResult.entry_count} entries found</p>
                  )}
                </div>
              ) : (
                <p>{validationResult.error || 'Invalid RSS feed'}</p>
              )}
            </div>
          </div>
        )}

        <Input
          label="Source Name"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="Enter a name for this source"
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description (optional)
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
            placeholder="Describe what this source covers..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Check Frequency (hours)
          </label>
          <select
            value={formData.check_frequency_hours}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              check_frequency_hours: parseInt(e.target.value) 
            }))}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
          >
            <option value={1}>Every hour</option>
            <option value={6}>Every 6 hours</option>
            <option value={12}>Every 12 hours</option>
            <option value={24}>Daily</option>
            <option value={72}>Every 3 days</option>
            <option value={168}>Weekly</option>
          </select>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="ai"
            loading={createMutation.isPending || validateMutation.isPending}
            disabled={!validationResult?.valid}
          >
            Add Source
          </Button>
        </div>
      </form>
    </Modal>
  )
}