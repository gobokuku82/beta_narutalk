import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { theme } from './styles/theme';
import ChatInterface from './components/ChatInterface';
import './styles/global.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#2D1B69',
              color: '#fff',
              borderRadius: '12px',
            },
          }}
        />
        <div className="app">
          <ChatInterface />
        </div>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;