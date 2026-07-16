'use client'

import { useState } from 'react'
import Sidebar from './Sidebar'
import { IconClose, IconHome } from './Icons'

export default function Layout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-[#0F172A]">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar onClose={() => setMobileOpen(false)} />
      </div>

      {/* Main */}
      <main className="flex-1 min-w-0 animate-fade-in">
        {/* Mobile header */}
        <div className="sticky top-0 z-30 flex items-center gap-3 px-4 py-3 bg-[#0F172A]/80 backdrop-blur-lg border-b border-[#334155] lg:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-1.5 rounded-lg hover:bg-[#1E293B] transition-colors text-[#94A3B8]"
            aria-label="Buka navigasi"
          >
            <IconHome size={20} />
          </button>
          <span className="text-sm font-medium text-[#F1F5F9]">BizComp AI</span>
        </div>

        <div className="p-4 lg:p-8 max-w-5xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
