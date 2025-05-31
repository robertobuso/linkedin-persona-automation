import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Switch } from '@headlessui/react'
import { 
  CpuChipIcon as BrainIcon, 
  CogIcon, 
  SparklesIcon,
  ClockIcon,
  ChatBubbleLeftIcon 
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'
import { notify } from '@/stores/uiStore'

export default function AIConfiguration() {
  const [settings, setSettings] = useState({
    contentSelection: {
      enabled: true,
      frequency: 'daily',
      relevanceThreshold: 0.7,
      maxArticlesPerDay: 5
    },
    draftGeneration: {
      enabled: true,
      tone: 'professional',
      includeHashtags: true,
      maxHashtags: 5,
      avgLength: 'medium'
    },
    engagement: {
      enabled: false,
      autoComment: false,
      commentTone: 'friendly',
      maxCommentsPerDay: 10
    },
    scheduling: {
      enabled: true,
      optimalTiming: true,
      timezone: 'America/New_York'
    }
  })

  const handleSave = () => {
    // Save settings logic
    notify.success('AI settings updated successfully!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">AI Configuration</h1>
          <p className="text-gray-600 mt-1">
            Configure your AI automation preferences and behavior
          </p>
        </div>
        <Button onClick={handleSave} variant="ai">
          Save Settings
        </Button>
      </div>

      {/* Content Selection Settings */}
      <Card intelligence>
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-6">
            <BrainIcon className="h-6 w-6 text-ai-purple-600" />
            <h2 className="text-xl font-semibold text-neural-700">Content Selection AI</h2>
            <SettingToggle 
              enabled={settings.contentSelection.enabled}
              onChange={(enabled) => setSettings(prev => ({
                ...prev,
                contentSelection: { ...prev.contentSelection, enabled }
              }))}
            />
          </div>

          {settings.contentSelection.enabled && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Selection Frequency
                  </label>
                  <select 
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
                    value={settings.contentSelection.frequency}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      contentSelection: { ...prev.contentSelection, frequency: e.target.value }
                    }))}
                  >
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Articles per Day
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="20"
                    value={settings.contentSelection.maxArticlesPerDay}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      contentSelection: { ...prev.contentSelection, maxArticlesPerDay: parseInt(e.target.value) }
                    }))}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Relevance Threshold: {Math.round(settings.contentSelection.relevanceThreshold * 100)}%
                </label>
                <input
                  type="range"
                  min="0.3"
                  max="1"
                  step="0.05"
                  value={settings.contentSelection.relevanceThreshold}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    contentSelection: { ...prev.contentSelection, relevanceThreshold: parseFloat(e.target.value) }
                  }))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Draft Generation Settings */}
      <Card intelligence>
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-6">
            <SparklesIcon className="h-6 w-6 text-ml-green-600" />
            <h2 className="text-xl font-semibold text-neural-700">Draft Generation AI</h2>
            <SettingToggle 
              enabled={settings.draftGeneration.enabled}
              onChange={(enabled) => setSettings(prev => ({
                ...prev,
                draftGeneration: { ...prev.draftGeneration, enabled }
              }))}
            />
          </div>

          {settings.draftGeneration.enabled && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Writing Tone
                  </label>
                  <select 
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
                    value={settings.draftGeneration.tone}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      draftGeneration: { ...prev.draftGeneration, tone: e.target.value }
                    }))}
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="enthusiastic">Enthusiastic</option>
                    <option value="analytical">Analytical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Length
                  </label>
                  <select 
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
                    value={settings.draftGeneration.avgLength}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      draftGeneration: { ...prev.draftGeneration, avgLength: e.target.value }
                    }))}
                  >
                    <option value="short">Short (50-100 words)</option>
                    <option value="medium">Medium (100-200 words)</option>
                    <option value="long">Long (200+ words)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Include Hashtags</span>
                <SettingToggle 
                  enabled={settings.draftGeneration.includeHashtags}
                  onChange={(enabled) => setSettings(prev => ({
                    ...prev,
                    draftGeneration: { ...prev.draftGeneration, includeHashtags: enabled }
                  }))}
                />
              </div>

              {settings.draftGeneration.includeHashtags && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Hashtags: {settings.draftGeneration.maxHashtags}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={settings.draftGeneration.maxHashtags}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      draftGeneration: { ...prev.draftGeneration, maxHashtags: parseInt(e.target.value) }
                    }))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Engagement AI Settings */}
      <Card intelligence>
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-6">
            <ChatBubbleLeftIcon className="h-6 w-6 text-prediction-600" />
            <h2 className="text-xl font-semibold text-neural-700">Engagement AI</h2>
            <Badge variant="warning" size="sm">Beta</Badge>
            <SettingToggle 
              enabled={settings.engagement.enabled}
              onChange={(enabled) => setSettings(prev => ({
                ...prev,
                engagement: { ...prev.engagement, enabled }
              }))}
            />
          </div>

          {settings.engagement.enabled && (
            <div className="space-y-4">
              <div className="bg-prediction-50 border border-prediction-200 rounded-lg p-4">
                <h4 className="font-medium text-prediction-800 mb-2">⚠️ Use with Caution</h4>
                <p className="text-sm text-prediction-700">
                  Auto-engagement features are experimental. We recommend manual review before enabling automated commenting.
                </p>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Auto Comment on Opportunities</span>
                <SettingToggle 
                  enabled={settings.engagement.autoComment}
                  onChange={(enabled) => setSettings(prev => ({
                    ...prev,
                    engagement: { ...prev.engagement, autoComment: enabled }
                  }))}
                />
              </div>

              {settings.engagement.autoComment && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Comment Tone
                    </label>
                    <select 
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
                      value={settings.engagement.commentTone}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        engagement: { ...prev.engagement, commentTone: e.target.value }
                      }))}
                    >
                      <option value="friendly">Friendly</option>
                      <option value="professional">Professional</option>
                      <option value="supportive">Supportive</option>
                      <option value="inquisitive">Inquisitive</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Comments per Day
                    </label>
                    <Input
                      type="number"
                      min="1"
                      max="50"
                      value={settings.engagement.maxCommentsPerDay}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        engagement: { ...prev.engagement, maxCommentsPerDay: parseInt(e.target.value) }
                      }))}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Scheduling AI */}
      <Card intelligence>
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-6">
            <ClockIcon className="h-6 w-6 text-neural-600" />
            <h2 className="text-xl font-semibold text-neural-700">Scheduling AI</h2>
            <SettingToggle 
              enabled={settings.scheduling.enabled}
              onChange={(enabled) => setSettings(prev => ({
                ...prev,
                scheduling: { ...prev.scheduling, enabled }
              }))}
            />
          </div>

          {settings.scheduling.enabled && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Use Optimal Timing Predictions</span>
                <SettingToggle 
                  enabled={settings.scheduling.optimalTiming}
                  onChange={(enabled) => setSettings(prev => ({
                    ...prev,
                    scheduling: { ...prev.scheduling, optimalTiming: enabled }
                  }))}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timezone
                </label>
                <select 
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
                  value={settings.scheduling.timezone}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    scheduling: { ...prev.scheduling, timezone: e.target.value }
                  }))}
                >
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

function SettingToggle({ 
  enabled, 
  onChange 
}: { 
  enabled: boolean
  onChange: (enabled: boolean) => void 
}) {
  return (
    <Switch
      checked={enabled}
      onChange={onChange}
      className={cn(
        'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
        enabled ? 'bg-ml-green-500' : 'bg-gray-200'
      )}
    >
      <span
        className={cn(
          'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
          enabled ? 'translate-x-6' : 'translate-x-1'
        )}
      />
    </Switch>
  )
}
