/** @type {import('tailwindcss').Config} */
module.exports = {
//   content: [
//     "./src/**/*.{html,ts}",
//   ],
//   theme: {
//     extend: {},
//   },
//   plugins: [],
// }

// export default {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#020617',
        surface: '#0f172a',
        card: '#1e293b',

        primary: '#22d3ee',
        primaryHover: '#06b6d4',

        textPrimary: '#e5e7eb',
        textSecondary: '#94a3b8',

        success: '#22c55e',
        danger: '#ef4444',
      }
    },
  },
  plugins: [],
}
