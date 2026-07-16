'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { IconHome, IconHistory, IconPalette, IconClose } from './Icons'

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Analisis Baru', icon: IconHome },
  { href: '/history', label: 'Riwayat', icon: IconHistory },
  { href: '/branding', label: 'Branding', icon: IconPalette },
]

export default function Sidebar({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname()

  return (
    <aside className="h-full flex flex-col bg-[#1E293B]/80 backdrop-blur-xl border-r border-[#334155]">
      <div className="flex items-center justify-between px-5 py-5 border-b border-[#334155]">
        <div>
          <h1 className="text-sm font-bold text-[#F1F5F9] tracking-tight">BizComp</h1>
          <p className="text-[10px] text-[#64748B] font-medium tracking-wider uppercase mt-0.5">AI v0.1</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-[#334155] transition-colors text-[#64748B] lg:hidden"
            aria-label="Tutup navigasi"
          >
            <IconClose size={16} />
          </button>
        )}
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-[#F58A2A]/10 text-[#F58A2A] shadow-[inset_0_0_0_1px_rgba(245,138,42,0.15)]'
                  : 'text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#334155]/50'
              }`}
            >
              <item.icon
                size={18}
                className={isActive ? 'text-[#F58A2A]' : 'text-[#64748B]'}
              />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="px-5 py-4 border-t border-[#334155]">
        <p className="text-[10px] text-[#475569] font-mono">&copy; 2026</p>
      </div>
    </aside>
  )
}
