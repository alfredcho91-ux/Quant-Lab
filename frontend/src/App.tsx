// Main App Component
import { Suspense, lazy, type ReactNode } from 'react';
import Layout from './components/Layout';
import { BrowserRouter, Navigate } from './router';
import { useLocation } from './router-context';
import WorkspaceExperience from './features/onboarding/WorkspaceExperience';
import { isSampleWorkspace } from './features/onboarding/workspaceSession';

const AIStrategyLabPage = lazy(() => import('./pages/AIStrategyLabPage'));
const TrendJudgmentPage = lazy(() => import('./pages/TrendJudgmentPage'));
const TrendChartPage = lazy(() => import('./pages/TrendChartPage'));
const StopLossLabPage = lazy(() => import('./pages/StopLossLabPage'));
const BacktestPage = lazy(() => import('./pages/BacktestPage'));
const BBMidPage = lazy(() => import('./pages/BBMidPage'));
const StreakAnalysisPage = lazy(() => import('./pages/StreakAnalysisPage'));
const TradingCompoundCalculatorPage = lazy(() => import('./pages/TradingCompoundCalculatorPage'));
const HoldReentryPage = lazy(() => import('./pages/HoldReentryPage'));
const JournalPage = lazy(() => import('./pages/JournalPage'));
const TradeAnalysisPage = lazy(() => import('./pages/TradeAnalysisPage'));
const RiskLabPage = lazy(() => import('./pages/RiskLabPage'));
const PlanLabPage = lazy(() => import('./pages/PlanLabPage'));
const PlaybookPage = lazy(() => import('./pages/PlaybookPage'));
const TradeExplorerPage = lazy(() => import('./pages/TradeExplorerPage'));

const routeFallback = <div className="card p-6 text-center text-dark-400">불러오는 중...</div>;

function AppRoutes() {
  const { pathname } = useLocation();
  const pages: Record<string, ReactNode> = {
    '/backtest': <BacktestPage />,
    '/trend-judgment': <TrendJudgmentPage />,
    '/trend-chart': <TrendChartPage />,
    '/volatility-statistics': <StopLossLabPage />,
    '/stop-loss-lab': <StopLossLabPage />,
    '/bb-mid': <BBMidPage />,
    '/streak-analysis': <StreakAnalysisPage />,
    '/compound-calculator': <TradingCompoundCalculatorPage />,
    '/hold-reentry': <HoldReentryPage />,
    '/ai-backtest-lab': <AIStrategyLabPage />,
    '/journal': <JournalPage />,
    '/trade-analysis': <TradeAnalysisPage />,
    '/risk-lab': <RiskLabPage />,
    '/plan-lab': <PlanLabPage />,
    '/playbook': <PlaybookPage />,
    '/trade-explorer': <TradeExplorerPage />,
  };

  const sample = isSampleWorkspace();
  const journalWorkspace = ['/journal', '/trade-analysis', '/risk-lab', '/plan-lab', '/playbook', '/trade-explorer'].includes(pathname);
  if (pathname === '/') return <Navigate to={sample ? '/journal' : '/trend-judgment'} replace />;
  if (sample && !journalWorkspace && !['/hold-reentry', '/compound-calculator'].includes(pathname)) return <Navigate to="/journal" replace />;
  if (pathname === '/ai-backtest-builder') {
    return <Navigate to="/ai-backtest-lab?tab=builder" replace />;
  }

  return <Layout>{journalWorkspace || sample ? <WorkspaceExperience>{pages[pathname]}</WorkspaceExperience> : (pages[pathname] ?? <Navigate to="/trend-judgment" replace />)}</Layout>;
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
