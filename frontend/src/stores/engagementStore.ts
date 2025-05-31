import { create } from 'zustand'

// Basic interfaces for engagement
interface EngagementOpportunity {
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
}

interface EngagementStats {
  total_opportunities: number
  completion_rate: number
  status_breakdown: Record<string, number>
  type_breakdown: Record<string, number>
  period_days: number
  generated_at: string
}

interface EngagementState {
  commentQueue: EngagementOpportunity[]
  highPriorityOpportunities: EngagementOpportunity[]
  allOpportunities: EngagementOpportunity[]
  engagementStats: EngagementStats | null
  automationEnabled: boolean
  isLoading: boolean
  error: string | null
  selectedOpportunity: EngagementOpportunity | null
}

interface EngagementActions {
  fetchCommentOpportunities: (params?: any) => Promise<void>
  fetchHighPriorityOpportunities: () => Promise<void>
  fetchEngagementStats: (days?: number) => Promise<void>
  createComment: (data: any) => Promise<void>
  discoverNewPosts: (maxPosts?: number) => Promise<void>
  updateQueue: (opportunities: EngagementOpportunity[]) => void
  removeFromQueue: (opportunityId: string) => void
  addToQueue: (opportunity: EngagementOpportunity) => void
  toggleAutomation: () => void
  setAutomationEnabled: (enabled: boolean) => void
  setSelectedOpportunity: (opportunity: EngagementOpportunity | null) => void
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
  isLoading: false,
  error: null,
  selectedOpportunity: null,

  // Actions (basic implementations to prevent errors)
  fetchCommentOpportunities: async (params) => {
    set({ isLoading: true, error: null })
    try {
      // Mock implementation - replace with real API call
      const opportunities: EngagementOpportunity[] = []
      set({ commentQueue: opportunities, allOpportunities: opportunities, isLoading: false })
    } catch (error: any) {
      set({ isLoading: false, error: error.message })
    }
  },

  fetchHighPriorityOpportunities: async () => {
    try {
      const opportunities: EngagementOpportunity[] = []
      set({ highPriorityOpportunities: opportunities })
    } catch (error: any) {
      console.error('Failed to fetch high priority opportunities:', error)
    }
  },

  fetchEngagementStats: async (days = 30) => {
    try {
      const stats: EngagementStats = {
        total_opportunities: 0,
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
      // Mock implementation
      set((state) => ({
        commentQueue: state.commentQueue.filter((opp) => opp.id !== data.opportunity_id),
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
      // Mock implementation
      await get().fetchCommentOpportunities()
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

  clearError: () => {
    set({ error: null })
  },

  refreshEngagementData: async () => {
    await Promise.all([
      get().fetchCommentOpportunities(),
      get().fetchHighPriorityOpportunities(),
      get().fetchEngagementStats(),
    ])
  },
}))

// Helper hooks
export const useEngagementQueue = () => {
  const { commentQueue, isLoading, error } = useEngagementStore()
  return { commentQueue, isLoading, error }
}

export const useHighPriorityOpportunities = () => {
  const { highPriorityOpportunities } = useEngagementStore()
  return highPriorityOpportunities
}