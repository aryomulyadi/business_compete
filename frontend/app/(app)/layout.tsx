'use client'

import Layout from '@/components/Layout'
import ErrorBoundary from '@/components/ErrorBoundary'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <Layout>{children}</Layout>
    </ErrorBoundary>
  )
}
