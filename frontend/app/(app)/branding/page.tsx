'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api-client'
import Breadcrumbs from '@/components/Breadcrumbs'
import { IconPalette, IconChevronRight } from '@/components/Icons'
import { SkeletonPage } from '@/components/Skeleton'
import type { BrandedReport } from '@/lib/types'

const PAGE_SIZE = 20

export default function BrandingGalleryPage() {
  const [reports, setReports] = useState<BrandedReport[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.getBrandedReports(offset, PAGE_SIZE)
      setReports(res.reports)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [offset])

  useEffect(() => { fetch() }, [fetch])

  return (
    <div className="animate-fade-in">
      <Breadcrumbs links={[{ label: 'Beranda', href: '/dashboard' }, { label: 'Branding' }]} />

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#F1F5F9]">Branding & Logo</h1>
      </div>

      {loading && <SkeletonPage />}

      {!loading && reports.length === 0 && (
        <div className="flex flex-col items-center py-16 text-center">
          <div className="w-14 h-14 rounded-xl bg-[#1E293B] flex items-center justify-center mb-4">
            <IconPalette size={28} className="text-[#475569]" />
          </div>
          <p className="text-[#94A3B8] text-sm mb-2">Belum ada rekomendasi brand</p>
          <Link href="/dashboard" className="text-[#F58A2A] text-sm hover:underline">Mulai analisis baru untuk menghasilkan brand</Link>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="space-y-3">
          {reports.map((r) => (
            <div
              key={r.row_id}
              className="card p-4 hover:bg-[#1E293B]/80 transition-all duration-200 animate-slide-up"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-[#F1F5F9] truncate">{r.field}</p>
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    {r.brand_names.map((name) => (
                      <span
                        key={name}
                        className="px-2.5 py-0.5 rounded-full bg-[#F58A2A]/10 border border-[#F58A2A]/20 text-xs text-[#F58A2A] font-medium"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-[#64748B] mt-2 font-mono">
                    {new Date(r.created_at).toLocaleString('id-ID')}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    href={`/report/${r.row_id}`}
                    className="btn-ghost text-xs px-3 py-1.5"
                  >
                    Laporan
                  </Link>
                  <Link
                    href={`/branding/${r.row_id}`}
                    className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
                  >
                    Detail
                    <IconChevronRight size={12} />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {reports.length > 0 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="btn-ghost text-xs"
          >
            Sebelumnya
          </button>
          <span className="text-xs text-[#64748B]">
            {offset + 1}–{offset + reports.length}
          </span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={reports.length < PAGE_SIZE}
            className="btn-ghost text-xs"
          >
            Selanjutnya
          </button>
        </div>
      )}
    </div>
  )
}
