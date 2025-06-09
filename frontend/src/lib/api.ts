import axios, { AxiosInstance, AxiosError } from 'axios'

// Types
export interface User {
  id: string
  email: string
  full_name?: string
  linkedin_profile_url?: string
  is_active: boolean
  is_verified: boolean
  preferences: Record<string, any>
  tone_profile: Record<string, any>
  created_at: string
  updated_at: string
  last_login_at?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface ContentItem {
  id: string
  source_id: string
  source_name: string
  title: string
  url: string
  content: string
  author?: string
  published_at: string
  category?: string
  tags: string[]
  status: string
  relevance_score?: number
  created_at: string
  ai_analysis?: {
    llm_selected: boolean
    selection_reason?: string
    topic_category?: string
    confidence_score?: number
  }
}

export interface PostDraft {
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
  updated_at?: string
  generation_metadata?: any
  ai_model_used?: string
}

// Enhanced Draft interface
export interface DraftWithContent extends PostDraft {
  updated_at: string
  generation_metadata?: any
  ai_model_used?: string
}

export interface EngagementOpportunity {
  id: string
  target_id: string
  target_content: string
  target_author: string
  target_url?: string
  engagement_type: 'comment' | 'like' | 'share'
  priority: 'urgent' | 'high' | 'medium' | 'low'
  status: 'pending' | 'scheduled' | 'completed' | 'failed' | 'skipped'
  relevance_score?: number
  context_tags?: string[]
  engagement_reason?: string
  suggested_comment?: string
  created_at: string
  ai_analysis?: {
    confidence_score?: number
  }
}

export interface AIRecommendation {
  id: string
  type: string
  title: string
  description: string
  reasoning: string
  confidence: number
  priority: number
  action_items: string[]
  created_at: string
}

export interface PersonaMetrics {
  authority_score: number
  engagement_trend: number
  content_quality_avg: number
  network_growth: number
  next_post_prediction?: any
  growth_metrics?: any
  trends?: any
  engagement_history?: Array<{
    date: string
    likes: number
    comments: number
    shares: number
    views: number
  }>
}

export interface DailySummary {
  date: string
  total_articles: number
  ai_selected_count: number
  summary_text: string
  selection_metadata: {
    avg_relevance_score: number
    top_categories: string[]
  }
}

export interface ScoredRecommendation {
  draft_id: string
  draft?: PostDraft
  score: number
  action: 'post_now' | 'review_and_edit' | 'schedule_later' | 'skip'
  reasoning: string
  content_score: ContentScore
  optimal_timing?: {
    recommended_time: string
    expected_engagement: number
    confidence: number
    reasoning: string
  }
  estimated_performance?: EngagementPrediction
}

export interface ContentScore {
  relevance_score: number
  source_credibility: number
  timeliness_score: number
  engagement_potential: number
  composite_score: number
  confidence: number
}

export interface EngagementPrediction {
  predicted_likes: number
  predicted_comments: number
  predicted_shares: number
  predicted_views: number
  predicted_engagement_rate: number
  confidence: number
  model_type: string
  predicted_at: string
}

export interface LinkedInStatus {
  connected: boolean
  has_token: boolean
  token_expires_at?: string
  profile?: {
    name: string
    picture?: string
    email?: string
  }
}

export interface ContentSource {
  id: string
  user_id: string
  name: string
  source_type: string
  url?: string
  description?: string
  is_active: boolean
  check_frequency_hours: number
  last_checked_at?: string
  total_items_found: number
  total_items_processed: number
  created_at: string
}

export interface ContentPreferences {
  id: string
  user_id: string
  job_role: string
  industry: string
  primary_interests: string[]
  custom_prompt: string
  min_relevance_score: number
  max_articles_per_day: number
  content_types: string[]
  preferred_content_length: string
  min_word_count: number
  max_word_count: number
  content_freshness_hours: number
  learn_from_interactions: boolean
  created_at: string
  updated_at: string
}

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Authentication
  async login(email: string, password: string): Promise<LoginResponse> {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const response = await this.client.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  }

