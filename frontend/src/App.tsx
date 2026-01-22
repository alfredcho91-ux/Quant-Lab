// Main App Component
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import PatternPage from './pages/PatternPage';
// ScannerPage removed - replaced by StrategyScannerPage
import BBMidPage from './pages/BBMidPage';
import ComboFilterPage from './pages/ComboFilterPage';
import MultiTFSqueezePage from './pages/MultiTFSqueezePage';
import PatternScannerPage from './pages/PatternScannerPage';
import JournalPage from './pages/JournalPage';
import StrategyScannerPage from './pages/StrategyScannerPage';
import StreakAnalysisPage from './pages/StreakAnalysisPage';
import WeeklyPatternPage from './pages/WeeklyPatternPage';
import HybridAnalysisPage from './pages/HybridAnalysisPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/streak-analysis" replace />} />
          {/* 백테스트 페이지 숨김 */}
          {/* <Route path="backtest" element={<BacktestPage />} /> */}
          {/* <Route path="backtest-advanced" element={<AdvancedBacktestPage />} /> */}
          <Route path="bb-mid" element={<BBMidPage />} />
          <Route path="combo-filter" element={<ComboFilterPage />} />
          <Route path="multi-tf-squeeze" element={<MultiTFSqueezePage />} />
          <Route path="pattern" element={<PatternPage />} />
          <Route path="pattern-scanner" element={<PatternScannerPage />} />
          <Route path="strategy-scanner" element={<StrategyScannerPage />} />
          <Route path="streak-analysis" element={<StreakAnalysisPage />} />
          <Route path="weekly-pattern" element={<WeeklyPatternPage />} />
          <Route path="hybrid-analysis" element={<HybridAnalysisPage />} />
          <Route path="journal" element={<JournalPage />} />
          <Route path="*" element={<Navigate to="/streak-analysis" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

