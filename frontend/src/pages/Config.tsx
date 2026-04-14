import { useState, useEffect } from 'react';
import { Settings, ShieldAlert, Cpu, Radio, Network } from 'lucide-react';

export default function Config() {
    const [autoTrade, setAutoTrade] = useState(true);
    const [extremeNews, setExtremeNews] = useState(false);
    const [riskLevel, setRiskLevel] = useState('MODERATE');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch current settings on mount
        fetch('http://127.0.0.1:8000/api/settings')
            .then(res => res.json())
            .then(data => {
                setAutoTrade(data.trading_mode === 'AUTO_PILOT');
                setRiskLevel(data.risk_tolerance || 'MODERATE');
                setExtremeNews(data.ignore_macro || false);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load settings:", err);
                setLoading(false);
            });
    }, []);

    const saveSettings = async (updates: any) => {
        try {
            await fetch('http://127.0.0.1:8000/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    risk_per_trade: 0.02,
                    trading_mode: updates.trading_mode !== undefined ? updates.trading_mode : (autoTrade ? 'AUTO_PILOT' : 'MANUAL'),
                    risk_tolerance: updates.risk_tolerance !== undefined ? updates.risk_tolerance : riskLevel,
                    ignore_macro: updates.ignore_macro !== undefined ? updates.ignore_macro : extremeNews
                })
            });
        } catch (err) {
            console.error("Failed to update settings:", err);
        }
    };

    const toggleAutoTrade = () => {
        const newMode = !autoTrade ? 'AUTO_PILOT' : 'MANUAL';
        setAutoTrade(!autoTrade); // Optimistic UI update
        saveSettings({ trading_mode: newMode });
    };

    const handleHaltTrading = async () => {
        if(window.confirm('WARNING: Are you sure you want to engage the DEFCON 1 killswitch? This will halt all active trading loops immediately.')) {
            try {
                await fetch('http://127.0.0.1:8000/api/killswitch', { method: 'POST' });
                alert('Killswitch engaged. System halted.');
            } catch (e) {
                console.error("Failed to engage killswitch:", e);
                alert('Killswitch API failed.');
            }
        }
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '18px', color: 'var(--text-primary)', letterSpacing: '2px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Settings size={20} className="neon-cyan" /> SYSTEM CONFIGURATION
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px' }}>

                {/* Protocol Settings */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Cpu size={16} /> TRADING PROTOCOLS
                    </h3>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>Autonomous Execution</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Allow Sovereign to place market orders without human intervention.</div>
                        </div>
                        <button
                            disabled={loading}
                            onClick={toggleAutoTrade}
                            className={autoTrade ? "glow-btn" : ""}
                            style={{
                                padding: '8px 16px', borderRadius: '4px', border: autoTrade ? '1px solid var(--accent-cyan)' : '1px solid var(--border-light)',
                                background: autoTrade ? 'rgba(0, 240, 255, 0.1)' : 'transparent', color: autoTrade ? 'var(--accent-cyan)' : 'var(--text-muted)',
                                fontWeight: 700, fontSize: '12px', letterSpacing: '1px', cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.3s', opacity: loading ? 0.5 : 1
                            }}
                        >
                            {autoTrade ? 'ACTIVE' : 'OFFLINE'}
                        </button>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>Risk Tolerance</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Algorithmic positioning constraints.</div>
                        </div>
                        <select
                            value={riskLevel}
                            onChange={(e) => {
                                setRiskLevel(e.target.value);
                                saveSettings({ risk_tolerance: e.target.value });
                            }}
                            style={{
                                appearance: 'none', background: 'rgba(0, 0, 0, 0.4)', border: '1px solid var(--border-light)',
                                color: 'var(--text-primary)', padding: '6px 12px', borderRadius: '4px', fontSize: '12px',
                                fontFamily: 'var(--font-mono)', fontWeight: 700, cursor: 'pointer', outline: 'none'
                            }}
                        >
                            <option value="CONSERVATIVE">CONSERVATIVE</option>
                            <option value="MODERATE">MODERATE</option>
                            <option value="AGGRESSIVE">AGGRESSIVE</option>
                        </select>
                    </div>
                </div>

                {/* Overrides */}
                <div className="glass-panel" style={{ padding: '24px', border: '1px solid rgba(255, 0, 60, 0.2)' }}>
                    <h3 style={{ fontSize: '12px', color: 'var(--accent-danger)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ShieldAlert size={16} /> OVERRIDE DIRECTIVES
                    </h3>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>Halt All Trading (DEFCON 1)</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Emergency killswitch to flatten positions and halt actions.</div>
                        </div>
                        <button
                            onClick={handleHaltTrading}
                            className="hover-glow"
                            style={{
                                padding: '8px 16px', borderRadius: '4px', border: '1px solid var(--accent-danger)',
                                background: 'rgba(255, 0, 60, 0.1)', color: 'var(--accent-danger)',
                                fontWeight: 700, fontSize: '12px', letterSpacing: '1px', cursor: 'pointer',
                                textShadow: '0 0 10px rgba(255,0,60,0.5)'
                            }}
                        >
                            ENGAGE
                        </button>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>Ignore Macro Events</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Force system into Technical-only trading mode.</div>
                        </div>
                        <button
                            onClick={() => {
                                setExtremeNews(!extremeNews);
                                saveSettings({ ignore_macro: !extremeNews });
                            }}
                            className={extremeNews ? "glow-btn" : ""}
                            style={{
                                padding: '8px 16px', borderRadius: '4px', border: extremeNews ? '1px solid var(--accent-warning)' : '1px solid var(--border-light)',
                                background: extremeNews ? 'rgba(245, 158, 11, 0.1)' : 'transparent', color: extremeNews ? 'var(--accent-warning)' : 'var(--text-muted)',
                                fontWeight: 700, fontSize: '12px', letterSpacing: '1px', cursor: 'pointer', transition: 'all 0.3s'
                            }}
                        >
                            {extremeNews ? 'OVERRIDING' : 'BYPASS'}
                        </button>
                    </div>
                </div>

                {/* API Connections */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Network size={16} /> EXTERNAL LINKS
                    </h3>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                        <Radio size={16} color="var(--accent-green)" />
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Gemini Neuro-Net: <strong style={{ color: 'var(--accent-green)' }}>CONNECTED</strong></span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                        <Radio size={16} color="var(--accent-green)" />
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>NSE Market Data: <strong style={{ color: 'var(--accent-green)' }}>SYNCED</strong></span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <Radio size={16} color="var(--text-muted)" />
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Broker Executions: <strong style={{ color: 'var(--text-muted)' }}>PAPER TRADING</strong></span>
                    </div>

                </div>
            </div>
        </div>
    );
}
