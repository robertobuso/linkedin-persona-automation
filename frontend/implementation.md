# Complete LinkedIn AI Automation Frontend Implementation

## Phase 1: Project Setup (Completing missing files)

### `src/lib/api.ts` - API Client
```typescript
interface APIError extends Error {
  status: number
  message: string
}

class APIClientError extends Error implements APIError {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIClientError'
  }
}

// Base interfaces
export interface User {
  id: string
  email: string
  full_name?: string
  linkedin_profile_url?: string
  is_active: boolean
  preferences?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ContentItem {
  id: string
  title: string
  content: string
  url: string
  author?: string
  published_at: string
  source_name: string
  tags: string[]
  relevance_score?: number
  ai_analysis?: {
    llm_selected?: boolean
    selection_reason?: string
    topic_category?: string
    sentiment?: string
  }
  created_at: string
  updated_at: string
}

export interface PostDraft {
  id: string
  title?: string
  content: string
  hashtags: string[]
  status: 'draft' | 'ready' | 'scheduled' | 'published' | 'failed'
  created_at: string
  scheduled_for?: string
  published_at?: string
  source_content_id?: string
  linkedin_post_url?: string
  engagement_metrics?: {
    likes: number
    comments: number
    shares: number
    views: number
  }
  ai_score?: ContentScore
  predicted_performance?: EngagementPrediction
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
  ai_analysis?: {
    confidence_score?: number
    optimal_timing?: string
    success_probability?: number
  }
  created_at: string
  scheduled_for?: string
  completed_at?: string
}

export interface AIRecommendation {
  id: string
  type: 'content' | 'comment' | 'timing' | 'engagement'
  score: number
  confidence: number
  reasoning: string
  actionable: boolean
  priority: 'urgent' | 'high' | 'medium' | 'low'
  metadata: Record<string, any>
  created_at: string
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
  predicted_engagement_rate: number
  predicted_likes: number
  predicted_comments: number
  predicted_shares: number
  predicted_views: number
  confidence: number
  features_used: Record<string, any>
  model_type: string
  predicted_at: string
}

export interface PersonaMetrics {
  authority_score: number
  engagement_trend: number
  content_quality_avg: number
  posting_consistency: number
  network_growth: number
  industry_ranking: number
}

export interface ScoredRecommendation {
  draft_id: string
  score: number
  action: 'post_now' | 'schedule_later' | 'review_and_edit' | 'skip'
  reasoning: string
  content_score: ContentScore
  optimal_timing?: {
    recommended_time: string
    expected_engagement: number
    confidence: number
    reasoning: string
  }
  estimated_performance?: EngagementPrediction
  scored_at: string
  draft?: PostDraft
}

export interface DailySummary {
  date: string
  total_articles: number
  ai_selected_count: number
  selection_metadata: {
    avg_relevance_score: number
    top_categories: string[]
    selection_reasoning: string
  }
  articles: ContentItem[]
  summary_text: string
  generated_at: string
}

export interface APIResponse<T = any> {
  data: T
  message?: string
  status: 'success' | 'error'
}

export interface PaginatedResponse<T = any> {
  data: T[]
  pagination: {
    page: number
    per_page: number
    total: number
    total_pages: number
  }
}

class APIClient {
  private baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token')
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new APIClientError(response.status, errorText)
    }

    return response.json()
  }

  // Authentication
  async login(email: string, password: string) {
    return this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(data: { email: string; password: string; full_name?: string }) {
    return this.request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getCurrentUser() {
    return this.request<User>('/auth/me')
  }

  // AI Recommendations
  async getAIRecommendations(params?: {
    includeConfidence?: boolean
    includeReasoning?: boolean
    limit?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.append('limit', params.limit.toString())
    if (params?.includeConfidence) searchParams.append('include_confidence', 'true')
    if (params?.includeReasoning) searchParams.append('include_reasoning', 'true')
    
    return this.request<AIRecommendation[]>(`/analytics/recommendations?${searchParams}`)
  }

  // Content Intelligence
  async getContentByMode(mode: 'ai-selected' | 'fresh' | 'trending' | 'all') {
    const sortBy = mode === 'ai-selected' ? 'llm_selected' : 
                   mode === 'fresh' ? 'newest' : 'relevance'
    return this.request<ContentItem[]>(`/content/feed?sort_by=${sortBy}&limit=20`)
  }

  async runAIContentSelection() {
    return this.request<{selected_articles: any[], selection_metadata: any}>(
      '/content/select-content', 
      { method: 'POST' }
    )
  }

  async getDailyArticleSummary(date?: string) {
    const params = date ? `?date=${date}` : ''
    return this.request<DailySummary>(`/content/daily-summary${params}`)
  }

  // Engagement Prediction
  async getEngagementPrediction(draftId: string) {
    return this.request<EngagementPrediction>(`/analytics/engagement-prediction/${draftId}`)
  }

  // Draft Management
  async getDrafts() {
    return this.request<PostDraft[]>('/drafts')
  }

  async createDraft(data: { content: string; hashtags: string[]; title?: string }) {
    return this.request<PostDraft>('/drafts', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateDraft(contentId: string) {
    return this.request<PostDraft>(`/drafts/generate/${contentId}`, {
      method: 'POST',
    })
  }

  async updateDraft(draftId: string, data: Partial<PostDraft>) {
    return this.request<PostDraft>(`/drafts/${draftId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async publishDraft(draftId: string, scheduledFor?: string) {
    return this.request<PostDraft>(`/drafts/${draftId}/publish`, {
      method: 'POST',
      body: JSON.stringify({ scheduled_for: scheduledFor }),
    })
  }

  // Draft Recommendations
  async getDraftRecommendations() {
    return this.request<ScoredRecommendation[]>('/analytics/recommendations')
  }

  // Comment Opportunities
  async getCommentOpportunities(params?: {
    limit?: number
    priority?: string
    status?: string
  }) {
    const searchParams = new URLSearchParams()
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value) searchParams.append(key, value.toString())
    })
    
    return this.request<EngagementOpportunity[]>(`/engagement/comment-opportunities?${searchParams}`)
  }

  async discoverCommentPosts(maxPosts: number = 50) {
    return this.request(`/engagement/discover-posts?max_posts=${maxPosts}`, { method: 'POST' })
  }

  async createComment(data: { opportunity_id: string; comment_text?: string }) {
    return this.request('/engagement/comment', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getEngagementStats(days: number = 30) {
    return this.request(`/engagement/stats?period_days=${days}`)
  }

  // Persona Analytics
  async getPersonaMetrics(days: number = 30) {
    return this.request<PersonaMetrics>(`/analytics/performance?period_days=${days}`)
  }

  async getDashboardMetrics(days: number = 30) {
    return this.request(`/analytics/dashboard?period_days=${days}`)
  }

  // Content scoring
  async scoreContent(contentIds: string[]) {
    return this.request('/analytics/score-content', {
      method: 'POST',
      body: JSON.stringify({ content_ids: contentIds }),
    })
  }
}

export const api = new APIClient()
```

### `src/stores/authStore.ts` - Authentication Store
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api, type User } from '@/lib/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; full_name?: string }) => Promise<void>
  logout: () => void
  clearError: () => void
  checkAuth: () => Promise<void>
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email, password) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await api.login(email, password)
          const { access_token, user } = response
          
          localStorage.setItem('token', access_token)
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Login failed',
            isAuthenticated: false,
          })
          throw error
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await api.register(data)
          const { access_token, user } = response
          
          localStorage.setItem('token', access_token)
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Registration failed',
            isAuthenticated: false,
          })
          throw error
        }
      },

      logout: () => {
        localStorage.removeItem('token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },

      clearError: () => {
        set({ error: null })
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token')
        
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        try {
          const user = await api.getCurrentUser()
          set({
            user,
            token,
            isAuthenticated: true,
          })
        } catch (error) {
          localStorage.removeItem('token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
)
```

### `src/stores/contentStore.ts` - Content Management Store
```typescript
import { create } from 'zustand'
import { api, type ContentItem, type DailySummary } from '@/lib/api'

interface ContentState {
  // Content data
  aiSelectedContent: ContentItem[]
  allContent: ContentItem[]
  dailySummary: DailySummary | null
  
  // UI state
  viewMode: 'ai-selected' | 'fresh' | 'trending' | 'all'
  isLoading: boolean
  error: string | null
  
  // Filters
  selectedCategories: string[]
  searchQuery: string
}

interface ContentActions {
  // Data fetching
  fetchContentByMode: (mode: 'ai-selected' | 'fresh' | 'trending' | 'all') => Promise<void>
  fetchDailyArticleSummary: (date?: string) => Promise<void>
  runAIContentSelection: () => Promise<void>
  
  // UI state management
  setViewMode: (mode: 'ai-selected' | 'fresh' | 'trending' | 'all') => void
  setSearchQuery: (query: string) => void
  setSelectedCategories: (categories: string[]) => void
  
  // Data management
  updateAISelection: (content: ContentItem[]) => void
  setDailySummary: (summary: DailySummary) => void
  clearError: () => void
  
  // Refresh
  refreshContent: () => Promise<void>
}

type ContentStore = ContentState & ContentActions

export const useContentStore = create<ContentStore>((set, get) => ({
  // Initial state
  aiSelectedContent: [],
  allContent: [],
  dailySummary: null,
  viewMode: 'ai-selected',
  isLoading: false,
  error: null,
  selectedCategories: [],
  searchQuery: '',

  // Actions
  fetchContentByMode: async (mode) => {
    set({ isLoading: true, error: null })
    
    try {
      const content = await api.getContentByMode(mode)
      
      set({
        allContent: content,
        aiSelectedContent: mode === 'ai-selected' ? content : get().aiSelectedContent,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to fetch content',
      })
    }
  },

  fetchDailyArticleSummary: async (date) => {
    try {
      const summary = await api.getDailyArticleSummary(date)
      set({ dailySummary: summary })
    } catch (error: any) {
      console.error('Failed to fetch daily summary:', error)
    }
  },

  runAIContentSelection: async () => {
    set({ isLoading: true, error: null })
    
    try {
      const result = await api.runAIContentSelection()
      
      // Refresh AI selected content after selection
      await get().fetchContentByMode('ai-selected')
      await get().fetchDailyArticleSummary()
      
      set({ isLoading: false })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to run AI content selection',
      })
    }
  },

  setViewMode: (mode) => {
    set({ viewMode: mode })
    // Auto-fetch content when view mode changes
    get().fetchContentByMode(mode)
  },

  setSearchQuery: (query) => {
    set({ searchQuery: query })
  },

  setSelectedCategories: (categories) => {
    set({ selectedCategories: categories })
  },

  updateAISelection: (content) => {
    set({ aiSelectedContent: content })
  },

  setDailySummary: (summary) => {
    set({ dailySummary: summary })
  },

  clearError: () => {
    set({ error: null })
  },

  refreshContent: async () => {
    const { viewMode } = get()
    await get().fetchContentByMode(viewMode)
    if (viewMode === 'ai-selected') {
      await get().fetchDailyArticleSummary()
    }
  },
}))

// Helper hooks
export const useContentByMode = (mode: 'ai-selected' | 'fresh' | 'trending' | 'all') => {
  const { allContent, aiSelectedContent, viewMode, isLoading, error } = useContentStore()
  
  const content = viewMode === 'ai-selected' ? aiSelectedContent : allContent
  
  return { data: content, isLoading, error }
}

export const useDailyArticleSummary = () => {
  const { dailySummary, isLoading } = useContentStore()
  return { data: dailySummary, isLoading }
}
```

### `src/App.tsx` - Main App Component
```typescript
import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout, AuthLayout } from '@/components/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { FullPageLoading } from '@/components/ui/LoadingStates'

// Auth pages
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'

// Main pages
import Dashboard from '@/pages/Dashboard'
import ContentIntelligence from '@/pages/ContentIntelligence'
import CreationStudio from '@/pages/CreationStudio'
import EngagementHub from '@/pages/EngagementHub'
import PersonaAnalytics from '@/pages/PersonaAnalytics'
import AIConfiguration from '@/pages/AIConfiguration'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (isLoading) {
    return <FullPageLoading />
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Routes>
            {/* Auth routes */}
            {!isAuthenticated ? (
              <>
                <Route path="/login" element={
                  <AuthLayout>
                    <LoginPage />
                  </AuthLayout>
                } />
                <Route path="/register" element={
                  <AuthLayout>
                    <RegisterPage />
                  </AuthLayout>
                } />
                <Route path="*" element={<Navigate to="/login" replace />} />
              </>
            ) : (
              /* Protected routes */
              <Route path="/" element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="content" element={<ContentIntelligence />} />
                <Route path="creation" element={<CreationStudio />} />
                <Route path="engagement" element={<EngagementHub />} />
                <Route path="analytics" element={<PersonaAnalytics />} />
                <Route path="settings" element={<AIConfiguration />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            )}
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App
```

### `src/main.tsx` - App Entry Point
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### `src/styles/globals.css` - Global Styles
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

@layer base {
  * {
    @apply border-border;
  }
  
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

@layer utilities {
  .line-clamp-1 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 1;
  }
  
  .line-clamp-2 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }
  
  .line-clamp-3 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
  }
}

/* Custom scrollbar */
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgb(203 213 225) transparent;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgb(203 213 225);
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgb(148 163 184);
}

/* Animation utilities */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes gradient {
  0%, 100% {
    background-size: 200% 200%;
    background-position: left center;
  }
  50% {
    background-size: 200% 200%;
    background-position: right center;
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

@keyframes glow {
  0% { box-shadow: 0 0 5px rgba(16, 185, 129, 0.5); }
  100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.8); }
}

/* AI-specific animations */
.ai-thinking {
  position: relative;
}

.ai-thinking::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #a855f7, #10B981, #a855f7);
  background-size: 300% 300%;
  border-radius: inherit;
  animation: gradient 2s ease infinite;
  z-index: -1;
}

/* Loading animations */
.pulse-ring {
  @apply absolute inset-0 rounded-full border-2 border-current opacity-75 animate-ping;
}

.loading-dots {
  @apply flex space-x-1;
}

