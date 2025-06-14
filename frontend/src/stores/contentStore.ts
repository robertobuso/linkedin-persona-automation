import { create } from 'zustand'
import { api, type ContentItem, type DailySummary, type ContentSource } from '@/lib/api'

interface ContentState {
  // Content data
  aiSelectedContent: ContentItem[]
  allContent: ContentItem[]
  dailySummary: DailySummary | null
  
  // Sources data
  contentSources: ContentSource[]
  
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
  fetchContentSources: () => Promise<void>
  
  // UI state management
  setViewMode: (mode: 'ai-selected' | 'fresh' | 'trending' | 'all') => void
  setSearchQuery: (query: string) => void
  setSelectedCategories: (categories: string[]) => void
  
  // Data management
  updateAISelection: (content: ContentItem[]) => void
  setDailySummary: (summary: DailySummary) => void
  setContentSources: (sources: ContentSource[]) => void
  clearError: () => void
  
  // Refresh
  refreshContent: () => Promise<void>
  refreshSources: () => Promise<void>
}

type ContentStore = ContentState & ContentActions

export const useContentStore = create<ContentStore>((set, get) => ({
  // Initial state
  aiSelectedContent: [],
  allContent: [],
  dailySummary: null,
  contentSources: [],
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

  fetchContentSources: async () => {
    try {
      const sources = await api.getContentSources()
      set({ contentSources: sources })
    } catch (error: any) {
      console.error('Failed to fetch content sources:', error)
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

  setContentSources: (sources) => {
    set({ contentSources: sources })
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

  refreshSources: async () => {
    await get().fetchContentSources()
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

export const useContentSources = () => {
  const { contentSources, isLoading, error } = useContentStore()
  return { data: contentSources, isLoading, error }
}