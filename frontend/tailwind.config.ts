import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#0F172A',
          50: '#1E293B',
          100: '#334155',
          200: '#475569',
          300: '#64748B',
          400: '#94A3B8',
          500: '#CBD5E1',
        },
        accent: {
          DEFAULT: '#F58A2A',
          dark: '#E07A1F',
          glow: '#FED16A',
        },
        warm: {
          DEFAULT: '#FED16A',
          dark: '#D4A845',
          glow: '#FFF4A4',
        },
        success: {
          DEFAULT: '#F58A2A',
          dark: '#E07A1F',
          glow: '#FED16A',
        },
        danger: {
          DEFAULT: '#EF4444',
          dark: '#DC2626',
          glow: '#FCA5A5',
        },
        cream: '#FAF7F2',
        navy: {
          DEFAULT: '#1E3557',
          light: '#2A4A6E',
        },
        orange: {
          DEFAULT: '#F58A2A',
          hover: '#E07A1F',
        },
        'surface-white': '#FFFFFF',
        'border-light': '#E8E4DC',
        'text-muted': '#667085',
      },
      animation: {
        shimmer: 'shimmer 2s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'gradient-x': 'gradientX 3s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(249, 122, 0, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(249, 122, 0, 0.6)' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      backgroundImage: {
        'gradient-accent': 'linear-gradient(135deg, #386641, #F97A00)',
        'gradient-warm': 'linear-gradient(135deg, #FED16A, #FFF4A4)',
        'gradient-success': 'linear-gradient(135deg, #386641, #F97A00)',
        'gradient-glass': 'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      },
    },
  },
  plugins: [],
}
export default config
