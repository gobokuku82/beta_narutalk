import { createTheme } from '@mui/material/styles';

// 2025 트렌드 컬러 팔레트
const colors = {
  // Pantone 2025 - Mocha Mousse
  mocha: {
    light: '#B08D7A',
    main: '#A67C6D',
    dark: '#8B6355',
  },
  // Digital Lavender
  lavender: {
    light: '#E6DEFF',
    main: '#A78BFA',
    dark: '#8B5CF6',
  },
  // Ethereal Blues
  ethereal: {
    light: '#E0F2FE',
    main: '#7DD3FC',
    dark: '#0EA5E9',
  },
  // Burnt Orange (Accent)
  accent: {
    light: '#FED7AA',
    main: '#FB923C',
    dark: '#EA580C',
  },
  // Neutrals
  neutral: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#E5E5E5',
    300: '#D4D4D4',
    400: '#A3A3A3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
  },
  // Gradient colors
  gradient: {
    start: '#A78BFA',
    middle: '#7DD3FC',
    end: '#FB923C',
  },
};

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      light: colors.lavender.light,
      main: colors.lavender.main,
      dark: colors.lavender.dark,
      contrastText: '#FFFFFF',
    },
    secondary: {
      light: colors.ethereal.light,
      main: colors.ethereal.main,
      dark: colors.ethereal.dark,
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#EF4444',
      light: '#FCA5A5',
      dark: '#DC2626',
    },
    warning: {
      main: colors.accent.main,
      light: colors.accent.light,
      dark: colors.accent.dark,
    },
    success: {
      main: '#10B981',
      light: '#86EFAC',
      dark: '#059669',
    },
    background: {
      default: '#FAFBFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: colors.neutral[900],
      secondary: colors.neutral[600],
    },
  },
  typography: {
    fontFamily: '"Pretendard", "Inter", "Noto Sans KR", -apple-system, BlinkMacSystemFont, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.7,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0,0,0,0.05)',
    '0px 4px 8px rgba(0,0,0,0.05)',
    '0px 8px 16px rgba(0,0,0,0.05)',
    '0px 12px 24px rgba(0,0,0,0.05)',
    '0px 16px 32px rgba(0,0,0,0.05)',
    '0px 20px 40px rgba(0,0,0,0.05)',
    '0px 24px 48px rgba(0,0,0,0.1)',
    '0px 28px 56px rgba(0,0,0,0.1)',
    '0px 32px 64px rgba(0,0,0,0.1)',
    '0px 36px 72px rgba(0,0,0,0.1)',
    '0px 40px 80px rgba(0,0,0,0.15)',
    '0px 44px 88px rgba(0,0,0,0.15)',
    '0px 48px 96px rgba(0,0,0,0.15)',
    '0px 52px 104px rgba(0,0,0,0.15)',
    '0px 56px 112px rgba(0,0,0,0.2)',
    '0px 60px 120px rgba(0,0,0,0.2)',
    '0px 64px 128px rgba(0,0,0,0.2)',
    '0px 68px 136px rgba(0,0,0,0.2)',
    '0px 72px 144px rgba(0,0,0,0.25)',
    '0px 76px 152px rgba(0,0,0,0.25)',
    '0px 80px 160px rgba(0,0,0,0.25)',
    '0px 84px 168px rgba(0,0,0,0.25)',
    '0px 88px 176px rgba(0,0,0,0.3)',
    '0px 92px 184px rgba(0,0,0,0.3)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '10px 20px',
          fontSize: '0.9375rem',
          fontWeight: 600,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 4px 12px rgba(0,0,0,0.1)',
          },
        },
        contained: {
          background: `linear-gradient(135deg, ${colors.lavender.main} 0%, ${colors.ethereal.main} 100%)`,
          '&:hover': {
            background: `linear-gradient(135deg, ${colors.lavender.dark} 0%, ${colors.ethereal.dark} 100%)`,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 4px 20px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            '&:hover fieldset': {
              borderColor: colors.lavender.main,
            },
            '&.Mui-focused fieldset': {
              borderColor: colors.lavender.main,
            },
          },
        },
      },
    },
  },
});

// 커스텀 색상 확장
declare module '@mui/material/styles' {
  interface Theme {
    colors: typeof colors;
  }
  interface ThemeOptions {
    colors?: typeof colors;
  }
}

theme.colors = colors;