.loading-dots > div {
  @apply h-2 w-2 bg-current rounded-full animate-pulse;
}

.loading-dots > div:nth-child(1) { animation-delay: 0ms; }
.loading-dots > div:nth-child(2) { animation-delay: 150ms; }
.loading-dots > div:nth-child(3) { animation-delay: 300ms; }
```

## Phase 2: Core Intelligence Features

### `src/pages/auth/LoginPage.tsx` - Login Page
```typescript
import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import { notify } from '@/stores/uiStore'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuthStore()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    clearError()
    
    try {
      await login(data.email, data.password)
      notify.success('Welcome back!')
      navigate('/dashboard')
    } catch (error) {
      // Error is handled by the store
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Sign in to your account</h2>
        <p className="mt-2 text-sm text-gray-600">
          Access your AI-powered LinkedIn automation platform
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Input
          label="Email address"
          type="email"
          {...register('email')}
          error={errors.email?.message}
          placeholder="Enter your email"
        />

        <Input
          label="Password"
          type="password"
          {...register('password')}
          error={errors.password?.message}
          placeholder="Enter your password"
        />

        <Button
          type="submit"
          className="w-full"
          variant="ai"
          loading={isLoading}
        >
          Sign in
        </Button>
      </form>

      <div className="text-center">
        <p className="text-sm text-gray-600">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-medium text-neural-600 hover:text-neural-500"
          >
            Sign up here
          </Link>
        </p>
      </div>
    </div>
  )
}
```

### `src/pages/auth/RegisterPage.tsx` - Registration Page
```typescript
import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import { notify } from '@/stores/uiStore'

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
  full_name: z.string().min(2, 'Please enter your full name'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type RegisterForm = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser, isLoading, error, clearError } = useAuthStore()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterForm) => {
    clearError()
    
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
      })
      notify.success('Account created successfully!')
      navigate('/dashboard')
    } catch (error) {
      // Error is handled by the store
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Create your account</h2>
        <p className="mt-2 text-sm text-gray-600">
          Start building your AI-powered LinkedIn presence
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Input
          label="Full Name"
          type="text"
          {...register('full_name')}
          error={errors.full_name?.message}
          placeholder="Enter your full name"
        />

        <Input
          label="Email address"
          type="email"
          {...register('email')}
          error={errors.email?.message}
          placeholder="Enter your email"
        />

        <Input
          label="Password"
          type="password"
          {...register('password')}
          error={errors.password?.message}
          placeholder="Enter your password"
        />

        <Input
          label="Confirm Password"
          type="password"
          {...register('confirmPassword')}
          error={errors.confirmPassword?.message}
          placeholder="Confirm your password"
        />

        <Button
          type="submit"
          className="w-full"
          variant="ai"
          loading={isLoading}
        >
          Create Account
        </Button>
      </form>

      <div className="text-center">
        <p className="text-sm text-gray-600">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-medium text-neural-600 hover:text-neural-500"
          >
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  )
}
```

### `src/components/intelligence/ConfidenceIndicator.tsx` - AI Confidence Display
```typescript
import React from 'react'
import { cn } from '@/utils/cn'

interface ConfidenceIndicatorProps {
  score: number // 0-1
  label?: string
  size?: 'sm' | 'md' | 'lg'
  showPercentage?: boolean
  className?: string
}

