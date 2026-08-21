// Main App Component
import { Suspense, lazy, type ReactNode } from 'react';
import Layout from './components/Layout';
import { BrowserRouter, Navigate } from './router';
import { useLocation } from './router-context';

const AIStrategyLabPage = lazy(() => import('./pages/AIStrategyLabPage'));
const TrendJudgmentPage = lazy(() => import('./pages/TrendJudgmentPage'));
const TrendChartPage = lazy(() => import('./pages/TrendChartPage'));
const BacktestPage = lazy(() => import('./pages/BacktestPage'));
const BBMidPage = lazy(() => import('./pages/BBMidPage'));
const StreakAnalysisPage = lazy(() => import('./pages/StreakAnalysisPage'));
const TradingCompoundCalculatorPage = lazy(() => import('./pages/TradingCompoundCalculatorPage'));
const HoldReentryPage = lazy(() => import('./pages/HoldReentryPage'));
const JournalPage = lazy(() => import('./pages/JournalPage'));
const TradeAnalysisPage = lazy(() => import('./pages/TradeAnalysisPage'));

const routeFallback = <div className="card p-6 text-center text-dark-400">Loading...</div>;

function AppRoutes() {
  const { pathname } = useLocation();
  const pages: Record<string, ReactNode> = {
    '/backtest': <BacktestPage />,
    '/trend-judgment': <TrendJudgmentPage />,
    '/trend-chart': <TrendChartPage />,
    '/bb-mid': <BBMidPage />,
    '/streak-analysis': <StreakAnalysisPage />,
    '/compound-calculator': <TradingCompoundCalculatorPage />,
    '/hold-reentry': <HoldReentryPage />,
    '/ai-backtest-lab': <AIStrategyLabPage />,
    '/journal': <JournalPage />,
    '/trade-analysis': <TradeAnalysisPage />,
  };

  if (pathname === '/') return <Navigate to="/trend-judgment" replace />;
  if (pathname === '/ai-backtest-builder') {
    return <Navigate to="/ai-backtest-lab?tab=builder" replace />;
  }

  return <Layout>{pages[pathname] ?? <Navigate to="/trend-judgment" replace />}</Layout>;
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={routeFallback}>
        <AppRoutes />
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
