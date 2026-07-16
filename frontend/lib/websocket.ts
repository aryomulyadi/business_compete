import type { TaskProgress } from './types'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function connectProgressWs(
  taskId: string,
  onProgress: (data: TaskProgress) => void,
  onError?: (err: Event) => void,
  onClose?: () => void
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/api/analysis/ws/progress/${taskId}`)

  ws.onmessage = (event) => {
    try {
      const data: TaskProgress = JSON.parse(event.data)
      onProgress(data)
    } catch {
      /* ignore parse errors */
    }
  }

  ws.onerror = (err) => onError?.(err)
  ws.onclose = () => onClose?.()

  return ws
}
