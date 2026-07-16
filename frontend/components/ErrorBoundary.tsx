'use client'

import { Component, type ReactNode } from 'react'
import { IconAlert } from './Icons'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
          <IconAlert size={32} className="text-[#EF4444] mb-4" />
          <h2 className="text-lg font-semibold text-[#F1F5F9] mb-2">Terjadi Kesalahan</h2>
          <p className="text-sm text-[#64748B] mb-4 max-w-md">
            {this.state.error?.message || 'Gagal memuat halaman.'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Muat Ulang
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
