import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import VisionCenter from './pages/VisionCenter';
import CortexLog from './pages/CortexLog';
import Technicals from './pages/Technicals';
import Ledger from './pages/Ledger';
import Config from './pages/Config';
import NewsRoom from './pages/NewsRoom';
import Scanner from './pages/Scanner';
import OracleDashboard from './pages/OracleDashboard';
import MutualFunds from './pages/MutualFunds';
import PilotMode from './pages/PilotMode';
import PortfolioHeatmap from './pages/PortfolioHeatmap';
import TradeJournal from './pages/TradeJournal';
import EconomicCalendar from './pages/EconomicCalendar';
import './index.css';
import { useState, useEffect } from 'react';

function App() {
  const [theme, setTheme] = useState(localStorage.getItem('sovereign_theme') || 'cyberpunk');

  useEffect(() => {
    if (theme === 'hellenic') {
      document.documentElement.classList.add('theme-greek');
    } else {
      document.documentElement.classList.remove('theme-greek');
    }
    localStorage.setItem('sovereign_theme', theme);
  }, [theme]);
  return (
    <Router>
      {/* Global artistic overlays */}
      <div className="ambient-vignette" />
      <div className="crt-overlay" />
      <div className="app-container">
        <Sidebar />
        <main style={{ flex: 1, padding: '24px', overflowY: 'auto', position: 'relative', zIndex: 1 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/oracle" element={<OracleDashboard />} />
            <Route path="/technicals" element={<Technicals />} />
            <Route path="/scanner" element={<Scanner />} />
            <Route path="/pilot" element={<PilotMode />} />
            <Route path="/funds" element={<MutualFunds />} />
            <Route path="/news" element={<NewsRoom />} />
            <Route path="/ledger" element={<Ledger />} />
            <Route path="/vision" element={<VisionCenter />} />
            <Route path="/cortex" element={<CortexLog />} />
            <Route path="/config" element={<Config theme={theme} setTheme={setTheme} />} />
            <Route path="/heatmap" element={<PortfolioHeatmap />} />
            <Route path="/journal" element={<TradeJournal />} />
            <Route path="/calendar" element={<EconomicCalendar />} />
            <Route path="*" element={<div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}><h2 className="neon-cyan">COMPONENT INACTIVE</h2><p>This module is currently offline.</p></div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

