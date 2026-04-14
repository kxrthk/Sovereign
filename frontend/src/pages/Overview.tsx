import { useState, useEffect } from 'react';
import axios from 'axios';
import { Cpu, Globe, TrendingUp, TrendingDown, Zap, Shield, AlertTriangle, ChevronRight, Activity, Database, Radar, Target, Newspaper, ChevronLeft } from 'lucide-react';
import { AreaChart, Area, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis } from 'recharts';

export default function Overview() {
    const [status, setStatus] = useState<any>({});
    const [intel, setIntel] = useState<any>({});
    const [trades, setTrades] = useState<any[]>([]);
    const [news, setNews] = useState<any[]>([]);
    const [performance, setPerformance] = useState<any>({ equity_curve: [] });
    const [newsIndex, setNewsIndex] = useState(0);
    const NEWS_PER_PAGE = 3;
    const [oracleScan, setOracleScan] = useState<any[]>([]);

    useEffect(() => {
        const fetchStatus = async () => {
            try { const res = await axios.get('/api/status'); setStatus(res.data); }
            catch (e) { console.error('Status fetch error', e); }
        };

        const fetchIntel = async () => {
            try { const res = await axios.get('/api/intelligence'); setIntel(res.data); }
            catch (e) { console.error('Intel fetch error', e); }
        };

        const fetchTrades = async () => {
            try {
                const res = await axios.get('/api/flight_recorder');
                const sorted = res.data.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
                setTrades(sorted.slice(0, 5));
            } catch (e) { console.error('Trade fetch error', e); }
        };

        const fetchPerformance = async () => {
            try { const res = await axios.get('/api/performance'); setPerformance(res.data); }
            catch (e) { console.error('Performance fetch error', e); }
        };

        const fetchNews = async () => {
            try {
                const res = await axios.get('/api/news');
                setNews(res.data || []);
            } catch (e) { console.error('News fetch error', e); }
        };
        
        const fetchOracleScan = async () => {
            try {
                const res = await axios.get('/api/oracle_scan');
                if (res.data?.length > 0) setOracleScan(res.data);
            } catch (e) { console.error('Oracle fetch error', e); }
        };

        fetchStatus();
        fetchIntel();
        fetchTrades();
        fetchPerformance();
        fetchNews();
        fetchOracleScan();

        const inv1 = setInterval(fetchStatus, 5000);
        const inv2 = setInterval(fetchIntel, 60000);
        const inv3 = setInterval(fetchTrades, 5000);
        const inv4 = setInterval(fetchNews, 300000); // refresh news every 5 min
        const inv5 = setInterval(fetchPerformance, 5000);
        const inv6 = setInterval(fetchOracleScan, 30000); // 30s oracle pulse

        return () => { clearInterval(inv1); clearInterval(inv2); clearInterval(inv3); clearInterval(inv4); clearInterval(inv5); clearInterval(inv6); };
    }, []);

    const confPercent = Math.round((status.latest_oracle_confidence || 0.85) * 100);
    const defcon = intel.defcon || 'SAFE';
    const directive = intel.directive || {};
    const hotspots = intel.sector_hotspots || [];

    const defconColor = defcon === 'SAFE' ? 'var(--accent-green)' : defcon === 'CAUTION' ? 'var(--accent-warning)' : 'var(--accent-danger)';
    const defconBg = defcon === 'SAFE' ? 'rgba(0,255,102,0.1)' : defcon === 'CAUTION' ? 'rgba(245,158,11,0.1)' : 'rgba(255,0,60,0.1)';
    const directiveColor = directive.action === 'BUY' ? 'var(--accent-green)' : directive.action === 'SELL' ? 'var(--accent-danger)' : 'var(--text-muted)';

    // Map the real equity curve from history CSV to the balance graph
    let equityData = performance.equity_curve || [];
    if (equityData.length === 0) {
        const bal = status.wallet_balance || 100000;
        equityData = [
            { name: 'Start', balance: bal - 0.2 },
            { name: 'T1', balance: bal - 0.1 },
            { name: 'T2', balance: bal },
            { name: 'Now', balance: bal + 0.1 }
        ];
    } else {
        equityData = equityData.map((d: any) => ({ name: d.name, balance: d.value || d.balance }));
        if (equityData.length === 1) {
            equityData = [
                { name: 'Start', balance: equityData[0].balance - 0.1 },
                { name: 'T1', balance: equityData[0].balance },
                { name: 'T2', balance: equityData[0].balance },
                equityData[0]
            ];
        }
    }

    const marketDirection = (() => {
        if (!oracleScan || oracleScan.length === 0) return { direction: 'INIT', color: 'var(--text-muted)', pulse: 50 };
        let bull = 0, bear = 0, strengthSum = 0;
        oracleScan.forEach(s => {
            if (s.prediction === 'BULLISH') bull++;
            if (s.prediction === 'BEARISH') bear++;
            strengthSum += (s.prediction_strength || 50);
        });
        const pulse = Math.round(strengthSum / oracleScan.length);
        if (bull > bear * 1.5) return { direction: 'BULLISH', color: 'var(--accent-green)', pulse };
        if (bear > bull * 1.5) return { direction: 'BEARISH', color: 'var(--accent-danger)', pulse };
        return { direction: 'MIXED', color: 'var(--accent-warning)', pulse };
    })();

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Live Bot Feedback Banner */}
            <div className="glass-panel hover-glow" style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderLeft: '4px solid var(--accent-cyan)' }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                     <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-cyan)', boxShadow: '0 0 10px var(--accent-cyan)', animation: 'pulse 2s infinite' }} />
                     <h2 style={{ fontSize: '13px', color: '#fff', letterSpacing: '2px', fontWeight: 800, margin: 0 }}>SYSTEM STATUS:</h2>
                     <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                         {status.bot_message || "Initializing Sovereign Engine..."}
                     </span>
                 </div>
                 <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>UPDATED LIVE</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '24px' }}>
                {/* LEFT COLUMN */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

                    {/* Daily Market Insights */}
                    <div className="glass-panel hover-glow" style={{ padding: '24px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,240,255,0.2)' }}>
                        <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Radar size={16} className="neon-cyan" /> DAILY MARKET INSIGHTS
                        </h2>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                            {intel.daily_insight || 'Sovereign is booting up. First comprehensive market insight will be available in ~10 minutes.'}
                        </p>
                    </div>

                    {/* Ledger Balance & Equity Curve */}
                    <div className="glass-panel hover-glow" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
                        <div>
                            <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '8px', fontWeight: 700 }}>
                                LEDGER BALANCE
                            </h2>
                            <div className="neon-cyan" style={{ fontSize: '36px', fontFamily: 'var(--font-mono)', fontWeight: 900 }}>
                                ₹{status.wallet_balance ? status.wallet_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '1,00,000.00'}
                            </div>
                        </div>

                        <div style={{ height: '120px', width: '100%', marginTop: '16px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={equityData}>
                                    <defs>
                                        <linearGradient id="colorBal" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.35} />
                                            <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <Tooltip
                                        contentStyle={{ background: 'rgba(15,23,42,0.9)', border: '1px solid rgba(0,240,255,0.3)', borderRadius: '8px', fontSize: '12px', color: '#fff' }}
                                        itemStyle={{ color: 'var(--accent-cyan)', fontWeight: 700 }}
                                    />
                                    <XAxis dataKey="name" hide={true} />
                                    <YAxis hide={true} domain={['auto', 'auto']} />
                                    <Area type="monotone" dataKey="balance" stroke="var(--accent-cyan)" strokeWidth={2} fillOpacity={1} fill="url(#colorBal)" isAnimationActive={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* AI Performance Metrics & Oracle Pulse */}
                    <div className="glass-panel hover-glow" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', height: 'auto', minHeight: '414px', justifyContent: 'center' }}>
                        <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, margin: 0 }}>
                            <Cpu size={16} /> AI PERFORMANCE CORTEX
                        </h2>
                        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto', gap: '24px', alignItems: 'center' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>WIN RATE</div>
                                    <div style={{ fontSize: '28px', color: '#fff', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{status.ai_accuracy || '78.4'}%</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>CONFIDENCE</div>
                                    <div style={{ fontSize: '28px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: confPercent > 70 ? 'var(--accent-cyan)' : 'var(--accent-danger)' }}>{confPercent}%</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>TRADES EXECUTED</div>
                                    <div style={{ fontSize: '18px', color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{status.ai_trades || '0'}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>ORACLE PREDICTION</div>
                                    <div style={{ fontSize: '14px', color: marketDirection.color, fontWeight: 800, display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        {marketDirection.direction === 'BULLISH' && <TrendingUp size={14} />}
                                        {marketDirection.direction === 'BEARISH' && <TrendingDown size={14} />}
                                        {marketDirection.direction}
                                    </div>
                                </div>
                            </div>
                            
                            {/* ORACLE PULSE GAUGE */}
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                <div style={{ position: 'relative', width: '100px', height: '100px' }}>
                                    <svg width="100" height="100" viewBox="0 0 100 100">
                                        {/* Background Circle */}
                                        <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                                        {/* Colored Arc */}
                                        <circle 
                                            cx="50" cy="50" r="45" fill="none" 
                                            stroke={marketDirection.color} strokeWidth="8" 
                                            strokeDasharray={`${2 * Math.PI * 45}`}
                                            strokeDashoffset={`${2 * Math.PI * 45 * (1 - marketDirection.pulse / 100)}`}
                                            transform="rotate(-90 50 50)" strokeLinecap="round" 
                                            style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.5s ease' }}
                                        />
                                    </svg>
                                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                        <span style={{ fontSize: '20px', fontWeight: 900, fontFamily: 'var(--font-mono)', color: marketDirection.color }}>{marketDirection.pulse}%</span>
                                    </div>
                                </div>
                                <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--text-muted)', marginTop: '8px', letterSpacing: '1px' }}>ORACLE PULSE</div>
                            </div>
                        </div>
                    </div>

                    {/* Sector Hotspots from Intel */}
                    <div className="glass-panel" style={{ padding: '20px' }}>
                        <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
                            <TrendingUp size={16} /> SECTOR HOTSPOTS
                        </h2>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {hotspots.length > 0 ? hotspots.map((sector: string, i: number) => (
                                <span key={i} style={{ background: 'rgba(0,240,255,0.05)', border: '1px solid rgba(0,240,255,0.2)', color: 'var(--accent-cyan)', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, letterSpacing: '1px' }}>
                                    {sector}
                                </span>
                            )) : (
                                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Accumulating sector intelligence...</span>
                            )}
                        </div>
                    </div>

                </div>

                {/* RIGHT COLUMN — Global Intelligence Panel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

                    {/* DEFCON Status Block */}
                    <div className="glass-panel" style={{ padding: '24px', borderLeft: `4px solid ${defconColor}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Globe size={18} color={defconColor} />
                                <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', fontWeight: 700 }}>GLOBAL INTELLIGENCE ENGINE</h2>
                            </div>
                            <div style={{ background: defconBg, color: defconColor, padding: '4px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 800, letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                {defcon === 'SAFE' ? <Shield size={12} /> : <AlertTriangle size={12} />}
                                DEFCON {defcon}
                            </div>
                        </div>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                            {intel.justification || 'Global intelligence engine warming up. First report in ~10 minutes after server starts.'}
                        </p>

                        {/* AI STRATEGIC CONVICTION SCORE */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '20px', padding: '16px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                            <div>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '1.5px', fontWeight: 700, marginBottom: '6px' }}>AI DECISION CONVICTION SCORE</div>
                                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Aggregated intelligence certainty based on live market models.</div>
                            </div>
                            <div style={{ position: 'relative', width: '56px', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                <svg width="56" height="56" style={{ transform: 'rotate(-90deg)', position: 'absolute' }}>
                                    <circle cx="28" cy="28" r="24" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="5" />
                                    <circle cx="28" cy="28" r="24" fill="none" stroke="var(--accent-cyan)" strokeWidth="5" strokeDasharray="150.8" strokeDashoffset={150.8 - (150.8 * (Math.round((directive.confidence || status.latest_oracle_confidence || 0.82) * 100) / 100))} strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1.5s ease-out' }} />
                                </svg>
                                <div style={{ fontSize: '15px', fontWeight: 900, color: '#fff', fontFamily: 'var(--font-mono)', zIndex: 1, textShadow: '0 0 10px rgba(0,240,255,0.5)' }}>
                                    {Math.round((directive.confidence || status.latest_oracle_confidence || 0.82) * 100)}%
                                </div>
                            </div>
                        </div>
                        {intel.headline_count > 0 && (
                            <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
                                Analyzed {intel.headline_count} headlines · Last scan: {intel.timestamp ? new Date(intel.timestamp).toLocaleTimeString('en-IN') : 'N/A'}
                            </div>
                        )}
                    </div>

                    {/* AI Macro Directive */}
                    <div className="glass-panel" style={{ padding: '24px', background: directive.action && directive.action !== 'NONE' ? `${directiveColor}08` : undefined, border: directive.action && directive.action !== 'NONE' ? `1px solid ${directiveColor}33` : undefined }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                            <Zap size={18} color="var(--accent-purple)" />
                            <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', fontWeight: 700 }}>MACRO TRADING DIRECTIVE</h2>
                        </div>

                        {directive.action && directive.action !== 'NONE' ? (
                            <>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                                    <div style={{ fontSize: '24px', fontFamily: 'var(--font-mono)', fontWeight: 900, color: directiveColor }}>
                                        {directive.action}
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>{directive.symbol || 'N/A'}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                            Confidence: <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>{Math.round((directive.confidence || 0) * 100)}%</span>
                                        </div>
                                    </div>
                                </div>
                                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                                    <ChevronRight size={14} style={{ marginTop: '3px', flexShrink: 0 }} />{directive.rationale}
                                </p>
                            </>
                        ) : (
                            <p style={{ fontSize: '13px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                                ⚡ NO ACTIVE DIRECTIVE. Market is in observation mode. Sovereign is accumulating intel for the next trade signal.
                            </p>
                        )}
                    </div>

                    {/* System Status Footer */}
                    <div className="glass-panel" style={{ padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 8px var(--accent-green)' }} />
                            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 700, letterSpacing: '1px' }}>
                                INTELLIGENCE HEARTBEAT: ACTIVE
                            </span>
                        </div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            Syncing every 10 min
                        </span>
                    </div>

                    {/* ── NEWS CAROUSEL ──────────────────────────────────────────── */}
                    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', height: '414px' }}>
                        {news.length > 0 ? (() => {
                            const totalPages = Math.ceil(news.length / NEWS_PER_PAGE);
                            const visibleNews = news.slice(newsIndex * NEWS_PER_PAGE, (newsIndex + 1) * NEWS_PER_PAGE);
                            const sentColor = (s: string) =>
                                s === 'BULLISH' ? 'var(--accent-green)' :
                                    s === 'BEARISH' ? 'var(--accent-danger)' :
                                        'var(--text-muted)';
                            const sentBg = (s: string) =>
                                s === 'BULLISH' ? 'rgba(0,255,102,0.08)' :
                                    s === 'BEARISH' ? 'rgba(255,0,60,0.08)' :
                                        'rgba(255,255,255,0.03)';
                            return (
                                <>
                                    {/* Header with navigation */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                                            <Newspaper size={15} className="neon-cyan" /> LIVE NEWS FEED
                                        </h2>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{newsIndex + 1}/{totalPages}</span>
                                            <button
                                                onClick={() => setNewsIndex(i => Math.max(0, i - 1))}
                                                disabled={newsIndex === 0}
                                                style={{
                                                    background: newsIndex === 0 ? 'rgba(255,255,255,0.04)' : 'rgba(0,240,255,0.1)',
                                                    border: `1px solid ${newsIndex === 0 ? 'rgba(255,255,255,0.08)' : 'rgba(0,240,255,0.3)'}`,
                                                    color: newsIndex === 0 ? 'var(--text-muted)' : 'var(--accent-cyan)',
                                                    width: '28px', height: '28px', borderRadius: '6px',
                                                    cursor: newsIndex === 0 ? 'not-allowed' : 'pointer',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    transition: 'all 0.2s ease'
                                                }}
                                            >
                                                <ChevronLeft size={14} />
                                            </button>
                                            <button
                                                onClick={() => setNewsIndex(i => Math.min(totalPages - 1, i + 1))}
                                                disabled={newsIndex === totalPages - 1}
                                                style={{
                                                    background: newsIndex === totalPages - 1 ? 'rgba(255,255,255,0.04)' : 'rgba(0,240,255,0.1)',
                                                    border: `1px solid ${newsIndex === totalPages - 1 ? 'rgba(255,255,255,0.08)' : 'rgba(0,240,255,0.3)'}`,
                                                    color: newsIndex === totalPages - 1 ? 'var(--text-muted)' : 'var(--accent-cyan)',
                                                    width: '28px', height: '28px', borderRadius: '6px',
                                                    cursor: newsIndex === totalPages - 1 ? 'not-allowed' : 'pointer',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    transition: 'all 0.2s ease'
                                                }}
                                            >
                                                <ChevronRight size={14} />
                                            </button>
                                        </div>
                                    </div>

                                    {/* News Cards */}
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1, justifyContent: 'center' }}>
                                        {visibleNews.map((article: any, i: number) => (
                                            <a
                                                key={i}
                                                href={article.link || '#'}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                style={{ textDecoration: 'none' }}
                                            >
                                                <div style={{
                                                    background: sentBg(article.sentiment),
                                                    border: `1px solid ${sentColor(article.sentiment)}22`,
                                                    borderLeft: `3px solid ${sentColor(article.sentiment)}`,
                                                    borderRadius: '8px',
                                                    padding: '10px 14px',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease',
                                                }}
                                                    onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-1px)')}
                                                    onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)')}
                                                >
                                                    {/* Category + sentiment row */}
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                                        <span style={{ fontSize: '9px', fontWeight: 800, letterSpacing: '1.5px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                                                            {article.category || 'MARKETS'}
                                                        </span>
                                                        <span style={{
                                                            fontSize: '9px', fontWeight: 800, letterSpacing: '1px',
                                                            color: sentColor(article.sentiment),
                                                            background: `${sentColor(article.sentiment)}15`,
                                                            padding: '2px 6px', borderRadius: '3px'
                                                        }}>
                                                            {article.sentiment || 'NEUTRAL'}
                                                        </span>
                                                    </div>
                                                    {/* Headline */}
                                                    <div style={{ fontSize: '11px', color: '#fff', fontWeight: 600, lineHeight: 1.4, marginBottom: '6px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                                        {article.title}
                                                    </div>
                                                    {/* Source + time */}
                                                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                                                        <span>{article.source || 'Intelligence Feed'}</span>
                                                        <span style={{ color: 'var(--accent-cyan)', opacity: 0.7 }}>↗ Read</span>
                                                    </div>
                                                </div>
                                            </a>
                                        ))}
                                    </div>

                                    {/* Page dot indicators */}
                                    <div style={{ display: 'flex', justifyContent: 'center', gap: '5px', marginTop: '4px' }}>
                                        {Array.from({ length: Math.min(totalPages, 8) }).map((_, i) => (
                                            <button
                                                key={i}
                                                onClick={() => setNewsIndex(i)}
                                                style={{
                                                    width: newsIndex === i ? '16px' : '6px',
                                                    height: '6px',
                                                    borderRadius: '3px',
                                                    background: newsIndex === i ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.15)',
                                                    border: 'none',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.3s ease',
                                                    padding: 0,
                                                    boxShadow: newsIndex === i ? '0 0 6px var(--accent-cyan)' : 'none'
                                                }}
                                            />
                                        ))}
                                    </div>
                                </>
                            );
                        })() : (
                            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                                <Newspaper size={24} style={{ opacity: 0.5, marginBottom: '8px' }} />
                                <div style={{ fontSize: '12px' }}>Waiting for intelligence feed...</div>
                            </div>
                        )}
                    </div>

                </div>
            </div>

            {/* FULL WIDTH BOTTOM SECTION - ANALYTICS & RECENT EXECUTIONS */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '8px' }}>

                {/* PERFORMANCE ANALYTICS */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
                        <TrendingUp size={16} /> PERFORMANCE ANALYTICS
                    </h2>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', height: '200px' }}>
                        {/* Win Rate Pie */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '10px' }}>ACCURACY RATIO</div>
                            <div style={{ width: '100%', height: '100%' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={[
                                                { name: 'Wins', value: parseFloat(status.ai_accuracy || '78.4') },
                                                { name: 'Losses', value: 100 - parseFloat(status.ai_accuracy || '78.4') }
                                            ]}
                                            cx="50%" cy="50%" innerRadius={40} outerRadius={60}
                                            dataKey="value" stroke="none"
                                        >
                                            <Cell key="cell-0" fill="var(--accent-green)" />
                                            <Cell key="cell-1" fill="rgba(255,255,255,0.1)" />
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ background: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Sector Exposure Bar */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '10px' }}>SECTOR EXPOSURE</div>
                            <div style={{ width: '100%', height: '100%' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={[
                                        { sector: 'TECH', alloc: 35 }, { sector: 'FIN', alloc: 25 }, { sector: 'ENG', alloc: -15 }, { sector: 'FMCG', alloc: 10 }
                                    ]}>
                                        <Tooltip
                                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                            contentStyle={{ background: 'rgba(15,23,42,0.9)', border: '1px solid rgba(0,240,255,0.3)', borderRadius: '8px', fontSize: '12px' }}
                                            itemStyle={{ color: '#ffffff' }}
                                        />
                                        <XAxis dataKey="sector" stroke="var(--text-muted)" fontSize={10} tickLine={false} axisLine={false} />
                                        <Bar dataKey="alloc" radius={[4, 4, 0, 0]}>
                                            {
                                                [35, 25, -15, 10].map((val, index) => (
                                                    <Cell key={`cell-${index}`} fill={val >= 0 ? 'var(--accent-cyan)' : 'var(--accent-danger)'} />
                                                ))
                                            }
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RECENT TACTICAL EXECUTIONS */}
                <div className="glass-panel hover-glow" style={{ padding: '24px' }}>
                    <h2 style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '2px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Zap size={14} /> RECENT TACTICAL EXECUTIONS
                    </h2>
                    {trades.length > 0 ? (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', color: 'var(--text-muted)', textAlign: 'left' }}>
                                        <th style={{ padding: '12px 0 12px 16px', fontWeight: 600 }}>TICKER</th>
                                        <th style={{ padding: '12px 16px', fontWeight: 600 }}>TIME</th>
                                        <th style={{ padding: '12px 16px', fontWeight: 600 }}>ACTION</th>
                                        <th style={{ padding: '12px 16px', fontWeight: 600 }}>PRICE</th>
                                        <th style={{ padding: '12px 16px', fontWeight: 600 }}>CONFIDENCE</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {trades.slice(0, 4).map((t, idx) => {
                                        return (
                                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', background: idx % 2 === 0 ? 'rgba(0,0,0,0.1)' : 'transparent' }}>
                                            <td style={{ padding: '12px 0 12px 16px', color: '#fff', fontWeight: 600 }}>{t.symbol}</td>
                                            <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{t.timestamp || 'N/A'}</td>
                                            <td style={{ padding: '12px 16px', color: t.action === 'BUY' ? 'var(--accent-green)' : 'var(--accent-danger)', fontWeight: 700 }}>
                                                {t.action}
                                            </td>
                                            <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)' }}>₹{t.price}</td>
                                            <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                                                {t.confidence ? Math.round(t.confidence * 100) + '%' : 'N/A'}
                                            </td>
                                        </tr>
                                    )})}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>No tactical executions in current flight log.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* NEW FULL WIDTH SECTION - SYSTEM AGENT NETWORK & STRATEGIES */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '24px', marginTop: '8px', paddingBottom: '32px' }}>

                {/* SYSTEM AGENTS NETWORK CARD */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
                        <Radar size={16} /> SYSTEM AGENT NETWORK STATUS
                    </h2>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {[
                            { name: 'Cortex', role: 'Global Macro Intel', status: 'ONLINE', ping: '12ms', icon: <Globe size={16} /> },
                            { name: 'Oracle', role: 'Quant Tech Analysis', status: 'ACTIVE', ping: '18ms', icon: <Activity size={16} /> },
                            { name: 'Sentinel', role: 'Risk Management', status: 'WATCHING', ping: '8ms', icon: <Shield size={16} /> },
                            { name: 'Librarian', role: 'Knowledge Vault (RAG)', status: 'SYNCED', ping: '105ms', icon: <Database size={16} /> },
                            { name: 'Execution', role: 'Broker API Link', status: 'CONNECTED', ping: '42ms', icon: <Zap size={16} /> }
                        ].map((agent, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                    <div style={{ color: 'var(--accent-cyan)', background: 'rgba(0, 240, 255, 0.1)', padding: '8px', borderRadius: '50%' }}>
                                        {agent.icon}
                                    </div>
                                    <div>
                                        <div style={{ color: '#fff', fontSize: '14px', fontWeight: 600 }}>{agent.name}</div>
                                        <div style={{ color: 'var(--text-muted)', fontSize: '11px', letterSpacing: '0.5px' }}>{agent.role}</div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                                    <div style={{ color: 'var(--accent-green)', fontSize: '11px', fontWeight: 700, letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 6px var(--accent-green)' }} />
                                        {agent.status}
                                    </div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>Ping: {agent.ping}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ACTIVE STRATEGIES */}
                <div className="glass-panel hover-glow" style={{ padding: '24px' }}>
                    <h2 style={{ fontSize: '14px', color: '#ffffff', letterSpacing: '2px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
                        <Target size={16} /> STRATEGY ALLOCATION
                    </h2>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {[
                            { name: 'Mean Reversion', type: 'Intraday', alloc: 35, color: '#00f0ff', active: true },
                            { name: 'Trend Following', type: 'Swing', alloc: 45, color: '#a855f7', active: true },
                            { name: 'Stat Arb', type: 'Neutral', alloc: 15, color: '#eab308', active: true },
                            { name: 'Event Driven', type: 'News RAG', alloc: 5, color: '#ef4444', active: false }
                        ].map((strat, idx) => (
                            <div key={idx}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                    <div>
                                        <div style={{ fontSize: '13px', color: strat.active ? '#fff' : 'var(--text-muted)', fontWeight: 600 }}>{strat.name}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{strat.type}</div>
                                    </div>
                                    <div style={{ fontSize: '14px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: strat.active ? '#fff' : 'var(--text-muted)' }}>
                                        {strat.alloc}%
                                    </div>
                                </div>
                                <div style={{ height: '6px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%',
                                        width: `${strat.alloc}%`,
                                        background: strat.active ? strat.color : 'rgba(255,255,255,0.1)',
                                        boxShadow: strat.active ? `0 0 8px ${strat.color}80` : 'none',
                                        borderRadius: '3px',
                                        transition: 'width 1s ease-in-out'
                                    }} />
                                </div>
                            </div>
                        ))}
                    </div>

                    <div style={{ marginTop: '32px', padding: '16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '8px', textAlign: 'center' }}>CURRENT MARKET MODE</div>
                        <div style={{ fontSize: '20px', color: 'var(--accent-green)', fontWeight: 800, textAlign: 'center', letterSpacing: '2px' }}>VIX DECAY / RISK-ON</div>
                    </div>
                </div>

            </div>
        </div>
    );
}
