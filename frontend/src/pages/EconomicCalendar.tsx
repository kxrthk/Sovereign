import { useState, useEffect } from 'react';
import { Calendar, AlertTriangle, Clock, TrendingUp, Shield, Zap } from 'lucide-react';

interface MarketEvent {
    id: string; title: string; date: string; time: string;
    impact: 'HIGH' | 'MEDIUM' | 'LOW'; category: string; description: string;
}

const STATIC_EVENTS: MarketEvent[] = [
    { id: '1', title: 'RBI Monetary Policy Decision', date: '2026-06-06', time: '10:00', impact: 'HIGH', category: 'CENTRAL BANK', description: 'Bi-monthly monetary policy review. Rate decision and forward guidance.' },
    { id: '2', title: 'F&O Monthly Expiry', date: '2026-05-29', time: '15:30', impact: 'HIGH', category: 'DERIVATIVES', description: 'Nifty & Bank Nifty monthly futures and options expiry.' },
    { id: '3', title: 'India GDP Q4 Data', date: '2026-05-30', time: '17:30', impact: 'HIGH', category: 'ECONOMY', description: 'Q4 FY26 GDP growth rate release by MOSPI.' },
    { id: '4', title: 'F&O Weekly Expiry', date: '2026-05-01', time: '15:30', impact: 'MEDIUM', category: 'DERIVATIVES', description: 'Weekly Nifty options expiry — elevated volatility expected.' },
    { id: '5', title: 'US Fed FOMC Minutes', date: '2026-05-21', time: '23:30', impact: 'HIGH', category: 'GLOBAL', description: 'Federal Reserve meeting minutes release — impacts global risk sentiment.' },
    { id: '6', title: 'India CPI Inflation', date: '2026-05-12', time: '17:30', impact: 'MEDIUM', category: 'ECONOMY', description: 'April 2026 Consumer Price Index data.' },
    { id: '7', title: 'FII/DII Activity Report', date: '2026-04-30', time: '18:00', impact: 'MEDIUM', category: 'FLOWS', description: 'Monthly institutional flow summary — FII and DII net positions.' },
    { id: '8', title: 'India PMI Manufacturing', date: '2026-05-01', time: '10:30', impact: 'MEDIUM', category: 'ECONOMY', description: 'S&P Global India Manufacturing PMI for April.' },
    { id: '9', title: 'US Non-Farm Payrolls', date: '2026-05-02', time: '18:00', impact: 'HIGH', category: 'GLOBAL', description: 'US jobs report — key driver of Fed policy expectations.' },
    { id: '10', title: 'Nifty IT Earnings Season', date: '2026-05-15', time: '09:15', impact: 'MEDIUM', category: 'EARNINGS', description: 'Q4 results from Infosys, TCS, HCL Tech, Wipro.' },
    { id: '11', title: 'India IIP Data', date: '2026-05-12', time: '17:30', impact: 'LOW', category: 'ECONOMY', description: 'Index of Industrial Production for March 2026.' },
    { id: '12', title: 'Bank Nifty Earnings', date: '2026-05-20', time: '09:15', impact: 'HIGH', category: 'EARNINGS', description: 'Q4 results from HDFC Bank, ICICI Bank, SBI, Kotak.' },
];

export default function EconomicCalendar() {
    const [events, setEvents] = useState<MarketEvent[]>([]);
    const [filter, setFilter] = useState<string>('ALL');

    useEffect(() => {
        const sorted = [...STATIC_EVENTS].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        setEvents(sorted);
    }, []);

    const now = new Date();
    const getCountdown = (dateStr: string, timeStr: string) => {
        const target = new Date(`${dateStr}T${timeStr}:00`);
        const diff = target.getTime() - now.getTime();
        if (diff <= 0) return 'PASSED';
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        if (days > 0) return `${days}d ${hours}h`;
        return `${hours}h`;
    };

    const impactColor = (impact: string) => {
        if (impact === 'HIGH') return 'var(--accent-danger)';
        if (impact === 'MEDIUM') return 'var(--accent-warning)';
        return 'var(--accent-cyan)';
    };

    const categories = ['ALL', ...Array.from(new Set(events.map(e => e.category)))];
    const filtered = filter === 'ALL' ? events : events.filter(e => e.category === filter);

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: 44, height: 44, borderRadius: '12px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Calendar size={24} color="var(--accent-warning)" />
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: '22px', fontWeight: 800, letterSpacing: '1px' }}>ECONOMIC <span style={{ color: 'var(--accent-warning)' }}>CALENDAR</span></h1>
                        <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Upcoming market events with impact severity</p>
                    </div>
                </div>
            </div>

            {/* Category filters */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {categories.map(cat => (
                    <button key={cat} onClick={() => setFilter(cat)} style={{
                        padding: '5px 12px', borderRadius: '20px', fontSize: '10px', fontWeight: 700,
                        fontFamily: 'var(--font-mono)', letterSpacing: '1px', cursor: 'pointer',
                        background: filter === cat ? 'rgba(245,158,11,0.15)' : 'transparent',
                        border: `1px solid ${filter === cat ? 'var(--accent-warning)' : 'rgba(255,255,255,0.08)'}`,
                        color: filter === cat ? 'var(--accent-warning)' : 'var(--text-muted)',
                    }}>{cat}</button>
                ))}
            </div>

            {/* Events list */}
            <div className="glass-panel" style={{ flex: 1, padding: '16px', overflow: 'auto' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {filtered.map(ev => {
                        const countdown = getCountdown(ev.date, ev.time);
                        const isPassed = countdown === 'PASSED';
                        return (
                            <div key={ev.id} style={{
                                display: 'grid', gridTemplateColumns: '100px 1fr 100px 80px',
                                gap: '16px', alignItems: 'center', padding: '14px 16px', borderRadius: '10px',
                                background: isPassed ? 'rgba(255,255,255,0.01)' : 'rgba(255,255,255,0.03)',
                                border: `1px solid ${isPassed ? 'rgba(255,255,255,0.04)' : `${impactColor(ev.impact)}20`}`,
                                opacity: isPassed ? 0.5 : 1,
                                borderLeft: `3px solid ${impactColor(ev.impact)}`,
                            }}>
                                <div>
                                    <div style={{ fontSize: '12px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{new Date(ev.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</div>
                                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{ev.time} IST</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '2px' }}>{ev.title}</div>
                                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{ev.description}</div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{
                                        display: 'inline-block', padding: '3px 10px', borderRadius: '12px', fontSize: '9px',
                                        fontWeight: 800, letterSpacing: '1px', fontFamily: 'var(--font-mono)',
                                        background: `${impactColor(ev.impact)}15`, color: impactColor(ev.impact),
                                        border: `1px solid ${impactColor(ev.impact)}30`,
                                    }}>{ev.impact}</div>
                                    <div style={{ fontSize: '8px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{ev.category}</div>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                                        <Clock size={10} color={isPassed ? 'var(--text-muted)' : 'var(--accent-cyan)'} />
                                        <span style={{ fontSize: '12px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: isPassed ? 'var(--text-muted)' : 'var(--accent-cyan)' }}>{countdown}</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
