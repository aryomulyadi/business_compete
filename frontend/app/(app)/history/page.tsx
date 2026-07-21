'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api-client'
import Breadcrumbs from '@/components/Breadcrumbs'
import { IconSearch } from '@/components/Icons'
import { SkeletonTable } from '@/components/Skeleton'
import type { HistoryItem } from '@/lib/types'

const PAGE_SIZE = 20

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getHistory(search || undefined, offset, PAGE_SIZE)
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
      setError(e instanceof Error ? e.message : 'Gagal memuat riwayat')
    } finally {
      setLoading(false)
    }
  }, [search, offset])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  const handleSearch = () => { setOffset(0); fetchHistory() }

  const statusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <span className="badge badge-success">✅ Selesai</span>
      case 'running': return <span className="badge badge-running">⏳ Berjalan</span>
      case 'failed': return <span className="badge badge-failed">❌ Gagal</span>
      default: return <span className="badge badge-running">{status}</span>
    }
  }

  return (
    <div className="animate-fade-in">
      <Breadcrumbs links={[{ label: 'Beranda', href: '/dashboard' }, { label: 'Riwayat' }]} />

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#F1F5F9]">Riwayat Analisis</h1>
      </div>

      <div className="relative mb-6">
        <IconSearch size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#64748B]" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Filter berdasarkan bidang bisnis..."
          className="input-field pl-10"
        />
      </div>

      {loading && <SkeletonTable />}

      {error && (
        <div className="px-4 py-3 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/20 text-[#FCA5A5] text-sm mb-6">
          {error}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="flex flex-col items-center py-16 text-center">
          <div className="w-12 h-12 rounded-xl bg-[#1E293B] flex items-center justify-center mb-4">
            <IconSearch size={24} className="text-[#475569]" />
          </div>
          <p className="text-[#94A3B8] text-sm mb-2">Belum ada analisis yang tersimpan</p>
          <Link href="/dashboard" className="text-[#F58A2A] text-sm hover:underline">Mulai analisis baru</Link>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="card p-4 hover:bg-[#1E293B]/80 transition-all duration-200 animate-slide-up"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-[#F1F5F9] truncate">{item.field}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    {statusBadge(item.status)}
                    {item.created_at && (
                      <span className="text-xs text-[#64748B] font-mono">
                        {new Date(item.created_at).toLocaleString('id-ID')}
                      </span>
                    )}
                  </div>
                  {item.error && (
                    <p className="text-xs text-[#FCA5A5] mt-1.5">{item.error}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {item.status === 'completed' && (
                    <>
                      <Link
                        href={`/report/${item.id}`}
                        className="btn-primary text-xs px-3 py-1.5"
                      >
                        Buka
                      </Link>
                      <div className="flex gap-1">
                        {(['md', 'html', 'pdf'] as const).map((fmt) => (
                          <a
                            key={fmt}
                            href={api.getExportUrl(item.id, fmt)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-ghost text-xs px-2 py-1.5"
                          >
                            {fmt.toUpperCase()}
                          </a>
                        ))}
                      </div>
                    </>
                  )}
                  {item.status === 'running' && (
                    <span className="text-xs text-[#64748B]">⏳ Berjalan</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {items.length > 0 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="btn-ghost text-xs"
          >
            Sebelumnya
          </button>
          <span className="text-xs text-[#64748B]">
            {offset + 1}–{offset + items.length}
          </span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={items.length < PAGE_SIZE}
            className="btn-ghost text-xs"
          >
            Selanjutnya
          </button>
        </div>
      )}
    </div>
  )
}
