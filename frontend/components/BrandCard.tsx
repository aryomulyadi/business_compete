'use client'

import { useState } from 'react'
import type { BrandConcept } from '@/lib/types'
import { api } from '@/lib/api-client'
import { IconSparkle, IconCheck } from './Icons'

interface HistoryLogo {
  id: number
  svg: string
  png_path: string | null
  style: string
  created_at: string
}

interface BrandCardProps {
  brand: BrandConcept
  index: number
  historyRowId?: number
  previousLogos?: HistoryLogo[]
}

const STYLE_OPTIONS = [
  'modern minimalis',
  'klasik elegan',
  'playful kreatif',
  'teknologi futuristik',
  'natural organik',
]

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function BrandCard({ brand, index, historyRowId, previousLogos }: BrandCardProps) {
  const [svg, setSvg] = useState<string | null>(null)
  const [aiImage, setAiImage] = useState<string | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [style, setStyle] = useState(STYLE_OPTIONS[0])

  const handleSvg = async () => {
    try {
      const res = await api.generateSvgLogo(brand.name)
      setSvg(res.svg)
      setAiImage(null)
    } catch {
      setAiError('Gagal generate SVG')
    }
  }

  const handleAi = async () => {
    setLoading(true)
    setAiError(null)
    try {
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
      if (res.error) {
        setAiError(res.error)
      } else if (res.image_base64) {
        setAiImage(`data:image/png;base64,${res.image_base64}`)
        setSvg(null)
      } else if (res.svg) {
        setSvg(res.svg)
        setAiImage(null)
      }
    } catch (err) {
      setAiError(err instanceof Error ? err.message : 'Gagal menghubungi server')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (aiImage) {
      const resp = await fetch(aiImage)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${brand.name}.png`
      a.click()
      URL.revokeObjectURL(url)
    } else if (svg) {
      const blob = new Blob([svg], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${brand.name}.svg`
      a.click()
      URL.revokeObjectURL(url)
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
        {previousLogos && previousLogos.length > 0 && (
          <span className="ml-auto text-[#64748B] text-xs">{previousLogos.length} logo{previousLogos.length > 1 ? 's' : ''}</span>
        )}
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

      {/* History thumbnails */}
      {previousLogos && previousLogos.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {previousLogos.slice(0, 6).map((logo) => (
            <div
              key={logo.id}
              className="w-10 h-10 rounded-lg bg-[#0F172A]/50 border border-[#334155] flex items-center justify-center overflow-hidden cursor-pointer hover:border-[#F58A2A]/50 transition-colors"
              title={`${logo.style} — ${new Date(logo.created_at).toLocaleString('id')}`}
            >
              {logo.png_path ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`${API_URL}/api/branding/logo/files/${logo.png_path}`}
                  alt=""
                  className="w-full h-full object-contain"
                />
              ) : logo.svg ? (
                <div dangerouslySetInnerHTML={{ __html: logo.svg }} className="w-8 h-8" />
              ) : null}
            </div>
          ))}
        </div>
      )}

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
      {loading && (
        <div className="flex justify-center p-4 mb-2 rounded-lg bg-[#0F172A]/50 border border-[#334155]">
          <div className="w-[150px] h-[150px] shimmer rounded-lg" />
        </div>
      )}
      {(svg || aiImage) && (
        <div className="flex justify-center p-4 mb-2 rounded-lg bg-[#0F172A]/50 border border-[#334155] relative group">
          {svg && <div dangerouslySetInnerHTML={{ __html: svg }} style={{ width: 150, height: 150 }} />}
          {aiImage && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={aiImage}
              alt={`${brand.name} logo`}
              className="max-w-[150px] max-h-[150px]"
              onError={() => setAiError('Gagal memuat gambar logo')}
            />
          )}
          <button
            onClick={handleDownload}
            className="absolute top-1 right-1 w-7 h-7 rounded-md bg-[#1E293B]/80 border border-[#334155] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-[#F58A2A]/20"
            title="Download logo"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7,10 12,15 17,10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}
