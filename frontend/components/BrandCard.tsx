'use client'

import { useState } from 'react'
import type { BrandConcept } from '@/lib/types'
import { api } from '@/lib/api-client'
import { IconSparkle, IconCheck } from './Icons'

interface BrandCardProps {
  brand: BrandConcept
  index: number
  historyRowId?: number
}

const STYLE_OPTIONS = [
  'modern minimalis',
  'vintage klasik',
  'futuristik neon',
  'natural organik',
  'mewah elegant',
]

export default function BrandCard({ brand, index, historyRowId }: BrandCardProps) {
  const [svg, setSvg] = useState<string | null>(null)
  const [aiImage, setAiImage] = useState<string | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [style, setStyle] = useState(STYLE_OPTIONS[0])

  const handleSvg = async () => {
    const res = await api.generateSvgLogo(brand.name)
    setSvg(res.svg)
    setAiImage(null)
  }

  const handleAi = async () => {
    setLoading(true)
    setAiError(null)
    const res = await api.generateAiLogo(
      brand.name,
      {
        meaning: brand.meaning || '',
        philosophy: brand.philosophy || '',
        target_market: brand.target_market || '',
        positioning: brand.positioning || '',
      },
      style,
      historyRowId
    )
    setLoading(false)
    if (res.error) {
      setAiError(res.error)
    } else if (res.image_base64) {
      setAiImage(`data:image/png;base64,${res.image_base64}`)
      setSvg(null)
    }
  }

  return (
    <div className="card p-5 flex flex-col animate-slide-up">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-[#F58A2A]/10 text-[#F58A2A] text-xs font-bold">
          {index}
        </span>
        <h3 className="text-base font-semibold text-[#F1F5F9]">{brand.name}</h3>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm mb-5">
        {brand.meaning && (
          <>
            <span className="text-[#64748B] text-xs uppercase tracking-wider font-medium">Makna</span>
            <span className="text-[#CBD5E1]">{brand.meaning}</span>
          </>
        )}
        {brand.philosophy && (
          <>
            <span className="text-[#64748B] text-xs uppercase tracking-wider font-medium">Filosofi</span>
            <span className="text-[#CBD5E1]">{brand.philosophy}</span>
          </>
        )}
        {brand.target_market && (
          <>
            <span className="text-[#64748B] text-xs uppercase tracking-wider font-medium">Target</span>
            <span className="text-[#CBD5E1]">{brand.target_market}</span>
          </>
        )}
        {brand.positioning && (
          <>
            <span className="text-[#64748B] text-xs uppercase tracking-wider font-medium">Positioning</span>
            <span className="text-[#CBD5E1]">{brand.positioning}</span>
          </>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 mb-4">
        <button onClick={handleSvg} className="btn-ghost flex-1 text-xs">
          <IconCheck size={14} className="inline mr-1" />
          SVG
        </button>
        <select
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          className="input-field text-xs w-auto px-2 py-1.5"
        >
          {STYLE_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button
          onClick={handleAi}
          disabled={loading}
          className="btn-primary flex-1 text-xs"
        >
          <IconSparkle size={14} className="inline mr-1" />
          {loading ? 'Memproses...' : 'AI Logo'}
        </button>
      </div>

      {aiError && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/20 text-[#FCA5A5] text-xs">
          {aiError}
        </div>
      )}

      {/* Preview */}
      {svg && (
        <div className="flex justify-center p-4 mb-2 rounded-lg bg-[#0F172A]/50 border border-[#334155]">
          <div dangerouslySetInnerHTML={{ __html: svg }} style={{ width: 150, height: 150 }} />
        </div>
      )}
      {aiImage && (
        <div className="flex justify-center p-4 mb-2 rounded-lg bg-[#0F172A]/50 border border-[#334155]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={aiImage} alt={`${brand.name} logo`} className="max-w-[150px] max-h-[150px]" />
        </div>
      )}
    </div>
  )
}
