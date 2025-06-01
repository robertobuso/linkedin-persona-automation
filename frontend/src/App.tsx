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
import PreferencesPage from '@/pages/Preferences'
import SourcesPage from '@/pages/Sources'

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
                <Route path="sources" element={<SourcesPage />} />
                <Route path="preferences" element={<PreferencesPage />} />
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
