import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { loadWorkspace, prepareSample } from './features/onboarding/workspaceSession'
import AppErrorBoundary from './components/AppErrorBoundary'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
    },
  },
})

const root = ReactDOM.createRoot(document.getElementById('root')!);
async function start() {
  root.render(<p role="status" className="p-8">작업 공간을 준비하고 있습니다…</p>);
  try {
    if (new URLSearchParams(window.location.search).get('sample') === 'reset') {
      const state = await loadWorkspace();
      if (state.mode !== 'normal') throw new Error('Reset requires the normal workspace.');
      window.location.replace(await prepareSample(true));
      return;
    }
    await loadWorkspace();
    const { default: App } = await import('./App');
    root.render(
  <React.StrictMode>
    <AppErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </AppErrorBoundary>
  </React.StrictMode>,
    );
  } catch (error) {
    root.render(<div role="alert" className="p-8"><p>{error instanceof Error ? error.message : '작업 공간을 불러오지 못했습니다.'}</p><button className="mt-4 underline" onClick={() => void start()}>다시 시도</button></div>);
  }
}
void start();
