import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { 
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  DocumentPlusIcon
} from '@heroicons/react/24/outline'

export function BatchOperationsPanel() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [batchOptions, setBatchOptions] = useState({
    max_posts: 5,
    min_relevance_score: 70,
    style: 'professional_thought_leader'
  })

  const queryClient = useQueryClient()

  const batchGenerateMutation = useMutation({
    mutationFn: () => api.batchGenerateDrafts(batchOptions),
    onSuccess: (drafts) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      notify.success(`Generated ${drafts.length} new drafts!`)
      setIsGenerating(false)
    },
    onError: (error: any) => {
      notify.error('Batch generation failed', error.message)
      setIsGenerating(false)
    }
  })

  const handleBatchGenerate = () => {
    setIsGenerating(true)
    batchGenerateMutation.mutate()
  }

  return (
    <Card variant="ai">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="h-5 w-5 text-ai-purple-600" />
            <h3 className="text-lg font-semibold text-neural-700">
              AI Batch Generation
            </h3>
            <Badge variant="ai" size="sm">Smart</Badge>
          </div>
        </div>

        <p className="text-gray-600 mb-4">
          Generate multiple drafts from your highest-relevance content automatically
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Posts
            </label>
            <select
              value={batchOptions.max_posts}
              onChange={(e) => setBatchOptions(prev => ({ 
                ...prev, 
                max_posts: parseInt(e.target.value) 
              }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500"
            >
              <option value={3}>3 posts</option>
              <option value={5}>5 posts</option>
              <option value={8}>8 posts</option>
              <option value={10}>10 posts</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min Relevance
            </label>
            <select
              value={batchOptions.min_relevance_score}
              onChange={(e) => setBatchOptions(prev => ({ 
                ...prev, 
                min_relevance_score: parseInt(e.target.value) 
              }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500"
            >
              <option value={60}>60% - More variety</option>
              <option value={70}>70% - Balanced</option>
              <option value={80}>80% - High quality</option>
              <option value={90}>90% - Ultra selective</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Style
            </label>
            <select
              value={batchOptions.style}
              onChange={(e) => setBatchOptions(prev => ({ 
                ...prev, 
                style: e.target.value 
              }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500"
            >
              <option value="professional_thought_leader">Professional</option>
              <option value="storytelling">Storytelling</option>
              <option value="educational">Educational</option>
              <option value="thought_provoking">Thought Provoking</option>
            </select>
          </div>
        </div>

        <Button
          variant="ai"
          onClick={handleBatchGenerate}
          loading={isGenerating || batchGenerateMutation.isPending}
          leftIcon={<DocumentPlusIcon className="h-4 w-4" />}
          className="w-full"
        >
          {isGenerating ? 'Generating Drafts...' : 'Generate Batch Drafts'}
        </Button>
      </div>
    </Card>
  )
}