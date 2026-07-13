/** @type {import('tailwindcss').Config} */
const config = {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      fontFamily: {
        // 'Pretendard Variable' 우선(가변 빌드 — 300/500 weight) → 정적 Pretendard 폴백(룩 동일).
        sans: ['Pretendard Variable', 'Pretendard', 'system-ui', '-apple-system', 'sans-serif'],
        // Meta display 페이스 — 한글 안전 위해 Pretendard 단일(메트릭 불일치 0). DESIGN-meta-적용계획 §4.1.
        display: ['Pretendard Variable', 'Pretendard', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      fontSize: {
        // TYPOGRAPHY.md §2 — text-2xs 신설 (10px), 이전 임의값 text-[9/10/11px] 통일 대체
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
        // Meta 타입 스케일 (DESIGN-meta-적용계획 §4.2) — ADD-only, 기존 text-* 불변.
        // letterSpacing 은 em(크기 비례), 한글 보호 위해 본문은 거의 0(§4.4 D7).
        hero: ['clamp(2.5rem,5vw,4rem)', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '500' }],
        'display-lg': ['3rem', { lineHeight: '1.08', letterSpacing: '-0.02em', fontWeight: '500' }],
        'heading-lg': ['2.25rem', { lineHeight: '1.15', letterSpacing: '-0.01em', fontWeight: '500' }],
        'heading-md': ['1.75rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '300' }],
        'heading-sm': ['1.5rem', { lineHeight: '1.25', letterSpacing: '-0.005em', fontWeight: '500' }],
        'body-md': ['1rem', { lineHeight: '1.5', letterSpacing: '-0.005em' }],
        'body-sm': ['0.875rem', { lineHeight: '1.43', letterSpacing: '0' }],
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        // ── Meta 적용 P1 (DESIGN-meta-적용계획 §3) — ADD-only, warm 미사용 ──
        'surface-soft': 'hsl(var(--surface-soft))',
        'hairline-soft': 'hsl(var(--hairline-soft))',
        // 잉크 6단 ramp (cool). ⚠ stone 은 텍스트 금지(대비 3.07) — 아이콘/장식 전용.
        'ink-deep': 'hsl(var(--ink-deep))',
        charcoal: 'hsl(var(--charcoal))',
        slate: 'hsl(var(--slate))',
        steel: 'hsl(var(--steel))',
        stone: 'hsl(var(--stone))',
        // 코발트 액션 액센트 (Meta 1차 액션). ⚠ soft 는 텍스트/링크 금지(대비 3.23).
        'accent-action': {
          DEFAULT: 'hsl(var(--accent-action))',
          deep: 'hsl(var(--accent-action-deep))',
          soft: 'hsl(var(--accent-action-soft))',
          foreground: 'hsl(var(--accent-action-foreground))',
        },
        // 4번째 시맨틱 — attention (foreground=dark ink).
        attention: {
          DEFAULT: 'hsl(var(--attention))',
          foreground: 'hsl(var(--attention-foreground))',
        },
        // 매체별 컬러
        channel: {
          naver: 'hsl(var(--channel-naver))',
          kakao: 'hsl(var(--channel-kakao))',
          meta: 'hsl(var(--channel-meta))',
          google: 'hsl(var(--channel-google))',
        },
        // 차트 팔레트
        chart: {
          1: 'hsl(var(--chart-1))',
          2: 'hsl(var(--chart-2))',
          3: 'hsl(var(--chart-3))',
          4: 'hsl(var(--chart-4))',
          5: 'hsl(var(--chart-5))',
        },
        // 의미적 토큰 — Workflow Canvas (spec 62 §4.1)
        node: {
          task: 'hsl(var(--node-task))',
          branch: 'hsl(var(--node-branch))',
          start: 'hsl(var(--node-start))',
          end: 'hsl(var(--node-end))',
          running: 'hsl(var(--node-running))',
          completed: 'hsl(var(--node-completed))',
          failed: 'hsl(var(--node-failed))',
          invalidated: 'hsl(var(--node-invalidated))',
        },
        edge: {
          DEFAULT: 'hsl(var(--edge-default))',
          invalidated: 'hsl(var(--edge-invalidated))',
        },
      },
      // ── Meta 전역 radius 스케일 (2026-06-20 재구축) — stock 키를 Meta 값으로 재정의.
      // 앱 전체 stock rounded-md/lg/xl 이 손 안 대도 Meta-둥글게 (lg 8→16 등). 시맨틱 키는 static Meta.
      borderRadius: {
        none: '0px',
        xs: '2px',
        sm: '6px',
        md: '10px',
        lg: '16px',   // 일반 카드/컨테이너 (warm 8 → 16)
        xl: '24px',
        '2xl': '32px',
        '3xl': '40px',
        full: '9999px',
        // 시맨틱 구조 토큰 (static Meta)
        button: '9999px',  // pill
        card: '32px',      // 쇼케이스 카드
        input: '10px',
        control: '9999px', // 칩/배지 pill
        panel: '24px',     // dialog/sheet/메뉴
        // 별칭
        xxl: '24px',
        xxxl: '32px',
        feature: '40px',
        circle: '9999px',
      },
      // ── Meta 적용 P1 — 대형 섹션 리듬 (ADD-only, SPACING.md 4px 그리드 유지) ──
      spacing: {
        section: '4rem',       // 64
        'section-lg': '5rem',  // 80
        hero: '7.5rem',        // 120
      },
      // ── Meta 그림자 — flat 기본. E2 린트(shadow-xl/2xl)와 무관 ──
      boxShadow: {
        card: 'none',                  // Meta 카드 = flat
        panel: 'var(--shadow-panel)',  // commerce sticky 패널 (light/dark 다름)
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'pulse-soft': 'pulse-soft 1.5s ease-in-out infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

module.exports = config;
