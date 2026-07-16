'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { api } from '@/lib/api-client'
import Breadcrumbs from '@/components/Breadcrumbs'
import BrandCard from '@/components/BrandCard'
import { IconPalette } from '@/components/Icons'
import { SkeletonPage } from '@/components/Skeleton'
import type { BrandConcept } from '@/lib/types'

export default function BrandingPage() {
  const params = useParams()
  const reportId = Number(params.reportId)

  const [concepts, setConcepts] = useState<BrandConcept[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [field, setField] = useState('')

  useEffect(() => {
    if (!reportId) return
    setLoading(true)
    Promise.all([
      api.getBrandConcepts(reportId),
      api.getReport(reportId).catch(() => null),
    ])
      .then(([brandData, reportData]) => {
        setConcepts(brandData.concepts)
        setField(reportData?.field || '')
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [reportId])

  if (loading) return <SkeletonPage />
  if (error) return (
    <div className="px-4 py-3 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/20 text-[#FCA5A5] text-sm animate-fade-in">
      {error}
    </div>
  )

  return (
    <div className="animate-fade-in">
      <Breadcrumbs
        links={[
          { label: 'Beranda', href: '/dashboard' },
          { label: 'Laporan', href: `/report/${reportId}` },
          { label: 'Branding & Logo' },
        ]}
      />

      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#F1F5F9]">
          Branding & Logo
        </h1>
        {field && <p className="text-sm text-[#64748B] mt-1">{field}</p>}
      </div>

      {concepts.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-center">
          <div className="w-14 h-14 rounded-xl bg-[#1E293B] flex items-center justify-center mb-4">
            <IconPalette size={28} className="text-[#475569]" />
          </div>
          <p className="text-[#94A3B8] text-sm mb-3">Tidak ditemukan rekomendasi brand di laporan ini.</p>
          <a href={`/report/${reportId}`} className="text-[#F58A2A] text-sm hover:underline">
            Kembali ke Laporan
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {concepts.map((brand, i) => (
            <BrandCard
              key={i}
              brand={brand}
              index={i + 1}
              historyRowId={reportId}
            />
          ))}
        </div>
      )}
    </div>
  )
}
