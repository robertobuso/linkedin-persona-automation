// Enhanced API methods for draft management

// Add these methods to the existing APIClient class in api.ts

export interface DraftWithContent {
  id: string
  user_id: string
  content: string
  hashtags: string[]
  title?: string
  status: string
  scheduled_for?: string
  published_at?: string
  linkedin_post_id?: string
  linkedin_post_url?: string
  created_at: string
  updated_at: string
  generation_metadata?: any
  ai_model_used?: string
}

export interface DraftRegenerateRequest {
  tone_style: string
  preserve_hashtags: boolean
}

export interface DraftRegenerateResponse {
  draft: DraftWithContent
  tone_style: string
  regenerated_at: string
  success: boolean
  message: string
}

// Add these methods to the APIClient class:

async getAllUserDrafts(): Promise<DraftWithContent[]> {
  const response = await this.client.get('/drafts/all')
  return response.data
}

async generateDraftFromContent(contentItemId: string, toneStyle: string): Promise<DraftWithContent> {
  const response = await this.client.post('/drafts/generate-from-content', {
    content_item_id: contentItemId,
    tone_style: toneStyle
  })
  return response.data
}

async regenerateDraft(draftId: string, options: {
  tone_style?: string
  preserve_hashtags?: boolean
}): Promise<DraftRegenerateResponse> {
  const response = await this.client.post(`/drafts/${draftId}/regenerate`, options)
  return response.data
}

async batchGenerateDrafts(options: {
  max_posts?: number
  min_relevance_score?: number
  style?: string
}): Promise<DraftWithContent[]> {
  const response = await this.client.post('/drafts/batch-generate', null, {
    params: options
  })
  return response.data
}

async deleteDraft(draftId: string): Promise<void> {
  await this.client.delete(`/drafts/${draftId}`)
}

async getToneStyles(): Promise<Array<{value: string, label: string, description: string}>> {
  const response = await this.client.get('/drafts/tone-styles')
  return response.data
}

async getContentWithDraftStatus(): Promise<Array<ContentItem & {draft_generated: boolean}>> {
  const response = await this.client.get('/content/with-draft-status')
  return response.data
}
