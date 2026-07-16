import type { TaskProgress } from '@/lib/types'

const AGENT_CONFIG = [
  { name: 'Researcher', desc: 'Mengumpulkan data kompetitor', icon: '🔍' },
  { name: 'Analyst', desc: 'Menganalisis SWOT, Five Forces, PESTEL', icon: '📊' },
  { name: 'Writer', desc: 'Menulis laporan akhir', icon: '✍️' },
]

export default function ProgressBar({ progress }: { progress: TaskProgress }) {
  const completed = new Set(progress.completed_tasks)

  return (
    <div className="card p-5 space-y-5 animate-slide-up">
      {/* Animated gradient bar */}
      <div className="relative h-2 bg-[#1E293B] rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${Math.min(progress.pct, 100)}%`,
            background: 'linear-gradient(90deg, #F58A2A, #FED16A, #F58A2A)',
            backgroundSize: '200% 100%',
            animation: 'gradientX 2s ease-in-out infinite',
          }}
        />
      </div>

      <p className="text-sm text-[#94A3B8] text-center">
        {progress.current_agent
          ? `Menganalisis ${progress.field}...`
          : 'Memulai analisis...'}
      </p>

      {/* Step indicators */}
      <div className="space-y-2">
        {AGENT_CONFIG.map((step) => {
          const done = completed.has(step.name)
          const active = progress.current_agent === step.name

          return (
            <div
              key={step.name}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all duration-300 ${
                done
                  ? 'bg-[#F58A2A]/10 border border-[#F58A2A]/20'
                  : active
                  ? 'bg-[#FED16A]/10 border border-[#FED16A]/20 animate-pulse-glow'
                  : 'bg-[#1E293B]/50 border border-transparent'
              }`}
            >
              {/* Icon */}
              <span className={`text-base ${done ? 'opacity-100' : active ? 'opacity-100' : 'opacity-30'}`}>
                {done ? '✅' : step.icon}
              </span>

              {/* Label */}
              <span
                className={`font-medium ${
                  done ? 'text-[#F58A2A]' : active ? 'text-[#FED16A]' : 'text-[#64748B]'
                }`}
              >
                {step.name}
              </span>

              {/* Status */}
              <span className="ml-auto text-xs">
                {done ? (
                  <span className="text-[#F58A2A]">Selesai</span>
                ) : active ? (
                  <span className="text-[#FED16A]">{step.desc}...</span>
                ) : (
                  <span className="text-[#475569]">Menunggu</span>
                )}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
