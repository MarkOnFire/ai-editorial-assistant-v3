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
        // PBS Wisconsin brand colors
        'pbs-blue': '#1d4f91',
        'pbs-red': '#c8102e',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
