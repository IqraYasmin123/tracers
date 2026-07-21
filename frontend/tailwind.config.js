/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        void: '#0B0E14',
        panel: '#12151D',
        hairline: '#232733',
        ink: '#E6E8EC',
        muted: '#8B93A3',
        cyan: {
          DEFAULT: '#3DD6C4',
          dim: '#2A9E92',
        },
        verdict: {
          clean: '#5FD98A',
          adversarial: '#E85C4A',
          warning: '#E8A83D',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      animation: {
        scanline: 'scanline 2s linear infinite',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
    },
  },
  plugins: [],
}
