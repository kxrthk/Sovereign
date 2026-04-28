import { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Search, ChevronDown, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from 'recharts';

interface SymEntry { symbol: string; label: string; }
const FALLBACK: SymEntry[] = [
    { symbol: 'RELIANCE.NS', label: 'RELIANCE INDUSTRIES' },
    { symbol: 'TCS.NS', label: 'TATA CONSULTANCY' },
    { symbol: 'HDFCBANK.NS', label: 'HDFC BANK' },
    { symbol: 'INFY.NS', label: 'INFOSYS' },
    { symbol: 'ICICIBANK.NS', label: 'ICICI BANK' },
    { symbol: 'SBIN.NS', label: 'STATE BANK OF INDIA' },
    { symbol: 'ITC.NS', label: 'ITC' },
    { symbol: 'TATASTEEL.NS', label: 'TATA STEEL' },
];

interface ForecastPoint { day: string; bullish: number; bearish: number; current?: number; }

function buildForecast(price: number, rsi: number, confidence: number, signal: string): ForecastPoint[] {
    const days = ['Now', '1D', '2D', '3D', '5D', '7D', '10D', '14D'];
    const bullMomentum = signal === 'BUY' ? 0.008 : signal === 'SELL' ? 0.002 : 0.004;
    const bearMomentum = signal === 'SELL' ? 0.008 : signal === 'BUY' ? 0.002 : 0.004;
    const vol = (100 - confidence * 100) * 0.0003 + 0.002;

    const data: ForecastPoint[] = [];
    let bull = price, bear = price;
    for (let i = 0; i < days.length; i++) {
        if (i === 0) {
            data.push({ day: days[i], bullish: price, bearish: price, current: price });
        } else {
            const drift = i * 0.15;
            bull = bull * (1 + bullMomentum + vol * Math.sin(drift) * 0.4);
            bear = bear * (1 - bearMomentum - vol * Math.cos(drift) * 0.3);
            data.push({ day: days[i], bullish: Math.round(bull * 100) / 100, bearish: Math.round(bear * 100) / 100 });
        }
    }
    return data;
}

export default function QuantCenter() {
    const [ticker, setTicker] = useState('ITC.NS');
    const [searchText, setSearchText] = useState('');
    const [showPicker, setShowPicker] = useState(false);
    const [allSymbols, setAllSymbols] = useState<SymEntry[]>(FALLBACK);
    const [isScanning, setIsScanning] = useState(false);
    const [analysis, setAnalysis] = useState<any[]>([]);
    const [forecast, setForecast] = useState<ForecastPoint[]>([]);
    const [livePrice, setLivePrice] = useState(0);
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        (async () => {
            try {
                const res = await fetch('http://127.0.0.1:8000/api/watchlist');
                const data = await res.json();
                const entries: SymEntry[] = [];
                const seen = new Set<string>();
                for (const [, items] of Object.entries(data)) {
                    for (const item of items as any[]) {
                        if (!seen.has(item.symbol)) {
                            entries.push({ symbol: item.symbol, label: item.label || item.symbol });
                            seen.add(item.symbol);
                        }
                    }
                }
                if (entries.length > 0) setAllSymbols(entries);
            } catch {}
        })();
    }, []);

    const filtered = allSymbols.filter(s =>
        s.symbol.includes(searchText.toUpperCase()) || s.label.toUpperCase().includes(searchText.toUpperCase())
    );

    const handleSelect = (sym: string) => { setTicker(sym); setShowPicker(false); setSearchText(''); };

    const runAnalysis = async () => {
        if (!ticker) return;
        setErrorMsg(''); setIsScanning(true); setAnalysis([]); setForecast([]);
        try {
            const [analysisRes, priceRes] = await Promise.all([
                axios.post('/api/vision_analyze', { context: ticker }),
                axios.get(`/api/price/${encodeURIComponent(ticker)}`),
            ]);
            const items = analysisRes.data;
            const price = priceRes.data?.price || 0;
            setLivePrice(price);
            setAnalysis(items);

            if (price > 0) {
                const map: any = {};
                items.forEach((d: any) => { map[d.label] = d.value; });
                const rsi = parseFloat(map['RSI (14)']) || 50;
                const conf = parseFloat(map['ORACLE CONFIDENCE']) / 100 || 0.7;
                const sig = map['CURRENT SIGNAL'] || 'HOLD';
                setForecast(buildForecast(price, rsi, conf, sig));
            }
        } catch (err: any) {
            setErrorMsg(err?.response?.data?.detail || err.message || 'Engine offline.');
        } finally { setIsScanning(false); }
    };

    const signal = analysis.find(a => a.label === 'CURRENT SIGNAL')?.value || '';
    const isBuy = signal === 'BUY';

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* ── Header ──────────────────────────────────────────── */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: 40, height: 40, borderRadius: '10px', background: 'rgba(0,240,255,0.08)', border: '1px solid rgba(0,240,255,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Activity size={20} color="var(--accent-cyan)" />
                </div>
                <div>
                    <h2 style={{ margin: 0, fontSize: '18px', letterSpacing: '2px', color: 'var(--text-primary)' }}>QUANTITATIVE <span className="neon-cyan">ORACLE</span></h2>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)' }}>PREDICTIVE ANALYSIS ENGINE</div>
                </div>
            </div>

            {/* ── Control Bar: Search + Execute + Compact Results ── */}
            <div className="glass-panel" style={{ padding: '16px', display: 'flex', gap: '12px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
                {/* Symbol picker */}
                <div style={{ position: 'relative', width: '200px', flexShrink: 0 }}>
                    <button onClick={() => setShowPicker(!showPicker)} style={{
                        width: '100%', padding: '10px 14px', background: 'var(--sub-panel-bg)',
                        border: '1px solid var(--border-light)', borderRadius: '8px', color: 'var(--accent-cyan)',
                        fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '13px', cursor: 'pointer',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                        <span>{ticker}</span>
                        <ChevronDown size={14} color="var(--accent-cyan)" style={{ transform: showPicker ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                    </button>
                    {showPicker && (
                        <div style={{ position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: '8px', zIndex: 999, overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
                            <div style={{ padding: '8px', position: 'relative' }}>
                                <Search size={14} style={{ position: 'absolute', left: '18px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                <input placeholder="Search name or symbol…" value={searchText} onChange={e => setSearchText(e.target.value)}
                                    onKeyDown={e => { if (e.key === 'Enter' && searchText) handleSelect(searchText.toUpperCase().includes('.') ? searchText.toUpperCase() : searchText.toUpperCase() + '.NS'); }}
                                    autoFocus style={{ width: '100%', background: 'var(--sub-panel-bg)', border: '1px solid var(--border-light)', borderRadius: '6px', color: 'var(--text-primary)', padding: '8px 10px 8px 32px', fontSize: '12px', fontFamily: 'var(--font-mono)', outline: 'none', boxSizing: 'border-box' }} />
                            </div>
                            <div style={{ maxHeight: '220px', overflowY: 'auto' }}>
                                {filtered.map(s => (
                                    <button key={s.symbol} onClick={() => handleSelect(s.symbol)} style={{ width: '100%', padding: '7px 14px', background: 'none', border: 'none', color: s.symbol === ticker ? 'var(--accent-cyan)' : 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: s.symbol === ticker ? 700 : 400, cursor: 'pointer', textAlign: 'left', borderTop: '1px solid rgba(255,255,255,0.03)', display: 'flex', justifyContent: 'space-between' }}>
                                        <span style={{ color: 'var(--text-muted)', fontSize: '10px', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '8px' }}>{s.label}</span>
                                        <span style={{ fontWeight: 700, flexShrink: 0 }}>{s.symbol.replace('.NS','')}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Execute button */}
                <button onClick={runAnalysis} disabled={isScanning} style={{
                    padding: '10px 24px', borderRadius: '8px', border: '1px solid var(--accent-cyan)',
                    background: isScanning ? 'rgba(0,240,255,0.05)' : 'rgba(0,240,255,0.1)',
                    color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontWeight: 800,
                    fontSize: '12px', letterSpacing: '2px', cursor: isScanning ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0,
                }}>
                    {isScanning ? <><div style={{ width: 12, height: 12, border: '2px solid rgba(0,240,255,0.2)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} /> SCANNING…</> : <><Zap size={13} /> ANALYZE</>}
                </button>

                {/* Compact results strip */}
                {analysis.length > 0 && (
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', flex: 1, alignItems: 'center' }}>
                        {analysis.map((item, i) => {
                            const isSignal = item.label === 'CURRENT SIGNAL';
                            const sigColor = item.value === 'BUY' ? 'var(--accent-green)' : item.value === 'SELL' ? 'var(--accent-danger)' : 'var(--accent-warning)';
                            return (
                                <div key={i} style={{
                                    padding: '6px 12px', borderRadius: '6px',
                                    background: isSignal ? `${sigColor}15` : 'rgba(255,255,255,0.02)',
                                    border: `1px solid ${isSignal ? sigColor + '40' : 'rgba(255,255,255,0.06)'}`,
                                    display: 'flex', flexDirection: 'column', gap: '2px',
                                }}>
                                    <span style={{ fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '1px', fontFamily: 'var(--font-mono)' }}>{item.label}</span>
                                    <span style={{ fontSize: isSignal ? '14px' : '12px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: isSignal ? sigColor : 'var(--text-primary)' }}>{item.value}</span>
                                </div>
                            );
                        })}
                    </div>
                )}
                {errorMsg && <div style={{ fontSize: '11px', color: 'var(--accent-danger)', fontFamily: 'var(--font-mono)', padding: '6px 12px' }}>{errorMsg}</div>}
            </div>

            {/* ── Main: Prediction Chart ───────────────────────────── */}
            <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                {forecast.length > 0 ? (
                    <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <div>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>PRICE FORECAST · {ticker.replace('.NS','')}</div>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>14-day projected trajectory based on technical indicators</div>
                            </div>
                            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <div style={{ width: 12, height: 3, borderRadius: 2, background: 'var(--accent-green)' }} />
                                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>BULLISH PATH</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <div style={{ width: 12, height: 3, borderRadius: 2, background: 'var(--accent-danger)' }} />
                                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>BEARISH PATH</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <div style={{ width: 12, height: 3, borderRadius: 2, background: 'var(--accent-warning)', opacity: 0.6 }} />
                                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>CURRENT PRICE</span>
                                </div>
                            </div>
                        </div>

                        {/* Big chart */}
                        <div style={{ flex: 1, minHeight: 0 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={forecast} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                                    <defs>
                                        <linearGradient id="bullGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--accent-green)" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="var(--accent-green)" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="bearGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--accent-danger)" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="var(--accent-danger)" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                    <XAxis dataKey="day" tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} tickLine={false} label={{ value: 'DURATION', position: 'insideBottom', offset: -5, fill: 'rgba(148,163,184,0.5)', fontSize: 9, fontFamily: 'JetBrains Mono, monospace', letterSpacing: 2 }} />
                                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} tickLine={false} domain={['auto', 'auto']} tickFormatter={(v: number) => `₹${v.toFixed(0)}`} width={65} />
                                    <Tooltip contentStyle={{ background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(0,240,255,0.3)', borderRadius: '8px', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }} formatter={(value: any, name: string) => [`₹${Number(value).toFixed(2)}`, name === 'bullish' ? 'Bullish' : name === 'bearish' ? 'Bearish' : 'Current']} labelStyle={{ color: 'var(--text-muted)', fontSize: '10px' }} />
                                    <ReferenceLine y={livePrice} stroke="var(--accent-warning)" strokeDasharray="5 5" strokeOpacity={0.5} label={{ value: `₹${livePrice.toFixed(0)}`, position: 'right', fill: 'var(--accent-warning)', fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                                    <Area type="monotone" dataKey="bullish" stroke="var(--accent-green)" strokeWidth={2.5} fill="url(#bullGrad)" fillOpacity={1} dot={{ r: 4, fill: 'var(--accent-green)', strokeWidth: 0 }} activeDot={{ r: 6, stroke: 'var(--accent-green)', strokeWidth: 2, fill: '#05050F' }} isAnimationActive={true} animationDuration={1500} />
                                    <Area type="monotone" dataKey="bearish" stroke="var(--accent-danger)" strokeWidth={2.5} fill="url(#bearGrad)" fillOpacity={1} dot={{ r: 4, fill: 'var(--accent-danger)', strokeWidth: 0 }} activeDot={{ r: 6, stroke: 'var(--accent-danger)', strokeWidth: 2, fill: '#05050F' }} isAnimationActive={true} animationDuration={1500} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Forecast summary */}
                        <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
                            <div style={{ flex: 1, padding: '12px 16px', borderRadius: '10px', background: 'rgba(0,255,102,0.04)', border: '1px solid rgba(0,255,102,0.12)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                                    <TrendingUp size={12} color="var(--accent-green)" />
                                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '1.5px', fontFamily: 'var(--font-mono)' }}>BULLISH TARGET (14D)</span>
                                </div>
                                <div style={{ fontSize: '22px', fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                                    ₹{forecast[forecast.length - 1]?.bullish.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                </div>
                                <div style={{ fontSize: '10px', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                                    +{((forecast[forecast.length - 1]?.bullish / livePrice - 1) * 100).toFixed(2)}%
                                </div>
                            </div>
                            <div style={{ flex: 1, padding: '12px 16px', borderRadius: '10px', background: 'rgba(255,0,60,0.04)', border: '1px solid rgba(255,0,60,0.12)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                                    <TrendingDown size={12} color="var(--accent-danger)" />
                                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '1.5px', fontFamily: 'var(--font-mono)' }}>BEARISH TARGET (14D)</span>
                                </div>
                                <div style={{ fontSize: '22px', fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--accent-danger)' }}>
                                    ₹{forecast[forecast.length - 1]?.bearish.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                </div>
                                <div style={{ fontSize: '10px', color: 'var(--accent-danger)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                                    {((forecast[forecast.length - 1]?.bearish / livePrice - 1) * 100).toFixed(2)}%
                                </div>
                            </div>
                            <div style={{ flex: 1, padding: '12px 16px', borderRadius: '10px', background: isBuy ? 'rgba(0,255,102,0.04)' : 'rgba(255,0,60,0.04)', border: `1px solid ${isBuy ? 'rgba(0,255,102,0.12)' : 'rgba(255,0,60,0.12)'}` }}>
                                <div style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '1.5px', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>AI RECOMMENDATION</div>
                                <div style={{ fontSize: '22px', fontWeight: 900, fontFamily: 'var(--font-mono)', color: isBuy ? 'var(--accent-green)' : signal === 'SELL' ? 'var(--accent-danger)' : 'var(--accent-warning)' }}>{signal || 'HOLD'}</div>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                                    {analysis.find(a => a.label === 'ORACLE CONFIDENCE')?.value || ''} confidence
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', opacity: 0.5 }}>
                        <Activity size={48} color="var(--accent-cyan)" strokeWidth={1} />
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.8 }}>
                            Select a target asset and execute analysis.<br />
                            <span style={{ color: 'var(--accent-cyan)', fontSize: '11px' }}>Prediction graph will appear with bullish & bearish trajectories.</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
