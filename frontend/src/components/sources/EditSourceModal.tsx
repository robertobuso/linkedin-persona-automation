import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { api, type ContentSource } from '@/lib/api'
import { notify } from '@/stores/uiStore'

interface EditSourceModalProps {
  source: ContentSource
  isOpen: boolean
  onClose: () => void
}

export function EditSourceModal({ source, isOpen, onClose }: EditSourceModalProps) {
  const [formData, setFormData] = useState({
    name: source.name,
    description: source.description || '',
    check_frequency_hours: source.check_frequency_hours,
    is_active: source.is_active,
  })

  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) => api.updateContentSource(source.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
      notify.success('Source updated successfully')
      onClose()
    },
    onError: (error: any) => {
      notify.error('Failed to update source', error.message)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Content Source"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Source Name"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
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

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
            className="h-4 w-4 text-ai-purple-600 focus:ring-ai-purple-500 border-gray-300 rounded"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
            Active
          </label>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="ai"
            loading={updateMutation.isPending}
          >
            Update Source
          </Button>
        </div>
      </form>
    </Modal>
  )
}