import { create } from 'zustand'
import { api, type EngagementOpportunity, type PostDraft } from '@/lib/api'

interface EngagementStats {
  total_opportunities: number
  completion_rate: number
  status_breakdown: Record<string, number>
  type_breakdown: Record<string, number>
  period_days: number
  generated_at: string
}

interface EngagementState {
  // Engagement opportunities
  commentQueue: EngagementOpportunity[]
  highPriorityOpportunities: EngagementOpportunity[]
  allOpportunities: EngagementOpportunity[]
  engagementStats: EngagementStats | null
  automationEnabled: boolean
  selectedOpportunity: EngagementOpportunity | null
  
  // Draft management
  drafts: PostDraft[]
  selectedDraft: PostDraft | null
  draftFilters: {
    status: string | null
    searchQuery: string
  }
  
  // UI state
  isLoading: boolean
  error: string | null
}

interface EngagementActions {
  // Engagement opportunities
  fetchCommentOpportunities: (params?: any) => Promise<void>
  fetchHighPriorityOpportunities: () => Promise<void>
  fetchEngagementStats: (days?: number) => Promise<void>
  createComment: (data: { opportunity_id: string; comment_text?: string }) => Promise<void>
  discoverNewPosts: (maxPosts?: number) => Promise<void>
  updateQueue: (opportunities: EngagementOpportunity[]) => void
  removeFromQueue: (opportunityId: string) => void
  addToQueue: (opportunity: EngagementOpportunity) => void
  toggleAutomation: () => void
  setAutomationEnabled: (enabled: boolean) => void
  setSelectedOpportunity: (opportunity: EngagementOpportunity | null) => void
  
  // Draft management
  fetchDrafts: () => Promise<void>
  setSelectedDraft: (draft: PostDraft | null) => void
  setDraftFilters: (filters: Partial<EngagementState['draftFilters']>) => void
  refreshDrafts: () => Promise<void>
  
  // Utility
  clearError: () => void
  refreshEngagementData: () => Promise<void>
}

type EngagementStore = EngagementState & EngagementActions

export const useEngagementStore = create<EngagementStore>((set, get) => ({
  // Initial state
  commentQueue: [],
  highPriorityOpportunities: [],
  allOpportunities: [],
  engagementStats: null,
  automationEnabled: false,
  selectedOpportunity: null,
  
  // Draft state
  drafts: [],
  selectedDraft: null,
  draftFilters: {
    status: null,
    searchQuery: ''
  },
  
  // UI state
  isLoading: false,
  error: null,

  // Engagement Actions
  fetchCommentOpportunities: async (params) => {
    set({ isLoading: true, error: null })
    try {
      const opportunities = await api.getCommentOpportunities(params)
      set({ 
        commentQueue: opportunities, 
        allOpportunities: opportunities, 
        isLoading: false 
      })
    } catch (error: any) {
      set({ isLoading: false, error: error.message })
    }
  },

  fetchHighPriorityOpportunities: async () => {
    try {
      const opportunities = await api.getCommentOpportunities({ 
        priority: 'high',
        limit: 10 
      })
      set({ highPriorityOpportunities: opportunities })
    } catch (error: any) {
      console.error('Failed to fetch high priority opportunities:', error)
    }
  },

  fetchEngagementStats: async (days = 30) => {
    try {
      // This would need to be implemented in your API
      const stats: EngagementStats = {
        total_opportunities: get().allOpportunities.length,
        completion_rate: 0,
        status_breakdown: {},
        type_breakdown: {},
        period_days: days,
        generated_at: new Date().toISOString()
      }
      set({ engagementStats: stats })
    } catch (error: any) {
      console.error('Failed to fetch engagement stats:', error)
    }
  },

  createComment: async (data) => {
    set({ isLoading: true, error: null })
    try {
      await api.createComment(data)
      set((state) => ({
        commentQueue: state.commentQueue.filter((opp) => opp.id !== data.opportunity_id),
        allOpportunities: state.allOpportunities.filter((opp) => opp.id !== data.opportunity_id),
        isLoading: false,
      }))
    } catch (error: any) {
      set({ isLoading: false, error: error.message })
      throw error
    }
  },

  discoverNewPosts: async (maxPosts = 50) => {
    set({ isLoading: true, error: null })
    try {
      await get().fetchCommentOpportunities({ limit: maxPosts })
      set({ isLoading: false })
    } catch (error: any) {
      set({ isLoading: false, error: error.message })
      throw error
    }
  },

  updateQueue: (opportunities) => {
    set({ commentQueue: opportunities })
  },

  removeFromQueue: (opportunityId) => {
    set((state) => ({
      commentQueue: state.commentQueue.filter((opp) => opp.id !== opportunityId),
      allOpportunities: state.allOpportunities.filter((opp) => opp.id !== opportunityId),
    }))
  },

  addToQueue: (opportunity) => {
    set((state) => ({
      commentQueue: [opportunity, ...state.commentQueue],
      allOpportunities: [opportunity, ...state.allOpportunities],
    }))
  },

  toggleAutomation: () => {
    set((state) => ({ automationEnabled: !state.automationEnabled }))
  },

  setAutomationEnabled: (enabled) => {
    set({ automationEnabled: enabled })
  },

  setSelectedOpportunity: (opportunity) => {
    set({ selectedOpportunity: opportunity })
  },

  // Draft Actions
  fetchDrafts: async () => {
    try {
      const drafts = await api.getDrafts()
      set({ drafts })
    } catch (error: any) {
      console.error('Failed to fetch drafts:', error)
      set({ error: error.message })
    }
  },

  setSelectedDraft: (draft) => {
    set({ selectedDraft: draft })
  },

  setDraftFilters: (filters) => {
    set(state => ({
      draftFilters: { ...state.draftFilters, ...filters }
    }))
  },

  refreshDrafts: async () => {
    await get().fetchDrafts()
  },

  // Utility Actions
  clearError: () => {
    set({ error: null })
  },

  refreshEngagementData: async () => {
    await Promise.all([
      get().fetchCommentOpportunities(),
      get().fetchHighPriorityOpportunities(),
      get().fetchEngagementStats(),
      get().fetchDrafts()
    ])
  },
}))

// Helper hooks
export const useDrafts = () => {
  const { drafts, isLoading, error } = useEngagementStore()
  return { data: drafts, isLoading, error }
}

export const useSelectedDraft = () => {
  const { selectedDraft, setSelectedDraft } = useEngagementStore()
  return { selectedDraft, setSelectedDraft }
}

export const useEngagementQueue = () => {
  const { commentQueue, isLoading, error } = useEngagementStore()
  return { data: commentQueue, isLoading, error }
}