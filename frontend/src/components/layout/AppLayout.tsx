import React from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { NotificationCenter } from './NotificationCenter'
import { AIStatusIndicator } from './AIStatusIndicator'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/utils/cn'

interface AppLayoutProps {
  children?: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const { sidebarOpen, sidebarCollapsed, globalLoading } = useUIStore()
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        {children || <Outlet />}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Global loading overlay */}
      {globalLoading && (
        <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="text-center space-y-4">
            <div className="relative mx-auto">
              <div className="h-12 w-12 rounded-full bg-gradient-to-r from-ai-purple-500 to-ml-green-500 animate-pulse" />
              <div className="absolute inset-0 h-12 w-12 rounded-full bg-gradient-to-r from-ai-purple-500 to-ml-green-500 animate-ping opacity-50" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neural-700">Processing</h3>
              <p className="text-gray-600">Please wait...</p>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div
        className={cn(
          'transition-all duration-300 ease-in-out',
          sidebarOpen && !sidebarCollapsed ? 'lg:pl-64' : 'lg:pl-16'
        )}
      >
        {/* Header */}
        <Header />

        {/* Main content */}
        <main className="flex-1">
          <div className="p-6 max-w-7xl mx-auto">
            {children || <Outlet />}
          </div>
        </main>
      </div>

      {/* Fixed UI elements */}
      <NotificationCenter />
      <AIStatusIndicator />
    </div>
  )
}

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neural-50 via-white to-ml-green-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-ai-purple-500 to-ml-green-500 rounded-2xl mb-4">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <span className="text-neural-600 font-bold text-lg">AI</span>
            </div>
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-neural-700 to-neural-600 bg-clip-text text-transparent">
            LinkedIn AI Automation
          </h1>
          <p className="text-gray-600 mt-2">
            AI-Powered LinkedIn Presence Platform
          </p>
        </div>

        {/* Auth content */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          {children}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          Powered by Advanced AI Intelligence
        </div>
      </div>
    </div>
  )
}

export function EmptyLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      {children}
    </div>
  )
}