import React, { useState } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface ToneStyleSelectorProps {
  isOpen: boolean
  onClose: () => void
  currentContent: string
  onToneApplied: (newContent: string) => void
}

const toneOptions = [
  {
    id: 'professional_thought_leader',
    name: 'Professional Thought Leader',
    description: 'Authoritative, insightful, industry-focused',
    example: 'Share insights with confidence and expertise'
  },
  {
    id: 'storytelling',
    name: 'Storytelling',
    description: 'Narrative-driven, personal, engaging',
    example: 'Transform insights into compelling stories'
  },
  {
    id: 'educational',
    name: 'Educational',
    description: 'Teaching-focused, step-by-step, helpful',
    example: 'Break down complex topics into digestible lessons'
  },
  {
    id: 'thought_provoking',
    name: 'Thought Provoking',
    description: 'Question-based, discussion-starting, controversial',
    example: 'Challenge conventional thinking with bold questions'
  },
  {
    id: 'casual_conversational',
    name: 'Casual Conversational',
    description: 'Friendly, approachable, down-to-earth',
    example: 'Share thoughts like chatting with a colleague'
  },
  {
    id: 'data_driven',
    name: 'Data-Driven',
    description: 'Fact-based, analytical, research-focused',
    example: 'Support every point with compelling statistics'
  }
]

export function ToneStyleSelector({ 
  isOpen, 
  onClose, 
  currentContent, 
  onToneApplied 
}: ToneStyleSelectorProps) {
  const [selectedTone, setSelectedTone] = useState('professional_thought_leader')
  const [isApplying, setIsApplying] = useState(false)

  const handleApplyTone = async () => {
    setIsApplying(true)
    
    // Simulate tone application (in real app, this would call an API)
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // For demo purposes, just add a tone indicator
    const toneLabel = toneOptions.find(t => t.id === selectedTone)?.name || 'Professional'
    const enhancedContent = `${currentContent}\n\n[Tone: ${toneLabel} applied]`
    
    onToneApplied(enhancedContent)
    setIsApplying(false)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Select Tone & Style"
      size="xl"
    >
      <div className="space-y-6">
        <p className="text-gray-600">
          Choose a tone to rewrite your content in a different style
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {toneOptions.map((tone) => (
            <Card
              key={tone.id}
              className={`cursor-pointer transition-all ${
                selectedTone === tone.id
                  ? 'ring-2 ring-ai-purple-500 bg-ai-purple-50'
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => setSelectedTone(tone.id)}
            >
              <div className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <input
                    type="radio"
                    checked={selectedTone === tone.id}
                    onChange={() => setSelectedTone(tone.id)}
                    className="text-ai-purple-600 focus:ring-ai-purple-500"
                  />
                  <h3 className="font-semibold text-neural-700">
                    {tone.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  {tone.description}
                </p>
                <p className="text-xs text-ai-purple-600 italic">
                  {tone.example}
                </p>
              </div>
            </Card>
          ))}
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            variant="outline"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            variant="ai"
            onClick={handleApplyTone}
            loading={isApplying}
          >
            Apply Tone
          </Button>
        </div>
      </div>
    </Modal>
  )
}