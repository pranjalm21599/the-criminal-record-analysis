export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          bg: '#0A0E14',
          surface: '#10161F',
          raised: '#151C27',
          border: '#1E2733',
          borderLight: '#2A3644',
        },
        signal: {
          DEFAULT: '#4C9AFF',
          dim: '#2B5A96',
        },
        risk: {
          critical: '#E5484D',
          high: '#F5A623',
          medium: '#F2C94C',
          low: '#27C93F',
        },
        ink: {
          primary: '#E4E9F0',
          muted: '#8A94A3',
          faint: '#4E5866',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      keyframes: {
        pulse_ring: {
          '0%': { transform: 'scale(0.9)', opacity: '0.8' },
          '80%, 100%': { transform: 'scale(1.6)', opacity: '0' },
        },
        scan: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '0 40px' },
        }
      },
      animation: {
        pulse_ring: 'pulse_ring 2s cubic-bezier(0.2,0.6,0.4,1) infinite',
      }
    },
  },
  plugins: [],
}
