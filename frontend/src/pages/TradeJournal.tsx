import { useState, useEffect } from 'react';
import { BookOpen, TrendingUp, TrendingDown, Award, Clock, BarChart3 } from 'lucide-react';

interface Trade { symbol: string; action: string; price: number; qty: number; confidence: number; timestamp: string; }

export default function TradeJournal() {
    const [trades, setTrades] = useState<Trade[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTrades = async () => {
            try {
                const res = await fetch('http://127.0.0.1:8000/api/flight_recorder');
                const data = await res.json();
                setTrades(data);
            } catch (e) { console.error(e); }
            setLoading(false);
        };
        fetchTrades();
        const inv = setInterval(fetchTrades, 5000); // Poll every 5s for new trades
        return () => clearInterval(inv);
    }, []);

    const buys = trades.filter(t => t.action === 'BUY');
    const sells = trades.filter(t => t.action === 'SELL');
    const totalVolume = trades.reduce((s, t) => s + t.price * t.qty, 0);

    // Streak calculation
    let streak = 0; let streakType = '';
    for (const t of trades) {
        if (streakType === '' || t.action === streakType) { streakType = t.action; streak++; }
        else break;
    }

    // Symbol frequency
    const symFreq: Record<string, number> = {};
    trades.forEach(t => { symFreq[t.symbol] = (symFreq[t.symbol] || 0) + 1; });
    const topSymbols = Object.entries(symFreq).sort((a, b) => b[1] - a[1]).slice(0, 5);

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'rgba(176,38,255,0.1)', border: '1px solid rgba(176,38,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <BookOpen size={24} color="var(--accent-purple)" />
                </div>
                <div>
                    <h1 style={{ margin: 0, fontSize: '22px', fontWeight: 800, letterSpacing: '1px' }}>TRADE <span className="neon-purple">JOURNAL</span></h1>
                    <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>AI-powered trade analytics & pattern recognition</p>
                </div>
            </div>

            {/* Stats row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px' }}>
                {[
                    { label: 'TOTAL TRADES', value: trades.length, icon: BarChart3, color: 'var(--accent-cyan)' },
                    { label: 'BUY ORDERS', value: buys.length, icon: TrendingUp, color: 'var(--accent-green)' },
                    { label: 'SELL ORDERS', value: sells.length, icon: TrendingDown, color: 'var(--accent-danger)' },
                    { label: 'CURRENT STREAK', value: `${streak} ${streakType}`, icon: Award, color: 'var(--accent-warning)' },
                    { label: 'VOLUME', value: `₹${(totalVolume / 100000).toFixed(1)}L`, icon: Clock, color: 'var(--accent-purple)' },
                ].map((s, i) => (
                    <div key={i} className="glass-panel" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <s.icon size={12} color={s.color} />
                            <span style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '1px', fontFamily: 'var(--font-mono)' }}>{s.label}</span>
                        </div>
                        <div style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: s.color }}>{s.value}</div>
                    </div>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '16px', flex: 1, minHeight: 0 }}>
                {/* Trade list */}
                <div className="glass-panel" style={{ padding: '16px', overflow: 'auto' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 700, marginBottom: '12px' }}>TRADE HISTORY</div>
                    {trades.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '12px' }}>No trades recorded yet.</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {trades.map((t, i) => (
                                <div key={i} style={{
                                    display: 'grid', gridTemplateColumns: '70px 1fr 100px 80px 1fr',
                                    gap: '10px', alignItems: 'center', padding: '10px 12px', borderRadius: '8px',
                                    background: t.action === 'BUY' ? 'rgba(0,255,102,0.03)' : 'rgba(255,0,60,0.03)',
                                    border: `1px solid ${t.action === 'BUY' ? 'rgba(0,255,102,0.1)' : 'rgba(255,0,60,0.1)'}`,
                                }}>
                                    <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: t.action === 'BUY' ? 'var(--accent-green)' : 'var(--accent-danger)' }}>{t.action}</span>
                                    <span style={{ fontSize: '12px', fontWeight: 700 }}>{t.symbol.replace('.NS', '')}</span>
                                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>₹{t.price.toFixed(2)}</span>
                                    <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{t.qty} sh</span>
                                    <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textAlign: 'right' }}>{t.timestamp}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Side analytics */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div className="glass-panel" style={{ padding: '16px' }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 700, marginBottom: '12px' }}>MOST TRADED</div>
                        {topSymbols.map(([sym, count], i) => (
                            <div key={sym} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)', width: '18px' }}>#{i + 1}</span>
                                    <span style={{ fontSize: '12px', fontWeight: 700 }}>{sym.replace('.NS', '')}</span>
                                </div>
                                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{count} trades</span>
                            </div>
                        ))}
                        {topSymbols.length === 0 && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>No data yet</div>}
                    </div>

                    <div className="glass-panel" style={{ padding: '16px', flex: 1 }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 700, marginBottom: '12px' }}>ACTION DISTRIBUTION</div>
                        <div style={{ display: 'flex', gap: '8px', height: '30px', borderRadius: '6px', overflow: 'hidden' }}>
                            <div style={{ flex: buys.length || 1, background: 'rgba(0,255,102,0.3)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                                BUY {trades.length > 0 ? Math.round(buys.length / trades.length * 100) : 0}%
                            </div>
                            <div style={{ flex: sells.length || 1, background: 'rgba(255,0,60,0.3)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-danger)' }}>
                                SELL {trades.length > 0 ? Math.round(sells.length / trades.length * 100) : 0}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
