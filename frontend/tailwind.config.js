/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#18262B',
        mute: '#5B6B70',
        paper: '#EAEFEA',
        panel: '#F7F9F6',
        rule: '#CBD5CD',
        archive: { DEFAULT: '#0E6A68', dark: '#0A4F4D', soft: '#D6EBE9' },
        marker: '#F5B700',
        danger: '#B3261E',
      },
      fontFamily: {
        sans: ['"Noto Sans Ethiopic"', '"Noto Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Noto Serif Ethiopic"', '"Noto Serif"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};
