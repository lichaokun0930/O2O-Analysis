import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { GlobalProvider } from './store/GlobalContext';
import App from './App';
import './index.css';

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean, error: Error | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', color: '#f87171', backgroundColor: '#1e293b', height: '100vh', fontFamily: 'monospace' }}>
          <h1 style={{ fontSize: '24px', marginBottom: '20px' }}>⚠️ System Malfunction</h1>
          <p style={{ color: '#cbd5e1' }}>The dashboard encountered a critical error while rendering.</p>
          <pre style={{ marginTop: '20px', padding: '20px', backgroundColor: '#0f172a', borderRadius: '8px', overflow: 'auto' }}>
            {this.state.error?.message}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '20px', padding: '10px 20px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Reboot System
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <GlobalProvider>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </GlobalProvider>
    </BrowserRouter>
  </React.StrictMode>
);
