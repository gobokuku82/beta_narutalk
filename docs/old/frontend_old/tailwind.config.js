/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors
        'luminous-blue': 'var(--color-luminous-blue)',
        'amore-blue': 'var(--color-amore-blue)',
        'pacific-blue': 'var(--color-pacific-blue)',

        // Semantic colors
        'accent': 'var(--accent)',
        'foreground': 'var(--foreground)',
        'background': 'var(--background)',
        'card': 'var(--card)',
        'border': 'var(--border)',
        'muted': 'var(--muted)',
        'muted-foreground': 'var(--muted-foreground)',

        // Channel colors
        'naver': 'var(--channel-naver)',
        'kakao': 'var(--channel-kakao)',
        'meta': 'var(--channel-meta)',
        'google': 'var(--channel-google)',

        // Semantic colors for UI states
        'success': 'var(--color-success)',
        'success-bg': 'var(--color-success-bg)',
        'success-dark': 'var(--color-success-dark)',
        'warning': 'var(--color-warning)',
        'warning-bg': 'var(--color-warning-bg)',
        'warning-dark': 'var(--color-warning-dark)',
        'danger': 'var(--color-danger)',
        'danger-bg': 'var(--color-danger-bg)',
        'danger-dark': 'var(--color-danger-dark)',
        'info': 'var(--color-info)',
        'info-bg': 'var(--color-info-bg)',
      },
      borderColor: {
        'success': 'var(--color-success)',
        'success-dark': 'var(--color-success-dark)',
        'warning': 'var(--color-warning)',
        'warning-dark': 'var(--color-warning-dark)',
        'danger': 'var(--color-danger)',
        'danger-dark': 'var(--color-danger-dark)',
        'info': 'var(--color-info)',
        'accent': 'var(--accent)',
      },
      backgroundColor: {
        'success': 'var(--color-success)',
        'success-bg': 'var(--color-success-bg)',
        'success-dark': 'var(--color-success-dark)',
        'warning': 'var(--color-warning)',
        'warning-bg': 'var(--color-warning-bg)',
        'warning-dark': 'var(--color-warning-dark)',
        'danger': 'var(--color-danger)',
        'danger-bg': 'var(--color-danger-bg)',
        'danger-dark': 'var(--color-danger-dark)',
        'info': 'var(--color-info)',
        'info-bg': 'var(--color-info-bg)',
        'accent': 'var(--accent)',
      },
      textColor: {
        'success': 'var(--color-success)',
        'success-dark': 'var(--color-success-dark)',
        'warning': 'var(--color-warning)',
        'warning-dark': 'var(--color-warning-dark)',
        'danger': 'var(--color-danger)',
        'danger-dark': 'var(--color-danger-dark)',
        'info': 'var(--color-info)',
        'accent': 'var(--accent)',
      },
      ringColor: {
        'accent': 'var(--accent)',
        'success': 'var(--color-success)',
        'warning': 'var(--color-warning)',
        'danger': 'var(--color-danger)',
      }
    },
  },
  plugins: [],
}