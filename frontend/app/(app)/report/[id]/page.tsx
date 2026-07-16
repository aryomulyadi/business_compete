'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { api } from '@/lib/api-client'
import Breadcrumbs from '@/components/Breadcrumbs'
import { IconDownload, IconPalette, IconChevronRight } from '@/components/Icons'
import { SkeletonPage } from '@/components/Skeleton'
import type { ReportData } from '@/lib/types'

export default function ReportPage() {
  const params = useParams()
  const id = Number(params.id)
  const [report, setReport] = useState<ReportData | null>(null)
  const [brandNames, setBrandNames] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'preview' | 'branding'>('preview')

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      api.getReport(id),
      api.getBrandConcepts(id).catch(() => ({ concepts: [], names: [] })),
    ])
      .then(([reportData, brandData]) => {
        setReport(reportData)
        setBrandNames(brandData.names)
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <SkeletonPage />
  if (error) return (
    <div className="px-4 py-3 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/20 text-[#FCA5A5] text-sm animate-fade-in">
      {error}
    </div>
  )
  if (!report) return (
    <div className="px-4 py-3 rounded-lg bg-[#FED16A]/10 border border-[#FED16A]/20 text-[#FFF4A4] text-sm animate-fade-in">
      Laporan tidak ditemukan
    </div>
  )

  return (
    <div className="animate-fade-in">
      <Breadcrumbs
        links={[
          { label: 'Beranda', href: '/dashboard' },
          { label: `Laporan: ${report.field}` },
        ]}
      />

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#F1F5F9]">
            {report.field}
          </h1>
          <p className="text-sm text-[#64748B] mt-1 font-mono">
            {new Date(report.created_at).toLocaleString('id-ID')}
          </p>
        </div>
      </div>

      <div className="flex gap-1 mb-6 border-b border-[#334155]">
        {(['preview', 'branding'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition-all duration-200 border-b-2 -mb-[1px] ${
              tab === t
                ? 'border-[#F58A2A] text-[#F58A2A]'
                : 'border-transparent text-[#64748B] hover:text-[#94A3B8]'
            }`}
          >
            {t === 'preview' ? 'Laporan' : 'Branding'}
          </button>
        ))}
      </div>

      {tab === 'preview' && (
        <div>
          <div className="flex flex-wrap gap-2 mb-6">
            {(['md', 'html', 'pdf'] as const).map((fmt) => (
              <a
                key={fmt}
                href={api.getExportUrl(id, fmt)}
                className="btn-ghost flex items-center gap-1.5 text-xs"
              >
                <IconDownload size={14} />
                {fmt.toUpperCase()}
              </a>
            ))}
          </div>

          <div className="card p-6">
            <div className="prose prose-invert prose-sm max-w-none">
              {report.content.split('\n').map((line, i) => {
                if (line.startsWith('# ')) {
                  return <h1 key={i} className="text-2xl font-bold text-[#F1F5F9] mt-6 mb-3">{line.slice(2)}</h1>
                }
                if (line.startsWith('## ')) {
                  return <h2 key={i} className="text-xl font-semibold text-[#CBD5E1] mt-5 mb-2">{line.slice(3)}</h2>
                }
                if (line.startsWith('### ')) {
                  return <h3 key={i} className="text-lg font-medium text-[#CBD5E1] mt-4 mb-2">{line.slice(4)}</h3>
                }
                if (line.startsWith('- ')) {
                  return <li key={i} className="text-[#94A3B8] ml-4">{line.slice(2)}</li>
                }
                if (line.startsWith('|')) {
                  return <pre key={i} className="text-xs text-[#64748B] font-mono whitespace-pre-wrap">{line}</pre>
                }
                if (line.trim() === '') {
                  return <div key={i} className="h-3" />
                }
                return <p key={i} className="text-[#94A3B8] leading-relaxed">{line}</p>
              })}
            </div>
          </div>
        </div>
      )}

      {tab === 'branding' && (
        <div>
          <h2 className="text-lg font-semibold text-[#F1F5F9] mb-4">Rekomendasi Brand</h2>
          {brandNames.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-center">
              <div className="w-12 h-12 rounded-xl bg-[#1E293B] flex items-center justify-center mb-3">
                <IconPalette size={24} className="text-[#475569]" />
              </div>
              <p className="text-[#64748B] text-sm">Tidak ada brand yang ditemukan di laporan ini.</p>
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              {brandNames.map((name) => (
                <a
                  key={name}
                  href={`/branding/${id}?brand=${encodeURIComponent(name)}`}
                  className="btn-primary flex items-center gap-2"
                >
                  <IconPalette size={16} />
                  {name}
                  <IconChevronRight size={14} />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
