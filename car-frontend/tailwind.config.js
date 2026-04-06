/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        accent: {
          blue: '#3B82F6',
          orange: '#F97316',
          glow: '#60A5FA',
        },
        surface: {
          900: '#0A0A0A',
          800: '#111111',
          700: '#1C1C1E',
          600: '#2C2C2E',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(59,130,246,0.3)',
        'glow-orange': '0 0 20px rgba(249,115,22,0.3)',
      },
    },
  },
  plugins: [],
};
