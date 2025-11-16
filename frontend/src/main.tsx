import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import App from './App'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Elegant monochromatic glassmorphism theme with high contrast
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00ffff', // Electric cyan for high contrast
      light: '#66ffff',
      dark: '#00cccc',
      contrastText: '#0a0a0a',
    },
    secondary: {
      main: '#c0c0c0', // Platinum silver
      light: '#e8e8e8',
      dark: '#909090',
    },
    background: {
      default: '#0a0a0a',
      paper: 'rgba(30, 30, 30, 0.4)', // Glassmorphism
    },
    text: {
      primary: '#f5f5f5',
      secondary: '#b0b0b0',
    },
    success: {
      main: '#00ffaa',
      light: '#66ffcc',
      dark: '#00cc88',
    },
    error: {
      main: '#ff0055',
      light: '#ff6688',
      dark: '#cc0044',
    },
    warning: {
      main: '#ffaa00',
      light: '#ffcc66',
      dark: '#cc8800',
    },
  },
  typography: {
    fontFamily: '"Manrope", "Segoe UI", sans-serif',
    h1: {
      fontFamily: '"Unbounded", "Manrope", sans-serif',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontFamily: '"Unbounded", "Manrope", sans-serif',
      fontWeight: 700,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontFamily: '"Unbounded", "Manrope", sans-serif',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontFamily: '"Unbounded", "Manrope", sans-serif',
      fontWeight: 600,
    },
    h5: {
      fontFamily: '"Unbounded", "Manrope", sans-serif',
      fontWeight: 600,
    },
    h6: {
      fontFamily: '"Unbounded", "Manrope", sans-serif',
      fontWeight: 500,
    },
    body1: {
      fontFamily: '"Manrope", sans-serif',
      fontWeight: 400,
    },
    body2: {
      fontFamily: '"Manrope", sans-serif',
      fontWeight: 400,
    },
    button: {
      fontFamily: '"Manrope", sans-serif',
      fontWeight: 600,
      letterSpacing: '0.03em',
      textTransform: 'none',
    },
    caption: {
      fontFamily: '"Manrope", sans-serif',
    },
    overline: {
      fontFamily: '"JetBrains Mono", monospace',
      letterSpacing: '0.1em',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(0, 255, 255, 0.3) rgba(20, 20, 20, 0.5)',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(20, 20, 20, 0.5)',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(0, 255, 255, 0.3)',
            borderRadius: '4px',
            '&:hover': {
              background: 'rgba(0, 255, 255, 0.5)',
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(20, 20, 20, 0.6)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          padding: '10px 24px',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 6px 20px rgba(0, 255, 255, 0.3)',
          },
        },
        contained: {
          background: 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)',
          color: '#0a0a0a',
          fontWeight: 700,
          '&:hover': {
            background: 'linear-gradient(135deg, #66ffff 0%, #00ffff 100%)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: 'rgba(30, 30, 30, 0.4)',
            backdropFilter: 'blur(10px)',
            borderRadius: '12px',
            transition: 'all 0.3s ease',
            '&:hover': {
              backgroundColor: 'rgba(30, 30, 30, 0.6)',
            },
            '&.Mui-focused': {
              backgroundColor: 'rgba(30, 30, 30, 0.7)',
              boxShadow: '0 0 0 2px rgba(0, 255, 255, 0.2)',
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          backgroundColor: 'rgba(30, 30, 30, 0.4)',
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease',
          '&:hover': {
            backgroundColor: 'rgba(30, 30, 30, 0.6)',
          },
          '&.Mui-focused': {
            backgroundColor: 'rgba(30, 30, 30, 0.7)',
            boxShadow: '0 0 0 2px rgba(0, 255, 255, 0.2)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          fontWeight: 600,
          backdropFilter: 'blur(10px)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        },
        head: {
          fontWeight: 700,
          fontSize: '0.875rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: '#00ffff',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontFamily: '"Unbounded", sans-serif',
          fontWeight: 600,
          textTransform: 'none',
          fontSize: '1rem',
          '&.Mui-selected': {
            color: '#00ffff',
          },
        },
      },
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
