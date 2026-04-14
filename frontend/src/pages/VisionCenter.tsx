import { useState } from 'react';
import axios from 'axios';
import { Activity, Search } from 'lucide-react';

export default function QuantCenter() {
    const [ticker, setTicker] = useState<string>('ITC.NS');
    const [isScanning, setIsScanning] = useState(false);
    const [analysis, setAnalysis] = useState<any[]>([]);
    const [errorMsg, setErrorMsg] = useState<string>('');

    const runAnalysis = async () => {
        if (!ticker) return;

        setErrorMsg('');
        setIsScanning(true);
        setAnalysis([]);

        try {
            const res = await axios.post('/api/vision_analyze', {
                context: ticker
            });

            setIsScanning(false);
            setAnalysis(res.data);
        } catch (err: any) {
            setIsScanning(false);
            setErrorMsg(err.message || '[CRITICAL FAILURE] Quant Engine offline.');
        }
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '18px', color: 'var(--text-primary)', letterSpacing: '2px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={20} className="neon-cyan" /> QUANTITATIVE ORACLE ENGINE
            </h2>

            <div className="vision-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: '24px', flex: 1 }}>

                {/* Input Panel */}
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', padding: '24px' }}>
                    <h3 style={{ fontSize: '14px', letterSpacing: '1px', marginBottom: '16px', color: 'var(--text-secondary)' }}>
                        TARGET ASSET
                    </h3>

                    <div style={{ position: 'relative', marginBottom: '24px' }}>
                        <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            type="text"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            style={{
                                width: '100%',
                                background: 'rgba(0,0,0,0.5)',
                                border: '1px solid var(--border-light)',
                                padding: '12px 12px 12px 40px',
                                color: 'var(--text-primary)',
                                borderRadius: '8px',
                                fontSize: '16px',
                                fontFamily: 'var(--font-mono)'
                            }}
                            placeholder="e.g. RELIANCE.NS"
                            onKeyDown={(e) => e.key === 'Enter' && runAnalysis()}
                        />
                    </div>

                    <button
                        className="glow-btn"
                        onClick={runAnalysis}
                        disabled={isScanning}
                        style={{
                            background: 'var(--bg-surface)',
                            border: '1px solid var(--accent-cyan)',
                            color: 'var(--accent-cyan)',
                            padding: '16px',
                            borderRadius: '8px',
                            cursor: isScanning ? 'not-allowed' : 'pointer',
                            fontFamily: 'var(--font-heading)',
                            fontSize: '16px',
                            letterSpacing: '2px',
                            fontWeight: 700,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px',
                            transition: 'all 0.2s'
                        }}
                    >
                        {isScanning ? (
                            <><div className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(0, 240, 255, 0.2)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} /> PROCESSING...</>
                        ) : (
                            'EXECUTE QUANT ANALYSIS'
                        )}
                    </button>

                    <div style={{ marginTop: 'auto', fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                        <span style={{ color: 'var(--accent-cyan)' }}>NOTE:</span> The Quant Engine computes pure non-lagging mathematical variables (Fibonacci, Bollinger Bounds, RSI divergence) directly from Live Exchange OHLCV arrays, eliminating generative AI hallucinations.
                    </div>
                </div>

                {/* Readout Panel */}
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
                    <h3 style={{ padding: '16px', borderBottom: '1px solid var(--border-light)', fontSize: '12px', letterSpacing: '2px', color: 'var(--text-muted)' }}>
                        ALGORITHMIC OUTPUT
                    </h3>
                    <div className="crt-effect" style={{ flex: 1, padding: '24px', background: 'rgba(0, 0, 0, 0.4)', overflowY: 'auto' }}>

                        {errorMsg && <div style={{ color: 'var(--accent-danger)', fontFamily: 'var(--font-mono)', fontSize: '14px' }}>{errorMsg}</div>}

                        {!isScanning && analysis.length === 0 && !errorMsg && (
                            <div style={{ opacity: 0.5, fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--accent-green)' }}>
                                Awaiting target coordinates...
                            </div>
                        )}

                        {analysis.length > 0 && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                {analysis.map((item, idx) => (
                                    <div key={idx} style={{
                                        padding: '16px',
                                        background: 'max(rgba(0, 240, 255, 0.05), rgba(10, 10, 15, 0.8))',
                                        borderLeft: '2px solid var(--accent-cyan)',
                                        borderRadius: '0 8px 8px 0'
                                    }}>
                                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', letterSpacing: '1px', marginBottom: '4px' }}>
                                            {item.label}
                                        </div>
                                        <div style={{ fontSize: '16px', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                                            {item.value}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
