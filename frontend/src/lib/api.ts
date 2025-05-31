// frontend/src/lib/api.ts
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
          // Token expired or invalid
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
    formData.append('username', email) // OAuth2 expects 'username' field
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

  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await this.client.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  // Content Management
  async getContentByMode(mode: 'ai-selected' | 'fresh' | 'trending' | 'all'): Promise<ContentItem[]> {
    const response = await this.client.get(`/content`, {
      params: { mode },
    })
    return response.data.items || response.data
  }

  async getDailyArticleSummary(date?: string): Promise<DailySummary> {
    const response = await this.client.get('/content/daily-summary', {
      params: date ? { date } : {},
    })
    return response.data
  }

  async runAIContentSelection(): Promise<{ message: string; selected_count: number }> {
    const response = await this.client.post('/content/ai-selection')
    return response.data
  }

  // Draft Management
  async getDrafts(): Promise<PostDraft[]> {
    const response = await this.client.get('/drafts')
    return response.data.items || response.data
  }

  async generateDraft(contentId: string): Promise<PostDraft> {
    const response = await this.client.post('/drafts', {
      content_item_id: contentId,
    })
    return response.data
  }

  async updateDraft(draftId: string, data: Partial<PostDraft>): Promise<PostDraft> {
    const response = await this.client.put(`/drafts/${draftId}`, data)
    return response.data
  }

  async publishDraft(draftId: string, scheduledFor?: string): Promise<any> {
    const response = await this.client.post(`/drafts/${draftId}/publish`, {
      scheduled_time: scheduledFor,
    })
    return response.data
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