import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { api, type ContentPreferences } from '@/lib/api'
import { notify } from '@/stores/uiStore'
import { 
  UserIcon,
  LightBulbIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline'

interface PreferencesFormData {
  jobRole: string
  industry: string
  interests: string[]
  customPrompt: string
  relevanceThreshold: number
  maxArticlesPerDay: number
}

const interests = [
  { id: 'ai_ml', label: '🤖 AI & Machine Learning' },
  { id: 'software_engineering', label: '💻 Software Engineering' },
  { id: 'product_management', label: '📱 Product Management' },
  { id: 'data_science', label: '📊 Data Science' },
  { id: 'blockchain', label: '⛓️ Blockchain & Web3' },
  { id: 'cloud_computing', label: '☁️ Cloud Computing' },
  { id: 'cybersecurity', label: '🔒 Cybersecurity' },
  { id: 'devops', label: '🔄 DevOps & Infrastructure' },
  { id: 'startups', label: '🚀 Startups & Entrepreneurship' },
  { id: 'leadership', label: '👥 Leadership & Management' },
  { id: 'finance_tech', label: '💳 FinTech' },
  { id: 'mobile_development', label: '📱 Mobile Development' }
]

export function ContentPreferencesForm() {
  const queryClient = useQueryClient()
  
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user-preferences'],
    queryFn: () => api.getUserPreferences(),
    retry: false // Don't retry if user has no preferences yet
  })

  const [formData, setFormData] = useState<PreferencesFormData>({
    jobRole: preferences?.job_role || '',
    industry: preferences?.industry || '',
    interests: preferences?.primary_interests || [],
    customPrompt: preferences?.custom_prompt || '',
    relevanceThreshold: preferences?.min_relevance_score ? preferences.min_relevance_score * 100 : 70,
    maxArticlesPerDay: preferences?.max_articles_per_day || 15
  })

  const saveMutation = useMutation({
    mutationFn: (data: PreferencesFormData) => api.saveQuickPreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] })
      notify.success('Preferences saved successfully!')
    },
    onError: (error: any) => {
      notify.error('Failed to save preferences', error.message)
    }
  })

  // Update form data when preferences load
  React.useEffect(() => {
    if (preferences) {
      setFormData({
        jobRole: preferences.job_role || '',
        industry: preferences.industry || '',
        interests: preferences.primary_interests || [],
        customPrompt: preferences.custom_prompt || '',
        relevanceThreshold: preferences.min_relevance_score ? preferences.min_relevance_score * 100 : 70,
        maxArticlesPerDay: preferences.max_articles_per_day || 15
      })
    }
  }, [preferences])

  const handleInterestToggle = (interestId: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interestId)
        ? prev.interests.filter(id => id !== interestId)
        : [...prev.interests, interestId]
    }))
  }

  const handleSliderChange = (field: 'relevanceThreshold' | 'maxArticlesPerDay', value: number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = () => {
    saveMutation.mutate(formData)
  }

  const getRelevanceLabel = (value: number) => {
    if (value < 60) return 'Permissive'
    if (value > 80) return 'Strict'
    return 'Balanced'
  }

  const generatePreview = () => {
    const selectedInterests = formData.interests.map(id => 
      interests.find(i => i.id === id)?.label.replace(/^.+?\s/, '') || id
    )
    
    let preview = 'The AI will look for content about: '
    
    if (selectedInterests.length > 0) {
      preview += selectedInterests.join(', ')
    }
    
    if (formData.customPrompt) {
      preview += (selectedInterests.length > 0 ? '. ' : '') + 
        'Custom instructions: "' + formData.customPrompt.substring(0, 100) + 
        (formData.customPrompt.length > 100 ? '..."' : '"')
    }
    
    if (selectedInterests.length === 0 && !formData.customPrompt) {
      preview = 'Your custom instructions will help the AI understand exactly what content you find valuable.'
    }
    
    return preview
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3, 4].map(i => (
          <Card key={i} className="animate-pulse">
            <div className="p-6 space-y-4">
              <div className="h-6 bg-gray-200 rounded w-1/4"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-neural-700 mb-2">
          📡 Content Discovery Preferences
        </h1>
        <p className="text-gray-600">
          Configure what kind of content you want to discover and analyze
        </p>
      </div>

      {/* Professional Context */}
      <Card>
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-4">
            <UserIcon className="h-5 w-5 text-ai-purple-500" />
            <h3 className="text-lg font-semibold text-neural-700">Professional Context</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Role
              </label>
              <select
                value={formData.jobRole}
                onChange={(e) => setFormData(prev => ({ ...prev, jobRole: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
              >
                <option value="">Select your role...</option>
                <option value="software_engineer">Software Engineer</option>
                <option value="product_manager">Product Manager</option>
                <option value="data_scientist">Data Scientist</option>
                <option value="engineering_manager">Engineering Manager</option>
                <option value="founder_ceo">Founder/CEO</option>
                <option value="marketing_manager">Marketing Manager</option>
                <option value="sales_professional">Sales Professional</option>
                <option value="consultant">Consultant</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <select
                value={formData.industry}
                onChange={(e) => setFormData(prev => ({ ...prev, industry: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
              >
                <option value="">Select industry...</option>
                <option value="technology">Technology</option>
                <option value="finance">Finance</option>
                <option value="healthcare">Healthcare</option>
                <option value="consulting">Consulting</option>
                <option value="education">Education</option>
                <option value="retail">Retail</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </div>
      </Card>

      {/* Content Interests */}
      <Card>
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-4">
            <LightBulbIcon className="h-5 w-5 text-ml-green-500" />
            <h3 className="text-lg font-semibold text-neural-700">Content Interests</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {interests.map((interest) => (
              <div
                key={interest.id}
                onClick={() => handleInterestToggle(interest.id)}
                className={`
                  flex items-center space-x-2 p-3 rounded-lg border-2 cursor-pointer transition-all
                  ${formData.interests.includes(interest.id)
                    ? 'bg-ai-purple-500 text-white border-ai-purple-500'
                    : 'bg-white text-gray-700 border-gray-200 hover:border-ai-purple-500 hover:bg-ai-purple-50'
                  }
                `}
              >
                <span className="text-sm font-medium">{interest.label}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Custom Instructions */}
      <Card>
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-4">
            <SparklesIcon className="h-5 w-5 text-prediction-500" />
            <h3 className="text-lg font-semibold text-neural-700">Custom Instructions</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tell the AI what you want to see (optional)
              </label>
              <textarea
                value={formData.customPrompt}
                onChange={(e) => setFormData(prev => ({ ...prev, customPrompt: e.target.value }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-ai-purple-500 focus:border-ai-purple-500"
                placeholder="Example: I'm interested in emerging technologies that could impact healthcare, especially AI applications in medical diagnosis. I prefer in-depth technical articles over news briefs."
              />
            </div>
            
            <div className="p-4 bg-prediction-50 rounded-lg border-l-4 border-prediction-500">
              <p className="text-sm text-prediction-700 italic">
                {generatePreview()}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Content Filters */}
      <Card>
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-4">
            <AdjustmentsHorizontalIcon className="h-5 w-5 text-neural-500" />
            <h3 className="text-lg font-semibold text-neural-700">Content Filters</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Relevance Threshold
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min="50"
                  max="95"
                  value={formData.relevanceThreshold}
                  onChange={(e) => handleSliderChange('relevanceThreshold', parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="text-center">
                  <span className="text-sm font-medium text-ai-purple-600">
                    {formData.relevanceThreshold}% - {getRelevanceLabel(formData.relevanceThreshold)}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Articles Per Day
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={formData.maxArticlesPerDay}
                  onChange={(e) => handleSliderChange('maxArticlesPerDay', parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="text-center">
                  <span className="text-sm font-medium text-ml-green-600">
                    {formData.maxArticlesPerDay} articles
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex justify-center space-x-4">
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            const preview = generatePreview()
            alert(`Preview of your content preferences:\n\nRole: ${formData.jobRole || 'Not specified'}\nIndustry: ${formData.industry || 'Not specified'}\nRelevance Threshold: ${formData.relevanceThreshold}%\nArticles per day: ${formData.maxArticlesPerDay}\n\n${preview}`)
          }}
        >
          👀 Preview
        </Button>
        <Button
          variant="ai"
          size="lg"
          onClick={handleSave}
          loading={saveMutation.isPending}
        >
          💾 Save Preferences
        </Button>
      </div>
    </div>
  )
}