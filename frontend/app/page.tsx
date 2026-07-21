import Link from 'next/link'

const FEATURES = [
  {
    title: 'Analisis SWOT',
    desc: 'Kekuatan, kelemahan, peluang, dan ancaman kompetitor bisnis Anda.',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F58A2A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/>
      </svg>
    ),
  },
  {
    title: 'Five Forces Porter',
    desc: 'Daya tawar pemasok & pembeli, ancaman pendatang baru & substitusi, rivalitas industri.',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F58A2A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
      </svg>
    ),
  },
  {
    title: 'PESTEL',
    desc: 'Pengaruh Politik, Ekonomi, Sosial, Teknologi, Lingkungan, dan Hukum terhadap bisnis.',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F58A2A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
      </svg>
    ),
  },
  {
    title: 'Branding & Logo AI',
    desc: 'Rekomendasi nama brand, filosofi, kepribadian, hingga generate logo berbasis AI.',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F58A2A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/><circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.52-4.5-10-10-10z"/>
      </svg>
    ),
  },
]

const STEPS = [
  { num: '01', title: 'Masukkan Bidang Bisnis', desc: 'Tentukan industri atau niche yang ingin dianalisis. Cukup 1 kalimat.' },
  { num: '02', title: 'AI Menganalisis', desc: 'Crew agen AI bekerja secara paralel — riset pasar, kompetitor, hingga strategi.' },
  { num: '03', title: 'Dapatkan Laporan', desc: 'Laporan lengkap + rekomendasi brand siap diunduh dalam MD, HTML, atau PDF.' },
]

const SECTIONS = [
  { label: 'SWOT',        pct: 80, color: '#F58A2A', icon: '📊' },
  { label: 'Five Forces', pct: 60, color: '#F58A2A', icon: '⚔️' },
  { label: 'PESTEL',      pct: 45, color: '#1E3557', icon: '🌍' },
  { label: 'Branding',    pct: 25, color: '#FED16A', icon: '🎨' },
]

function ReportPreviewGrid() {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-[#E8E4DC] p-6 max-w-lg w-full">
      <div className="flex items-center gap-2 mb-6">
        <div className="w-2.5 h-2.5 rounded-full bg-[#F58A2A]" />
        <span className="text-sm font-semibold text-[#1E3557]">Analisis Berjalan</span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {SECTIONS.map((s) => (
          <div key={s.label} className="bg-[#FAF7F2] rounded-xl p-4 min-h-[110px]">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{s.icon}</span>
              <span className="text-xs font-bold text-[#1E3557] uppercase tracking-wider">{s.label}</span>
            </div>
            <div className="h-2 bg-[#E8E4DC] rounded-full overflow-hidden mb-2">
              <div className="h-full rounded-full transition-all" style={{ width: `${s.pct}%`, background: s.color }} />
            </div>
            <span className="text-[11px] font-semibold" style={{ color: s.color }}>{s.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#FAF7F2] font-sans">
      {/* Nav */}
      <nav className="bg-white border-b border-[#E8E4DC]">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-1.5">
            <span className="text-lg font-bold text-[#1E3557] tracking-tight font-heading">BizComp</span>
            <span className="text-xs text-[#667085] font-medium">AI</span>
          </div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-[#F58A2A] text-white text-sm font-semibold hover:bg-[#E07A1F] transition-all duration-200 shadow-sm"
          >
            Mulai
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-20 md:pt-20 md:pb-24">
        <div className="flex flex-col md:flex-row items-center gap-12 md:gap-16">
          <div className="flex-[1]">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[#1E3557] leading-[1.1] tracking-tight font-heading mb-5">
              Navigasi Arah Bisnis,<br />
              <span className="text-[#F58A2A]">Kuasai Peta Persaingan.</span>
            </h1>
            <p className="text-base md:text-lg text-[#667085] max-w-md leading-relaxed mb-8">
              Analisis kompetitor berbasis AI — SWOT, Five Forces, PESTEL, dan strategi brand dalam satu laporan otomatis.
            </p>
            <div className="flex items-center gap-3 mb-8">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#F58A2A] text-white font-semibold text-sm hover:bg-[#E07A1F] transition-all duration-200 shadow-md shadow-[#F58A2A]/20"
              >
                Mulai Analisis Sekarang
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </Link>
            </div>
          </div>

          <div className="flex-[1.3] flex justify-center md:justify-center">
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-br from-[#F58A2A]/10 via-transparent to-[#1E3557]/5 rounded-3xl blur-2xl" />
              <ReportPreviewGrid />
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white">
        <div className="max-w-6xl mx-auto px-6 py-20 md:py-24">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E3557] font-heading mb-3">
              Analisis Mendalam,<br className="md:hidden" /> Satu Platform
            </h2>
            <p className="text-[#667085] max-w-md mx-auto">
              Empat kerangka analisis terintegrasi untuk melihat bisnis dari semua sisi.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-2xl border border-[#E8E4DC] p-6 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200"
              >
                <div className="w-10 h-10 rounded-xl bg-[#F58A2A]/10 flex items-center justify-center mb-4">
                  {f.icon}
                </div>
                <h3 className="text-lg font-semibold text-[#1E3557] mb-1.5 font-heading">{f.title}</h3>
                <p className="text-sm text-[#667085] leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Steps */}
      <section className="bg-[#FAF7F2]">
        <div className="max-w-4xl mx-auto px-6 py-20 md:py-24">
          <h2 className="text-3xl md:text-4xl font-bold text-[#1E3557] text-center font-heading mb-14">
            Cara Kerja
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((s) => (
              <div key={s.num} className="text-center">
                <div className="text-4xl font-bold text-[#F58A2A]/30 font-heading mb-3">{s.num}</div>
                <h3 className="text-lg font-semibold text-[#1E3557] mb-2 font-heading">{s.title}</h3>
                <p className="text-sm text-[#667085] leading-relaxed max-w-xs mx-auto">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-white">
        <div className="max-w-2xl mx-auto px-6 py-20 md:py-24 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-[#1E3557] font-heading mb-3">
            Siap Menganalisis Bisnis Anda?
          </h2>
          <p className="text-[#667085] mb-8">
            Masukkan bidang bisnis Anda dan dapatkan hasilnya dalam hitungan menit.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-[#F58A2A] text-white font-semibold text-sm hover:bg-[#E07A1F] transition-all duration-200 shadow-md shadow-[#F58A2A]/20"
          >
            Mulai Sekarang
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#E8E4DC] bg-[#FAF7F2]">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-bold text-[#1E3557] font-heading">BizComp</span>
            <span className="text-[10px] text-[#667085]">AI</span>
          </div>
          <p className="text-xs text-[#667085]">&copy; 2026 BizComp AI</p>
        </div>
      </footer>
    </div>
  )
}
