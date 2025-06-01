import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  PlusIcon,
  PencilIcon,
  TrashIcon,
  RssIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal, ConfirmModal } from '@/components/ui/Modal'
import { api, type ContentSource } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { formatDistanceToNow } from 'date-fns'
import { AddSourceModal } from './AddSourceModal'
import { EditSourceModal } from './EditSourceModal'

export function ContentSourcesList() {
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingSource, setEditingSource] = useState<ContentSource | null>(null)
  const [deletingSource, setDeletingSource] = useState<ContentSource | null>(null)
  
  const queryClient = useQueryClient()

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['content-sources'],
    queryFn: () => api.getContentSources(),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteContentSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
      notify.success('Source deleted successfully')
      setDeletingSource(null)
    },
    onError: (error: any) => {
      notify.error('Failed to delete source', error.message)
    }
  })

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string, is_active: boolean }) => 
      api.updateContentSource(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-sources'] })
    },
    onError: (error: any) => {
      notify.error('Failed to update source', error.message)
    }
  })

  const getStatusIcon = (source: ContentSource) => {
    if (!source.is_active) {
      return <XCircleIcon className="h-5 w-5 text-gray-400" />
    }
    
    if (source.total_items_found === 0) {
      return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
    }
    
    return <CheckCircleIcon className="h-5 w-5 text-ml-green-500" />
  }

  const getStatusBadge = (source: ContentSource) => {
    if (!source.is_active) return { variant: 'secondary' as const, text: 'Inactive' }
    if (source.total_items_found === 0) return { variant: 'warning' as const, text: 'No Data' }
    return { variant: 'success' as const, text: 'Active' }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Card key={i} className="animate-pulse">
            <div className="p-6 space-y-4">
              <div className="flex justify-between">
                <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              <div className="flex justify-between">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-8 bg-gray-200 rounded w-20"></div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Content Sources</h1>
          <p className="text-gray-600 mt-2">
            Manage your RSS feeds and content sources
          </p>
        </div>
        <Button
          variant="ai"
          onClick={() => setShowAddModal(true)}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Add Source
        </Button>
      </div>

      {sources.length === 0 ? (
        <Card className="text-center py-12">
          <RssIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No content sources</h3>
          <p className="text-gray-600 mb-6">
            Add RSS feeds to start discovering relevant content
          </p>
          <Button
            variant="ai"
            onClick={() => setShowAddModal(true)}
            leftIcon={<PlusIcon className="h-4 w-4" />}
          >
            Add Your First Source
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4">
          {sources.map((source) => {
            const statusBadge = getStatusBadge(source)
            
            return (
              <Card key={source.id} hover="lift">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className="flex-shrink-0 mt-1">
                        {getStatusIcon(source)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-lg font-semibold text-neural-700 truncate">
                            {source.name}
                          </h3>
                          <Badge variant={statusBadge.variant} size="sm">
                            {statusBadge.text}
                          </Badge>
                        </div>
                        
                        {source.description && (
                          <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                            {source.description}
                          </p>
                        )}
                        
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-ai-purple-600 hover:text-ai-purple-700 text-sm truncate block"
                          >
                            {source.url}
                          </a>
                        )}
                        
                        <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                          <span>
                            {source.total_items_found} items found
                          </span>
                          <span>
                            {source.total_items_processed} processed
                          </span>
                          <span>
                            Check every {source.check_frequency_hours}h
                          </span>
                          {source.last_checked_at && (
                            <span>
                              Last: {formatDistanceToNow(new Date(source.last_checked_at), { addSuffix: true })}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleActiveMutation.mutate({ 
                          id: source.id, 
                          is_active: !source.is_active 
                        })}
                        loading={toggleActiveMutation.isPending}
                      >
                        {source.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setEditingSource(source)}
                      >
                        <PencilIcon className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeletingSource(source)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Add Source Modal */}
      <AddSourceModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />

      {/* Edit Source Modal */}
      {editingSource && (
        <EditSourceModal
          source={editingSource}
          isOpen={true}
          onClose={() => setEditingSource(null)}
        />
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={!!deletingSource}
        onClose={() => setDeletingSource(null)}
        onConfirm={() => deletingSource && deleteMutation.mutate(deletingSource.id)}
        title="Delete Content Source"
        message={`Are you sure you want to delete "${deletingSource?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="destructive"
        loading={deleteMutation.isPending}
      />
    </div>
  )
}