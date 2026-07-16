import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'BizComp AI',
  description: 'Navigasi Arah Bisnis, Kuasai Peta Persaingan.',
  icons: { icon: '/favicon.svg' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
