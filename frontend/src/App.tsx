// Main App Component
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import BacktestPage from './pages/BacktestPage';
import MaCrossPage from './pages/MaCrossPage';
import PatternPage from './pages/PatternPage';
import ScannerPage from './pages/ScannerPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/backtest" replace />} />
          <Route path="backtest" element={<BacktestPage />} />
          <Route path="ma-cross" element={<MaCrossPage />} />
          <Route path="pattern" element={<PatternPage />} />
          <Route path="scanner" element={<ScannerPage />} />
          <Route path="*" element={<Navigate to="/backtest" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

