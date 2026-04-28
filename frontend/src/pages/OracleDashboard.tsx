import { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { Activity, Brain, Target, TrendingUp, TrendingDown, ArrowRight, Zap, RefreshCw, Layers } from 'lucide-react';

interface OracleFactor {
    symbol: string;
    price: number;
    change_pct: number;
    signal: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    prediction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    prediction_strength: number;
    cycle_phase: string;
    rsi: number;
    atr_pct: number;
    adx: number;
    stoch_rsi: number;
    ema9: number;
    ema21: number;
    vwap: number;
    supertrend_bullish: boolean;
    vol_ratio: number;
    reason: string;
}

export default function OracleDashboard() {
    const [data, setData] = useState<OracleFactor[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastScan, setLastScan] = useState<Date | null>(null);
    const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/api/oracle_scan');
            const unique = Array.from(new Map(res.data.map((item: OracleFactor) => [item.symbol, item])).values()) as OracleFactor[];
            setData(unique);
            if (unique.length > 0 && !selectedSymbol) {
                setSelectedSymbol(unique[0].symbol);
            }
            setLastScan(new Date());
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const selectedData = data.find(d => d.symbol === selectedSymbol) || data[0];

    const getRadarData = (d: OracleFactor | undefined) => {
        if (!d) return [];
        return [
            { factor: 'RSI', value: d.rsi, fullMark: 100 },
            { factor: 'Momentum', value: Math.min(d.adx * 2, 100), fullMark: 100 },
            { factor: 'Volume', value: Math.min(d.vol_ratio * 30, 100), fullMark: 100 },
            { factor: 'StochRSI', value: d.stoch_rsi, fullMark: 100 },
            { factor: 'VWAP', value: Math.min(50 + (((d.price - d.vwap) / d.vwap) * 100 * 20), 100), fullMark: 100 },
            { factor: 'EMA Trend', value: d.ema9 > d.ema21 ? 80 : 20, fullMark: 100 },
            { factor: 'Supertrend', value: d.supertrend_bullish ? 90 : 10, fullMark: 100 },
            { factor: 'Volatility', value: Math.min(d.atr_pct * 30, 100), fullMark: 100 },
        ];
    };

    const radarData = getRadarData(selectedData);
    const buys = data.filter(d => d.signal === 'BUY').sort((a,b) => b.confidence - a.confidence);
    const sells = data.filter(d => d.signal === 'SELL').sort((a,b) => b.confidence - a.confidence);

    const getPredictionColor = (pred: string) => {
        if (pred === 'BULLISH') return 'var(--accent-green)';
        if (pred === 'BEARISH') return 'var(--accent-danger)';
        return 'var(--accent-cyan)';
    };

    return (
        <div style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
            
            {/* Header */}
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ width: '48px', height: '48px', background: 'rgba(176, 38, 255, 0.1)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-purple)', border: '1px solid rgba(176, 38, 255, 0.3)' }}>
                        <Brain size={28} />
                    </div>
                    <div>
                        <h1 style={{ fontSize: '24px', margin: 0, fontWeight: 800, letterSpacing: '1px' }}>ORACLE <span className="neon-purple">CORTEX</span></h1>
                        <p style={{ color: 'var(--text-muted)', fontSize: '12px', margin: 0, fontFamily: 'var(--font-mono)' }}>
                            10-Factor Self-Sufficient Prediction Engine
                        </p>
                    </div>
                </div>
                
                <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>SCANNED ASSETS</div>
                        <div style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{data.length} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>/ 65</span></div>
                    </div>
                    <div style={{ width: '1px', height: '40px', background: 'var(--border-light)' }} />
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>LAST CYCLE</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                            {lastScan ? lastScan.toLocaleTimeString() : '--:--:--'}
                        </div>
                    </div>
                    <button 
                        onClick={fetchData}
                        className="glow-btn"
                        style={{ height: '40px', padding: '0 16px', background: 'rgba(0, 240, 255, 0.1)', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                        <RefreshCw size={16} className={loading ? 'spin' : ''} />
                        FORCE SCAN
                    </button>
                </div>
            </div>

            {/* Main Content: Heatmap + Radar side by side */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', flex: 1, minHeight: 0 }}>
                
                {/* Left: Market Heatmap */}
                <div className="glass-panel" style={{ padding: '20px', overflow: 'auto' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                        <Layers size={18} className="neon-purple" />
                        <h2 style={{ fontSize: '16px', margin: 0, letterSpacing: '1px' }}>MARKET HEATMAP</h2>
                    </div>
                    
                    {loading && data.length === 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px', color: 'var(--text-muted)' }}>
                            <RefreshCw size={32} className="spin" style={{ marginRight: '10px' }} /> Initializing Oracle Tensor Matrix...
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px' }}>
                            {[...data].sort((a, b) => a.symbol.localeCompare(b.symbol)).map(d => {
                                const isSelected = selectedSymbol === d.symbol;
                                let bg = 'rgba(255, 255, 255, 0.02)';
                                let border = 'rgba(255, 255, 255, 0.05)';
                                if (d.signal === 'BUY') {
                                    bg = `rgba(0, 255, 102, ${0.05 + (d.confidence * 0.2)})`;
                                    border = `rgba(0, 255, 102, ${0.2 + d.confidence})`;
                                } else if (d.signal === 'SELL') {
                                    bg = `rgba(255, 0, 60, ${0.05 + (d.confidence * 0.2)})`;
                                    border = `rgba(255, 0, 60, ${0.2 + d.confidence})`;
                                }
                                return (
                                    <div 
                                        key={d.symbol}
                                        onClick={() => setSelectedSymbol(d.symbol)}
                                        style={{ background: bg, border: `1px solid ${isSelected ? 'var(--accent-purple)' : border}`, boxShadow: isSelected ? '0 0 15px rgba(176, 38, 255, 0.4)' : 'none', borderRadius: '6px', padding: '8px', cursor: 'pointer', transition: 'all 0.2s ease', position: 'relative', overflow: 'hidden' }}
                                        className="hover-glow"
                                    >
                                        <div style={{ fontSize: '11px', fontWeight: 800 }}>{d.symbol.replace('.NS', '')}</div>
                                        <div style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginTop: '2px' }}>
                                            ₹{d.price.toFixed(2)} <span style={{ color: d.change_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-danger)' }}>
                                                {d.change_pct >= 0 ? '+' : ''}{d.change_pct.toFixed(2)}%
                                            </span>
                                        </div>
                                        <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                            {d.prediction === 'BULLISH' && <TrendingUp size={12} color="var(--accent-green)" />}
                                            {d.prediction === 'BEARISH' && <TrendingDown size={12} color="var(--accent-danger)" />}
                                            {d.prediction === 'NEUTRAL' && <ArrowRight size={12} color="var(--accent-cyan)" />}
                                            <div style={{ fontSize: '9px', fontWeight: 800, color: d.signal === 'BUY' ? 'var(--accent-green)' : d.signal === 'SELL' ? 'var(--accent-danger)' : 'var(--text-muted)' }}>
                                                {d.signal !== 'HOLD' ? `${(d.confidence * 100).toFixed(0)}%` : '--'}
                                            </div>
                                        </div>
                                        {d.signal !== 'HOLD' && (
                                            <div style={{ position: 'absolute', bottom: 0, left: 0, height: '2px', background: d.signal === 'BUY' ? 'var(--accent-green)' : 'var(--accent-danger)', width: `${d.confidence * 100}%` }} />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Right: Cortex Analysis — Compact Square */}
                {selectedData ? (
                    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflow: 'auto' }}>
                        {/* Symbol Header */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h2 style={{ fontSize: '18px', margin: 0 }}>{selectedData.symbol.replace('.NS', '')}</h2>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                                    ₹{selectedData.price.toFixed(2)} | <span style={{ color: selectedData.signal === 'BUY' ? 'var(--accent-green)' : selectedData.signal === 'SELL' ? 'var(--accent-danger)' : 'var(--text-muted)', fontWeight: 800 }}>{selectedData.signal}</span>
                                </div>
                            </div>
                            {/* Prediction badge inline */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: `rgba(${selectedData.prediction === 'BULLISH' ? '0,255,102' : selectedData.prediction === 'BEARISH' ? '255,0,60' : '0,240,255'}, 0.1)`, border: `2px solid ${getPredictionColor(selectedData.prediction)}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    {selectedData.prediction === 'BULLISH' && <TrendingUp size={18} color="var(--accent-green)" />}
                                    {selectedData.prediction === 'BEARISH' && <TrendingDown size={18} color="var(--accent-danger)" />}
                                    {selectedData.prediction === 'NEUTRAL' && <ArrowRight size={18} color="var(--accent-cyan)" />}
                                </div>
                                <div>
                                    <div style={{ fontSize: '14px', fontWeight: 800, color: getPredictionColor(selectedData.prediction), letterSpacing: '1px' }}>{selectedData.prediction}</div>
                                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{selectedData.prediction_strength}% STRENGTH</div>
                                </div>
                            </div>
                        </div>

                        {/* Radar Chart — primary visual */}
                        <div style={{ flex: 1, minHeight: '320px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                    <PolarAngleAxis dataKey="factor" tick={{ fill: '#FFFFFF', fontSize: 12, fontWeight: 700, fontFamily: "'Rajdhani', sans-serif" }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar name={selectedData.symbol} dataKey="value" stroke="var(--accent-purple)" fill="var(--accent-purple)" fillOpacity={0.3} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Bottom section: stats + rationale */}
                        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {/* Compact stats row */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                            <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', borderLeft: '2px solid var(--accent-purple)' }}>
                                <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>CYCLE PHASE</div>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>{selectedData.cycle_phase.replace('_', ' ')}</div>
                            </div>
                            <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', borderLeft: `2px solid ${selectedData.vol_ratio > 1 ? 'var(--accent-green)' : 'var(--accent-danger)'}` }}>
                                <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>VOL RATIO</div>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>{selectedData.vol_ratio.toFixed(2)}x</div>
                            </div>
                            <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', borderLeft: `2px solid ${selectedData.confidence > 0.7 ? 'var(--accent-green)' : 'var(--accent-cyan)'}` }}>
                                <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>CONFIDENCE</div>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>{(selectedData.confidence * 100).toFixed(0)}%</div>
                            </div>
                        </div>

                        {/* Rationale */}
                        <div style={{ padding: '12px 14px', background: 'rgba(0,0,0,0.3)', borderRadius: '6px', fontSize: '13px', color: 'var(--text-secondary)', borderLeft: `3px solid ${selectedData.signal === 'BUY' ? 'var(--accent-green)' : selectedData.signal === 'SELL' ? 'var(--accent-danger)' : 'var(--text-muted)'}`, lineHeight: '1.5' }}>
                            <strong>Rationale:</strong> {selectedData.reason}
                        </div>
                        </div> {/* end bottom section */}
                    </div>
                ) : (
                    <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                        Select a symbol from the heatmap to view Cortex analysis.
                    </div>
                )}
            </div>

            {/* Bottom: Top Signals — full width */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div className="glass-panel" style={{ padding: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--accent-green)' }}>
                        <Zap size={14} />
                        <h3 style={{ fontSize: '13px', margin: 0, letterSpacing: '1px' }}>TOP BULLISH SIGNALS</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {buys.slice(0, 5).map(b => (
                            <div key={b.symbol} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 10px', background: 'rgba(0,255,102,0.05)', borderRadius: '5px', border: '1px solid rgba(0,255,102,0.1)', cursor: 'pointer' }} onClick={() => setSelectedSymbol(b.symbol)} className="hover-glow">
                                <span style={{ fontWeight: 700, fontSize: '12px' }}>{b.symbol.replace('.NS', '')}</span>
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-green)', fontWeight: 800 }}>{(b.confidence * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                        {buys.length === 0 && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>No strong buy signals active.</div>}
                    </div>
                </div>

                <div className="glass-panel" style={{ padding: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--accent-danger)' }}>
                        <Target size={14} />
                        <h3 style={{ fontSize: '13px', margin: 0, letterSpacing: '1px' }}>TOP BEARISH SIGNALS</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {sells.slice(0, 5).map(s => (
                            <div key={s.symbol} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 10px', background: 'rgba(255,0,60,0.05)', borderRadius: '5px', border: '1px solid rgba(255,0,60,0.1)', cursor: 'pointer' }} onClick={() => setSelectedSymbol(s.symbol)} className="hover-glow">
                                <span style={{ fontWeight: 700, fontSize: '12px' }}>{s.symbol.replace('.NS', '')}</span>
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-danger)', fontWeight: 800 }}>{(s.confidence * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                        {sells.length === 0 && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>No strong sell signals active.</div>}
                    </div>
                </div>
            </div>
            
        </div>
    );
}
