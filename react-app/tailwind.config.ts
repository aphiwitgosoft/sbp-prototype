import type { Config } from 'tailwindcss';

/**
 * Design tokens ported จาก assets/sbp.css :root
 * ใช้ชื่อ semantic เดียวกับ prototype เดิม (primary / ink / muted / line ฯลฯ)
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2f6fed',
          dark: '#1f5ad6',
          soft: '#eaf2ff',
        },
        brandteal: '#15b6a6',
        ink: '#2b3440',
        muted: '#7c8794',
        line: '#e4ebf3',
        appbg: '#eef4fc',
        card: '#ffffff',
        thbg: '#d8e8fb',
        think: '#2c5488',
        sidebar: '#eef5fe',
        danger: '#ef4444',
        success: '#16a34a',
        warn: '#f59e0b',
        seven: {
          green: '#00803d',
          orange: '#f47b20',
          red: '#e1251b',
        },
      },
      fontFamily: {
        sans: ['Prompt', 'Sarabun', 'Segoe UI', 'sans-serif'],
        num: ['Sarabun', 'Prompt', 'sans-serif'],
      },
      borderRadius: {
        card: '14px',
      },
      boxShadow: {
        card: '0 6px 20px rgba(31,72,104,.07)',
      },
      spacing: {
        header: '64px',
        sidebar: '258px',
      },
      keyframes: {
        growBar: {
          '0%': { transform: 'scaleY(0)' },
          '100%': { transform: 'scaleY(1)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        growBar: 'growBar .9s cubic-bezier(.2,.7,.2,1) forwards',
        fadeInUp: 'fadeInUp .4s ease forwards',
      },
    },
  },
  plugins: [],
} satisfies Config;
