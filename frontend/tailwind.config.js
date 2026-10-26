/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#DBEAFE', // Light Blue
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563EB', // Primary Blue
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1E3A8A', // Deep Trust Blue
          950: '#0F172A', // Dark Navy
          trust: '#1E3A8A',
          primary: '#2563EB',
          light: '#DBEAFE',
          navy: '#0F172A',
          bg: '#F8FAFC',
          card: '#FFFFFF',
          muted: '#64748B',
          border: '#E2E8F0',
        },
        alert: {
          healthy: '#16A34A',
          'healthy-light': '#DCFCE7',
          'healthy-border': '#BBF7D0',
          info: '#2563EB',
          'info-light': '#DBEAFE',
          'info-border': '#BFDBFE',
          low: '#EAB308',
          'low-light': '#FEF9C3',
          'low-border': '#FEF08A',
          warning: '#F97316',
          'warning-light': '#FFEDD5',
          'warning-border': '#FED7AA',
          critical: '#DC2626',
          'critical-light': '#FEE2E2',
          'critical-border': '#FECACA',
          ai: '#7C3AED',
          'ai-light': '#EDE9FE',
          'ai-border': '#DDD6FE',
          neutral: '#64748B',
          'neutral-light': '#F1F5F9',
          'neutral-border': '#E2E8F0',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)',
        'card-hover': '0 10px 25px -5px rgba(30, 58, 138, 0.08), 0 8px 10px -6px rgba(30, 58, 138, 0.04)',
        'blue-glow': '0 4px 14px 0 rgba(37, 99, 235, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
