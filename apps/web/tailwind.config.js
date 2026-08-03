/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0b0f1a',
          card: '#141a2b',
          muted: '#1e2740',
        },
        accent: {
          DEFAULT: '#5b8cff',
          soft: '#2a3c6e',
        },
        ok: '#2fd47b',
        warn: '#f5b544',
        danger: '#f2555a',
      },
      borderRadius: { xl2: '1.25rem' },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
