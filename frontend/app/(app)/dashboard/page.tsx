'use client'

import { useState, useRef, useCallback } from 'react'
import { api } from '@/lib/api-client'
import { connectProgressWs } from '@/lib/websocket'
import ProgressBar from '@/components/ProgressBar'
import { IconSparkle, IconSearch, IconChevronRight } from '@/components/Icons'
import type { TaskProgress } from '@/lib/types'

export default function DashboardPage() {
  const [field, setField] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [rowId, setRowId] = useState<number | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const startAnalysis = useCallback(async () => {
    const trimmed = field.trim()
    if (!trimmed || trimmed.length < 10) {
      setError('Bidang bisnis terlalu pendek (min. 10 karakter)')
      return
    }

    setLoading(true)
    setError(null)
    setProgress(null)
    setRowId(null)

    try {
      const { task_id } = await api.startAnalysis(trimmed)

      const ws = connectProgressWs(
        task_id,
        (data) => {
          setProgress(data)
          if (data.status === 'completed' && data.row_id) {
            setRowId(data.row_id)
            ws.close()
          }
          if (data.status === 'failed') {
            setError(data.error || 'Analisis gagal')
            ws.close()
          }
        },
        () => setError('Koneksi gagal — server tidak merespon')
      )

      wsRef.current = ws
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [field])

  return (
    <div className="animate-fade-in">
      <div className="mb-10">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-3 bg-gradient-to-r from-[#F58A2A] via-[#FED16A] to-[#FFF4A4] bg-clip-text text-transparent bg-[length:200%_100%] animate-gradient-x">
          BizComp AI
        </h1>
        <p className="text-[#94A3B8] text-base max-w-xl">
          Navigasi Arah Bisnis, Kuasai Peta Persaingan.
        </p>
      </div>

      <div className="card p-5 md:p-6 mb-6">
        <label className="block text-sm font-medium text-[#CBD5E1] mb-3">
          Bidang bisnis yang ingin dianalisis
        </label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <IconSearch size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#64748B]" />
            <input
              type="text"
              value={field}
              onChange={(e) => setField(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && startAnalysis()}
              placeholder="Contoh: E-commerce Fesyen, SaaS HR, Fintech Indonesia"
              className="input-field pl-10"
              disabled={loading || (progress?.status === 'running')}
            />
          </div>
          <button
            onClick={startAnalysis}
            disabled={loading || !field.trim() || (progress?.status === 'running')}
            className="btn-primary flex items-center gap-2"
          >
            <IconSparkle size={16} />
            Analisis Sekarang
          </button>
        </div>
        {error && (
          <div className="mt-3 px-4 py-2.5 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/20 text-[#FCA5A5] text-sm">
            {error}
          </div>
        )}
      </div>

      {progress && progress.status === 'running' && (
        <div className="mb-6">
          <ProgressBar progress={progress} />
        </div>
      )}

      {loading && !progress && (
        <div className="space-y-4 animate-fade-in">
          <div className="card p-4">
            <div className="flex items-center gap-3 text-sm text-[#94A3B8]">
              <div className="w-4 h-4               border-2 border-[#F58A2A] border-t-transparent rounded-full animate-spin" />
              Menyiapkan analisis...
            </div>
          </div>
        </div>
      )}

      {rowId && (
        <div className="card p-5 border-[#F58A2A]/30 animate-slide-up">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[#F58A2A] font-semibold text-sm">Analisis Selesai ✓</p>
              <p className="text-[#64748B] text-xs mt-1">Laporan siap untuk ditinjau</p>
            </div>
            <a
              href={`/report/${rowId}`}
              className="btn-primary flex items-center gap-1.5"
            >
              Lihat Laporan
              <IconChevronRight size={16} />
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
