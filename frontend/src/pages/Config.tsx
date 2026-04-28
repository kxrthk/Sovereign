import { useState, useEffect, useRef, useCallback } from 'react';
import { Settings, ShieldAlert, Cpu, Radio, Network, TerminalSquare, ChevronDown } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════
//  RISK PROFILES — wave behaviour per tolerance level
// ═══════════════════════════════════════════════════════════════════════
type RiskLevel = 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';

interface WaveLayer {
    color: string;       // r, g, b
    baseAmp: number;     // height multiplier
    freq: number;        // sine frequency
    speed: number;       // phase speed
    width: number;       // stroke width
    glow: number;        // shadow blur px
}

interface RiskProfile {
    layers: WaveLayer[];
    speedMultiplier: number;    // global phase speed
    spikeIntensity: number;     // heartbeat spike height
    dotColor: string;           // r, g, b
    borderRgb: string;          // r, g, b  for border/glow
    statusLabel: string;
    statusColor: string;        // CSS value
    boxGlow: string;            // CSS box-shadow value
    dashStyle: number[];        // baseline dash pattern
    noiseAmount: number;        // extra random jitter (0 = none)
}

const RISK_PROFILES: Record<RiskLevel, RiskProfile> = {
    CONSERVATIVE: {
        layers: [
            { color: '0, 200, 220',  baseAmp: 0.18, freq: 0.8,  speed: 0.55, width: 2.0, glow: 10 }, // soft teal primary
            { color: '80, 160, 255', baseAmp: 0.10, freq: 1.2,  speed: 0.35, width: 1.4, glow:  7 }, // calm blue
            { color: '0, 210, 180',  baseAmp: 0.06, freq: 1.8,  speed: 0.25, width: 0.9, glow:  5 }, // quiet aqua harmonic
        ],
        speedMultiplier: 0.45,
        spikeIntensity: 0.45,
        dotColor: '80, 200, 255',
        borderRgb: '0, 200, 220',
        statusLabel: '◈  CONSERVATIVE PROTOCOL — LOW RISK',
        statusColor: '#00C8DC',
        boxGlow: '0 0 24px rgba(0, 200, 220, 0.07), inset 0 0 40px rgba(0, 0, 0, 0.5)',
        dashStyle: [6, 12],
        noiseAmount: 0,
    },
    MODERATE: {
        layers: [
            { color: '0, 240, 255',  baseAmp: 0.38, freq: 1.0,  speed: 1.00, width: 2.5, glow: 18 }, // cyan primary
            { color: '176, 38, 255', baseAmp: 0.25, freq: 1.4,  speed: 0.70, width: 1.8, glow: 14 }, // purple
            { color: '0, 255, 102',  baseAmp: 0.15, freq: 2.1,  speed: 1.30, width: 1.2, glow: 10 }, // green harmonic
        ],
        speedMultiplier: 1.0,
        spikeIntensity: 1.2,
        dotColor: '0, 240, 255',
        borderRgb: '0, 240, 255',
        statusLabel: '◈  NEURAL LINK ACTIVE — MODERATE',
        statusColor: 'var(--accent-cyan)',
        boxGlow: '0 0 30px rgba(0, 240, 255, 0.06), inset 0 0 40px rgba(0, 0, 0, 0.4)',
        dashStyle: [4, 8],
        noiseAmount: 0,
    },
    AGGRESSIVE: {
        layers: [
            { color: '255, 80, 0',   baseAmp: 0.55, freq: 1.2,  speed: 1.60, width: 3.0, glow: 24 }, // hot orange primary
            { color: '255, 0, 60',   baseAmp: 0.38, freq: 2.2,  speed: 1.10, width: 2.0, glow: 18 }, // red surge
            { color: '245, 158, 11', baseAmp: 0.22, freq: 3.3,  speed: 2.00, width: 1.4, glow: 12 }, // amber harmonic
        ],
        speedMultiplier: 1.75,
        spikeIntensity: 2.2,
        dotColor: '255, 80, 0',
        borderRgb: '255, 80, 0',
        statusLabel: '⚡  AGGRESSIVE PROTOCOL — HIGH RISK',
        statusColor: '#FF5000',
        boxGlow: '0 0 40px rgba(255, 80, 0, 0.12), 0 0 80px rgba(255, 0, 60, 0.06), inset 0 0 40px rgba(0, 0, 0, 0.4)',
        dashStyle: [2, 6],
        noiseAmount: 2.5,
    },
};

