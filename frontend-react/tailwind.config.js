/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        slate: {
          800: '#1e293b',
          850: '#151e2e',
          900: '#0f172a',
          950: '#020617',
        },
        neon: {
          purple: '#a78bfa',
          blue: '#60a5fa',
          cyan: '#22d3ee',
          green: '#34d399',
          yellow: '#fbbf24',
          rose: '#f87171',
        }
      },
      animation: {
        // 核心入场动画 - 急起缓停的物理质感
        'enter': 'enter-keyframe 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in-up': 'fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'aurora': 'aurora 20s linear infinite',
        'shimmer': 'shimmer 8s infinite linear',
        // 卡片悬浮效果
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        // 核心入场动画：上浮 + 放大 + 渐现
        'enter-keyframe': {
          '0%': { 
            opacity: '0', 
            transform: 'translateY(20px) scale(0.98)' 
          },
          '100%': { 
            opacity: '1', 
            transform: 'translateY(0) scale(1)' 
          },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px) scale(0.98)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        aurora: {
          '0%': { transform: 'rotate(0deg) scale(1)' },
          '50%': { transform: 'rotate(180deg) scale(1.1)' },
          '100%': { transform: 'rotate(360deg) scale(1)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-150%) skewX(-15deg)' },
          '50%': { transform: 'translateX(-150%) skewX(-15deg)' },
          '100%': { transform: 'translateX(250%) skewX(-15deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      }
    },
  },
  plugins: [
    // 自定义插件生成 stagger 错峰延迟类
    function({ addUtilities }) {
      const staggerUtilities = {
        '.stagger-1': { 'animation-delay': '50ms' },
        '.stagger-2': { 'animation-delay': '100ms' },
        '.stagger-3': { 'animation-delay': '150ms' },
        '.stagger-4': { 'animation-delay': '200ms' },
        '.stagger-5': { 'animation-delay': '250ms' },
        '.stagger-6': { 'animation-delay': '300ms' },
        '.stagger-7': { 'animation-delay': '350ms' },
        '.stagger-8': { 'animation-delay': '400ms' },
        // 初始状态：隐藏，等待动画触发
        '.animate-ready': { 
          'opacity': '0',
          'transform': 'translateY(20px) scale(0.98)'
        },
      }
      addUtilities(staggerUtilities)
    }
  ],
}
