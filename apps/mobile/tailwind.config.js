/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        'bg-deep': '#0D1210',
        'bg-surface': '#151E1A',
        'bg-raised': '#1C2923',

        'accent-moss': '#36664A',
        'accent-olive': '#6F8B57',
        'accent-gold': '#D4A854',
        'accent-clay': '#C9604A',

        'text-primary': '#F0EDE6',
        'text-secondary': '#9B978E',
        'text-tertiary': '#5C5850',

        'border-subtle': '#252E28',
        'border-accent': 'rgba(54, 102, 74, 0.20)',
      },
      fontFamily: {
        display: ['CormorantGaramond_700Bold'],
        'display-semi': ['CormorantGaramond_600SemiBold'],
        sans: ['DMSans_400Regular'],
        'sans-medium': ['DMSans_500Medium'],
        'sans-semibold': ['DMSans_600SemiBold'],
        mono: ['IBMPlexMono_400Regular'],
        'mono-medium': ['IBMPlexMono_500Medium'],
      },
      borderRadius: {
        xl: '20px',
        '2xl': '24px',
        '3xl': '28px',
      },
      boxShadow: {
        moss: '0 16px 28px rgba(54, 102, 74, 0.22)',
        gold: '0 12px 24px rgba(212, 168, 84, 0.18)',
      },
    },
  },
  plugins: [],
}