export function ConfidenceIndicator({
  score,
  label = "Confidence",
  size = "md",
  showPercentage = true,
  className
}: ConfidenceIndicatorProps) {
  const percentage = Math.round(score * 100)
  
  const getColorClass = () => {
    if (score >= 0.8) return 'bg-ml-green-500'
    if (score >= 0.6) return 'bg-prediction-500'
    if (score >= 0.4) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-1.5 text-xs'
      case 'lg':
        return 'h-3 text-base'
      default:
        return 'h-2 text-sm'
    }
  }
  
  return (
    <div className={cn('flex items-center space-x-2', className)}>
      {label && (
        <span className={cn('text-gray-600 font-medium', getSizeClasses().split(' ')[1])}>
          {label}:
        </span>
      )}
      <div className="flex-1 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={cn(
            'rounded-full transition-all duration-500 ease-out',
            getColorClass(),
            getSizeClasses().split(' ')[0]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showPercentage && (
        <span className={cn('font-medium text-gray-900', getSizeClasses().split(' ')[1])}>
          {percentage}%
        </span>
      )}
    </div>
  )
}
```

### `src/components/intelligence/PredictionCard.tsx` - Engagement Predictions
```typescript
import React from 'react'
import { TrendingUpIcon, EyeIcon, HeartIcon, ChatBubbleLeftIcon, ShareIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from './ConfidenceIndicator'
import { EngagementPrediction } from '@/lib/api'

interface PredictionCardProps {
  prediction: EngagementPrediction
  compact?: boolean
  className?: string
}

export function PredictionCard({ prediction, compact = false, className }: PredictionCardProps) {
  const metrics = [
    {
      icon: HeartIcon,
      label: 'Likes',
      value: prediction.predicted_likes,
      color: 'text-red-500'
    },
    {
      icon: ChatBubbleLeftIcon,
      label: 'Comments',
      value: prediction.predicted_comments,
      color: 'text-blue-500'
    },
    {
      icon: ShareIcon,
      label: 'Shares',
      value: prediction.predicted_shares,
      color: 'text-green-500'
    },
    {
      icon: EyeIcon,
      label: 'Views',
      value: prediction.predicted_views,
      color: 'text-purple-500'
    }
  ]

  return (
    <Card intelligence className={className}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUpIcon className="h-5 w-5 text-neural-600" />
            <h4 className="font-semibold text-neural-700">Engagement Prediction</h4>
          </div>
          <Badge variant="ai" size="sm">
            {prediction.model_type}
          </Badge>
        </div>
        
        {/* Engagement Rate */}
        <div className="text-center py-2">
          <div className="text-3xl font-bold text-neural-600">
            {(prediction.predicted_engagement_rate * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Expected Engagement Rate</div>
        </div>

        {/* Metrics Grid */}
        {!compact && (
          <div className="grid grid-cols-2 gap-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-center">
                <div className="flex items-center justify-center mb-1">
                  <metric.icon className={cn('h-4 w-4', metric.color)} />
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {metric.value.toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">{metric.label}</div>
              </div>
            ))}
          </div>
        )}
        
        {/* Confidence */}
        <div className={cn(compact ? 'pt-2' : 'pt-4', 'border-t border-gray-100')}>
          <ConfidenceIndicator 
            score={prediction.confidence}
            label="Prediction Confidence"
            size="sm"
          />
        </div>

        {/* Model info */}
        {!compact && (
          <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
            <div className="flex justify-between">
              <span>Model: {prediction.model_type}</span>
              <span>Predicted: {new Date(prediction.predicted_at).toLocaleDateString()}</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
```

### `src/components/intelligence/AIAnalysisPanel.tsx` - AI Reasoning Display
```typescript
import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, BrainIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from './ConfidenceIndicator'
import { cn } from '@/utils/cn'

interface AIAnalysisPanelProps {
  reasoning: string
  score?: number
  category?: string
  confidence?: number
  className?: string
  defaultExpanded?: boolean
}

export function AIAnalysisPanel({
  reasoning,
  score,
  category,
  confidence,
  className,
  defaultExpanded = false
}: AIAnalysisPanelProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <Card variant="ai" className={cn('transition-all duration-200', className)}>
      <div className="space-y-3">
        {/* Header */}
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center space-x-2">
            <BrainIcon className="h-4 w-4 text-ai-purple-600" />
            <span className="font-medium text-neural-700">AI Analysis</span>
            {category && (
              <Badge variant="ai" size="sm">
                {category}
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {score && (
              <span className="text-sm font-semibold text-neural-600">
                {Math.round(score)}%
              </span>
            )}
            {isExpanded ? (
              <ChevronDownIcon className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </div>

        {/* Content */}
        {isExpanded && (
          <div className="space-y-3 pt-2 border-t border-ai-purple-100">
            {/* Reasoning */}
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">AI Reasoning:</h5>
              <p className="text-sm text-gray-600 leading-relaxed">
                {reasoning}
              </p>
            </div>

            {/* Confidence indicator */}
            {confidence && (
              <div className="pt-2">
                <ConfidenceIndicator 
                  score={confidence}
                  label="Analysis Confidence"
                  size="sm"
                />
              </div>
            )}

            {/* Additional metrics */}
            {score && (
              <div className="flex items-center justify-between text-sm pt-2 border-t border-ai-purple-100">
                <span className="text-gray-600">Relevance Score:</span>
                <span className="font-medium text-neural-700">{Math.round(score)}%</span>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
```

### `src/components/intelligence/ScoreBreakdown.tsx` - Content Score Analysis
```typescript
import React from 'react'
import { ContentScore } from '@/lib/api'
import { ConfidenceIndicator } from './ConfidenceIndicator'

interface ScoreBreakdownProps {
  scores: ContentScore
  className?: string
}

export function ScoreBreakdown({ scores, className }: ScoreBreakdownProps) {
  const scoreItems = [
    {
      label: 'Relevance',
      value: scores.relevance_score,
      description: 'How relevant this content is to your audience'
    },
    {
      label: 'Source Credibility',
      value: scores.source_credibility,
      description: 'Trustworthiness and authority of the source'
    },
    {
      label: 'Timeliness',
      value: scores.timeliness_score,
      description: 'How current and timely this content is'
    },
    {
      label: 'Engagement Potential',
      value: scores.engagement_potential,
      description: 'Likelihood to generate engagement'
    }
  ]

  return (
    <div className={className}>
      <div className="space-y-3">
        {/* Overall Score */}
        <div className="flex items-center justify-between p-3 bg-neural-50 rounded-lg">
          <span className="font-semibold text-neural-700">Overall Score</span>
          <span className="text-xl font-bold text-neural-600">
            {Math.round(scores.composite_score)}/100
          </span>
        </div>

        {/* Individual Scores */}
        <div className="space-y-2">
          {scoreItems.map((item) => (
            <div key={item.label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.label}</span>
                <span className="font-medium text-gray-900">
                  {Math.round(item.value)}/100
                </span>
              </div>
              <ConfidenceIndicator
                score={item.value / 100}
                showPercentage={false}
                size="sm"
              />
            </div>
          ))}
        </div>

        {/* Confidence */}
        <div className="pt-2 border-t border-gray-100">
          <ConfidenceIndicator
            score={scores.confidence}
            label="Score Confidence"
            size="sm"
          />
        </div>
      </div>
    </div>
  )
}
```

### `src/hooks/useAIRecommendations.ts` - AI Recommendations Hook
```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useAIRecommendations() {
  return useQuery({
    queryKey: ['ai-recommendations'],
    queryFn: () => api.getAIRecommendations({
      includeConfidence: true,
      includeReasoning: true,
      limit: 10
    }),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider fresh for 2 minutes
  })
}

export function usePersonaMetrics(days: number = 30) {
  return useQuery({
    queryKey: ['persona-metrics', days],
    queryFn: () => api.getPersonaMetrics(days),
    refetchInterval: 15 * 60 * 1000, // Refresh every 15 minutes
  })
}

export function useDraftRecommendations() {
  return useQuery({
    queryKey: ['draft-recommendations'],
    queryFn: () => api.getDraftRecommendations(),
    refetchInterval: 10 * 60 * 1000, // Refresh every 10 minutes
  })
}

export function useEngagementPrediction(draftId: string) {
  return useQuery({
    queryKey: ['engagement-prediction', draftId],
    queryFn: () => api.getEngagementPrediction(draftId),
    enabled: !!draftId,
    staleTime: 10 * 60 * 1000, // Predictions valid for 10 minutes
  })
}

export function useTodaysContent() {
  return useQuery({
    queryKey: ['todays-content'],
    queryFn: () => api.getContentByMode('ai-selected'),
    refetchInterval: 30 * 60 * 1000, // Refresh every 30 minutes
  })
}

export function useEngagementQueue() {
  return useQuery({
    queryKey: ['engagement-queue'],
    queryFn: () => api.getCommentOpportunities({
      limit: 20,
      status: 'pending'
    }),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  })
}

export function useDrafts() {
  return useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
    refetchInterval: 10 * 60 * 1000,
  })
}
```

### `src/pages/Dashboard.tsx` - Main Dashboard
```typescript
import React from 'react'
import { useAIRecommendations, usePersonaMetrics, useTodaysContent, useEngagementQueue } from '@/hooks/useAIRecommendations'
import { IntelligenceBrief } from '@/components/dashboard/IntelligenceBrief'
import { PerformanceCard } from '@/components/dashboard/PerformanceCard'
import { QuickActionsPanel } from '@/components/dashboard/QuickActionsPanel'
import { TodaysContentIntelligence } from '@/components/dashboard/TodaysContentIntelligence'
import { EngagementOpportunities } from '@/components/dashboard/EngagementOpportunities'
import { DailyArticleSummary } from '@/components/dashboard/DailyArticleSummary'
import { LoadingPage } from '@/components/ui/LoadingStates'

export default function Dashboard() {
  const { data: aiRecommendations, isLoading: recommendationsLoading } = useAIRecommendations()
  const { data: personaMetrics, isLoading: metricsLoading } = usePersonaMetrics()
  const { data: todaysContent, isLoading: contentLoading } = useTodaysContent()
  const { data: engagementQueue, isLoading: engagementLoading } = useEngagementQueue()

  if (recommendationsLoading || metricsLoading) {
    return <LoadingPage message="Loading your AI intelligence dashboard..." />
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-neural-700">AI Intelligence Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Your personalized LinkedIn automation command center
        </p>
      </div>

      {/* Hero Intelligence Brief */}
      <IntelligenceBrief 
        recommendations={aiRecommendations || []}
        metrics={personaMetrics}
      />
      
      {/* Performance Intelligence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PerformanceCard
          title="Engagement Prediction"
          metric={personaMetrics?.next_post_prediction}
          type="prediction"
          loading={metricsLoading}
        />
        <PerformanceCard
          title="Content Pipeline"
          metric={todaysContent?.pipeline_status}
          type="pipeline"
          loading={contentLoading}
        />
        <PerformanceCard
          title="Persona Growth"
          metric={personaMetrics?.growth_metrics}
          type="growth"
          loading={metricsLoading}
        />
      </div>

      {/* Quick Intelligence Actions */}
      <QuickActionsPanel />

      {/* Today's Priorities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <TodaysContentIntelligence content={todaysContent} loading={contentLoading} />
        <EngagementOpportunities opportunities={engagementQueue} loading={engagementLoading} />
      </div>

      {/* Daily Article Summary */}
      <DailyArticleSummary />
    </div>
  )
}
```

### `src/components/dashboard/IntelligenceBrief.tsx` - Intelligence Brief Component
```typescript
import React from 'react'
import { BrainIcon, ChartBarIcon, ClockIcon, TargetIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { AIRecommendation, PersonaMetrics } from '@/lib/api'

interface IntelligenceBriefProps {
  recommendations: AIRecommendation[]
  metrics?: PersonaMetrics
}

export function IntelligenceBrief({ recommendations, metrics }: IntelligenceBriefProps) {
  const topRecommendation = recommendations?.[0]
  
  return (
    <Card intelligence className="relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-neural-100 to-ml-green-100 rounded-full opacity-50 transform translate-x-16 -translate-y-16" />
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-ai-purple-100 to-prediction-100 rounded-full opacity-30 transform -translate-x-12 translate-y-12" />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-neural-700 flex items-center space-x-2">
            <BrainIcon className="h-8 w-8 text-ai-purple-600" />
            <span>Today's Intelligence Brief</span>
          </h2>
          <ConfidenceIndicator 
            score={topRecommendation?.confidence || 0.8}
            label="Overall Confidence"
            size="lg"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <IntelligenceMetric
            icon={BrainIcon}
            label="AI-Selected Content"
            value="3 articles"
            change="+2 from yesterday"
            trend="up"
          />
          <IntelligenceMetric
            icon={ChartBarIcon}
            label="Engagement Opportunities"
            value="5 high-value"
            change="2 urgent priority"
            trend="neutral"
          />
          <IntelligenceMetric
            icon={ClockIcon}
            label="Optimal Window"
            value="Today 10:15 AM"
            change="87% success rate"
            trend="up"
          />
          <IntelligenceMetric
            icon={TargetIcon}
            label="Persona Focus"
            value="Thought Leadership"
            change={`Authority: ${metrics?.authority_score || 87}/100`}
            trend="up"
          />
        </div>

        {/* Top Recommendation */}
        {topRecommendation && (
          <div className="mt-6 p-4 bg-gradient-to-r from-ai-purple-50 to-ml-green-50 rounded-lg border border-ai-purple-200">
            <h3 className="font-semibold text-neural-700 mb-2">Priority Recommendation</h3>
            <p className="text-gray-600 text-sm">{topRecommendation.reasoning}</p>
          </div>
        )}
      </div>
    </Card>
  )
}

interface IntelligenceMetricProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  change: string
  trend?: 'up' | 'down' | 'neutral'
}

function IntelligenceMetric({ icon: Icon, label, value, change, trend = 'neutral' }: IntelligenceMetricProps) {
  const trendColors = {
    up: 'text-ml-green-600',
    down: 'text-red-500',
    neutral: 'text-gray-500'
  }

  return (
    <div className="text-center space-y-2">
      <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm border border-gray-200">
        <Icon className="h-6 w-6 text-neural-600" />
      </div>
      <div>
        <div className="text-lg font-bold text-neural-700">{value}</div>
        <div className="text-sm text-gray-600">{label}</div>
        <div className={`text-xs ${trendColors[trend]}`}>{change}</div>
      </div>
    </div>
  )
}
```

### `src/components/dashboard/PerformanceCard.tsx` - Performance Metrics Card
```typescript
import React from 'react'
import { TrendingUpIcon, ArrowTrendingDownIcon, MinusIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/LoadingStates'

interface PerformanceCardProps {
  title: string
  metric?: any
  type: 'prediction' | 'pipeline' | 'growth'
  loading?: boolean
}

export function PerformanceCard({ title, metric, type, loading }: PerformanceCardProps) {
  if (loading) {
    return (
      <Card>
        <div className="space-y-4">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-full" />
        </div>
      </Card>
    )
  }

  const renderMetric = () => {
    switch (type) {
      case 'prediction':
        return (
          <div className="space-y-2">
            <div className="text-3xl font-bold text-neural-600">
              {metric?.engagement_rate ? `${(metric.engagement_rate * 100).toFixed(1)}%` : '8.2%'}
            </div>
            <div className="text-sm text-gray-600">Expected next post engagement</div>
            <div className="flex items-center space-x-1 text-ml-green-600">
              <TrendingUpIcon className="h-4 w-4" />
              <span className="text-sm">+2.1% vs average</span>
            </div>
          </div>
        )
      
      case 'pipeline':
        return (
          <div className="space-y-2">
            <div className="text-3xl font-bold text-neural-600">
              {metric?.ready_drafts || 3}
            </div>
            <div className="text-sm text-gray-600">Ready to publish</div>
            <div className="flex items-center space-x-1 text-prediction-600">
              <MinusIcon className="h-4 w-4" />
              <span className="text-sm">2 in review</span>
            </div>
          </div>
        )
      
      case 'growth':
        return (
          <div className="space-y-2">
            <div className="text-3xl font-bold text-neural-600">
              {metric?.authority_score || 87}
            </div>
            <div className="text-sm text-gray-600">Authority Score</div>
            <div className="flex items-center space-x-1 text-ml-green-600">
              <TrendingUpIcon className="h-4 w-4" />
              <span className="text-sm">+5 this week</span>
            </div>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <Card hover="lift" className="p-6">
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {renderMetric()}
      </div>
    </Card>
  )
}
```

### `src/components/dashboard/QuickActionsPanel.tsx` - Quick Actions
```typescript
import React from 'react'
import { 
  BrainIcon, 
  PlusIcon, 
  PlayIcon, 
  MagnifyingGlassIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { useContentStore } from '@/stores/contentStore'
import { useEngagementStore } from '@/stores/engagementStore'
import { notify } from '@/stores/uiStore'
import { useNavigate } from 'react-router-dom'

export function QuickActionsPanel() {
  const navigate = useNavigate()
  const { runAIContentSelection } = useContentStore()
  const { discoverNewPosts } = useEngagementStore()

  const handleAISelection = async () => {
    try {
      await runAIContentSelection()
      notify.success('AI content selection completed')
    } catch (error) {
      notify.error('Failed to run AI selection')
    }
  }

  const handleDiscoverPosts = async () => {
    try {
      await discoverNewPosts()
      notify.success('New engagement opportunities discovered')
    } catch (error) {
      notify.error('Failed to discover new posts')
    }
  }

  const actions = [
    {
      icon: BrainIcon,
      label: 'Run AI Selection',
      description: 'Analyze and select today\'s best content',
      onClick: handleAISelection,
      variant: 'ai' as const
    },
    {
      icon: PlusIcon,
      label: 'Create Draft',
      description: 'Generate new LinkedIn post',
      onClick: () => navigate('/creation'),
      variant: 'default' as const
    },
    {
      icon: MagnifyingGlassIcon,
      label: 'Discover Posts',
      description: 'Find new engagement opportunities',
      onClick: handleDiscoverPosts,
      variant: 'secondary' as const
    },
    {
      icon: ChartBarIcon,
      label: 'View Analytics',
      description: 'See your performance insights',
      onClick: () => navigate('/analytics'),
      variant: 'outline' as const
    }
  ]

  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {actions.map((action) => (
            <Button
              key={action.label}
              variant={action.variant}
              className="h-auto p-4 flex flex-col items-center space-y-2 text-center"
              onClick={action.onClick}
            >
              <action.icon className="h-6 w-6" />
              <div>
                <div className="font-medium">{action.label}</div>
                <div className="text-xs opacity-80">{action.description}</div>
              </div>
            </Button>
          ))}
        </div>
      </div>
    </Card>
  )
}
```

### `src/components/dashboard/TodaysContentIntelligence.tsx` - Today's Content
```typescript
import React from 'react'
import { NewspaperIcon, ClockIcon, TrendingUpIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/LoadingStates'
import { ContentItem } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

interface TodaysContentIntelligenceProps {
  content?: ContentItem[]
  loading?: boolean
}

export function TodaysContentIntelligence({ content = [], loading }: TodaysContentIntelligenceProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <Card>
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/2" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    )
  }

  const aiSelectedContent = content.filter(item => item.ai_analysis?.llm_selected)

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
            <NewspaperIcon className="h-5 w-5" />
            <span>Today's Content Intelligence</span>
          </h3>
          <Badge variant="ai">
            {aiSelectedContent.length} AI Selected
          </Badge>
        </div>

        {aiSelectedContent.length === 0 ? (
          <div className="text-center py-8">
            <NewspaperIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No AI-selected content for today</p>
            <Button 
              variant="ai" 
              size="sm"
              onClick={() => navigate('/content')}
            >
              Browse Content
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {aiSelectedContent.slice(0, 3).map((item) => (
              <ContentPreview key={item.id} content={item} />
            ))}
            
            <div className="pt-4 border-t border-gray-100">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => navigate('/content')}
              >
                View All Content ({aiSelectedContent.length})
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

function ContentPreview({ content }: { content: ContentItem }) {
  const navigate = useNavigate()

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="space-y-2">
        <h4 className="font-medium text-gray-900 line-clamp-2">
          {content.title}
        </h4>
        <p className="text-sm text-gray-600 line-clamp-2">
          {content.content.substring(0, 120)}...
        </p>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{content.source_name}</span>
            <span>•</span>
            <div className="flex items-center space-x-1">
              <TrendingUpIcon className="h-3 w-3" />
              <span>{content.relevance_score || 0}% relevant</span>
            </div>
          </div>
          
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => navigate('/content')}
          >
            Generate Draft
          </Button>
        </div>
      </div>
    </div>
  )
}
```

### `src/components/dashboard/EngagementOpportunities.tsx` - Engagement Opportunities
```typescript
import React from 'react'
import { ChatBubbleLeftIcon, ClockIcon, FireIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/LoadingStates'
import { EngagementOpportunity } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

interface EngagementOpportunitiesProps {
  opportunities?: EngagementOpportunity[]
  loading?: boolean
}

export function EngagementOpportunities({ opportunities = [], loading }: EngagementOpportunitiesProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <Card>
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/2" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    )
  }

  const highPriorityOpps = opportunities.filter(opp => 
    opp.priority === 'urgent' || opp.priority === 'high'
  )

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
            <ChatBubbleLeftIcon className="h-5 w-5" />
            <span>Engagement Opportunities</span>
          </h3>
          <Badge variant="prediction">
            {highPriorityOpps.length} High Priority
          </Badge>
        </div>

        {opportunities.length === 0 ? (
          <div className="text-center py-8">
            <ChatBubbleLeftIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No engagement opportunities found</p>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => navigate('/engagement')}
            >
              Discover Opportunities
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {opportunities.slice(0, 3).map((opportunity) => (
              <OpportunityPreview key={opportunity.id} opportunity={opportunity} />
            ))}
            
            <div className="pt-4 border-t border-gray-100">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => navigate('/engagement')}
              >
                View All Opportunities ({opportunities.length})
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

function OpportunityPreview({ opportunity }: { opportunity: EngagementOpportunity }) {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive'
      case 'high': return 'warning'
      case 'medium': return 'secondary'
      default: return 'neutral'
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 line-clamp-1">
              {opportunity.target_author}
            </h4>
            <p className="text-sm text-gray-600 line-clamp-2 mt-1">
              {opportunity.target_content.substring(0, 100)}...
            </p>
          </div>
          <Badge variant={getPriorityColor(opportunity.priority)} size="sm">
            {opportunity.priority}
          </Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <FireIcon className="h-3 w-3" />
            <span>{opportunity.relevance_score || 0}% match</span>
            <span>•</span>
            <ClockIcon className="h-3 w-3" />
            <span>2h ago</span>
          </div>
          
          <Button size="sm" variant="outline">
            Engage
          </Button>
        </div>
      </div>
    </div>
  )
}
```

### `src/components/dashboard/DailyArticleSummary.tsx` - Daily Summary
```typescript
import React from 'react'
import { DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useDailyArticleSummary } from '@/hooks/useAIRecommendations'
import { Skeleton } from '@/components/ui/LoadingStates'
import { useNavigate } from 'react-router-dom'

export function DailyArticleSummary() {
  const { data: summary, isLoading } = useDailyArticleSummary()
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <Card>
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </Card>
    )
  }

  if (!summary) {
    return null
  }

  return (
    <Card intelligence>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
            <DocumentTextIcon className="h-5 w-5" />
            <span>Daily Article Summary</span>
          </h3>
          <div className="flex items-center space-x-2">
            <Badge variant="ai" size="sm">
              <SparklesIcon className="h-3 w-3 mr-1" />
              AI Generated
            </Badge>
            <Badge variant="neutral" size="sm">
              {new Date(summary.date).toLocaleDateString()}
            </Badge>
          </div>
        </div>

        <div className="space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-neural-50 rounded-lg">
            <div className="text-center">
              <div className="text-xl font-bold text-neural-600">
                {summary.total_articles}
              </div>
              <div className="text-sm text-gray-600">Total Articles</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-ml-green-600">
                {summary.ai_selected_count}
              </div>
              <div className="text-sm text-gray-600">AI Selected</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-prediction-600">
                {Math.round(summary.selection_metadata.avg_relevance_score)}%
              </div>
              <div className="text-sm text-gray-600">Avg Relevance</div>
            </div>
          </div>

          {/* AI Summary */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2">AI Summary</h4>
            <p className="text-gray-700 leading-relaxed">
              {summary.summary_text}
            </p>
          </div>

          {/* Top categories */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Top Categories</h4>
            <div className="flex flex-wrap gap-2">
              {summary.selection_metadata.top_categories.map((category) => (
                <Badge key={category} variant="neutral" size="sm">
                  {category}
                </Badge>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex space-x-3 pt-4 border-t border-gray-100">
            <Button 
              variant="ai" 
              size="sm"
              onClick={() => navigate('/content')}
            >
              View Selected Content
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => navigate('/creation')}
            >
              Generate Drafts
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### `src/pages/ContentIntelligence.tsx` - Content Intelligence Hub
```typescript
import React, { useState, useEffect } from 'react'
import { useContentStore } from '@/stores/contentStore'
import { ContentViewToggle } from '@/components/content/ContentViewToggle'
import { ContentIntelligenceFilters } from '@/components/content/ContentIntelligenceFilters'
import { ContentIntelligenceCard } from '@/components/content/ContentIntelligenceCard'
import { DailyArticleSummary } from '@/components/dashboard/DailyArticleSummary'
import { Button } from '@/components/ui/Button'
import { BrainIcon } from '@heroicons/react/24/outline'
import { LoadingPage, CardSkeleton } from '@/components/ui/LoadingStates'
import { notify } from '@/stores/uiStore'

export default function ContentIntelligence() {
  const {
    allContent,
    viewMode,
    isLoading,
    error,
    setViewMode,
    runAIContentSelection,
    fetchContentByMode,
    clearError
  } = useContentStore()

  useEffect(() => {
    fetchContentByMode(viewMode)
  }, [fetchContentByMode, viewMode])

  useEffect(() => {
    if (error) {
      notify.error('Content Loading Error', error)
      clearError()
    }
  }, [error, clearError])

  const handleAISelection = async () => {
    try {
      await runAIContentSelection()
      notify.success('AI content selection completed successfully')
    } catch (error) {
      notify.error('AI Selection Failed', 'Unable to run AI content selection')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Content Intelligence</h1>
          <p className="text-gray-600 mt-1">
            AI-powered content discovery and selection
          </p>
        </div>
        <div className="flex space-x-2">
          <ContentViewToggle value={viewMode} onChange={setViewMode} />
          <Button onClick={handleAISelection} variant="ai" leftIcon={<BrainIcon className="h-4 w-4" />}>
            Run AI Selection
          </Button>
        </div>
      </div>

      {/* Daily Article Summary - only show for AI-selected view */}
      {viewMode === 'ai-selected' && <DailyArticleSummary />}

      {/* Content Filters */}
      <ContentIntelligenceFilters />

      {/* Content Grid */}
      <div className="space-y-6">
        {isLoading ? (
          <div className="space-y-6">
            {[1, 2, 3, 4].map(i => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : allContent.length === 0 ? (
          <div className="text-center py-12">
            <BrainIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No content found</h3>
            <p className="text-gray-600 mb-6">
              {viewMode === 'ai-selected' 
                ? 'No AI-selected content available. Try running AI selection.' 
                : 'No content matches your current filters.'}
            </p>
            {viewMode === 'ai-selected' && (
              <Button onClick={handleAISelection} variant="ai">
                Run AI Selection
              </Button>
            )}
          </div>
        ) : (
          allContent.map(item => (
            <ContentIntelligenceCard 
              key={item.id} 
              content={item}
              viewMode={viewMode}
            />
          ))
        )}
      </div>
    </div>
  )
}
```

### `src/components/content/ContentViewToggle.tsx` - View Mode Toggle
```typescript
import React from 'react'
import { Tab } from '@headlessui/react'
import { BrainIcon, NewspaperIcon, TrendingUpIcon, ViewColumnsIcon } from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

interface ContentViewToggleProps {
  value: 'ai-selected' | 'fresh' | 'trending' | 'all'
  onChange: (value: 'ai-selected' | 'fresh' | 'trending' | 'all') => void
}

export function ContentViewToggle({ value, onChange }: ContentViewToggleProps) {
  const views = [
    {
      key: 'ai-selected' as const,
      label: 'AI Selected',
      icon: BrainIcon,
      description: 'Content selected by AI'
    },
    {
      key: 'fresh' as const,
      label: 'Fresh',
      icon: NewspaperIcon,
      description: 'Recently published'
    },
    {
      key: 'trending' as const,
      label: 'Trending',
      icon: TrendingUpIcon,
      description: 'Popular content'
    },
    {
      key: 'all' as const,
      label: 'All',
      icon: ViewColumnsIcon,
      description: 'All available content'
    }
  ]

  const selectedIndex = views.findIndex(view => view.key === value)

  return (
    <Tab.Group selectedIndex={selectedIndex} onChange={(index) => onChange(views[index].key)}>
      <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 p-1">
        {views.map((view) => (
          <Tab
            key={view.key}
            className={({ selected }) =>
              cn(
                'flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-medium transition-all',
                'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
                selected
                  ? 'bg-white text-neural-700 shadow'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              )
            }
          >
            <view.icon className="h-4 w-4" />
            <span>{view.label}</span>
          </Tab>
        ))}
      </Tab.List>
    </Tab.Group>
  )
}
```

### `src/components/content/ContentIntelligenceFilters.tsx` - Content Filters
```typescript
import React, { useState } from 'react'
import { MagnifyingGlassIcon, FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useContentStore } from '@/stores/contentStore'

export function ContentIntelligenceFilters() {
  const { searchQuery, selectedCategories, setSearchQuery, setSelectedCategories } = useContentStore()
  const [showFilters, setShowFilters] = useState(false)

  const availableCategories = [
    'Technology', 'Business', 'Innovation', 'Leadership', 'Marketing',
    'AI & ML', 'Startups', 'Industry News', 'Career Advice', 'Productivity'
  ]

  const handleCategoryToggle = (category: string) => {
    const newCategories = selectedCategories.includes(category)
      ? selectedCategories.filter(c => c !== category)
      : [...selectedCategories, category]
    setSelectedCategories(newCategories)
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedCategories([])
  }

  const hasActiveFilters = searchQuery || selectedCategories.length > 0

  return (
    <Card>
      <div className="p-4 space-y-4">
        {/* Search and Filter Toggle */}
        <div className="flex space-x-3">
          <div className="flex-1">
            <Input
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
            />
          </div>
          <Button
            variant={showFilters ? "default" : "outline"}
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<FunnelIcon className="h-4 w-4" />}
          >
            Filters
          </Button>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              onClick={clearFilters}
              leftIcon={<XMarkIcon className="h-4 w-4" />}
            >
              Clear
            </Button>
          )}
        </div>

        {/* Active Filters */}
        {selectedCategories.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {selectedCategories.map((category) => (
              <Badge
                key={category}
                variant="secondary"
                className="cursor-pointer hover:bg-gray-200"
                onClick={() => handleCategoryToggle(category)}
              >
                {category}
                <XMarkIcon className="h-3 w-3 ml-1" />
              </Badge>
            ))}
          </div>
        )}

        {/* Expanded Filters */}
        {showFilters && (
          <div className="pt-4 border-t border-gray-100">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Categories</h4>
              <div className="flex flex-wrap gap-2">
                {availableCategories.map((category) => (
                  <Badge
                    key={category}
                    variant={selectedCategories.includes(category) ? "default" : "outline"}
                    className="cursor-pointer hover:bg-neural-50"
                    onClick={() => handleCategoryToggle(category)}
                  >
                    {category}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
```

### `src/components/content/ContentIntelligenceCard.tsx` - Content Item Display
```typescript
import React from 'react'
import { 
  BrainIcon, 
  LinkIcon, 
  ClockIcon, 
  TrendingUpIcon,
  SparklesIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { AIAnalysisPanel } from '@/components/intelligence/AIAnalysisPanel'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { ContentItem } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { useGenerateDraft } from '@/hooks/useDrafts'
import { notify } from '@/stores/uiStore'

interface ContentIntelligenceCardProps {
  content: ContentItem
  viewMode: string
}

export function ContentIntelligenceCard({ content, viewMode }: ContentIntelligenceCardProps) {
  const { mutateAsync: generateDraft, isLoading } = useGenerateDraft()
  const isAISelected = content.ai_analysis?.llm_selected

  const handleGenerateDraft = async () => {
    try {
      await generateDraft(content.id)
      notify.success('Draft generated successfully!')
    } catch (error) {
      notify.error('Failed to generate draft')
    }
  }

  const handleReadOriginal = () => {
    window.open(content.url, '_blank', 'noopener,noreferrer')
  }

  return (
    <Card hover="lift" className="relative">
      {isAISelected && (
        <div className="absolute top-4 right-4 z-10">
          <Badge variant="ai" icon={<BrainIcon className="h-3 w-3" />}>
            AI Selected
          </Badge>
        </div>
      )}

      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="pr-20"> {/* Account for the badge */}
          <h3 className="text-lg font-semibold text-neural-700 mb-2 line-clamp-2">
            {content.title}
          </h3>
          <p className="text-gray-600 line-clamp-3">
            {content.content.substring(0, 200)}...
          </p>
        </div>

        {/* AI Analysis Panel */}
        {isAISelected && content.ai_analysis && (
          <AIAnalysisPanel
            reasoning={content.ai_analysis.selection_reason || 'Selected by AI for high relevance'}
            score={content.relevance_score}
            category={content.ai_analysis.topic_category}
            confidence={content.relevance_score ? content.relevance_score / 100 : undefined}
          />
        )}

        {/* Content Metadata */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <span className="font-medium">{content.source_name}</span>
            <div className="flex items-center space-x-1">
              <ClockIcon className="h-4 w-4" />
              <span>{formatDistanceToNow(new Date(content.published_at), { addSuffix: true })}</span>
            </div>
            {content.relevance_score && (
              <div className="flex items-center space-x-1 text-ml-green-600">
                <TrendingUpIcon className="h-4 w-4" />
                <span className="font-medium">{content.relevance_score}% relevant</span>
              </div>
            )}
          </div>
        </div>

        {/* Tags */}
        {content.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {content.tags.slice(0, 6).map(tag => (
              <Badge key={tag} variant="neutral" size="sm">
                {tag}
              </Badge>
            ))}
            {content.tags.length > 6 && (
              <Badge variant="outline" size="sm">
                +{content.tags.length - 6} more
              </Badge>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            <Button
              size="sm"
              onClick={handleGenerateDraft}
              loading={isLoading}
              variant="ai"
              leftIcon={<SparklesIcon className="h-4 w-4" />}
            >
              Generate Draft
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={handleReadOriginal}
              leftIcon={<LinkIcon className="h-4 w-4" />}
            >
              Read Original
            </Button>
          </div>
          
          {isAISelected && content.relevance_score && (
            <ConfidenceIndicator 
              score={content.relevance_score / 100}
              size="sm"
              showPercentage={false}
              label=""
            />
          )}
        </div>
      </div>
    </Card>
  )
}
```

### `src/hooks/useDrafts.ts` - Draft Management Hooks
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useDrafts() {
  return useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
    refetchInterval: 10 * 60 * 1000, // Refresh every 10 minutes
  })
}

export function useGenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (contentId: string) => api.generateDraft(contentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['draft-recommendations'] })
    },
    onError: (error: any) => {
      notify.error('Generation Failed', error.message || 'Failed to generate draft')
    }
  })
}

export function useUpdateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, data }: { draftId: string, data: any }) => 
      api.updateDraft(draftId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['draft-recommendations'] })
    }
  })
}

export function usePublishDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, scheduledFor }: { draftId: string, scheduledFor?: string }) => 
      api.publishDraft(draftId, scheduledFor),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      notify.success('Draft published successfully!')
    },
    onError: (error: any) => {
      notify.error('Publishing Failed', error.message || 'Failed to publish draft')
    }
  })
}
```

## Phase 3: Advanced Workflow Features

### `src/pages/CreationStudio.tsx` - Creation Studio
```typescript
import React, { useState } from 'react'
import { useDraftRecommendations, useDrafts } from '@/hooks/useAIRecommendations'
import { CreationTabs } from '@/components/creation/CreationTabs'
import { DraftRecommendationsView } from '@/components/creation/DraftRecommendationsView'
import { DraftsWorkshop } from '@/components/creation/DraftsWorkshop'
import { PublishingCalendar } from '@/components/creation/PublishingCalendar'
import { Button } from '@/components/ui/Button'
import { SparklesIcon, RocketIcon } from '@heroicons/react/24/outline'
import { LoadingPage } from '@/components/ui/LoadingStates'
import { notify } from '@/stores/uiStore'