  async register(data: {
    email: string
    password: string
    full_name?: string
  }): Promise<LoginResponse> {
    const response = await this.client.post('/auth/register', data)
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  // Content Management
  async getContentByMode(mode: 'ai-selected' | 'fresh' | 'trending' | 'all'): Promise<ContentItem[]> {
    const response = await this.client.get('/content/content-by-mode', {
      params: { 
        mode,
        limit: 50,
        offset: 0 
      }
    })
    return response.data || []
  }

  async getDailyArticleSummary(date?: string): Promise<DailySummary> {
    const response = await this.client.get('/content/daily-summary', {
      params: date ? { date } : {},
    })
    return response.data
  }

  async runAIContentSelection(): Promise<{ message: string; selected_count: number }> {
    const response = await this.client.post('/content/trigger-ingestion')
    return response.data
  }

  // Draft Management - CONSOLIDATED METHODS
  async getDrafts(): Promise<PostDraft[]> {
    const response = await this.client.get('/drafts')
    return response.data.items || response.data
  }

  async getAllUserDrafts(): Promise<DraftWithContent[]> {
    const response = await this.client.get('/drafts/all')
    return response.data
  }

  async generateDraft(contentId: string): Promise<PostDraft> {
    const response = await this.client.post('/drafts', {
      content_item_id: contentId,
    })
    return response.data
  }

  async generateDraftFromContent(contentItemId: string, toneStyle: string): Promise<DraftWithContent> {
    const response = await this.client.post('/drafts/generate-from-content', {
      content_item_id: contentItemId,
      tone_style: toneStyle
    })
    return response.data
  }

  async updateDraft(draftId: string, data: Partial<PostDraft>): Promise<PostDraft> {
    const response = await this.client.put(`/drafts/${draftId}`, data)
    return response.data
  }

  async deleteDraft(draftId: string): Promise<void> {
    await this.client.delete(`/drafts/${draftId}`)
  }

  async publishDraft(draftId: string, scheduledFor?: string): Promise<any> {
    const response = await this.client.post(`/drafts/${draftId}/publish`, {
      scheduled_time: scheduledFor,
    })
    return response.data
  }

  async regenerateDraft(draftId: string, options: {
    tone_style?: string
    preserve_hashtags?: boolean
  }): Promise<DraftWithContent> {
    const response = await this.client.post(`/drafts/${draftId}/regenerate`, options)
    return response.data.draft || response.data
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

  async getToneStyles(): Promise<Array<{value: string, label: string, description: string}>> {
    return [
      { value: 'professional', label: 'Professional', description: 'Formal, business-focused tone' },
      { value: 'conversational', label: 'Conversational', description: 'Friendly, approachable tone' },
      { value: 'storytelling', label: 'Storytelling', description: 'Narrative-driven, engaging tone' },
      { value: 'humorous', label: 'Humorous', description: 'Light-hearted, entertaining tone' }
    ]
  }

  // AI Recommendations
  async getAIRecommendations(params?: {
    includeConfidence?: boolean
    includeReasoning?: boolean
    limit?: number
  }): Promise<AIRecommendation[]> {
    const response = await this.client.get('/analytics/recommendations', {
      params,
    })
    return response.data.recommendations || response.data
  }

  async getDraftRecommendations(): Promise<ScoredRecommendation[]> {
    const response = await this.client.get('/drafts/recommendations')
    return response.data.recommendations || response.data
  }

  async getPersonaMetrics(days: number = 30): Promise<PersonaMetrics> {
    const response = await this.client.get('/analytics/persona-metrics', {
      params: { days },
    })
    return response.data
  }

  async getEngagementPrediction(draftId: string): Promise<EngagementPrediction> {
    const response = await this.client.get(`/drafts/${draftId}/prediction`)
    return response.data
  }

  // Engagement
  async getCommentOpportunities(params?: {
    limit?: number
    status?: string
    priority?: string
  }): Promise<EngagementOpportunity[]> {
    const response = await this.client.get('/engagement/opportunities', {
      params,
    })
    return response.data.items || response.data
  }

  async createComment(data: {
    opportunity_id: string
    comment_text?: string
  }): Promise<any> {
    const response = await this.client.post('/engagement/comment', data)
    return response.data
  }

  // LinkedIn Connection
  async getLinkedInStatus(): Promise<LinkedInStatus> {
    const response = await this.client.get('/auth/linkedin/status')
    return response.data
  }

  async connectLinkedIn(): Promise<{ authorization_url: string; state: string; message: string }> {
    const response = await this.client.get('/auth/linkedin/connect')
    return response.data
  }

  async disconnectLinkedIn(): Promise<{ message: string }> {
    const response = await this.client.delete('/auth/linkedin/disconnect')
    return response.data
  }

  // Content Sources Management
  async getContentSources(): Promise<ContentSource[]> {
    const response = await this.client.get('/content/sources')
    return response.data
  }

  async createContentSource(data: {
    name: string
    source_type: string
    url?: string
    description?: string
    is_active?: boolean
    check_frequency_hours?: number
  }): Promise<ContentSource> {
    const response = await this.client.post('/content/sources', data)
    return response.data
  }

  async updateContentSource(id: string, data: Partial<ContentSource>): Promise<ContentSource> {
    const response = await this.client.put(`/content/sources/${id}`, data)
    return response.data
  }

  async deleteContentSource(id: string): Promise<void> {
    await this.client.delete(`/content/sources/${id}`)
  }

  async validateFeedUrl(url: string): Promise<{
    valid: boolean
    title?: string
    description?: string
    entry_count?: number
    error?: string
  }> {
    const response = await this.client.post('/content/validate-feed', { url })
    return response.data
  }

  // Content Preferences
  async getUserPreferences(): Promise<ContentPreferences> {
    const response = await this.client.get('/preferences/preferences')
    return response.data
  }

  async saveQuickPreferences(data: {
    jobRole: string
    industry: string
    interests: string[]
    customPrompt: string
    relevanceThreshold: number
    maxArticlesPerDay: number
  }): Promise<ContentPreferences> {
    const response = await this.client.post('/preferences/quick-setup', data)
    return response.data
  }

  async updatePreferences(data: Partial<ContentPreferences>): Promise<ContentPreferences> {
    const response = await this.client.put('/preferences/preferences', data)
    return response.data
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health')
    return response.data
  }
}

// Export singleton instance
export const api = new APIClient()

// Error handling helper
export function handleAPIError(error: any): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    if (error.message) {
      return error.message
    }
  }
  return 'An unexpected error occurred'
}