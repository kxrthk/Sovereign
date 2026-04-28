import { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, TrendingUp, TrendingDown, Activity, Zap, Target, BarChart2, RefreshCw, Search } from 'lucide-react';

interface Candidate {
    symbol: string;
    price: number;
    rsi: number;
    oracle_confidence?: number;
    signal?: 'BUY' | 'SELL' | 'WATCH' | 'HOLD';
    sma200?: number;
    change_pct?: number;
    // New fields
    prediction?: string;
    cycle_phase?: string;
    vol_ratio?: number;
    adx?: number;
    vwap?: number;
    supertrend_bullish?: boolean;
}

function SignalBadge({ signal }: { signal?: string }) {
    const map: Record<string, { color: string; bg: string }> = {
        BUY: { color: 'var(--accent-green)', bg: 'rgba(0,255,102,0.1)' },
        SELL: { color: 'var(--accent-danger)', bg: 'rgba(255,0,60,0.1)' },
        WATCH: { color: 'var(--accent-warning)', bg: 'rgba(245,158,11,0.1)' },
        HOLD: { color: 'var(--text-muted)', bg: 'rgba(255,255,255,0.05)' },
    };
    const s = map[signal || 'WATCH'] || map.WATCH;
    return (
        <span style={{ background: s.bg, color: s.color, border: `1px solid ${s.color}40`, padding: '3px 10px', borderRadius: '4px', fontSize: '10px', fontWeight: 800, letterSpacing: '1px' }}>
            {signal || 'WATCH'}
        </span>
    );
}