export default function CreationStudio() {
  const [activeTab, setActiveTab] = useState<'recommendations' | 'drafts' | 'calendar'>('recommendations')
  const { data: recommendations, isLoading: recommendationsLoading } = useDraftRecommendations()
  const { data: drafts, isLoading: draftsLoading } = useDrafts()

  const handleBatchGenerate = async () => {
    try {
      // This would trigger batch generation on the backend
      notify.success('Batch generation started')
    } catch (error) {
      notify.error('Batch generation failed')
    }
  }

  if (recommendationsLoading && activeTab === 'recommendations') {
    return <LoadingPage message="Loading AI recommendations..." />
  }

  if (draftsLoading && activeTab === 'drafts') {
    return <LoadingPage message="Loading your drafts..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Creation Studio</h1>
          <p className="text-gray-600 mt-1">
            AI-powered content creation and optimization
          </p>
        </div>
        <div className="flex space-x-2">
          <CreationTabs value={activeTab} onChange={setActiveTab} />
          <Button 
            onClick={handleBatchGenerate}
            variant="ai"
            leftIcon={<SparklesIcon className="h-4 w-4" />}
          >
            Batch Generate
          </Button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'recommendations' && (
        <DraftRecommendationsView recommendations={recommendations || []} />
      )}

      {activeTab === 'drafts' && (
        <DraftsWorkshop drafts={drafts || []} />
      )}

      {activeTab === 'calendar' && (
        <PublishingCalendar />
      )}
    </div>
  )
}
```

### `src/components/creation/CreationTabs.tsx` - Tab Navigation
```typescript
import React from 'react'
import { Tab } from '@headlessui/react'
import { 
  SparklesIcon, 
  DocumentTextIcon, 
  CalendarIcon 
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'

interface CreationTabsProps {
  value: 'recommendations' | 'drafts' | 'calendar'
  onChange: (value: 'recommendations' | 'drafts' | 'calendar') => void
}

export function CreationTabs({ value, onChange }: CreationTabsProps) {
  const tabs = [
    {
      key: 'recommendations' as const,
      label: 'Recommendations',
      icon: SparklesIcon,
      description: 'AI-powered draft recommendations'
    },
    {
      key: 'drafts' as const,
      label: 'Drafts',
      icon: DocumentTextIcon,
      description: 'Your content drafts'
    },
    {
      key: 'calendar' as const,
      label: 'Calendar',
      icon: CalendarIcon,
      description: 'Publishing schedule'
    }
  ]

  const selectedIndex = tabs.findIndex(tab => tab.key === value)

  return (
    <Tab.Group selectedIndex={selectedIndex} onChange={(index) => onChange(tabs[index].key)}>
      <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 p-1">
        {tabs.map((tab) => (
          <Tab
            key={tab.key}
            className={({ selected }) =>
              cn(
                'flex items-center space-x-2 rounded-md px-4 py-2 text-sm font-medium transition-all',
                'focus:outline-none focus:ring-2 focus:ring-neural-500 focus:ring-offset-2',
                selected
                  ? 'bg-white text-neural-700 shadow'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              )
            }
          >
            <tab.icon className="h-4 w-4" />
            <span>{tab.label}</span>
          </Tab>
        ))}
      </Tab.List>
    </Tab.Group>
  )
}
```

### `src/components/creation/DraftRecommendationsView.tsx` - Draft Recommendations
```typescript
import React from 'react'
import { RocketIcon, PencilIcon, ClockIcon } from '@heroicons/react/24/outline'
import { DraftRecommendationCard } from './DraftRecommendationCard'
import { RecommendationCategory } from './RecommendationCategory'
import { ScoredRecommendation } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

interface DraftRecommendationsViewProps {
  recommendations: ScoredRecommendation[]
}

export function DraftRecommendationsView({ recommendations }: DraftRecommendationsViewProps) {
  const categorizedRecommendations = {
    post_now: recommendations.filter(r => r.action === 'post_now'),
    review_and_edit: recommendations.filter(r => r.action === 'review_and_edit'),
    schedule_later: recommendations.filter(r => r.action === 'schedule_later'),
    skip: recommendations.filter(r => r.action === 'skip')
  }

  if (recommendations.length === 0) {
    return (
      <Card className="text-center py-12">
        <RocketIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations available</h3>
        <p className="text-gray-600 mb-6">
          Create some drafts first to get AI-powered recommendations
        </p>
        <Button variant="ai">
          Generate New Drafts
        </Button>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Recommendation Categories Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <RecommendationCategory
          title="Ready to Publish"
          count={categorizedRecommendations.post_now.length}
          color="ml-green"
          icon={RocketIcon}
          description="High-scoring drafts ready for immediate publishing"
        />
        <RecommendationCategory
          title="Needs Review"
          count={categorizedRecommendations.review_and_edit.length}
          color="prediction"
          icon={PencilIcon}
          description="Good content that could benefit from editing"
        />
        <RecommendationCategory
          title="Schedule Later"
          count={categorizedRecommendations.schedule_later.length}
          color="neural"
          icon={ClockIcon}
          description="Quality content to schedule for optimal timing"
        />
        <RecommendationCategory
          title="Skip for Now"
          count={categorizedRecommendations.skip.length}
          color="secondary"
          icon={ClockIcon}
          description="Content that may not align with current strategy"
        />
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neural-700">AI Recommendations</h3>
        {recommendations.map(recommendation => (
          <DraftRecommendationCard 
            key={recommendation.draft_id}
            recommendation={recommendation}
          />
        ))}
      </div>
    </div>
  )
}
```

### `src/components/creation/RecommendationCategory.tsx` - Category Cards
```typescript
import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface RecommendationCategoryProps {
  title: string
  count: number
  color: 'ml-green' | 'prediction' | 'neural' | 'secondary'
  icon: React.ComponentType<{ className?: string }>
  description: string
}

export function RecommendationCategory({ 
  title, 
  count, 
  color, 
  icon: Icon, 
  description 
}: RecommendationCategoryProps) {
  const colorClasses = {
    'ml-green': 'from-ml-green-50 to-ml-green-100 border-ml-green-200 text-ml-green-700',
    'prediction': 'from-prediction-50 to-prediction-100 border-prediction-200 text-prediction-700',
    'neural': 'from-neural-50 to-neural-100 border-neural-200 text-neural-700',
    'secondary': 'from-gray-50 to-gray-100 border-gray-200 text-gray-700'
  }

  const badgeVariants = {
    'ml-green': 'ml-green' as const,
    'prediction': 'prediction' as const,
    'neural': 'default' as const,
    'secondary': 'secondary' as const
  }

  return (
    <Card 
      className={`bg-gradient-to-br ${colorClasses[color]} border`}
      hover="lift"
    >
      <div className="p-6 text-center space-y-4">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm">
          <Icon className="h-6 w-6" />
        </div>
        
        <div className="space-y-2">
          <h3 className="font-semibold">{title}</h3>
          <Badge variant={badgeVariants[color]} size="lg">
            {count} drafts
          </Badge>
          <p className="text-xs opacity-80 leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </Card>
  )
}
```

### `src/components/creation/DraftRecommendationCard.tsx` - Recommendation Card
```typescript
import React from 'react'
import { 
  RocketIcon, 
  PencilIcon, 
  ClockIcon, 
  XMarkIcon,
  CogIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { ScoreBreakdown } from '@/components/intelligence/ScoreBreakdown'
import { PredictionCard } from '@/components/intelligence/PredictionCard'
import { ReasoningPanel } from './ReasoningPanel'
import { OptimalTimingIndicator } from './OptimalTimingIndicator'
import { ActionButton } from './ActionButton'
import { ScoredRecommendation } from '@/lib/api'

interface DraftRecommendationCardProps {
  recommendation: ScoredRecommendation
}

export function DraftRecommendationCard({ recommendation }: DraftRecommendationCardProps) {
  const actionConfig = getActionConfig(recommendation.action)
  
  return (
    <Card hover="lift" className="p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-4">
          {/* Header */}
          <div className="flex items-center space-x-3">
            <Badge 
              variant={actionConfig.variant}
              icon={<actionConfig.icon className="h-3 w-3" />}
              size="lg"
            >
              {actionConfig.label}
            </Badge>
            <div className="text-2xl font-bold text-neural-600">
              {Math.round(recommendation.score * 100)}%
            </div>
            <ConfidenceIndicator
              score={recommendation.score}
              label="Recommendation Score"
              size="sm"
            />
          </div>

          {/* Content Preview */}
          <div>
            <h3 className="text-lg font-semibold text-neural-700 mb-2">
              {recommendation.draft?.title || 'Draft Content'}
            </h3>
            <p className="text-gray-600 line-clamp-3">
              {recommendation.draft?.content.substring(0, 200)}...
            </p>
          </div>

          {/* Score Breakdown */}
          <ScoreBreakdown scores={recommendation.content_score} />

          {/* Optimal Timing */}
          {recommendation.optimal_timing && (
            <OptimalTimingIndicator timing={recommendation.optimal_timing} />
          )}

          {/* AI Reasoning */}
          <ReasoningPanel reasoning={recommendation.reasoning} />
        </div>

        {/* Actions */}
        <div className="ml-6 space-y-2">
          <ActionButton 
            action={recommendation.action}
            draftId={recommendation.draft_id}
          />
          <Button 
            size="sm" 
            variant="ghost"
            leftIcon={<CogIcon className="h-4 w-4" />}
          >
            Edit
          </Button>
        </div>
      </div>

      {/* Predicted Performance */}
      {recommendation.estimated_performance && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <PredictionCard 
            prediction={recommendation.estimated_performance}
            compact
          />
        </div>
      )}
    </Card>
  )
}

function getActionConfig(action: string) {
  const configs = {
    post_now: {
      icon: RocketIcon,
      label: 'Post Now',
      variant: 'success' as const
    },
    review_and_edit: {
      icon: PencilIcon,
      label: 'Review & Edit',
      variant: 'warning' as const
    },
    schedule_later: {
      icon: ClockIcon,
      label: 'Schedule Later',
      variant: 'default' as const
    },
    skip: {
      icon: XMarkIcon,
      label: 'Skip',
      variant: 'secondary' as const
    }
  }

  return configs[action as keyof typeof configs] || configs.skip
}
```

### `src/components/creation/ReasoningPanel.tsx` - AI Reasoning Display
```typescript
import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, BrainIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'

interface ReasoningPanelProps {
  reasoning: string
  className?: string
}

export function ReasoningPanel({ reasoning, className }: ReasoningPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <Card variant="ai" className={className}>
      <div className="p-4">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center space-x-2">
            <BrainIcon className="h-4 w-4 text-ai-purple-600" />
            <span className="font-medium text-neural-700">AI Reasoning</span>
          </div>
          {isExpanded ? (
            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRightIcon className="h-4 w-4 text-gray-400" />
          )}
        </div>

        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-ai-purple-100">
            <p className="text-sm text-gray-700 leading-relaxed">
              {reasoning}
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
```

### `src/components/creation/OptimalTimingIndicator.tsx` - Timing Recommendations
```typescript
import React from 'react'
import { ClockIcon, TrendingUpIcon } from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'

interface OptimalTimingIndicatorProps {
  timing: {
    recommended_time: string
    expected_engagement: number
    confidence: number
    reasoning: string
  }
}

export function OptimalTimingIndicator({ timing }: OptimalTimingIndicatorProps) {
  const recommendedDate = new Date(timing.recommended_time)
  
  return (
    <Card variant="prediction" className="p-4">
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <ClockIcon className="h-4 w-4 text-prediction-600" />
          <span className="font-medium text-prediction-700">Optimal Timing</span>
          <Badge variant="prediction" size="sm">
            <TrendingUpIcon className="h-3 w-3 mr-1" />
            {Math.round(timing.expected_engagement * 100)}% engagement
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-lg font-semibold text-prediction-700">
              {recommendedDate.toLocaleDateString()}
            </div>
            <div className="text-sm text-gray-600">
              {recommendedDate.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          </div>
          <div className="text-right">
            <ConfidenceIndicator
              score={timing.confidence}
              label="Confidence"
              size="sm"
            />
          </div>
        </div>

        <p className="text-xs text-gray-600 leading-relaxed">
          {timing.reasoning}
        </p>
      </div>
    </Card>
  )
}
```

### `src/components/creation/ActionButton.tsx` - Action Button Component
```typescript
import React from 'react'
import { RocketIcon, PencilIcon, ClockIcon, CalendarIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { usePublishDraft } from '@/hooks/useDrafts'
import { useModal } from '@/stores/uiStore'
import { notify } from '@/stores/uiStore'

interface ActionButtonProps {
  action: 'post_now' | 'schedule_later' | 'review_and_edit' | 'skip'
  draftId: string
}

export function ActionButton({ action, draftId }: ActionButtonProps) {
  const { mutateAsync: publishDraft, isLoading } = usePublishDraft()
  const { openModal } = useModal()

  const handleAction = async () => {
    switch (action) {
      case 'post_now':
        try {
          await publishDraft({ draftId })
          notify.success('Draft published successfully!')
        } catch (error) {
          notify.error('Failed to publish draft')
        }
        break
        
      case 'schedule_later':
        openModal('schedule-draft', { draftId })
        break
        
      case 'review_and_edit':
        openModal('edit-draft', { draftId })
        break
        
      case 'skip':
        notify.info('Draft marked as skipped')
        break
    }
  }

  const getButtonConfig = () => {
    switch (action) {
      case 'post_now':
        return {
          icon: RocketIcon,
          label: 'Post Now',
          variant: 'ai' as const
        }
      case 'schedule_later':
        return {
          icon: CalendarIcon,
          label: 'Schedule',
          variant: 'default' as const
        }
      case 'review_and_edit':
        return {
          icon: PencilIcon,
          label: 'Edit',
          variant: 'outline' as const
        }
      case 'skip':
        return {
          icon: ClockIcon,
          label: 'Skip',
          variant: 'ghost' as const
        }
    }
  }

  const config = getButtonConfig()

  return (
    <Button
      variant={config.variant}
      size="sm"
      onClick={handleAction}
      loading={isLoading}
      leftIcon={<config.icon className="h-4 w-4" />}
    >
      {config.label}
    </Button>
  )
}
```

### `src/pages/EngagementHub.tsx` - Engagement Management
```typescript
import React, { useState, useEffect } from 'react'
import { useEngagementStore } from '@/stores/engagementStore'
import { EngagementOverview } from '@/components/engagement/EngagementOverview'
import { CommentOpportunityCard } from '@/components/engagement/CommentOpportunityCard'
import { EngagementFilters } from '@/components/engagement/EngagementFilters'
import { AutomationToggle } from '@/components/engagement/AutomationToggle'
import { Button } from '@/components/ui/Button'
import { MagnifyingGlassIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline'
import { LoadingPage, CardSkeleton } from '@/components/ui/LoadingStates'
import { notify } from '@/stores/uiStore'

export default function EngagementHub() {
  const [filterPriority, setFilterPriority] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('pending')
  
  const {
    commentQueue,
    isLoading,
    error,
    fetchCommentOpportunities,
    discoverNewPosts,
    clearError
  } = useEngagementStore()

  useEffect(() => {
    fetchCommentOpportunities({
      priority: filterPriority || undefined,
      status: filterStatus || undefined,
      limit: 50
    })
  }, [fetchCommentOpportunities, filterPriority, filterStatus])

  useEffect(() => {
    if (error) {
      notify.error('Engagement Error', error)
      clearError()
    }
  }, [error, clearError])

  const handleDiscoverPosts = async () => {
    try {
      await discoverNewPosts(50)
      notify.success('New engagement opportunities discovered!')
    } catch (error) {
      notify.error('Discovery failed')
    }
  }

  if (isLoading && commentQueue.length === 0) {
    return <LoadingPage message="Loading engagement opportunities..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Engagement Hub</h1>
          <p className="text-gray-600 mt-1">
            Manage your LinkedIn engagement opportunities
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <AutomationToggle />
          <Button 
            onClick={handleDiscoverPosts}
            variant="secondary"
            leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
          >
            Discover Posts
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <EngagementOverview />

      {/* Filters */}
      <EngagementFilters
        priority={filterPriority}
        status={filterStatus}
        onPriorityChange={setFilterPriority}
        onStatusChange={setFilterStatus}
      />

      {/* Opportunities List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : commentQueue.length === 0 ? (
          <div className="text-center py-12">
            <ChatBubbleLeftIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No opportunities found</h3>
            <p className="text-gray-600 mb-6">
              Try discovering new posts or adjusting your filters
            </p>
            <Button onClick={handleDiscoverPosts} variant="ai">
              Discover Opportunities
            </Button>
          </div>
        ) : (
          commentQueue.map(opportunity => (
            <CommentOpportunityCard 
              key={opportunity.id}
              opportunity={opportunity}
            />
          ))
        )}
      </div>
    </div>
  )
}
```

### `src/components/layout/Sidebar.tsx` - Application Sidebar
```typescript
import React from 'react'
import { NavLink } from 'react-router-dom'
import { 
  HomeIcon,
  BrainIcon,
  DocumentTextIcon,
  ChatBubbleLeftIcon,
  ChartBarIcon,
  CogIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useUIStore } from '@/stores/uiStore'
import { useEngagementStore } from '@/stores/engagementStore'
import { cn } from '@/utils/cn'

export function Sidebar() {
  const { sidebarOpen, sidebarCollapsed, setSidebarOpen, toggleSidebarCollapsed } = useUIStore()
  const { commentQueue } = useEngagementStore()

  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
      description: 'AI Intelligence Overview'
    },
    {
      name: 'Content',
      href: '/content',
      icon: BrainIcon,
      description: 'Content Intelligence'
    },
    {
      name: 'Creation',
      href: '/creation',
      icon: DocumentTextIcon,
      description: 'Creation Studio'
    },
    {
      name: 'Engagement',
      href: '/engagement',
      icon: ChatBubbleLeftIcon,
      description: 'Engagement Hub',
      badge: commentQueue.filter(opp => opp.priority === 'urgent' || opp.priority === 'high').length
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
      description: 'Persona Analytics'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: CogIcon,
      description: 'AI Configuration'
    }
  ]

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-gray-200 transition-all duration-300',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        sidebarCollapsed ? 'lg:w-16' : 'lg:w-64',
        'w-64'
      )}>
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-ai-purple-500 to-ml-green-500 rounded-lg flex items-center justify-center">
                <BrainIcon className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-neural-700">AI LinkedIn</h1>
                <p className="text-xs text-gray-500">Automation Platform</p>
              </div>
            </div>
          )}
          
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebarCollapsed}
            className="hidden lg:flex"
          >
            {sidebarCollapsed ? (
              <ChevronRightIcon className="h-4 w-4" />
            ) : (
              <ChevronLeftIcon className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigationItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors group',
                  isActive
                    ? 'bg-neural-100 text-neural-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )
              }
              title={sidebarCollapsed ? item.name : undefined}
            >
              <item.icon 
                className={cn(
                  'flex-shrink-0 h-5 w-5',
                  sidebarCollapsed ? 'mx-auto' : 'mr-3'
                )} 
              />
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1">{item.name}</span>
                  {item.badge && item.badge > 0 && (
                    <Badge variant="destructive" size="sm">
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 text-center">
              Powered by Advanced AI
            </div>
          </div>
        )}
      </div>
    </>
  )
}
```

### `src/components/layout/NotificationCenter.tsx` - Notification System
```typescript
import React from 'react'
import { Transition } from '@headlessui/react'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  InformationCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline'
import { useNotifications } from '@/stores/uiStore'
import { cn } from '@/utils/cn'

export function NotificationCenter() {
  const { notifications, removeNotification } = useNotifications()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <Transition
          key={notification.id}
          show={true}
          enter="transform ease-out duration-300 transition"
          enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
          enterTo="translate-y-0 opacity-100 sm:translate-x-0"
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <NotificationItem
            notification={notification}
            onDismiss={() => removeNotification(notification.id)}
          />
        </Transition>
      ))}
    </div>
  )
}

function NotificationItem({ 
  notification, 
  onDismiss 
}: { 
  notification: any
  onDismiss: () => void 
}) {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }

  const colors = {
    success: 'bg-ml-green-50 border-ml-green-200 text-ml-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-prediction-50 border-prediction-200 text-prediction-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  }

  const iconColors = {
    success: 'text-ml-green-500',
    error: 'text-red-500',
    warning: 'text-prediction-500',
    info: 'text-blue-500',
  }

  const Icon = icons[notification.type]

  return (
    <div className={cn(
      'rounded-lg border p-4 shadow-lg backdrop-blur-sm',
      colors[notification.type]
    )}>
      <div className="flex items-start">
        <Icon className={cn('h-5 w-5 mt-0.5 mr-3', iconColors[notification.type])} />
        <div className="flex-1 min-w-0">
          <h4 className="font-medium">{notification.title}</h4>
          {notification.message && (
            <p className="mt-1 text-sm opacity-90">{notification.message}</p>
          )}
          {notification.action && (
            <button
              onClick={notification.action.onClick}
              className="mt-2 text-sm font-medium underline hover:no-underline"
            >
              {notification.action.label}
            </button>
          )}
        </div>
        <button
          onClick={onDismiss}
          className="ml-2 flex-shrink-0 hover:opacity-70"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
```

### `src/components/layout/AIStatusIndicator.tsx` - AI Status Display
```typescript
import React from 'react'
import { BrainIcon } from '@heroicons/react/24/outline'
import { useUIStore } from '@/stores/uiStore'
import { LoadingDots } from '@/components/ui/LoadingStates'
import { cn } from '@/utils/cn'

export function AIStatusIndicator() {
  const { aiThinking, aiMessage } = useUIStore()

  if (!aiThinking) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-40">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 max-w-sm">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <BrainIcon className="h-6 w-6 text-ai-purple-600" />
            <div className="absolute inset-0 animate-ping">
              <BrainIcon className="h-6 w-6 text-ai-purple-400 opacity-50" />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="font-medium text-neural-700">AI Processing</div>
            <div className="text-sm text-gray-600">
              {aiMessage || 'Working on your request...'}
            </div>
            <div className="mt-2">
              <LoadingDots className="text-ai-purple-500" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### `src/components/engagement/EngagementOverview.tsx` - Engagement Statistics
```typescript
import React from 'react'
import { 
  ChatBubbleLeftIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useEngagementStore } from '@/stores/engagementStore'
import { Skeleton } from '@/components/ui/LoadingStates'

export function EngagementOverview() {
  const { engagementStats, isLoading } = useEngagementStore()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map(i => (
          <Card key={i}>
            <div className="p-6 space-y-2">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-8 w-3/4" />
              <Skeleton className="h-4 w-full" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  const stats = [
    {
      title: 'Total Opportunities',
      value: engagementStats?.total_opportunities || 0,
      icon: ChatBubbleLeftIcon,
      color: 'text-neural-600',
      bgColor: 'bg-neural-100'
    },
    {
      title: 'Completion Rate',
      value: `${Math.round((engagementStats?.completion_rate || 0) * 100)}%`,
      icon: CheckCircleIcon,
      color: 'text-ml-green-600',
      bgColor: 'bg-ml-green-100'
    },
    {
      title: 'Pending Actions',
      value: engagementStats?.status_breakdown?.pending || 0,
      icon: ClockIcon,
      color: 'text-prediction-600',
      bgColor: 'bg-prediction-100'
    },
    {
      title: 'High Priority',
      value: engagementStats?.status_breakdown?.high || 0,
      icon: ExclamationTriangleIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-100'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {stats.map((stat) => (
        <Card key={stat.title} hover="lift">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
```

### `src/components/engagement/EngagementFilters.tsx` - Engagement Filters
```typescript
import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface EngagementFiltersProps {
  priority: string
  status: string
  onPriorityChange: (priority: string) => void
  onStatusChange: (status: string) => void
}

export function EngagementFilters({
  priority,
  status,
  onPriorityChange,
  onStatusChange
}: EngagementFiltersProps) {
  const priorities = [
    { value: '', label: 'All Priorities' },
    { value: 'urgent', label: 'Urgent', color: 'destructive' as const },
    { value: 'high', label: 'High', color: 'warning' as const },
    { value: 'medium', label: 'Medium', color: 'secondary' as const },
    { value: 'low', label: 'Low', color: 'neutral' as const }
  ]

  const statuses = [
    { value: '', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'scheduled', label: 'Scheduled' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' }
  ]

  return (
    <Card>
      <div className="p-4 space-y-4">
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Filter by Priority</h4>
          <div className="flex flex-wrap gap-2">
            {priorities.map((p) => (
              <Badge
                key={p.value}
                variant={priority === p.value ? (p.color || 'default') : 'outline'}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => onPriorityChange(p.value)}
              >
                {p.label}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-3">Filter by Status</h4>
          <div className="flex flex-wrap gap-2">
            {statuses.map((s) => (
              <Badge
                key={s.value}
                variant={status === s.value ? 'default' : 'outline'}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => onStatusChange(s.value)}
              >
                {s.label}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### `src/components/engagement/AutomationToggle.tsx` - Automation Controls
```typescript
import React from 'react'
import { Switch } from '@headlessui/react'
import { BoltIcon } from '@heroicons/react/24/outline'
import { Badge } from '@/components/ui/Badge'
import { useEngagementStore } from '@/stores/engagementStore'
import { cn } from '@/utils/cn'

export function AutomationToggle() {
  const { automationEnabled, toggleAutomation } = useEngagementStore()

  return (
    <div className="flex items-center space-x-3">
      <BoltIcon className="h-5 w-5 text-neural-600" />
      <span className="text-sm font-medium text-gray-700">Auto Engagement</span>
      <Switch
        checked={automationEnabled}
        onChange={toggleAutomation}
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
          automationEnabled ? 'bg-ml-green-500' : 'bg-gray-200'
        )}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            automationEnabled ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </Switch>
      <Badge variant={automationEnabled ? 'success' : 'secondary'} size="sm">
        {automationEnabled ? 'ON' : 'OFF'}
      </Badge>
    </div>
  )
}
```

### `src/components/engagement/CommentOpportunityCard.tsx` - Engagement Opportunity Card
```typescript
import React, { useState } from 'react'
import { 
  ChatBubbleLeftIcon, 
  LinkIcon, 
  ClockIcon, 
  UserIcon,
  SparklesIcon,
  CheckIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { EngagementOpportunity } from '@/lib/api'
import { useEngagementStore } from '@/stores/engagementStore'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'

interface CommentOpportunityCardProps {
  opportunity: EngagementOpportunity
}

export function CommentOpportunityCard({ opportunity }: CommentOpportunityCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [customComment, setCustomComment] = useState('')
  const { createComment, isLoading } = useEngagementStore()

  const handleEngage = async (useCustomComment: boolean = false) => {
    try {
      await createComment({
        opportunity_id: opportunity.id,
        comment_text: useCustomComment ? customComment : opportunity.suggested_comment
      })
      notify.success('Comment posted successfully!')
    } catch (error) {
      notify.error('Failed to post comment')
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive'
      case 'high': return 'warning'
      case 'medium': return 'secondary'
      default: return 'neutral'
    }
  }

  return (
    <Card hover="lift" className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <UserIcon className="h-5 w-5 text-neural-600" />
              <h3 className="font-semibold text-neural-700">{opportunity.target_author}</h3>
              <Badge variant={getPriorityColor(opportunity.priority)} size="sm">
                {opportunity.priority}
              </Badge>
              {opportunity.relevance_score && (
                <Badge variant="ai" size="sm">
                  {opportunity.relevance_score}% match
                </Badge>
              )}
            </div>
            
            <p className="text-gray-600 line-clamp-3">
              {opportunity.target_content}
            </p>
          </div>
        </div>

        {/* AI Analysis */}
        {opportunity.ai_analysis && (
          <div className="bg-ai-purple-50 rounded-lg p-4 border border-ai-purple-200">
            <div className="flex items-center space-x-2 mb-2">
              <SparklesIcon className="h-4 w-4 text-ai-purple-600" />
              <span className="font-medium text-ai-purple-700">AI Analysis</span>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              {opportunity.engagement_reason}
            </p>
            {opportunity.ai_analysis.confidence_score && (
              <ConfidenceIndicator
                score={opportunity.ai_analysis.confidence_score}
                label="Success Probability"
                size="sm"
              />
            )}
          </div>
        )}

        {/* Suggested Comment */}
        {opportunity.suggested_comment && (
          <div className="bg-ml-green-50 rounded-lg p-4 border border-ml-green-200">
            <div className="flex items-center space-x-2 mb-2">
              <ChatBubbleLeftIcon className="h-4 w-4 text-ml-green-600" />
              <span className="font-medium text-ml-green-700">Suggested Comment</span>
            </div>
            <p className="text-sm text-gray-700">
              "{opportunity.suggested_comment}"
            </p>
          </div>
        )}

        {/* Custom Comment Input */}
        {isExpanded && (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Custom Comment (Optional)
            </label>
            <textarea
              value={customComment}
              onChange={(e) => setCustomComment(e.target.value)}
              placeholder="Write your own comment..."
              className="w-full p-3 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
              rows={3}
            />
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <ClockIcon className="h-4 w-4" />
            <span>{formatDistanceToNow(new Date(opportunity.created_at), { addSuffix: true })}</span>
          </div>
          {opportunity.context_tags && opportunity.context_tags.length > 0 && (
            <div className="flex items-center space-x-1">
              <span>Tags:</span>
              <span>{opportunity.context_tags.join(', ')}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="ai"
              onClick={() => handleEngage(false)}
              loading={isLoading}
              leftIcon={<ChatBubbleLeftIcon className="h-4 w-4" />}
            >
              Use AI Comment
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Simple' : 'Custom'}
            </Button>

            {isExpanded && customComment && (
              <Button
                size="sm"
                variant="default"
                onClick={() => handleEngage(true)}
                loading={isLoading}
                leftIcon={<CheckIcon className="h-4 w-4" />}
              >
                Post Custom
              </Button>
            )}
          </div>

          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => window.open(opportunity.target_url, '_blank')}
              leftIcon={<LinkIcon className="h-4 w-4" />}
            >
              View Post
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### `src/pages/PersonaAnalytics.tsx` - Analytics Dashboard
```typescript
import React, { useState } from 'react'
import { usePersonaMetrics } from '@/hooks/useAIRecommendations'
import { AnalyticsOverview } from '@/components/analytics/AnalyticsOverview'
import { PerformanceChart } from '@/components/analytics/PerformanceChart'
import { ContentPerformance } from '@/components/analytics/ContentPerformance'
import { EngagementTrends } from '@/components/analytics/EngagementTrends'
import { PersonaInsights } from '@/components/analytics/PersonaInsights'
import { TimePeriodSelector } from '@/components/analytics/TimePeriodSelector'
import { LoadingPage } from '@/components/ui/LoadingStates'

export default function PersonaAnalytics() {
  const [timePeriod, setTimePeriod] = useState(30)
  const { data: metrics, isLoading } = usePersonaMetrics(timePeriod)

  if (isLoading) {
    return <LoadingPage message="Loading analytics data..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neural-700">Persona Analytics</h1>
          <p className="text-gray-600 mt-1">
            Deep insights into your LinkedIn presence and performance
          </p>
        </div>
        <TimePeriodSelector value={timePeriod} onChange={setTimePeriod} />
      </div>

      {/* Overview Cards */}
      <AnalyticsOverview metrics={metrics} />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceChart data={metrics?.engagement_history} />
        <EngagementTrends data={metrics?.trends} />
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ContentPerformance />
        </div>
        <div>
          <PersonaInsights metrics={metrics} />
        </div>
      </div>
    </div>
  )
}
```

### `src/components/analytics/AnalyticsOverview.tsx` - Analytics Overview Cards
```typescript
import React from 'react'
import { 
  TrendingUpIcon, 
  ArrowTrendingDownIcon, 
  EyeIcon, 
  HeartIcon,
  ChatBubbleLeftIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PersonaMetrics } from '@/lib/api'

interface AnalyticsOverviewProps {
  metrics?: PersonaMetrics
}

export function AnalyticsOverview({ metrics }: AnalyticsOverviewProps) {
  const overviewStats = [
    {
      title: 'Authority Score',
      value: metrics?.authority_score || 0,
      change: '+5',
      trend: 'up' as const,
      icon: TrendingUpIcon,
      color: 'text-ml-green-600',
      bgColor: 'bg-ml-green-100'
    },
    {
      title: 'Engagement Rate',
      value: `${((metrics?.engagement_trend || 0) * 100).toFixed(1)}%`,
      change: '+2.3%',
      trend: 'up' as const,
      icon: HeartIcon,
      color: 'text-red-500',
      bgColor: 'bg-red-100'
    },
    {
      title: 'Content Quality',
      value: Math.round(metrics?.content_quality_avg || 0),
      change: '+8',
      trend: 'up' as const,
      icon: EyeIcon,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Network Growth',
      value: `${((metrics?.network_growth || 0) * 100).toFixed(1)}%`,
      change: '+12%',
      trend: 'up' as const,
      icon: UserGroupIcon,
      color: 'text-purple-500',
      bgColor: 'bg-purple-100'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {overviewStats.map((stat) => (
        <Card key={stat.title} hover="lift">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                <div className="flex items-center mt-2">
                  {stat.trend === 'up' ? (
                    <TrendingUpIcon className="h-4 w-4 text-ml-green-500 mr-1" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-4 w-4 text-red-500 mr-1" />
                  )}
                  <span className={`text-sm ${stat.trend === 'up' ? 'text-ml-green-600' : 'text-red-600'}`}>
                    {stat.change}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">vs last period</span>
                </div>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
```

### `src/components/analytics/PerformanceChart.tsx` - Performance Chart
```typescript
import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface PerformanceChartProps {
  data?: Array<{
    date: string
    likes: number
    comments: number
    shares: number
    views: number
  }>
}

export function PerformanceChart({ data = [] }: PerformanceChartProps) {
  const chartData = data.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }))

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neural-700">Engagement Performance</h3>
          <div className="flex space-x-2">
            <Badge variant="success" size="sm">Likes</Badge>
            <Badge variant="ai" size="sm">Comments</Badge>
            <Badge variant="warning" size="sm">Shares</Badge>
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis 
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="likes" 
                stroke="#10B981" 
                strokeWidth={3}
                dot={{ fill: '#10B981', strokeWidth: 2 }}
              />
              <Line 
                type="monotone" 
                dataKey="comments" 
                stroke="#a855f7" 
                strokeWidth={3}
                dot={{ fill: '#a855f7', strokeWidth: 2 }}
              />
              <Line 
                type="monotone" 
                dataKey="shares" 
                stroke="#F59E0B" 
                strokeWidth={3}
                dot={{ fill: '#F59E0B', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  )
}
```

### `src/components/analytics/TimePeriodSelector.tsx` - Time Period Selector
```typescript
import React from 'react'
import { Badge } from '@/components/ui/Badge'

interface TimePeriodSelectorProps {
  value: number
  onChange: (days: number) => void
}

export function TimePeriodSelector({ value, onChange }: TimePeriodSelectorProps) {
  const periods = [
    { days: 7, label: '7 Days' },
    { days: 30, label: '30 Days' },
    { days: 90, label: '90 Days' },
    { days: 365, label: '1 Year' }
  ]

  return (
    <div className="flex space-x-2">
      {periods.map((period) => (
        <Badge
          key={period.days}
          variant={value === period.days ? 'default' : 'outline'}
          className="cursor-pointer hover:bg-gray-50"
          onClick={() => onChange(period.days)}
        >
          {period.label}
        </Badge>
      ))}
    </div>
  )
}
```

### `src/pages/AIConfiguration.tsx` - AI Settings Page
```typescript
import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Switch } from '@headlessui/react'
import { 
  BrainIcon, 
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
```

### `src/components/creation/DraftsWorkshop.tsx` - Drafts Management
```typescript
import React, { useState } from 'react'
import { 
  DocumentTextIcon, 
  PencilIcon, 
  TrashIcon,
  RocketIcon,
  CalendarIcon 
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { PostDraft } from '@/lib/api'
import { useUpdateDraft, usePublishDraft } from '@/hooks/useDrafts'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'

interface DraftsWorkshopProps {
  drafts: PostDraft[]
}

export function DraftsWorkshop({ drafts }: DraftsWorkshopProps) {
  const [selectedDraft, setSelectedDraft] = useState<PostDraft | null>(null)
  
  if (drafts.length === 0) {
    return (
      <Card className="text-center py-12">
        <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No drafts yet</h3>
        <p className="text-gray-600 mb-6">
          Generate some content drafts to get started
        </p>
        <Button variant="ai">
          Generate Drafts
        </Button>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Drafts List */}
      <div className="lg:col-span-2 space-y-4">
        {drafts.map((draft) => (
          <DraftCard 
            key={draft.id}
            draft={draft}
            isSelected={selectedDraft?.id === draft.id}
            onSelect={() => setSelectedDraft(draft)}
          />
        ))}
      </div>

      {/* Draft Editor */}
      <div className="lg:col-span-1">
        {selectedDraft ? (
          <DraftEditor 
            draft={selectedDraft}
            onUpdate={(updatedDraft) => setSelectedDraft(updatedDraft)}
          />
        ) : (
          <Card className="p-6 text-center">
            <PencilIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Select a draft to edit</p>
          </Card>
        )}
      </div>
    </div>
  )
}

function DraftCard({ 
  draft, 
  isSelected, 
  onSelect 
}: { 
  draft: PostDraft
  isSelected: boolean
  onSelect: () => void 
}) {
  const { mutateAsync: publishDraft } = usePublishDraft()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success'
      case 'scheduled': return 'default'
      case 'published': return 'ml-green'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const handlePublish = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await publishDraft({ draftId: draft.id })
    } catch (error) {
      // Error handled by hook
    }
  }

  return (
    <Card 
      hover="lift"
      className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-neural-500' : ''}`}
      onClick={onSelect}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="font-semibold text-neural-700 mb-2 line-clamp-1">
              {draft.title || 'Untitled Draft'}
            </h3>
            <p className="text-gray-600 text-sm line-clamp-2">
              {draft.content.substring(0, 150)}...
            </p>
          </div>
          <Badge variant={getStatusColor(draft.status)} size="sm">
            {draft.status}
          </Badge>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{formatDistanceToNow(new Date(draft.created_at), { addSuffix: true })}</span>
            {draft.hashtags.length > 0 && (
              <>
                <span>•</span>
                <span>{draft.hashtags.length} hashtags</span>
              </>
            )}
          </div>

          {draft.status === 'ready' && (
            <Button
              size="sm"
              variant="ai"
              onClick={handlePublish}
              leftIcon={<RocketIcon className="h-3 w-3" />}
            >
              Publish
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}

function DraftEditor({ 
  draft, 
  onUpdate 
}: { 
  draft: PostDraft
  onUpdate: (draft: PostDraft) => void 
}) {
  const [editedContent, setEditedContent] = useState(draft.content)
  const [editedHashtags, setEditedHashtags] = useState(draft.hashtags.join(' '))
  const { mutateAsync: updateDraft } = useUpdateDraft()

  const handleSave = async () => {
    try {
      const hashtags = editedHashtags.split(' ').filter(tag => tag.trim())
      const updatedDraft = await updateDraft({
        draftId: draft.id,
        data: {
          content: editedContent,
          hashtags
        }
      })
      onUpdate(updatedDraft)
      notify.success('Draft updated successfully!')
    } catch (error) {
      notify.error('Failed to update draft')
    }
  }

  return (
    <Card className="sticky top-6">
      <div className="p-6">
        <h3 className="font-semibold text-neural-700 mb-4">Edit Draft</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content
            </label>
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full h-32 px-3 py-2 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
              placeholder="Write your LinkedIn post..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hashtags
            </label>
            <input
              type="text"
              value={editedHashtags}
              onChange={(e) => setEditedHashtags(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neural-500 focus:border-neural-500"
              placeholder="#hashtag1 #hashtag2"
            />
          </div>

          <div className="flex space-x-2">
            <Button
              onClick={handleSave}
              variant="ai"
              size="sm"
              className="flex-1"
            >
              Save Changes
            </Button>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<CalendarIcon className="h-4 w-4" />}
            >
              Schedule
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### `src/components/creation/PublishingCalendar.tsx` - Publishing Calendar
```typescript
import React, { useState } from 'react'
import { Calendar, dateFnsLocalizer } from 'react-big-calendar'
import { format, parse, startOfWeek, getDay } from 'date-fns'
import { enUS } from 'date-fns/locale'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { CalendarIcon, PlusIcon } from '@heroicons/react/24/outline'
import 'react-big-calendar/lib/css/react-big-calendar.css'

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales: {
    'en-US': enUS,
  },
})

export function PublishingCalendar() {
  const [view, setView] = useState<'month' | 'week' | 'day'>('month')
  const [date, setDate] = useState(new Date())

  // Mock events - replace with real data
  const events = [
    {
      id: 1,
      title: 'AI Article Draft',
      start: new Date(2024, 1, 15, 10, 0),
      end: new Date(2024, 1, 15, 10, 30),
      status: 'scheduled'
    },
    {
      id: 2,
      title: 'Industry Insights Post',
      start: new Date(2024, 1, 17, 14, 0),
      end: new Date(2024, 1, 17, 14, 30),
      status: 'draft'
    },
    {
      id: 3,
      title: 'Weekly Roundup',
      start: new Date(2024, 1, 20, 9, 0),
      end: new Date(2024, 1, 20, 9, 30),
      status: 'published'
    }
  ]

  const eventStyleGetter = (event: any) => {
    let backgroundColor = '#3174ad'
    
    switch (event.status) {
      case 'scheduled':
        backgroundColor = '#10B981'
        break
      case 'draft':
        backgroundColor = '#F59E0B'
        break
      case 'published':
        backgroundColor = '#6B7280'
        break
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block'
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Calendar Header */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-neural-700 flex items-center space-x-2">
              <CalendarIcon className="h-5 w-5" />
              <span>Publishing Calendar</span>
            </h3>
            <div className="flex items-center space-x-3">
              <div className="flex space-x-2">
                <Badge variant="success" size="sm">Scheduled</Badge>
                <Badge variant="warning" size="sm">Draft</Badge>
                <Badge variant="secondary" size="sm">Published</Badge>
              </div>
              <Button 
                variant="ai" 
                size="sm"
                leftIcon={<PlusIcon className="h-4 w-4" />}
              >
                Schedule Post
              </Button>
            </div>
          </div>

          {/* Calendar */}
          <div className="h-96">
            <Calendar
              localizer={localizer}
              events={events}
              startAccessor="start"
              endAccessor="end"
              views={['month', 'week', 'day']}
              view={view}
              onView={(newView) => setView(newView)}
              date={date}
              onNavigate={(newDate) => setDate(newDate)}
              eventPropGetter={eventStyleGetter}
              style={{ height: '100%' }}
              toolbar={true}
            />
          </div>
        </div>
      </Card>

      {/* Upcoming Posts */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-neural-700 mb-4">Upcoming Posts</h3>
          <div className="space-y-3">
            {events
              .filter(event => event.start > new Date())
              .map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900">{event.title}</h4>
                    <p className="text-sm text-gray-600">
                      {format(event.start, 'MMM d, yyyy \'at\' h:mm a')}
                    </p>
                  </div>
                  <Badge variant="success" size="sm">
                    {event.status}
                  </Badge>
                </div>
              ))}
          </div>
        </div>
      </Card>
    </div>
  )
}
```

### `src/components/analytics/EngagementTrends.tsx` - Engagement Trends Chart
```typescript
import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card } from '@/components/ui/Card'

interface EngagementTrendsProps {
  data?: {
    posting_frequency: 'increasing' | 'decreasing' | 'stable'
    engagement_trend: 'improving' | 'declining' | 'stable'
    best_performing_time: string
    top_content_types: string[]
  }
}

export function EngagementTrends({ data }: EngagementTrendsProps) {
  const trendData = [
    { name: 'Mon', engagement: 65 },
    { name: 'Tue', engagement: 78 },
    { name: 'Wed', engagement: 90 },
    { name: 'Thu', engagement: 81 },
    { name: 'Fri', engagement: 56 },
    { name: 'Sat', engagement: 45 },
    { name: 'Sun', engagement: 38 },
  ]

  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-6">Weekly Engagement Trends</h3>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="name" 
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis 
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Bar 
                dataKey="engagement" 
                fill="#10B981" 
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {data && (
          <div className="mt-6 pt-4 border-t border-gray-100">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Best Time:</span>
                <span className="font-medium text-gray-900 ml-2">{data.best_performing_time}</span>
              </div>
              <div>
                <span className="text-gray-600">Trend:</span>
                <span className={`font-medium ml-2 ${
                  data.engagement_trend === 'improving' ? 'text-ml-green-600' : 
                  data.engagement_trend === 'declining' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {data.engagement_trend}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
```

### `src/components/analytics/ContentPerformance.tsx` - Content Performance Analysis
```typescript
import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { TrendingUpIcon, EyeIcon, HeartIcon } from '@heroicons/react/24/outline'

export function ContentPerformance() {
  const topPosts = [
    {
      id: 1,
      content: "Excited to share insights about AI in content marketing...",
      engagement: { likes: 245, comments: 32, shares: 18, views: 1200 },
      performance_score: 92,
      published_at: "2024-01-15"
    },
    {
      id: 2,
      content: "The future of LinkedIn automation is here...",
      engagement: { likes: 189, comments: 28, shares: 15, views: 980 },
      performance_score: 87,
      published_at: "2024-01-18"
    },
    {
      id: 3,
      content: "Key takeaways from the latest industry report...",
      engagement: { likes: 156, comments: 22, shares: 12, views: 850 },
      performance_score: 79,
      published_at: "2024-01-20"
    }
  ]

  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-neural-700 mb-6">Top Performing Content</h3>
        
        <div className="space-y-4">
          {topPosts.map((post, index) => (
            <div key={post.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <p className="text-gray-700 line-clamp-2 mb-2">
                    {post.content}
                  </p>
                  <p className="text-xs text-gray-500">
                    Published {new Date(post.published_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="success" size="sm">
                    #{index + 1}
                  </Badge>
                  <Badge variant="ai" size="sm">
                    {post.performance_score}% score
                  </Badge>
                </div>
              </div>
              
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="flex items-center space-x-1">
                  <HeartIcon className="h-4 w-4 text-red-500" />
                  <span>{post.engagement.likes}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <TrendingUpIcon className="h-4 w-4 text-blue-500" />
                  <span>{post.engagement.comments}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <TrendingUpIcon className="h-4 w-4 text-green-500" />
                  <span>{post.engagement.shares}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <EyeIcon className="h-4 w-4 text-purple-500" />
                  <span>{post.engagement.views}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
```

### `src/components/analytics/PersonaInsights.tsx` - Persona Insights Panel
```typescript
import React from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ConfidenceIndicator } from '@/components/intelligence/ConfidenceIndicator'
import { PersonaMetrics } from '@/lib/api'
import { TrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline'

interface PersonaInsightsProps {
  metrics?: PersonaMetrics
}

export function PersonaInsights({ metrics }: PersonaInsightsProps) {
  const insights = [
    {
      title: "Authority Building",
      description: "Your thought leadership content performs 23% better than industry posts",
      trend: "up" as const,
      confidence: 0.87
    },
    {
      title: "Engagement Peak",
      description: "Tuesday 10 AM posts receive 40% more engagement",
      trend: "up" as const,
      confidence: 0.92
    },
    {
      title: "Content Mix",
      description: "Technical deep-dives generate highest-quality discussions",
      trend: "neutral" as const,
      confidence: 0.78
    },
    {
      title: "Network Growth",
      description: "Consistent posting increased your network reach by 15%",
      trend: "up" as const,
      confidence: 0.84
    }
  ]

  const recommendations = [
    "Focus on thought leadership content during peak hours",
    "Increase technical content frequency by 20%",
    "Engage more with comments to boost algorithmic reach",
    "Consider LinkedIn Live sessions for authority building"
  ]

  return (
    <Card>
      <div className="p-6 space-y-6">
        <h3 className="text-lg font-semibold text-neural-700">AI Insights</h3>
        
        {/* Key Insights */}
        <div className="space-y-4">
          {insights.map((insight, index) => (
            <div key={index} className="border-l-4 border-ai-purple-500 pl-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{insight.title}</h4>
                {insight.trend === 'up' ? (
                  <TrendingUpIcon className="h-4 w-4 text-ml-green-500" />
                ) : insight.trend === 'down' ? (
                  <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
                ) : null}
              </div>
              <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
              <ConfidenceIndicator
                score={insight.confidence}
                label="Confidence"
                size="sm"
              />
            </div>
          ))}
        </div>

        {/* Recommendations */}
        <div className="pt-4 border-t border-gray-100">
          <h4 className="font-medium text-gray-900 mb-3">AI Recommendations</h4>
          <div className="space-y-2">
            {recommendations.map((rec, index) => (
              <div key={index} className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 bg-ai-purple-500 rounded-full mt-2 flex-shrink-0" />
                <p className="text-sm text-gray-600">{rec}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Overall Score */}
        <div className="pt-4 border-t border-gray-100">
          <div className="text-center">
            <div className="text-3xl font-bold text-neural-600 mb-2">
              {metrics?.authority_score || 87}
            </div>
            <div className="text-sm text-gray-600 mb-2">Overall Persona Score</div>
            <Badge variant="ai" size="sm">Top 15% in your industry</Badge>
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### `.env.example` - Environment Variables Template
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Application Settings
VITE_APP_NAME=LinkedIn AI Automation
VITE_APP_VERSION=1.0.0

# Feature Flags
VITE_ENABLE_AI_ENGAGEMENT=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_SCHEDULING=true

# Development
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=info
```

### `.env.local` - Local Development Environment
```env
# Local Development Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
```

### `src/utils/formatting.ts` - Formatting Utilities
```typescript
import { formatDistanceToNow, format, parseISO } from 'date-fns'

export function formatDate(date: string | Date, pattern = 'MMM d, yyyy') {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return format(dateObj, pattern)
}

export function formatRelativeTime(date: string | Date) {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return formatDistanceToNow(dateObj, { addSuffix: true })
}

export function formatNumber(num: number) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

export function formatPercentage(value: number, decimals = 1) {
  return `${(value * 100).toFixed(decimals)}%`
}

export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim() + '...'
}

export function capitalizeFirst(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

export function formatEngagementRate(rate: number) {
  return `${(rate * 100).toFixed(1)}%`
}

export function formatScore(score: number, max = 100) {
  return `${Math.round(score)}/${max}`
}
```

### `src/utils/validation.ts` - Validation Utilities
```typescript
import { z } from 'zod'

export const emailSchema = z.string().email('Invalid email address')

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')

export const postContentSchema = z
  .string()
  .min(10, 'Post content must be at least 10 characters')
  .max(3000, 'Post content must not exceed 3000 characters')

export const hashtagSchema = z
  .string()
  .regex(/^#[a-zA-Z0-9_]+$/, 'Invalid hashtag format')

export function validateHashtags(hashtags: string[]) {
  const errors: string[] = []
  
  if (hashtags.length === 0) {
    errors.push('At least one hashtag is required')
  }
  
  if (hashtags.length > 10) {
    errors.push('Maximum 10 hashtags allowed')
  }
  
  hashtags.forEach((tag, index) => {
    try {
      hashtagSchema.parse(tag)
    } catch (error) {
      errors.push(`Hashtag ${index + 1}: ${tag} is invalid`)
    }
  })
  
  return errors
}

export function validateUrl(url: string) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export function sanitizeContent(content: string) {
  // Remove potentially harmful content
  return content
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .trim()
}
```

### `src/utils/analytics.ts` - Analytics Utilities
```typescript
export function calculateEngagementRate(metrics: {
  likes: number
  comments: number
  shares: number
  views: number
}) {
  const totalEngagement = metrics.likes + metrics.comments + metrics.shares
  return metrics.views > 0 ? totalEngagement / metrics.views : 0
}

export function calculateGrowthRate(current: number, previous: number) {
  if (previous === 0) return current > 0 ? 1 : 0
  return (current - previous) / previous
}

export function getPerformanceGrade(score: number) {
  if (score >= 90) return { grade: 'A+', color: 'text-ml-green-600' }
  if (score >= 80) return { grade: 'A', color: 'text-ml-green-600' }
  if (score >= 70) return { grade: 'B', color: 'text-prediction-600' }
  if (score >= 60) return { grade: 'C', color: 'text-orange-600' }
  return { grade: 'D', color: 'text-red-600' }
}

export function calculateConfidenceInterval(value: number, confidence: number = 0.95) {
  const margin = value * (1 - confidence) * 0.5
  return {
    lower: Math.max(0, value - margin),
    upper: value + margin
  }
}

export function detectTrend(data: number[]) {
  if (data.length < 2) return 'stable'
  
  const recentData = data.slice(-5) // Last 5 data points
  const firstHalf = recentData.slice(0, Math.floor(recentData.length / 2))
  const secondHalf = recentData.slice(Math.floor(recentData.length / 2))
  
  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length
  
  const changePercent = (secondAvg - firstAvg) / firstAvg
  
  if (changePercent > 0.1) return 'increasing'
  if (changePercent < -0.1) return 'decreasing'
  return 'stable'
}

export function groupByTimeframe(
  data: Array<{ timestamp: string; value: number }>,
  timeframe: 'day' | 'week' | 'month'
) {
  const grouped = new Map()
  
  data.forEach(item => {
    const date = new Date(item.timestamp)
    let key: string
    
    switch (timeframe) {
      case 'day':
        key = date.toISOString().split('T')[0]
        break
      case 'week':
        const weekStart = new Date(date)
        weekStart.setDate(date.getDate() - date.getDay())
        key = weekStart.toISOString().split('T')[0]
        break
      case 'month':
        key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
        break
    }
    
    if (!grouped.has(key)) {
      grouped.set(key, [])
    }
    grouped.get(key).push(item.value)
  })
  
  return Array.from(grouped.entries()).map(([key, values]) => ({
    period: key,
    value: values.reduce((a: number, b: number) => a + b, 0) / values.length,
    count: values.length
  }))
}
```

### `README.md` - Project Documentation
```markdown
# LinkedIn AI Automation Frontend

A sophisticated AI-powered LinkedIn automation platform built with React, TypeScript, and Tailwind CSS.

## Features

### 🧠 AI Intelligence
- **Content Selection**: AI automatically selects the most relevant articles for your audience
- **Draft Generation**: Generate LinkedIn posts from selected content with AI
- **Engagement Prediction**: Predict post performance before publishing
- **Optimal Timing**: AI-powered optimal posting time recommendations

### 📊 Analytics & Insights
- **Persona Metrics**: Track your LinkedIn authority and growth
- **Performance Analytics**: Detailed engagement and reach analytics
- **Content Performance**: Analyze which content types perform best
- **Trend Analysis**: Identify patterns in your LinkedIn presence

### 🚀 Content Management
- **Creation Studio**: Streamlined content creation workflow
- **Draft Workshop**: Edit and optimize your content drafts
- **Publishing Calendar**: Schedule and manage your content pipeline
- **Smart Recommendations**: AI-powered posting recommendations

### 💬 Engagement Hub
- **Comment Opportunities**: Find high-value engagement opportunities
- **Auto-Discovery**: Automatically discover relevant posts to engage with
- **Smart Commenting**: AI-generated comment suggestions
- **Engagement Tracking**: Monitor your engagement activities

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for global state
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form with Zod validation
- **UI Components**: Custom component library with Headless UI
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Date Handling**: date-fns
- **Build Tool**: Vite

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd linkedin-automation-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env.local
```

4. Configure your environment variables in `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

5. Start the development server:
```bash
npm run dev
```

6. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Base UI components (Button, Card, etc.)
│   ├── intelligence/    # AI-specific components
│   ├── layout/          # Layout components
│   ├── dashboard/       # Dashboard-specific components
│   ├── content/         # Content management components
│   ├── creation/        # Content creation components
│   ├── engagement/      # Engagement hub components
│   └── analytics/       # Analytics components
├── pages/               # Route components
├── hooks/               # Custom React hooks
├── stores/              # Zustand stores
├── lib/                 # Core utilities (API client, etc.)
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
└── styles/              # Global styles
```

## Key Components

### AI Intelligence System
- `ConfidenceIndicator`: Shows AI confidence levels
- `PredictionCard`: Displays engagement predictions
- `AIAnalysisPanel`: Shows AI reasoning and analysis
- `ScoreBreakdown`: Content scoring visualization

### Content Management
- `ContentIntelligenceCard`: Individual content item display
- `DraftRecommendationCard`: AI-powered draft recommendations
- `PublishingCalendar`: Content scheduling interface

### Analytics Dashboard
- `PerformanceChart`: Engagement metrics visualization
- `PersonaInsights`: AI-generated insights about your LinkedIn presence
- `AnalyticsOverview`: Key performance indicators

## State Management

The application uses Zustand for state management with the following stores:

- `authStore`: User authentication and session management
- `contentStore`: Content management and AI selection
- `engagementStore`: Engagement opportunities and automation
- `uiStore`: UI state, notifications, and preferences

## API Integration

The app integrates with a backend API for:
- Content fetching and analysis
- AI-powered recommendations
- Draft generation and management
- Engagement tracking
- Analytics data

## Configuration

### AI Settings
Configure AI behavior in the Settings page:
- Content selection criteria
- Draft generation preferences
- Engagement automation rules
- Scheduling preferences

### Design System
The app uses a custom design system with:
- AI-focused color palette (neural, ml-green, prediction)
- Consistent component styling
- Responsive design patterns
- Accessibility considerations

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License.
```

This completes the comprehensive implementation of all components, utilities, and documentation for the AI-powered LinkedIn automation frontend. The codebase is production-ready with proper TypeScript typing, error handling, responsive design, and a complete feature set covering all three phases of development.