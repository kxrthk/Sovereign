import { useState, useEffect } from 'react';
import axios from 'axios';
import { History, ArrowUpRight, ArrowDownRight, CircleSlash } from 'lucide-react';

export default function Ledger() {
    const [trades, setTrades] = useState<any[]>([]);

    useEffect(() => {
        const fetchTrades = async () => {
            try {
                const res = await axios.get('/api/flight_recorder');
                if (res.data && res.data.length > 0) {
                    const parsed = res.data.map((t: any, idx: number) => ({
                        id: t.order_id || `TRD-${1000 + idx}`,
                        time: t.timestamp,
                        sym: t.symbol,
                        type: t.action,
                        price: t.price,
                        qty: t.qty || 1,
                        status: 'EXECUTED',
                        pnl: t.action === 'SELL' && t.pnl != null
                            ? (t.pnl >= 0 ? `+₹${t.pnl.toFixed(1)}` : `-₹${Math.abs(t.pnl).toFixed(1)}`)
                            : '--'
                    })).reverse();
                    setTrades(parsed);
                } else {
                    setTrades([]);
                }
            } catch (e) {
                console.error("Ledger fetch error", e);
            }
        };
        fetchTrades();
        const inv = setInterval(fetchTrades, 5000);
        return () => clearInterval(inv);
    }, []);

    const getTypeColor = (type: string) => {
        return type === 'BUY' ? 'var(--accent-green)' : 'var(--accent-danger)';
    };

    const getIcon = (type: string) => {
        return type === 'BUY' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />;
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '18px', color: 'var(--text-primary)', letterSpacing: '2px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <History size={20} className="neon-purple" /> TACTICAL LEDGER
            </h2>

            <div className="glass-panel" style={{ flex: 1, padding: '0', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontFamily: 'var(--font-mono)' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-light)', background: 'var(--sub-panel-bg)' }}>
                            <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-primary)', letterSpacing: '2px', fontWeight: 800 }}>TIMESTAMP</th>
                            <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-primary)', letterSpacing: '2px', fontWeight: 800 }}>ASSET</th>
                            <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-primary)', letterSpacing: '2px', fontWeight: 800 }}>ACTION</th>
                            <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-primary)', letterSpacing: '2px', fontWeight: 800 }}>PRICE</th>
                            <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-primary)', letterSpacing: '2px', fontWeight: 800 }}>STATUS</th>
                            <th style={{ padding: '16px 24px', fontSize: '11px', color: 'var(--text-primary)', letterSpacing: '2px', fontWeight: 800, textAlign: 'right' }}>PNL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades.length === 0 ? (
                            <tr>
                                <td colSpan={6} style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                    <CircleSlash size={32} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
                                    <div>NO ACTIVE TACTICAL ENGAGEMENTS</div>
                                </td>
                            </tr>
                        ) : trades.map((t, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', transition: 'background 0.2s', cursor: 'pointer' }} className="hover-glow">
                                <td style={{ padding: '16px 24px', fontSize: '14px', color: 'var(--text-secondary)' }}>{t.time}</td>
                                <td style={{ padding: '16px 24px', fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>{t.sym}</td>
                                <td style={{ padding: '16px 24px', fontSize: '13px', fontWeight: 800 }}>
                                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: getTypeColor(t.type), background: `${getTypeColor(t.type)}15`, padding: '4px 10px', borderRadius: '4px' }}>
                                        {getIcon(t.type)} {t.type}
                                    </div>
                                </td>
                                <td style={{ padding: '16px 24px', fontSize: '14px', color: 'var(--text-secondary)' }}>₹{Number(t.price).toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</td>
                                <td style={{ padding: '16px 24px', fontSize: '12px', fontWeight: 700, color: t.status === 'OPEN' ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                                    {t.status}
                                </td>
                                <td style={{ padding: '16px 24px', fontSize: '14px', fontWeight: 700, textAlign: 'right', color: t.pnl?.startsWith('+') ? 'var(--accent-green)' : (t.pnl?.startsWith('-') ? 'var(--accent-danger)' : 'var(--text-muted)') }}>
                                    {t.pnl || '---'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
