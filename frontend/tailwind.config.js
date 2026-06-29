/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: '#0b1020', mute: '#8a93ad', brand: '#6366f1',
        up: '#16a34a', down: '#dc2626', canvas: '#f6f7fb',
      },
    },
  },
  plugins: [],
}
