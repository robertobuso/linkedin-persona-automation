// frontend/src/pages/Sources.tsx
import React from 'react'
import { ContentSourcesList } from '@/components/sources/ContentSourcesList'

export default function SourcesPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <ContentSourcesList />
    </div>
  )
}