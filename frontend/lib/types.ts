export interface BrandConcept {
  name: string
  meaning?: string
  philosophy?: string
  target_market?: string
  positioning?: string
  personality?: string[]
  visual_direction?: string
  color_palette?: string[]
}

export interface HistoryItem {
  id: number
  field: string
  status: 'running' | 'completed' | 'failed'
  created_at: string
  report_path: string | null
  error: string | null
}

export interface LogoItem {
  id: number
  history_row_id: number
  brand_name: string
  concept: string
  svg: string
  png_path: string | null
  style: string
  created_at: string
}

export interface TaskProgress {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  field: string
  current_agent: string | null
  completed_tasks: string[]
  pct: number
  error: string | null
  row_id: number | null
  report_path: string | null
}

export interface ReportData {
  id: number
  field: string
  status: string
  created_at: string
  content: string
}

export interface HistoryListResponse {
  items: HistoryItem[]
  offset: number
  limit: number
  total: number
}

export interface BrandedReport {
  row_id: number
  field: string
  created_at: string
  brand_names: string[]
}

export interface BrandedReportsResponse {
  reports: BrandedReport[]
  offset: number
  limit: number
  total: number
}
