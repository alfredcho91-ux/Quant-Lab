// Main App Component
import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
// ScannerPage removed - replaced by StrategyScannerPage

const AIStrategyLabPage = lazy(() => import('./pages/AIStrategyLabPage'));
const TrendJudgmentPage = lazy(() => import('./pages/TrendJudgmentPage'));
const BacktestPage = lazy(() => import('./pages/BacktestPage'));
const AdvancedBacktestPage = lazy(() => import('./pages/AdvancedBacktestPage'));
const BBMidPage = lazy(() => import('./pages/BBMidPage'));
const ComboFilterPage = lazy(() => import('./pages/ComboFilterPage'));
const HybridAnalysisPage = lazy(() => import('./pages/HybridAnalysisPage'));
const PatternPage = lazy(() => import('./pages/PatternPage'));
const PatternScannerPage = lazy(() => import('./pages/PatternScannerPage'));
const StrategyScannerPage = lazy(() => import('./pages/StrategyScannerPage'));
const StreakAnalysisPage = lazy(() => import('./pages/StreakAnalysisPage'));
const JournalPage = lazy(() => import('./pages/JournalPage'));

const routeFallback = <div className="card p-6 text-center text-dark-400">Loading...</div>;

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={routeFallback}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/trend-judgment" replace />} />
            {/* 백테스트 페이지 복구 */}
            <Route path="backtest" element={<BacktestPage />} />
            <Route path="backtest-advanced" element={<AdvancedBacktestPage />} />
            <Route path="trend-judgment" element={<TrendJudgmentPage />} />
            <Route path="bb-mid" element={<BBMidPage />} />
            <Route path="combo-filter" element={<ComboFilterPage />} />
            <Route path="hybrid-analysis" element={<HybridAnalysisPage />} />
            <Route path="pattern" element={<PatternPage />} />
            <Route path="pattern-scanner" element={<PatternScannerPage />} />
            <Route path="strategy-scanner" element={<StrategyScannerPage />} />
            <Route path="streak-analysis" element={<StreakAnalysisPage />} />
            <Route path="ai-backtest-lab" element={<AIStrategyLabPage />} />
            <Route
              path="ai-backtest-builder"
              element={<Navigate to="/ai-backtest-lab?tab=builder" replace />}
            />
            <Route path="journal" element={<JournalPage />} />
            <Route path="*" element={<Navigate to="/trend-judgment" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
