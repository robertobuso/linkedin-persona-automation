import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  read?: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

interface UIState {
  // Navigation
  sidebarOpen: boolean
  activeTab: string
  sidebarCollapsed: boolean
  
  // Notifications
  notifications: Notification[]
  
  // Modals
  activeModal: string | null
  modalData: any
  
  // Loading states
  globalLoading: boolean
  loadingStates: Record<string, boolean>
  
  // Theme and preferences
  theme: 'light' | 'dark' | 'system'
  
  // AI Features
  aiThinking: boolean
  aiMessage: string | null
}

interface UIActions {
  // Navigation
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  toggleSidebarCollapsed: () => void
  setActiveTab: (tab: string) => void
  
  // Notifications
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  
  // Modals
  openModal: (modalId: string, data?: any) => void
  closeModal: () => void
  
  // Loading states
  setGlobalLoading: (loading: boolean) => void
  setLoadingState: (key: string, loading: boolean) => void
  
  // Theme
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  
  // AI Features
  setAIThinking: (thinking: boolean, message?: string) => void
  clearAIState: () => void
}

type UIStore = UIState & UIActions

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // Initial state
      sidebarOpen: true,
      activeTab: 'dashboard',
      sidebarCollapsed: false,
      notifications: [],
      activeModal: null,
      modalData: null,
      globalLoading: false,
      loadingStates: {},
      theme: 'system',
      aiThinking: false,
      aiMessage: null,

      // Actions
      setSidebarOpen: (open) => {
        set({ sidebarOpen: open })
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }))
      },

      toggleSidebarCollapsed: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
      },

      setActiveTab: (tab) => {
        set({ activeTab: tab })
      },

      addNotification: (notification) => {
        const id = Math.random().toString(36).substr(2, 9)
        const newNotification: Notification = {
          id,
          duration: 5000, // Default 5 seconds
          read: false,
          ...notification,
        }

        set((state) => ({
          notifications: [...state.notifications, newNotification],
        }))

        // Auto-remove after duration
        if (newNotification.duration && newNotification.duration > 0) {
          setTimeout(() => {
            get().removeNotification(id)
          }, newNotification.duration)
        }

        return id
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }))
      },

      clearNotifications: () => {
        set({ notifications: [] })
      },

      openModal: (modalId, data) => {
        set({ activeModal: modalId, modalData: data })
      },

      closeModal: () => {
        set({ activeModal: null, modalData: null })
      },

      setGlobalLoading: (loading) => {
        set({ globalLoading: loading })
      },

      setLoadingState: (key, loading) => {
        set((state) => ({
          loadingStates: {
            ...state.loadingStates,
            [key]: loading,
          },
        }))
      },

      setTheme: (theme) => {
        set({ theme })
      },

      setAIThinking: (thinking, message) => {
        set({ aiThinking: thinking, aiMessage: message || null })
      },

      clearAIState: () => {
        set({ aiThinking: false, aiMessage: null })
      },
    }),
    {
      name: 'ui-preferences',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
)

// Helper hooks
export const useNotifications = () => {
  const { notifications, addNotification, removeNotification, clearNotifications } = useUIStore()
  return { notifications, addNotification, removeNotification, clearNotifications }
}

export const useModal = () => {
  const { activeModal, modalData, openModal, closeModal } = useUIStore()
  return { activeModal, modalData, openModal, closeModal }
}

export const useLoadingState = (key: string) => {
  const { loadingStates, setLoadingState } = useUIStore()
  return {
    isLoading: loadingStates[key] || false,
    setLoading: (loading: boolean) => setLoadingState(key, loading),
  }
}

// Notification helpers
export const notify = {
  success: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'success', title, message })
  },
  error: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'error', title, message, duration: 8000 })
  },
  warning: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'warning', title, message })
  },
  info: (title: string, message?: string) => {
    useUIStore.getState().addNotification({ type: 'info', title, message })
  },
}