// ═══════════════════════════════════════════════════════════════════════
//  SOVEREIGN HEARTBEAT — risk-aware canvas animation
// ═══════════════════════════════════════════════════════════════════════
function SovereignHeartbeat({ isOnline, riskLevel }: { isOnline: boolean; riskLevel: RiskLevel }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animRef = useRef<number>(0);
    const phaseRef = useRef(0);
    const amplitudeRef = useRef(isOnline ? 1 : 0);
    // Smooth profile transition
    const profileAmpRef = useRef({ CONSERVATIVE: 0, MODERATE: 1, AGGRESSIVE: 0 } as Record<RiskLevel, number>);

    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width;
        const H = rect.height;

        ctx.clearRect(0, 0, W, H);

        // ── System online/offline amplitude lerp ──────────────────
        const onlineTarget = isOnline ? 1.0 : 0.0;
        amplitudeRef.current += (onlineTarget - amplitudeRef.current) * 0.04;
        const amp = amplitudeRef.current;

        // ── Profile blend — lerp each profile's weight ─────────────
        const profileWeights = profileAmpRef.current;
        const allLevels: RiskLevel[] = ['CONSERVATIVE', 'MODERATE', 'AGGRESSIVE'];
        for (const lvl of allLevels) {
            const target = lvl === riskLevel ? 1.0 : 0.0;
            profileWeights[lvl] += (target - profileWeights[lvl]) * 0.03;
        }

        // ── Active profile (primary) ────────────────────────────────
        const profile = RISK_PROFILES[riskLevel];

        // Phase speed is a blend of the active profile
        const blendedSpeed =
            profileWeights.CONSERVATIVE * RISK_PROFILES.CONSERVATIVE.speedMultiplier +
            profileWeights.MODERATE     * RISK_PROFILES.MODERATE.speedMultiplier +
            profileWeights.AGGRESSIVE   * RISK_PROFILES.AGGRESSIVE.speedMultiplier;

        phaseRef.current += 0.03 * blendedSpeed * (0.3 + amp * 0.7);
        const phase = phaseRef.current;
        const midY = H / 2;

        // Blended spike intensity
        const blendedSpike =
            profileWeights.CONSERVATIVE * RISK_PROFILES.CONSERVATIVE.spikeIntensity +
            profileWeights.MODERATE     * RISK_PROFILES.MODERATE.spikeIntensity +
            profileWeights.AGGRESSIVE   * RISK_PROFILES.AGGRESSIVE.spikeIntensity;

        // ── Draw blended wave layers ────────────────────────────────
        // We blend between profiles visually during transition
        for (const lvl of allLevels) {
            const w = profileWeights[lvl];
            if (w < 0.01) continue;
            const p = RISK_PROFILES[lvl];

            for (const layer of p.layers) {
                const layerAmp = layer.baseAmp * amp * midY * w;
                if (layerAmp < 0.5) continue;

                ctx.beginPath();
                ctx.strokeStyle = `rgba(${layer.color}, ${(0.1 + amp * 0.8) * w})`;
                ctx.lineWidth = layer.width * w;
                ctx.shadowColor = `rgba(${layer.color}, ${amp * 0.5 * w})`;
                ctx.shadowBlur = layer.glow * amp * w;
                ctx.lineJoin = 'round';
                ctx.lineCap = 'round';

                for (let x = 0; x <= W; x += 1) {
                    const t = x / W;
                    const sine = Math.sin(t * Math.PI * 2 * layer.freq + phase * layer.speed);
                    const spike = Math.exp(-Math.pow((t * 4 - 1.0 - (phase * layer.speed * 0.15) % 4) * 3, 2));
                    const harmonic = Math.sin(t * Math.PI * 2 * layer.freq * 3.17 + phase * layer.speed * 1.6) * 0.18;

                    // Aggressive noise jitter
                    const noise = p.noiseAmount > 0 ? (Math.random() - 0.5) * p.noiseAmount * amp * w * 0.3 : 0;

                    const y = midY + (sine * 0.5 + spike * blendedSpike * 0.5 + harmonic) * layerAmp + noise;

                    if (x === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }
                ctx.stroke();
                ctx.shadowBlur = 0;
            }
        }

        // ── Baseline dash ───────────────────────────────────────────
        ctx.beginPath();
        ctx.strokeStyle = `rgba(148, 163, 184, ${0.05 + (1 - amp) * 0.08})`;
        ctx.lineWidth = 1;
        ctx.setLineDash(profile.dashStyle);
        ctx.moveTo(0, midY);
        ctx.lineTo(W, midY);
        ctx.stroke();
        ctx.setLineDash([]);

        // ── Scanner dot ─────────────────────────────────────────────
        if (amp > 0.05) {
            const dotX = ((phase * 0.14) % 1) * W;
            const t = dotX / W;
            const sine = Math.sin(t * Math.PI * 2 * profile.layers[0].freq + phase * profile.layers[0].speed);
            const spike = Math.exp(-Math.pow((t * 4 - 1.0 - (phase * 0.15) % 4) * 3, 2));
            const dotY = midY + (sine * 0.5 + spike * blendedSpike * 0.5) * profile.layers[0].baseAmp * amp * midY;

            const dotRgb = profile.dotColor;
            const dotR = 12 + profileWeights.AGGRESSIVE * 6; // aggressive dot is bigger

            const grad = ctx.createRadialGradient(dotX, dotY, 0, dotX, dotY, dotR * amp);
            grad.addColorStop(0,   `rgba(${dotRgb}, ${0.9 * amp})`);
            grad.addColorStop(0.5, `rgba(${dotRgb}, ${0.2 * amp})`);
            grad.addColorStop(1,   `rgba(${dotRgb}, 0)`);
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(dotX, dotY, dotR * amp, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = `rgba(255, 255, 255, ${0.95 * amp})`;
            ctx.beginPath();
            ctx.arc(dotX, dotY, (2.5 + profileWeights.AGGRESSIVE * 1.5) * amp, 0, Math.PI * 2);
            ctx.fill();
        }

        // ── Aggressive: extra voltage sparks ────────────────────────
        if (profileWeights.AGGRESSIVE > 0.3 && amp > 0.1) {
            const sparkCount = Math.floor(profileWeights.AGGRESSIVE * 3 * amp);
            for (let s = 0; s < sparkCount; s++) {
                const sx = (phase * 0.77 + s * 0.37) % 1 * W;
                const sy = midY + (Math.sin(sx / W * Math.PI * 8 + phase * 3) * 0.3 * midY * amp);
                const sparkAlpha = Math.random() * 0.6 * profileWeights.AGGRESSIVE * amp;

                ctx.fillStyle = `rgba(255, 160, 0, ${sparkAlpha})`;
                ctx.beginPath();
                ctx.arc(sx, sy, 1 + Math.random() * 2, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        animRef.current = requestAnimationFrame(draw);
    }, [isOnline, riskLevel]);

    useEffect(() => {
        animRef.current = requestAnimationFrame(draw);
        return () => cancelAnimationFrame(animRef.current);
    }, [draw]);

    const profile = RISK_PROFILES[riskLevel];
    const borderRgb = profile.borderRgb;
    const statusColor = isOnline ? profile.statusColor : 'var(--text-muted)';
    const statusText = isOnline ? profile.statusLabel : '◈  SYSTEMS OFFLINE';

    const canvasBorder = isOnline
        ? `1px solid rgba(${borderRgb}, 0.3)`
        : `1px solid rgba(148, 163, 184, 0.08)`;

    const boxShadow = isOnline ? profile.boxGlow : 'inset 0 0 40px rgba(0, 0, 0, 0.4)';

    return (
        <div style={{ position: 'relative', width: '100%' }}>
            {/* Status row */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginBottom: '8px', padding: '0 4px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {/* Pulsing status dot */}
                    <div style={{
                        width: 8, height: 8, borderRadius: '50%',
                        background: statusColor,
                        boxShadow: isOnline ? `0 0 8px ${statusColor}, 0 0 20px ${statusColor}` : 'none',
                        transition: 'all 1s ease'
                    }} />
                    <span style={{
                        fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 700,
                        letterSpacing: '2px', color: statusColor,
                        textShadow: isOnline ? `0 0 10px ${statusColor}` : 'none',
                        transition: 'all 1s ease'
                    }}>
                        {statusText}
                    </span>
                </div>
                <span style={{
                    fontSize: '9px', fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)', letterSpacing: '1px'
                }}>
                    SOVEREIGN TELEMETRY v3.0
                </span>
            </div>

            {/* Canvas container */}
            <div style={{
                position: 'relative', borderRadius: '8px',
                border: canvasBorder,
                background: 'rgba(3, 3, 5, 0.6)', overflow: 'hidden',
                boxShadow,
                transition: 'border-color 1s ease, box-shadow 1s ease'
            }}>
                {/* Grid overlay */}
                <div style={{
                    position: 'absolute', inset: 0, opacity: 0.03, pointerEvents: 'none',
                    backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                                      linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
                    backgroundSize: '20px 20px'
                }} />

                {/* Aggressive red edge bleed */}
                {riskLevel === 'AGGRESSIVE' && isOnline && (
                    <div style={{
                        position: 'absolute', inset: 0, pointerEvents: 'none',
                        background: 'linear-gradient(90deg, rgba(255,0,60,0.05) 0%, transparent 20%, transparent 80%, rgba(255,80,0,0.05) 100%)',
                        borderRadius: '8px'
                    }} />
                )}

                {/* Conservative soft glow */}
                {riskLevel === 'CONSERVATIVE' && isOnline && (
                    <div style={{
                        position: 'absolute', inset: 0, pointerEvents: 'none',
                        background: 'radial-gradient(ellipse at 50% 100%, rgba(0,200,220,0.04) 0%, transparent 70%)',
                        borderRadius: '8px'
                    }} />
                )}

                <canvas
                    ref={canvasRef}
                    style={{ width: '100%', height: '80px', display: 'block' }}
                />
            </div>

            {/* Risk level indicator chips */}
            <div style={{
                display: 'flex', gap: '6px', marginTop: '8px', justifyContent: 'flex-end'
            }}>
                {(['CONSERVATIVE', 'MODERATE', 'AGGRESSIVE'] as RiskLevel[]).map((lvl) => {
                    const p = RISK_PROFILES[lvl];
                    const isActive = lvl === riskLevel && isOnline;
                    return (
                        <div key={lvl} style={{
                            fontSize: '8px', fontFamily: 'var(--font-mono)', fontWeight: 700,
                            letterSpacing: '1px', padding: '2px 7px', borderRadius: '3px',
                            border: `1px solid rgba(${p.borderRgb}, ${isActive ? 0.5 : 0.12})`,
                            color: isActive ? p.statusColor : 'var(--text-muted)',
                            background: isActive ? `rgba(${p.borderRgb}, 0.08)` : 'transparent',
                            textShadow: isActive ? `0 0 8px ${p.statusColor}` : 'none',
                            transition: 'all 0.8s ease'
                        }}>
                            {lvl.slice(0, 4)}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════
//  CONFIG PAGE
// ═══════════════════════════════════════════════════════════════════════
export default function Config({ theme, setTheme }: { theme?: string, setTheme?: any }) {
    const [autoTrade, setAutoTrade] = useState(true);
    const [extremeNews, setExtremeNews] = useState(false);
    const [riskLevel, setRiskLevel] = useState<RiskLevel>('MODERATE');
    const [loading, setLoading] = useState(true);
    const [cortexLogs, setCortexLogs] = useState('System Online. Awaiting logs...');
    const [showCortex, setShowCortex] = useState(false);
    const cortexBottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!showCortex) return;
        const fetchLogs = async () => {
            try {
                const res = await fetch('http://127.0.0.1:8000/api/cortex_log');
                const data = await res.json();
                if (data.log_text) setCortexLogs(data.log_text);
            } catch {}
        };
        fetchLogs();
        const inv = setInterval(fetchLogs, 5000);
        return () => clearInterval(inv);
    }, [showCortex]);

    useEffect(() => {
        fetch('http://127.0.0.1:8000/api/settings')
            .then(res => res.json())
            .then(data => {
                setAutoTrade(data.trading_mode === 'AUTO_PILOT');
                const lvl = data.risk_tolerance || 'MODERATE';
                setRiskLevel(lvl as RiskLevel);
                setExtremeNews(data.ignore_macro || false);
                setLoading(false);
            })
            .catch(() => setLoading(false));
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
        setAutoTrade(!autoTrade);
        saveSettings({ trading_mode: newMode });
    };

    const handleHaltTrading = async () => {
        if (window.confirm('WARNING: Are you sure you want to engage the DEFCON 1 killswitch? This will halt all active trading loops immediately.')) {
            try {
                await fetch('http://127.0.0.1:8000/api/killswitch', { method: 'POST' });
                alert('Killswitch engaged. System halted.');
            } catch (e) {
                alert('Killswitch API failed.');
            }
        }
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '18px', color: 'var(--text-primary)', letterSpacing: '2px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Settings size={20} className="neon-cyan" /> SYSTEM CONFIGURATION
            </h2>

            {/* ── RISK-AWARE HEARTBEAT STRIPE ────────────────────── */}
            <div style={{ marginBottom: '28px' }}>
                <SovereignHeartbeat isOnline={autoTrade && !loading} riskLevel={riskLevel} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px' }}>

                {/* Trading Protocols */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Cpu size={16} /> TRADING PROTOCOLS
                    </h3>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Autonomous Execution</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Allow Sovereign to place market orders without human intervention.</div>
                        </div>
                        <button
                            disabled={loading}
                            onClick={toggleAutoTrade}
                            className={autoTrade ? "glow-btn" : ""}
                            style={{
                                padding: '8px 16px', borderRadius: '4px',
                                border: autoTrade ? '1px solid var(--accent-cyan)' : '1px solid var(--border-light)',
                                background: autoTrade ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
                                color: autoTrade ? 'var(--accent-cyan)' : 'var(--text-muted)',
                                fontWeight: 700, fontSize: '12px', letterSpacing: '1px',
                                cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.5 : 1
                            }}
                        >
                            {autoTrade ? 'ACTIVE' : 'OFFLINE'}
                        </button>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Risk Tolerance</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Algorithmic positioning constraints.</div>
                        </div>
                        <select
                            value={riskLevel}
                            onChange={(e) => {
                                const lvl = e.target.value as RiskLevel;
                                setRiskLevel(lvl);
                                saveSettings({ risk_tolerance: lvl });
                            }}
                            style={{
                                appearance: 'none', background: 'rgba(0, 0, 0, 0.4)',
                                border: `1px solid rgba(${RISK_PROFILES[riskLevel].borderRgb}, 0.4)`,
                                color: RISK_PROFILES[riskLevel].statusColor,
                                padding: '6px 12px', borderRadius: '4px', fontSize: '12px',
                                fontFamily: 'var(--font-mono)', fontWeight: 700,
                                cursor: 'pointer', outline: 'none',
                                transition: 'border-color 0.8s ease, color 0.8s ease'
                            }}
                        >
                            <option value="CONSERVATIVE">CONSERVATIVE</option>
                            <option value="MODERATE">MODERATE</option>
                            <option value="AGGRESSIVE">AGGRESSIVE</option>
                        </select>
                    </div>
                </div>

                {/* Aesthetic Engine (Theme) */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Settings size={16} /> AESTHETIC ENGINE
                    </h3>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>UI/UX Environment</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Shift between original Cyberpunk and Old Greek structurals.</div>
                        </div>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <button
                            onClick={() => setTheme && setTheme('cyberpunk')}
                            className={theme === 'cyberpunk' ? "glow-btn" : ""}
                            style={{
                                flex: 1, padding: '12px', borderRadius: '4px',
                                border: theme === 'cyberpunk' ? '1px solid var(--accent-cyan)' : '1px solid var(--border-light)',
                                background: theme === 'cyberpunk' ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
                                color: theme === 'cyberpunk' ? 'var(--text-primary)' : 'var(--text-muted)',
                                fontWeight: 800, fontSize: '12px', letterSpacing: '1px', cursor: 'pointer',
                                transition: 'all 0.3s ease'
                            }}
                        >
                            SOVEREIGN MK-I
                        </button>
                        <button
                            onClick={() => setTheme && setTheme('hellenic')}
                            className={theme === 'hellenic' ? "glow-btn" : ""}
                            style={{
                                flex: 1, padding: '12px', borderRadius: '4px',
                                border: theme === 'hellenic' ? '1px solid var(--accent-cyan)' : '1px solid var(--border-light)',
                                background: theme === 'hellenic' ? 'var(--accent-cyan)' : 'transparent',
                                color: theme === 'hellenic' ? 'var(--text-primary)' : 'var(--text-muted)',
                                fontWeight: 800, fontSize: '12px', letterSpacing: '1px', cursor: 'pointer',
                                transition: 'all 0.3s ease'
                            }}
                        >
                            HELLENIC
                        </button>
                    </div>
                </div>

                {/* Override Directives */}
                <div className="glass-panel" style={{ padding: '24px', border: '1px solid rgba(255, 0, 60, 0.2)' }}>
                    <h3 style={{ fontSize: '12px', color: 'var(--accent-danger)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ShieldAlert size={16} /> OVERRIDE DIRECTIVES
                    </h3>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <div>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Halt All Trading (DEFCON 1)</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Emergency killswitch to flatten positions and halt actions.</div>
                        </div>
                        <button
                            onClick={handleHaltTrading}
                            className="hover-glow"
                            style={{
                                padding: '8px 16px', borderRadius: '4px',
                                border: '1px solid var(--accent-danger)',
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
                            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Ignore Macro Events</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Force system into Technical-only trading mode.</div>
                        </div>
                        <button
                            onClick={() => {
                                setExtremeNews(!extremeNews);
                                saveSettings({ ignore_macro: !extremeNews });
                            }}
                            className={extremeNews ? "glow-btn" : ""}
                            style={{
                                padding: '8px 16px', borderRadius: '4px',
                                border: extremeNews ? '1px solid var(--accent-warning)' : '1px solid var(--border-light)',
                                background: extremeNews ? 'rgba(245, 158, 11, 0.1)' : 'transparent',
                                color: extremeNews ? 'var(--accent-warning)' : 'var(--text-muted)',
                                fontWeight: 700, fontSize: '12px', letterSpacing: '1px', cursor: 'pointer'
                            }}
                        >
                            {extremeNews ? 'OVERRIDING' : 'BYPASS'}
                        </button>
                    </div>
                </div>

                {/* External Links */}
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

                {/* Cortex Neural Logs — moved from sidebar */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: '1 / -1' }}>
                    <button
                        onClick={() => setShowCortex(!showCortex)}
                        style={{
                            width: '100%', background: 'none', border: 'none', cursor: 'pointer',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: 0, color: 'var(--text-primary)'
                        }}
                    >
                        <h3 style={{ fontSize: '12px', color: 'var(--accent-purple)', letterSpacing: '2px', textTransform: 'uppercase', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <TerminalSquare size={16} /> CORTEX NEURAL LOGS
                        </h3>
                        <ChevronDown size={16} style={{ color: 'var(--text-muted)', transform: showCortex ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }} />
                    </button>
                    {showCortex && (
                        <div style={{
                            marginTop: '16px', padding: '20px',
                            background: 'rgba(0, 0, 0, 0.6)', borderRadius: '8px',
                            border: '1px solid rgba(176, 38, 255, 0.2)',
                            maxHeight: '300px', overflowY: 'auto',
                        }}>
                            <pre style={{
                                margin: 0, fontFamily: 'var(--font-mono)', fontSize: '12px',
                                color: 'var(--text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap'
                            }}>
                                {cortexLogs}
                            </pre>
                            <div ref={cortexBottomRef} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
