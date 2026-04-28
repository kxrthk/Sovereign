import { useState, useEffect } from 'react';
import { LayoutGrid, TrendingUp, TrendingDown, RefreshCw, AlertTriangle } from 'lucide-react';

interface Position { symbol: string; quantity: number; avg_price: number; }
interface PriceData { symbol: string; price: number; change_pct: number; }

export default function PortfolioHeatmap() {
    const [positions, setPositions] = useState<Position[]>([]);
    const [prices, setPrices] = useState<Record<string, PriceData>>({});
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const posRes = await fetch('http://127.0.0.1:8000/api/positions');
            const posData = await posRes.json();
            setPositions(posData);

            const priceMap: Record<string, PriceData> = {};
            for (const pos of posData) {
                try {
                    const pr = await fetch(`http://127.0.0.1:8000/api/price/${pos.symbol}`);
                    const pd = await pr.json();
                    const change = pos.avg_price > 0 ? ((pd.price - pos.avg_price) / pos.avg_price) * 100 : 0;
                    priceMap[pos.symbol] = { symbol: pos.symbol, price: pd.price, change_pct: change };
                } catch { priceMap[pos.symbol] = { symbol: pos.symbol, price: pos.avg_price, change_pct: 0 }; }
            }
            setPrices(priceMap);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const totalValue = positions.reduce((s, p) => s + (prices[p.symbol]?.price || p.avg_price) * p.quantity, 0);
    const totalCost = positions.reduce((s, p) => s + p.avg_price * p.quantity, 0);
    const totalPnl = totalValue - totalCost;
    const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0;

    const getHeatColor = (pct: number) => {
        if (pct > 5) return 'rgba(0, 255, 102, 0.35)';
        if (pct > 2) return 'rgba(0, 255, 102, 0.2)';
        if (pct > 0) return 'rgba(0, 255, 102, 0.08)';
        if (pct > -2) return 'rgba(255, 0, 60, 0.08)';
        if (pct > -5) return 'rgba(255, 0, 60, 0.2)';
        return 'rgba(255, 0, 60, 0.35)';
    };

    const maxWeight = Math.max(...positions.map(p => (prices[p.symbol]?.price || p.avg_price) * p.quantity), 1);

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'rgba(0,240,255,0.1)', border: '1px solid rgba(0,240,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <LayoutGrid size={24} color="var(--accent-cyan)" />
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: '22px', fontWeight: 800, letterSpacing: '1px' }}>PORTFOLIO <span className="neon-cyan">HEATMAP</span></h1>
                        <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Real-time position P&L visualization</p>
                    </div>
                </div>
                <button onClick={fetchData} className="glow-btn" style={{ padding: '8px 16px', background: 'rgba(0,240,255,0.1)', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700 }}>
                    <RefreshCw size={14} className={loading ? 'spin' : ''} /> REFRESH
                </button>
            </div>

            {/* Summary strip */}
            <div className="glass-panel" style={{ padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                <div><div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', fontFamily: 'var(--font-mono)' }}>POSITIONS</div><div style={{ fontSize: '22px', fontWeight: 800 }}>{positions.length}</div></div>
                <div><div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', fontFamily: 'var(--font-mono)' }}>PORTFOLIO VALUE</div><div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>₹{totalValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>
                <div><div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', fontFamily: 'var(--font-mono)' }}>TOTAL P&L</div><div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: totalPnl >= 0 ? 'var(--accent-green)' : 'var(--accent-danger)' }}>₹{totalPnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>
                <div><div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', fontFamily: 'var(--font-mono)' }}>P&L %</div><div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: totalPnlPct >= 0 ? 'var(--accent-green)' : 'var(--accent-danger)' }}>{totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%</div></div>
            </div>

            {/* Heatmap Grid */}
            <div className="glass-panel" style={{ flex: 1, padding: '20px', overflow: 'auto' }}>
                {positions.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', color: 'var(--text-muted)' }}>
                        <AlertTriangle size={40} style={{ opacity: 0.3 }} />
                        <div style={{ fontSize: '14px', fontFamily: 'var(--font-mono)' }}>No open positions</div>
                        <div style={{ fontSize: '11px' }}>Place trades in Pilot Mode to populate the heatmap.</div>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px' }}>
                        {positions.map(pos => {
                            const pd = prices[pos.symbol];
                            const pct = pd?.change_pct || 0;
                            const value = (pd?.price || pos.avg_price) * pos.quantity;
                            const weight = value / maxWeight;
                            return (
                                <div key={pos.symbol} style={{
                                    padding: '16px', borderRadius: '12px',
                                    background: getHeatColor(pct),
                                    border: `1px solid ${pct >= 0 ? 'rgba(0,255,102,0.2)' : 'rgba(255,0,60,0.2)'}`,
                                    minHeight: `${60 + weight * 80}px`,
                                    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                                    transition: 'all 0.3s',
                                }} className="hover-glow">
                                    <div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span style={{ fontSize: '14px', fontWeight: 800 }}>{pos.symbol.replace('.NS', '')}</span>
                                            {pct >= 0 ? <TrendingUp size={16} color="var(--accent-green)" /> : <TrendingDown size={16} color="var(--accent-danger)" />}
                                        </div>
                                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{pos.quantity} shares @ ₹{pos.avg_price.toFixed(2)}</div>
                                    </div>
                                    <div style={{ marginTop: '12px' }}>
                                        <div style={{ fontSize: '18px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: pct >= 0 ? 'var(--accent-green)' : 'var(--accent-danger)' }}>
                                            {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                                        </div>
                                        <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>₹{value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                                        {/* Concentration bar */}
                                        <div style={{ marginTop: '6px', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                                            <div style={{ height: '100%', width: `${(value / totalValue * 100)}%`, background: weight > 0.4 ? 'var(--accent-warning)' : 'var(--accent-cyan)', borderRadius: '2px', transition: 'width 0.5s' }} />
                                        </div>
                                        <div style={{ fontSize: '8px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{(value / totalValue * 100).toFixed(1)}% of portfolio</div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