function RsiBar({ rsi }: { rsi: number }) {
    const color = rsi > 70 ? 'var(--accent-danger)' : rsi < 30 ? 'var(--accent-green)' : 'var(--accent-cyan)';
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
            <div style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', position: 'relative' }}>
                <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${Math.min(rsi, 100)}%`, background: color, borderRadius: '2px', transition: 'width 0.5s ease' }} />
                <div style={{ position: 'absolute', left: '30%', top: '-2px', width: '1px', height: '8px', background: 'rgba(255,255,255,0.2)' }} />
                <div style={{ position: 'absolute', left: '70%', top: '-2px', width: '1px', height: '8px', background: 'rgba(255,255,255,0.2)' }} />
            </div>
            <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color, minWidth: '35px', textAlign: 'right' }}>{rsi.toFixed(1)}</span>
        </div>
    );
}

function ConfidenceArc({ value }: { value: number }) {
    const pct = Math.round(value * 100);
    const color = pct >= 80 ? 'var(--accent-green)' : pct >= 60 ? 'var(--accent-warning)' : 'var(--accent-danger)';
    return (
        <div style={{ position: 'relative', width: '48px', height: '48px', flexShrink: 0 }}>
            <svg width="48" height="48" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="18" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
                <circle cx="24" cy="24" r="18" fill="none" stroke={color} strokeWidth="4"
                    strokeDasharray={`${2 * Math.PI * 18}`}
                    strokeDashoffset={`${2 * Math.PI * 18 * (1 - pct / 100)}`}
                    transform="rotate(-90 24 24)" strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.6s ease' }}
                />
            </svg>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color }}>{pct}%</div>
        </div>
    );
}

// Generates demo candidates when backend doesn't return live scan data
function demoCandidates(): Candidate[] {
    return [
        { symbol: 'RELIANCE.NS', price: 2987.45, rsi: 44.2, oracle_confidence: 0.87, signal: 'BUY', change_pct: 0.82, adx: 35.2, vwap: 2980.1, supertrend_bullish: true, vol_ratio: 1.8, prediction: 'BULLISH', cycle_phase: 'MID_BULL' },
        { symbol: 'TCS.NS', price: 3842.10, rsi: 48.6, oracle_confidence: 0.81, signal: 'BUY', change_pct: 0.31, adx: 22.1, vwap: 3840.0, supertrend_bullish: true, vol_ratio: 1.2, prediction: 'BULLISH', cycle_phase: 'EARLY_BULL' },
        { symbol: 'HDFCBANK.NS', price: 1724.30, rsi: 42.1, oracle_confidence: 0.76, signal: 'WATCH', change_pct: -0.12, adx: 18.5, vwap: 1730.2, supertrend_bullish: false, vol_ratio: 0.9, prediction: 'NEUTRAL', cycle_phase: 'CONSOLIDATION' },
    ];
}

export default function Scanner() {
    const [candidates, setCandidates] = useState<Candidate[]>(demoCandidates());
    const [scanning, setScanning] = useState(false);
    const [lastScan, setLastScan] = useState<Date | null>(null);
    const [sortBy, setSortBy] = useState<'confidence' | 'rsi' | 'change'>('confidence');
    const [signalFilter, setSignalFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'WATCH' | 'HOLD'>('ALL');
    const [searchQuery, setSearchQuery] = useState('');

    const runScan = async () => {
        setScanning(true);
        try {
            const res = await axios.get('/api/oracle_scan', { timeout: 120000 });
            const data = res.data?.length > 0 ? res.data : demoCandidates();
            // Map confidence field correctly if different
            const mapped = data.map((d: any) => ({ ...d, oracle_confidence: d.confidence || d.oracle_confidence || 0 }));
            setCandidates(mapped);
            setLastScan(new Date());
        } catch (err) {
            console.error("Scanner Sweep Failed:", err);
            setLastScan(new Date());
        } finally {
            setScanning(false);
        }
    };

    useEffect(() => { runScan(); }, []);

    const sorted = [...candidates]
        .filter(c => signalFilter === 'ALL' || c.signal === signalFilter || (signalFilter === 'WATCH' && c.signal === 'HOLD'))
        .filter(c => c.symbol.toLowerCase().includes(searchQuery.toLowerCase()))
        .sort((a, b) => {
            if (sortBy === 'confidence') return (b.oracle_confidence || 0) - (a.oracle_confidence || 0);
            if (sortBy === 'rsi') return a.rsi - b.rsi;
            if (sortBy === 'change') return (b.change_pct || 0) - (a.change_pct || 0);
            return 0;
        });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '17px', color: 'var(--text-primary)', letterSpacing: '2px', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                        <Radar size={18} className="neon-cyan" /> ALPHA SCANNER
                    </h2>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        10-Factor AI Analysis & Pattern Prediction Matrix
                        {lastScan && ` · Last scan: ${lastScan.toLocaleTimeString('en-IN')}`}
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                        <Search size={14} style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }} />
                        <input 
                            type="text" 
                            placeholder="Search asset..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{ 
                                background: 'rgba(0,0,0,0.3)', 
                                border: '1px solid rgba(255,255,255,0.08)', 
                                color: 'var(--text-primary)', 
                                padding: '8px 12px 8px 36px', 
                                borderRadius: '8px', 
                                fontSize: '12px',
                                outline: 'none',
                                width: '200px',
                                transition: 'all 0.2s ease',
                            }}
                            onFocus={(e) => Object.assign(e.target.style, { borderColor: 'var(--accent-cyan)', boxShadow: '0 0 10px rgba(0,240,255,0.1)' })}
                            onBlur={(e) => Object.assign(e.target.style, { borderColor: 'rgba(255,255,255,0.08)', boxShadow: 'none' })}
                        />
                    </div>
                    <button
                        onClick={runScan} disabled={scanning}
                        style={{ background: 'rgba(0,240,255,0.08)', border: '1px solid rgba(0,240,255,0.3)', color: 'var(--accent-cyan)', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700 }}
                    >
                        <RefreshCw size={13} style={{ animation: scanning ? 'spin 1s linear infinite' : 'none' }} />
                        {scanning ? 'SCANNING...' : 'RUN SCAN'}
                    </button>
                </div>
            </div>

            {/* Filter + Sort controls */}
            <div className="glass-panel" style={{ padding: '14px 20px', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: '6px' }}>
                    {(['ALL', 'BUY', 'HOLD', 'SELL'] as const).map(s => (
                        <button key={s} onClick={() => setSignalFilter(s)}
                            style={{ background: signalFilter === s ? 'rgba(0,240,255,0.1)' : 'transparent', border: signalFilter === s ? '1px solid var(--accent-cyan)' : '1px solid rgba(255,255,255,0.08)', color: signalFilter === s ? 'var(--accent-cyan)' : 'var(--text-muted)', padding: '4px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '11px', fontWeight: 700, letterSpacing: '1px' }}>
                            {s}
                        </button>
                    ))}
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Sort:</span>
                    {(['confidence', 'rsi', 'change'] as const).map(s => (
                        <button key={s} onClick={() => setSortBy(s)}
                            style={{ background: sortBy === s ? 'rgba(0,240,255,0.08)' : 'transparent', border: sortBy === s ? '1px solid rgba(0,240,255,0.4)' : '1px solid rgba(255,255,255,0.06)', color: sortBy === s ? 'var(--accent-cyan)' : 'var(--text-muted)', padding: '4px 10px', borderRadius: '5px', cursor: 'pointer', fontSize: '11px', fontWeight: 700 }}>
                            {s === 'confidence' ? 'Oracle' : s === 'rsi' ? 'RSI' : 'Change'}
                        </button>
                    ))}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--accent-green)', fontWeight: 700 }}>
                    {sorted.length} candidate{sorted.length !== 1 ? 's' : ''} found
                </div>
            </div>

            {/* Candidate table */}
            <div style={{ flex: 1, overflowY: 'auto' }}>
                {/* Column headers (Updated for 6 columns) */}
                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1.5fr 1fr 1.5fr', gap: '12px', padding: '8px 20px', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1.5px', fontWeight: 700 }}>
                    <span><Target size={10} style={{ display: 'inline', marginRight: '4px' }} />SYMBOL</span>
                    <span>PRICE</span>
                    <span><BarChart2 size={10} style={{ display: 'inline', marginRight: '4px' }} />RSI (14)</span>
                    <span>TECH (ADX / VWAP)</span>
                    <span>PREDICTION</span>
                    <span><Zap size={10} style={{ display: 'inline', marginRight: '4px' }} />ORACLE SCORE</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {scanning ? (
                        Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="glass-panel" style={{ height: '72px', padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <div style={{ height: '14px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', width: '30%', animation: 'pulse 2s infinite' }} />
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', fontSize: '11px', fontWeight: 700, letterSpacing: '2px', animation: 'pulse 1.5s infinite' }}>
                                    <Activity size={12} /> ANALYZING...
                                </div>
                            </div>
                        ))
                    ) : sorted.length === 0 ? (
                        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
                            <Activity size={32} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                            <div style={{ fontFamily: 'var(--font-mono)', letterSpacing: '2px' }}>NO CANDIDATES MATCH CRITERIA</div>
                        </div>
                    ) : sorted.map((c) => (
                        <div key={c.symbol} className="glass-panel hover-glow" style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1.5fr 1fr 1.5fr', gap: '12px', alignItems: 'center', padding: '16px 20px', transition: 'all 0.15s' }}>
                            {/* SYMBOL */}
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{c.symbol.replace('.NS', '')}</div>
                                    {c.supertrend_bullish !== undefined && (
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: c.supertrend_bullish ? 'var(--accent-green)' : 'var(--accent-danger)' }} title={c.supertrend_bullish ? 'Supertrend Bullish' : 'Supertrend Bearish'} />
                                    )}
                                </div>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    NSE {c.cycle_phase && <span style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>• {c.cycle_phase.replace('_', ' ')}</span>}
                                </div>
                            </div>
                            
                            {/* PRICE */}
                            <div>
                                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>₹{c.price.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                                {c.change_pct !== undefined && (
                                    <div style={{ fontSize: '11px', color: c.change_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-danger)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '2px' }}>
                                        {c.change_pct >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                                        {c.change_pct >= 0 ? '+' : ''}{c.change_pct.toFixed(2)}%
                                    </div>
                                )}
                            </div>
                            
                            {/* RSI */}
                            <RsiBar rsi={c.rsi} />
                            
                            {/* TECH (ADX/VWAP/VOL) */}
                            <div>
                                <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: (c.adx || 0) > 25 ? 'var(--accent-green)' : 'var(--text-muted)' }}>ADX {(c.adx || 0).toFixed(1)}</span>
                                    <span style={{ margin: '0 4px', color: 'var(--border-light)' }}>|</span>
                                    <span>VWAP {c.vwap ? c.vwap.toFixed(1) : '--'}</span>
                                </div>
                                {c.vol_ratio !== undefined && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                                        <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>VOL</div>
                                        <div style={{ flex: 1, height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', position: 'relative' }}>
                                            <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${Math.min((c.vol_ratio / 3) * 100, 100)}%`, background: c.vol_ratio > 1.2 ? 'var(--accent-green)' : c.vol_ratio < 0.8 ? 'var(--accent-danger)' : 'var(--accent-warning)', borderRadius: '1.5px' }} />
                                        </div>
                                    </div>
                                )}
                            </div>
                            
                            {/* PREDICTION */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                {c.prediction === 'BULLISH' && <TrendingUp size={16} color="var(--accent-green)" />}
                                {c.prediction === 'BEARISH' && <TrendingDown size={16} color="var(--accent-danger)" />}
                                {(!c.prediction || c.prediction === 'NEUTRAL') && <Activity size={16} color="var(--text-muted)" />}
                                <div style={{ fontSize: '12px', fontWeight: 800, color: c.prediction === 'BULLISH' ? 'var(--accent-green)' : c.prediction === 'BEARISH' ? 'var(--accent-danger)' : 'var(--text-muted)' }}>
                                    {c.prediction || 'NEUTRAL'}
                                </div>
                            </div>
                            
                            {/* ORACLE SCORE & SIGNAL */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <ConfidenceArc value={c.oracle_confidence || 0} />
                                <SignalBadge signal={c.signal} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
