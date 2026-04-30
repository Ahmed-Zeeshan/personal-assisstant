/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{astro,html,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b0d10',
        surface: '#13161b',
        border: '#1f242c',
        fg: '#e6e8eb',
        muted: '#9aa3ad',
        dim: '#7d8590',
        accent: '#9580ff',
        success: '#34d399',
        warn: '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'h1-fluid': ['clamp(2.5rem, 6vw, 4.5rem)', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        'h2-fluid': ['clamp(1.75rem, 3.5vw, 2.5rem)', { lineHeight: '1.15', letterSpacing: '-0.02em' }],
      },
      transitionTimingFunction: { 'enter': 'cubic-bezier(0.2, 0.8, 0.2, 1)' },
      maxWidth: { 'content': '1200px', 'prose-narrow': '720px' },
    },
  },
  plugins: [],
};
