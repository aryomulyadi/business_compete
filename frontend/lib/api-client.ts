import type { BrandConcept, HistoryItem, HistoryListResponse, ReportData, TaskProgress, BrandedReportsResponse } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status}: ${body || res.statusText}`)
  }
  return res.json()
}

export const api = {
  // Analysis
  startAnalysis(businessField: string): Promise<{ task_id: string; field: string }> {
    return request('/api/analysis/start', {
      method: 'POST',
      body: JSON.stringify({ business_field: businessField }),
    })
  },

  getTaskStatus(taskId: string): Promise<TaskProgress> {
    return request(`/api/analysis/status/${taskId}`)
  },

  // Reports
  getReport(rowId: number): Promise<ReportData> {
    return request(`/api/reports/${rowId}`)
  },

  getExportUrl(rowId: number, fmt: 'md' | 'html' | 'pdf'): string {
    return `${API_URL}/api/reports/${rowId}/export/${fmt}`
  },

  getBrandConcepts(rowId: number): Promise<{ concepts: BrandConcept[]; names: string[] }> {
    return request(`/api/reports/${rowId}/branding/concepts`, { method: 'POST' })
  },

  // Branding
  getStyles(): Promise<{ styles: string[] }> {
    return request('/api/branding/styles')
  },

  getBrandedReports(offset = 0, limit = 20): Promise<BrandedReportsResponse> {
    return request(`/api/branding/concepts?offset=${offset}&limit=${limit}`)
  },

  generateSvgLogo(brandName: string, size?: number): Promise<{ svg: string; brand_name: string }> {
    return request('/api/branding/logo/svg', {
      method: 'POST',
      body: JSON.stringify({ brand_name: brandName, size: size || 200 }),
    })
  },

  async generateAiLogo(
    brandName: string,
    concept?: Record<string, string>,
    style?: string,
    historyRowId?: number
  ): Promise<{ image_base64: string | null; error: string | null }> {
    return request('/api/branding/logo/ai', {
      method: 'POST',
      body: JSON.stringify({
        brand_name: brandName,
        concept,
        style: style || 'modern minimalis',
        history_row_id: historyRowId,
      }),
    })
  },

  getLogoHistory(historyRowId: number): Promise<{ logos: any[] }> {
    return request(`/api/branding/logo/history/${historyRowId}`)
  },

  // History
  getHistory(search?: string, offset?: number, limit?: number): Promise<HistoryListResponse> {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (offset) params.set('offset', String(offset))
    if (limit) params.set('limit', String(limit))
    return request(`/api/history?${params}`)
  },

  getHistoryItem(rowId: number): Promise<HistoryItem> {
    return request(`/api/history/${rowId}`)
  },

  // Health
  health(): Promise<{ status: string; service: string }> {
    return request('/api/health')
  },
}
