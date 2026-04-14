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
import './index.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/oracle" element={<OracleDashboard />} />
            <Route path="/technicals" element={<Technicals />} />
            <Route path="/scanner" element={<Scanner />} />
            <Route path="/funds" element={<MutualFunds />} />
            <Route path="/news" element={<NewsRoom />} />
            <Route path="/ledger" element={<Ledger />} />
            <Route path="/vision" element={<VisionCenter />} />
            <Route path="/cortex" element={<CortexLog />} />
            <Route path="/config" element={<Config />} />
            <Route path="*" element={<div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}><h2 className="neon-cyan">COMPONENT INACTIVE</h2><p>This module is currently offline.</p></div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

