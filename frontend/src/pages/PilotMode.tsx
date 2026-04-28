import { useState, useEffect, useRef, useCallback } from 'react';
import { Rocket, Zap, TrendingUp, TrendingDown, Target, RefreshCw, ChevronDown, Brain, Calculator } from 'lucide-react';

// ─── Colour palette ────────────────────────────────────────────────────────────
const C = {
    pink:   '#FF006E',
    blue:   '#00B4FF',
    lime:   '#39FF14',
    amber:  '#FFB800',
    purple: '#9B30FF',
    red:    '#FF3040',
    chrome: '#D4D4D4',
    bg:     '#05050F',
};

// ─── Types ─────────────────────────────────────────────────────────────────────
interface Star { x: number; y: number; r: number; speed: number; opacity: number; twinkle: number; }
interface Particle { x: number; y: number; vx: number; vy: number; life: number; maxLife: number; color: string; size: number; }
interface MissionLog { symbol: string; action: string; qty: number; price: number; time: string; status: string; orderId: string; }

// ═══════════════════════════════════════════════════════════════════════════════
//  SPACE CANVAS — stars, ship, particles, price trail
// ═══════════════════════════════════════════════════════════════════════════════
function SpaceCanvas({ action, launchCounter, onLaunchComplete, balance, symbol, livePrice: livePriceProp }:
    { action: 'BUY' | 'SELL'; launchCounter: number; onLaunchComplete: () => void; balance: number; symbol: string; livePrice: number }) {

    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animRef   = useRef<number>(0);
    const starsRef  = useRef<Star[]>([]);
    const particlesRef = useRef<Particle[]>([]);
    const shipYRef    = useRef(0.5);
    const shipYTarget = useRef(0.5);
    const priceTrailRef = useRef<number[]>([]);
    const launchFrames  = useRef(0);
    const thrustPhase   = useRef(0);
    const lastSymbolRef = useRef('');

    // init stars
    useEffect(() => {
        const count = 180;
        starsRef.current = Array.from({ length: count }, () => ({
            x: Math.random(),
            y: Math.random(),
            r: Math.random() * 1.8 + 0.3,
            speed: Math.random() * 0.0004 + 0.0001,
            opacity: Math.random() * 0.7 + 0.3,
            twinkle: Math.random() * Math.PI * 2,
        }));
    }, []);

    // trigger launch — fires on every new launchCounter increment
    const prevLaunchCounter = useRef(0);
    useEffect(() => {
        if (launchCounter > 0 && launchCounter !== prevLaunchCounter.current) {
            prevLaunchCounter.current = launchCounter;
            launchFrames.current = 90;
            shipYTarget.current = action === 'BUY' ? 0.18 : 0.82;
            shipYRef.current = 0.5; // Start from centre Y

            // Spawn explosion particles
            const canvas = canvasRef.current;
            if (canvas) {
                const cx = canvas.getBoundingClientRect().width * 0.38;
                const cy = canvas.getBoundingClientRect().height * shipYRef.current;
                const color = action === 'BUY' ? C.lime : C.pink;
                for (let i = 0; i < 60; i++) {
                    const angle = Math.random() * Math.PI * 2;
                    const speed = Math.random() * 6 + 2;
                    particlesRef.current.push({
                        x: cx, y: cy,
                        vx: Math.cos(angle) * speed,
                        vy: Math.sin(angle) * speed,
                        life: 1, maxLife: 1,
                        color,
                        size: Math.random() * 4 + 1,
                    });
                }
            }
        }
    }, [launchCounter, action]);

    const drawShip = useCallback((ctx: CanvasRenderingContext2D, x: number, y: number, thrust: number, isBuy: boolean) => {
        ctx.save();
        ctx.translate(x, y);

        // ── Engine thrust flame ───────────────────────────────────
        if (thrust > 0) {
            const flameColor = isBuy ? C.lime : C.pink;
            const flameLen = 30 + Math.random() * 20 * thrust;

            const grad = ctx.createLinearGradient(-flameLen, 0, 10, 0);
            grad.addColorStop(0,   'rgba(255,255,255,0)');
            grad.addColorStop(0.3, `${flameColor}44`);
            grad.addColorStop(0.8, `${flameColor}cc`);
            grad.addColorStop(1,   'var(--text-primary)');

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(-8, -6 * thrust);
            ctx.lineTo(-8 - flameLen, 0);
            ctx.lineTo(-8, 6 * thrust);
            ctx.closePath();
            ctx.fill();

            // secondary inner flame
            ctx.fillStyle = `rgba(255,255,255,${0.6 * thrust})`;
            ctx.beginPath();
            ctx.moveTo(-8, -3 * thrust);
            ctx.lineTo(-8 - flameLen * 0.5, 0);
            ctx.lineTo(-8, 3 * thrust);
            ctx.closePath();
            ctx.fill();
        }

        // ── Body (chrome fuselage) ────────────────────────────────
        const bodyGrad = ctx.createLinearGradient(-18, -10, 18, 10);
        bodyGrad.addColorStop(0,   'var(--text-primary)');
        bodyGrad.addColorStop(0.3, '#aaaacc');
        bodyGrad.addColorStop(0.6, '#6666aa');
        bodyGrad.addColorStop(1,   '#222244');
        ctx.fillStyle = bodyGrad;
        ctx.beginPath();
        ctx.moveTo(22, 0);    // nose
        ctx.lineTo(0, -8);
        ctx.lineTo(-18, -6);
        ctx.lineTo(-22, 0);
        ctx.lineTo(-18, 6);
        ctx.lineTo(0, 8);
        ctx.closePath();
        ctx.fill();

        // ── Wings ─────────────────────────────────────────────────
        const wingColor = isBuy ? C.lime : C.pink;
        ctx.fillStyle = wingColor + '99';
        // top wing
        ctx.beginPath();
        ctx.moveTo(0, -8); ctx.lineTo(-12, -24); ctx.lineTo(-22, -10); ctx.lineTo(-18, -6); ctx.closePath();
        ctx.fill();
        // bottom wing
        ctx.beginPath();
        ctx.moveTo(0, 8); ctx.lineTo(-12, 24); ctx.lineTo(-22, 10); ctx.lineTo(-18, 6); ctx.closePath();
        ctx.fill();

        // Wing accent line
        ctx.strokeStyle = wingColor;
        ctx.lineWidth = 1.5;
        ctx.shadowColor = wingColor;
        ctx.shadowBlur = 8;
        ctx.beginPath(); ctx.moveTo(0, -8); ctx.lineTo(-18, -16); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, 8);  ctx.lineTo(-18, 16);  ctx.stroke();
        ctx.shadowBlur = 0;

        // ── Cockpit dome ──────────────────────────────────────────
        const cockpitGrad = ctx.createRadialGradient(6, -3, 0, 6, -3, 9);
        cockpitGrad.addColorStop(0, 'rgba(0,200,255,0.9)');
        cockpitGrad.addColorStop(1, 'rgba(0,50,120,0.5)');
        ctx.fillStyle = cockpitGrad;
        ctx.beginPath();
        ctx.ellipse(6, 0, 9, 6, 0, 0, Math.PI * 2);
        ctx.fill();

        // ── Glow outline ──────────────────────────────────────────
        ctx.strokeStyle = thrust > 0 ? wingColor : 'rgba(0,200,255,0.4)';
        ctx.lineWidth = 1;
        ctx.shadowColor = thrust > 0 ? wingColor : C.blue;
        ctx.shadowBlur = thrust > 0 ? 16 : 6;
        ctx.beginPath();
        ctx.moveTo(22, 0); ctx.lineTo(0, -8); ctx.lineTo(-18, -6);
        ctx.lineTo(-22, 0); ctx.lineTo(-18, 6); ctx.lineTo(0, 8); ctx.closePath();
        ctx.stroke();
        ctx.shadowBlur = 0;

        ctx.restore();
    }, []);

    const actionRef = useRef(action);
    const balanceRef = useRef(balance);
    const onLaunchCompleteRef = useRef(onLaunchComplete);
    const livePriceRef = useRef(livePriceProp);
    const symbolRef = useRef(symbol);

    useEffect(() => { actionRef.current = action; }, [action]);
    useEffect(() => { balanceRef.current = balance; }, [balance]);
    useEffect(() => { onLaunchCompleteRef.current = onLaunchComplete; }, [onLaunchComplete]);
    useEffect(() => { livePriceRef.current = livePriceProp; }, [livePriceProp]);
    useEffect(() => { symbolRef.current = symbol; }, [symbol]);

    // Fetch real chart data when symbol changes
    useEffect(() => {
        if (!symbol || symbol === lastSymbolRef.current) return;
        lastSymbolRef.current = symbol;
        (async () => {
            try {
                const res = await fetch(`http://127.0.0.1:8000/api/chart_data/${encodeURIComponent(symbol)}`);
                const data = await res.json();
                if (data && data.length > 0) {
                    // Use last 120 close prices as the initial trail
                    const closes = data.map((d: any) => d.close).filter((c: number) => c > 0);
                    priceTrailRef.current = closes.slice(-120);
                }
            } catch {
                priceTrailRef.current = [];
            }
        })();
    }, [symbol]);

    // Append live price ticks to the trail
    useEffect(() => {
        if (livePriceProp > 0 && priceTrailRef.current.length > 0) {
            priceTrailRef.current.push(livePriceProp);
            // Keep max 200 points for smooth rendering
            if (priceTrailRef.current.length > 200) priceTrailRef.current.shift();
        }
    }, [livePriceProp]);

    // Stable ref for drawShip so the loop never re-creates
    const drawShipRef = useRef(drawShip);
    useEffect(() => { drawShipRef.current = drawShip; }, [drawShip]);

    // Single, stable animation loop — never restarts on re-render
    useEffect(() => {
        let running = true;
        const loop = () => {
            if (!running) return;
            const canvas = canvasRef.current;
            if (!canvas) { animRef.current = requestAnimationFrame(loop); return; }
            const ctx = canvas.getContext('2d');
            if (!ctx) { animRef.current = requestAnimationFrame(loop); return; }

            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) { animRef.current = requestAnimationFrame(loop); return; }
            if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
                canvas.width  = rect.width  * dpr;
                canvas.height = rect.height * dpr;
            }
            ctx.save();
            ctx.scale(dpr, dpr);
            const W = rect.width; const H = rect.height;

        // ── Deep space background ─────────────────────────────────
        ctx.fillStyle = C.bg;
        ctx.fillRect(0, 0, W, H);

        // Nebula clouds
        for (let i = 0; i < 3; i++) {
            const nx = (0.2 + i * 0.3) * W;
            const ny = (0.3 + Math.sin(i * 1.3) * 0.3) * H;
            const grad = ctx.createRadialGradient(nx, ny, 0, nx, ny, 120);
            const rgb = i === 0 ? '155,48,255' : i === 1 ? '0,80,180' : '255,0,110';
            grad.addColorStop(0, `rgba(${rgb},0.04)`);
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, W, H);
        }

        // ── Stars ─────────────────────────────────────────────────
        const now = Date.now() * 0.001;
        for (const s of starsRef.current) {
            s.x -= s.speed;
            if (s.x < 0) { s.x = 1; s.y = Math.random(); }
            const twinkle = 0.5 + 0.5 * Math.sin(now * 2 + s.twinkle);
            ctx.fillStyle = `rgba(255,255,255,${s.opacity * twinkle})`;
            ctx.beginPath();
            ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
            ctx.fill();
        }

        // ── Price trail (FULL WIDTH) ─────────────────────────────
        const trailPad = 16;
        const trailX = trailPad;
        const trailW = W - trailPad * 2;
        const trailH = H * 0.75;
        const trailY0 = H * 0.12;
        const trail = priceTrailRef.current;

        if (trail.length < 2) {
            ctx.fillStyle = 'rgba(148,163,184,0.4)';
            ctx.font = `700 11px 'JetBrains Mono', monospace`;
            ctx.textAlign = 'center';
            ctx.fillText('Loading price data…', W / 2, H / 2);
        }

        if (trail.length >= 2) {
        // Find min/max for dynamic scaling
        const trailMin = Math.min(...trail);
        const trailMax = Math.max(...trail);
        const trailRange = trailMax - trailMin || 1;

        // Trail area label
        ctx.fillStyle = 'rgba(148,163,184,0.5)';
        ctx.font = `700 9px 'JetBrains Mono', monospace`;
        ctx.fillText('PRICE TRAJECTORY', trailX, trailY0 - 6);

        // Price labels on right edge
        ctx.textAlign = 'right';
        ctx.fillStyle = 'rgba(148,163,184,0.35)';
        ctx.font = `600 8px 'JetBrains Mono', monospace`;
        for (let g = 0; g <= 4; g++) {
            const gy = trailY0 + (g / 4) * trailH;
            const priceVal = trailMax - (g / 4) * trailRange;
            ctx.fillText(`₹${priceVal.toFixed(1)}`, trailX + trailW, gy - 3);
        }
        ctx.textAlign = 'left';
        // Grid lines
        for (let g = 0; g <= 4; g++) {
            const gy = trailY0 + (g / 4) * trailH;
            ctx.strokeStyle = 'rgba(255,255,255,0.03)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(trailX, gy);
            ctx.lineTo(trailX + trailW, gy);
            ctx.stroke();
        }

        // Build path points
        const pts: [number, number][] = [];
        for (let i = 0; i < trail.length; i++) {
            const px = trailX + (i / (trail.length - 1)) * trailW;
            const norm = (trail[i] - trailMin) / trailRange;
            const py = trailY0 + (1 - norm) * trailH;
            pts.push([px, py]);
        }

        // Gradient fill
        if (pts.length > 2) {
            ctx.beginPath();
            ctx.moveTo(pts[0][0], pts[0][1]);
            for (let i = 1; i < pts.length; i++) {
                ctx.lineTo(pts[i][0], pts[i][1]);
            }
            ctx.lineTo(pts[pts.length - 1][0], trailY0 + trailH);
            ctx.lineTo(pts[0][0], trailY0 + trailH);
            ctx.closePath();

            const isUp = trail[trail.length - 1] > trail[0];
            const trailColor = isUp ? C.lime : C.pink;

            const trailFill = ctx.createLinearGradient(0, trailY0, 0, trailY0 + trailH);
            trailFill.addColorStop(0, `${trailColor}18`);
            trailFill.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = trailFill;
            ctx.fill();

            // Main line
            ctx.beginPath();
            ctx.moveTo(pts[0][0], pts[0][1]);
            for (let i = 1; i < pts.length; i++) {
                ctx.lineTo(pts[i][0], pts[i][1]);
            }
            ctx.strokeStyle = trailColor;
            ctx.lineWidth = 2;
            ctx.shadowColor = trailColor;
            ctx.shadowBlur = 10;
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Glowing dot at end
            const lastPt = pts[pts.length - 1];
            ctx.beginPath();
            ctx.arc(lastPt[0], lastPt[1], 4, 0, Math.PI * 2);
            ctx.fillStyle = trailColor;
            ctx.shadowColor = trailColor;
            ctx.shadowBlur = 16;
            ctx.fill();
            ctx.shadowBlur = 0;

            // Pulse ring
            const pulseR = 6 + Math.sin(now * 4) * 3;
            ctx.beginPath();
            ctx.arc(lastPt[0], lastPt[1], pulseR, 0, Math.PI * 2);
            ctx.strokeStyle = `${trailColor}60`;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }
        } // end trail.length >= 2

        // ── Ship smooth flight path ───────────────────────────────
        const lf = launchFrames.current;
        const thrust = lf > 0 ? 1 : 0;
        
        let shipX = W * 0.38;
        let shipY = shipYRef.current * H;
        const currentAction = actionRef.current;

        if (lf > 0) {
            launchFrames.current--;
            thrustPhase.current += 0.3;
            
            // X positioning: start left, accelerate off the right side
            const progress = (90 - launchFrames.current) / 90;
            const currentX = -0.1 + (progress * progress * 1.5);
            shipX = W * currentX;

            // Y positioning: curve towards target
            shipYRef.current += (shipYTarget.current - shipYRef.current) * 0.05;
            shipY = shipYRef.current * H;

            if (launchFrames.current === 0) {
                if (onLaunchCompleteRef.current) onLaunchCompleteRef.current();
            }

            // Ship contrail
            for (let i = 0; i < 12; i++) {
                const trailAlpha = ((12 - i) / 12) * 0.25 * thrust;
                const ty = shipY + (Math.random() - 0.5) * 6 * i * 0.1;
                ctx.fillStyle = `rgba(${currentAction === 'BUY' ? '57,255,20' : '255,0,110'},${trailAlpha})`;
                ctx.beginPath();
                ctx.arc(shipX - i * 5, ty, 2 * (1 - i / 12), 0, Math.PI * 2);
                ctx.fill();
            }

            // Draw ship
            drawShipRef.current(ctx, shipX, shipY, thrust, currentAction === 'BUY');
        }

        // ── Particles ─────────────────────────────────────────────
        particlesRef.current = particlesRef.current.filter(p => p.life > 0);
        for (const p of particlesRef.current) {
            p.x  += p.vx;
            p.y  += p.vy;
            p.vy += 0.08; // gravity
            p.vx *= 0.97;
            p.life -= 0.02;
            const alpha = p.life;
            ctx.fillStyle = p.color + Math.floor(alpha * 255).toString(16).padStart(2, '0');
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            ctx.fill();
        }

        // ── Wallet balance HUD ────────────────────────────────────
        ctx.font = `700 11px 'JetBrains Mono', monospace`;
        ctx.fillStyle = 'rgba(148,163,184,0.5)';
        ctx.fillText('WALLET', 16, 20);
        ctx.font = `800 18px 'Rajdhani', sans-serif`;
        const bal = balanceRef.current;
        const balColor = bal > 100000 ? C.lime : bal > 80000 ? C.amber : C.pink;
        ctx.fillStyle = balColor;
        ctx.shadowColor = balColor;
        ctx.shadowBlur = 12;
        ctx.fillText(`₹${bal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, 16, 42);
        ctx.shadowBlur = 0;

        ctx.restore();
            animRef.current = requestAnimationFrame(loop);
        };
        animRef.current = requestAnimationFrame(loop);
        return () => { running = false; if (animRef.current) cancelAnimationFrame(animRef.current); };
    }, []); // empty deps — runs once, never restarts

    return (
        <canvas
            ref={canvasRef}
            style={{ width: '100%', height: '100%', display: 'block', borderRadius: '12px' }}
        />
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  PORTFOLIO PIE — canvas-drawn real positions
// ═══════════════════════════════════════════════════════════════════════════════
const PIE_COLORS = ['#00B4FF','#39FF14','#FF006E','#FFB800','#9B30FF','#FF6600','#00FFD4','#FF3040'];

function PortfolioPie({ positions }: { positions: any[] }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current; if (!canvas) return;
        const ctx = canvas.getContext('2d'); if (!ctx) return;
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width; const H = rect.height;
        ctx.clearRect(0, 0, W, H);

        if (!positions.length) {
            // Empty state ring
            ctx.strokeStyle = 'rgba(255,255,255,0.06)';
            ctx.lineWidth = 12;
            ctx.beginPath();
            ctx.arc(W / 2, H / 2, Math.min(W, H) / 2 - 14, 0, Math.PI * 2);
            ctx.stroke();
            ctx.fillStyle = 'rgba(148,163,184,0.4)';
            ctx.font = `700 10px monospace`;
            ctx.textAlign = 'center';
            ctx.fillText('NO POSITIONS', W / 2, H / 2 + 4);
            return;
        }

        const total = positions.reduce((s, p) => s + p.quantity * p.avg_price, 0);
        const cx = W / 2; const cy = H / 2;
        const r = Math.min(W, H) / 2 - 14;
        let startAngle = -Math.PI / 2;

        positions.forEach((p, i) => {
            const slice = (p.quantity * p.avg_price) / total;
            const endAngle = startAngle + slice * Math.PI * 2;
            const mid = (startAngle + endAngle) / 2;
            const color = PIE_COLORS[i % PIE_COLORS.length];

            // Slice
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, r, startAngle, endAngle);
            ctx.closePath();
            ctx.fillStyle = color + 'cc';
            ctx.fill();

            // Glow border
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.shadowColor = color;
            ctx.shadowBlur = 6;
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Label if slice big enough
            if (slice > 0.08) {
                const lx = cx + Math.cos(mid) * r * 0.65;
                const ly = cy + Math.sin(mid) * r * 0.65;
                ctx.fillStyle = 'var(--text-primary)';
                ctx.font = `700 9px monospace`;
                ctx.textAlign = 'center';
                ctx.fillText(p.symbol.replace('.NS','').slice(0,6), lx, ly);
            }

            startAngle = endAngle;
        });

        // Centre hole
        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = '#05050F';
        ctx.fill();

        // Centre label
        ctx.fillStyle = 'rgba(148,163,184,0.7)';
        ctx.font = `700 8px monospace`;
        ctx.textAlign = 'center';
        ctx.fillText('PORTFOLIO', cx, cy - 4);
        ctx.fillStyle = 'var(--text-primary)';
        ctx.font = `800 11px monospace`;
        ctx.fillText(`₹${(total/1000).toFixed(0)}K`, cx, cy + 10);
    }, [positions]);

    return <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════
// Watchlist-based symbol data (fetched from API)
interface SymbolEntry { symbol: string; label: string; category?: string; }
const FALLBACK_SYMBOLS: SymbolEntry[] = [
    { symbol: 'RELIANCE.NS', label: 'RELIANCE INDUSTRIES' },
    { symbol: 'TCS.NS', label: 'TATA CONSULTANCY' },
    { symbol: 'HDFCBANK.NS', label: 'HDFC BANK' },
    { symbol: 'INFY.NS', label: 'INFOSYS' },
    { symbol: 'ICICIBANK.NS', label: 'ICICI BANK' },
    { symbol: 'SBIN.NS', label: 'STATE BANK OF INDIA' },
    { symbol: 'NTPC.NS', label: 'NTPC' },
    { symbol: 'TATASTEEL.NS', label: 'TATA STEEL' },
    { symbol: 'ITC.NS', label: 'ITC' },
    { symbol: 'BHARTIARTL.NS', label: 'BHARTI AIRTEL' },
    { symbol: 'ADANIENT.NS', label: 'ADANI ENTERPRISES' },
    { symbol: 'BEL.NS', label: 'BHARAT ELECTRONICS' },
];

export default function PilotMode() {
    const [symbol, setSymbol]       = useState('RELIANCE.NS');
    const [customSym, setCustomSym] = useState('');
    const [action, setAction]       = useState<'BUY' | 'SELL'>('BUY');
    const [qty, setQty]             = useState(1);
    const [livePrice, setLivePrice] = useState(0);
    const [priceError, setPriceError] = useState(false);
    const [isFetchingPrice, setIsFetchingPrice] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<string>('');
    const [balance, setBalance]     = useState(100000);
    const [isLaunching, setIsLaunching] = useState(false);
    const [launchCounter, setLaunchCounter] = useState(0);
    const [logs, setLogs]           = useState<MissionLog[]>([]);
    const [positions, setPositions] = useState<any[]>([]);
    const [orderFeedback, setOrderFeedback] = useState<{ msg: string; ok: boolean } | null>(null);
    const [showSymPicker, setShowSymPicker] = useState(false);
    const [isLoadingOrder, setIsLoadingOrder] = useState(false);
    const [oracleSignal, setOracleSignal] = useState<any>(null);
    const [oracleLoading, setOracleLoading] = useState(false);
    const [allSymbols, setAllSymbols] = useState<SymbolEntry[]>(FALLBACK_SYMBOLS);
    const [timingData, setTimingData] = useState<{timing: string; urgency: string; reason: string} | null>(null);

    // Fetch watchlist symbols for fuzzy search
    useEffect(() => {
        (async () => {
            try {
                const res = await fetch('http://127.0.0.1:8000/api/watchlist');
                const data = await res.json();
                const entries: SymbolEntry[] = [];
                const seen = new Set<string>();
                for (const [cat, items] of Object.entries(data)) {
                    for (const item of items as any[]) {
                        if (!seen.has(item.symbol)) {
                            entries.push({ symbol: item.symbol, label: item.label || item.symbol, category: cat });
                            seen.add(item.symbol);
                        }
                    }
                }
                if (entries.length > 0) setAllSymbols(entries);
            } catch {}
        })();
    }, []);

    // Oracle quick-scan for selected symbol
    const fetchOracleSignal = useCallback(async (sym: string) => {
        setOracleSignal(null);
        setOracleLoading(true);
        try {
            const res = await fetch('http://127.0.0.1:8000/api/vision_analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context: sym }),
            });
            if (res.ok) {
                const data = await res.json();
                // data is array of {label, value}
                const map: any = {};
                data.forEach((d: any) => { map[d.label] = d.value; });
                setOracleSignal(map);
            }
        } catch {}
        finally { setOracleLoading(false); }
    }, []);

    // Fetch live price — locked, not user-editable
    const fetchPrice = useCallback(async (sym: string) => {
        setIsFetchingPrice(true);
        setPriceError(false);
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/price/${encodeURIComponent(sym)}`);
            const data = await res.json();
            if (data.price && data.price > 0) {
                setLivePrice(data.price);
                setLastUpdated(new Date().toLocaleTimeString());
            } else {
                setPriceError(true);
            }
        } catch {
            setPriceError(true);
        } finally {
            setIsFetchingPrice(false);
        }
    }, []);

    // Fetch balance + positions + trade history (mission logs)
    const fetchState = useCallback(async () => {
        try {
            const [s, p, trades] = await Promise.all([
                fetch('http://127.0.0.1:8000/api/status').then(r => r.json()),
                fetch('http://127.0.0.1:8000/api/positions').then(r => r.json()),
                fetch('http://127.0.0.1:8000/api/flight_recorder').then(r => r.json()).catch(() => []),
            ]);
            setBalance(s.wallet_balance ?? 100000);
            setPositions(p);
            // Populate mission log from persisted trade history (newest first)
            if (Array.isArray(trades) && trades.length > 0) {
                const persistedLogs: MissionLog[] = trades.reverse().slice(0, 15).map((t: any) => ({
                    symbol: t.symbol || '---',
                    action: t.action || 'BUY',
                    qty: t.qty || t.quantity || 0,
                    price: t.price || t.avg_price || 0,
                    time: t.timestamp || '---',
                    status: 'FILLED',
                    orderId: t.order_id || '---',
                }));
                setLogs(persistedLogs);
            }
        } catch {}
    }, []);

    // On symbol change: fetch price + state + oracle
    useEffect(() => {
        setLivePrice(0);
        fetchState();
        fetchPrice(symbol);
        fetchOracleSignal(symbol);
    }, [symbol, fetchPrice, fetchState, fetchOracleSignal]);

    // Auto-refresh price every 30 seconds
    useEffect(() => {
        const interval = setInterval(() => fetchPrice(symbol), 30000);
        return () => clearInterval(interval);
    }, [symbol, fetchPrice]);

    const handleSymbolSelect = (s: string) => {
        setSymbol(s); setShowSymPicker(false);
    };

    const placeOrder = async () => {
        if (!livePrice || qty < 1 || isLaunching) return;
        setIsLoadingOrder(true);
        try {
            const res = await fetch('http://127.0.0.1:8000/api/manual_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, action, quantity: qty, price: livePrice }),
            });
            const data = await res.json();

            if (data.status === 'success') {
                setIsLaunching(true);
                setLaunchCounter(c => c + 1);
                setOrderFeedback({ msg: `✓ ORDER FILLED  ·  ${action} ${qty}×${symbol.replace('.NS','')} @ ₹${livePrice.toLocaleString('en-IN')}`, ok: true });
                const newLog: MissionLog = {
                    symbol, action, qty, price: livePrice,
                    time: new Date().toLocaleTimeString(),
                    status: 'FILLED',
                    orderId: data.order_id || '---',
                };
                setLogs(prev => [newLog, ...prev.slice(0, 14)]);
                // Safety timeout — always unlock after 3.5s even if animation callback missed
                setTimeout(() => setIsLaunching(false), 3500);
                fetchState();
            } else {
                setOrderFeedback({ msg: `✗ ${data.message || 'Order failed'}`, ok: false });
            }
        } catch (e) {
            setOrderFeedback({ msg: '✗ Backend unreachable', ok: false });
        } finally {
            setIsLoadingOrder(false);
            setTimeout(() => setOrderFeedback(null), 5000);
        }
    };

    const estimatedCost = livePrice * qty;
    const canAfford     = action === 'BUY' ? estimatedCost <= balance : true;

    return (
        <div style={{
            display: 'flex', flexDirection: 'column', height: '100%', gap: '20px',
            fontFamily: 'var(--font-base)',
        }}>

            {/* ── Header ──────────────────────────────────────────── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        width: 40, height: 40, borderRadius: '10px',
                        background: `linear-gradient(135deg, ${C.pink}, ${C.purple})`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        boxShadow: `0 0 20px ${C.pink}60`,
                    }}>
                        <Rocket size={20} color="#fff" />
                    </div>
                    <div>
                        <h2 style={{
                            margin: 0, fontSize: '20px', letterSpacing: '3px', fontFamily: 'var(--font-heading)',
                            background: `linear-gradient(90deg, #fff 0%, ${C.pink} 40%, ${C.blue} 100%)`,
                            WebkitBackgroundClip: 'text', backgroundClip: 'text', WebkitTextFillColor: 'transparent'
                        }}>PILOT MODE</h2>
                        <div style={{ fontSize: '10px', color: C.blue, letterSpacing: '3px', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                            MANUAL TRADING COCKPIT · PAPER SESSION
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <div style={{
                        padding: '6px 14px', borderRadius: '20px', fontSize: '11px', fontWeight: 800,
                        fontFamily: 'var(--font-mono)', letterSpacing: '2px',
                        background: 'rgba(57,255,20,0.08)', border: `1px solid ${C.lime}40`,
                        color: C.lime, boxShadow: `0 0 12px ${C.lime}20`
                    }}>
                        PAPER TRADING
                    </div>
                    <button onClick={fetchState} style={{
                        background: 'none', border: 'none', color: 'var(--text-muted)',
                        cursor: 'pointer', padding: '6px', display: 'flex',
                    }}>
                        <RefreshCw size={15} />
                    </button>
                </div>
            </div>

            {/* ── Top Row: Cockpit + Canvas ─────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '16px' }}>

                {/* LEFT — Cockpit Form ────────────────────────────── */}
                <div style={{
                    background: 'rgba(5,5,20,0.85)',
                    border: `1px solid ${C.pink}30`,
                    borderRadius: '16px', padding: '20px',
                    backdropFilter: 'blur(20px)',
                    boxShadow: `inset 0 0 30px rgba(0,0,0,0.5), 0 0 30px ${C.pink}08`,
                    display: 'flex', flexDirection: 'column', gap: '16px',
                    position: 'relative', overflow: 'hidden',
                }}>
                    {/* Corner accent */}
                    <div style={{
                        position: 'absolute', top: 0, left: 0, width: '120px', height: '120px',
                        background: `radial-gradient(circle at top left, ${C.pink}15, transparent 70%)`,
                        borderRadius: '16px 0 0 0', pointerEvents: 'none',
                    }} />

                    <div style={{ fontSize: '11px', color: C.pink, letterSpacing: '3px', fontFamily: 'var(--font-mono)', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Target size={13} /> ORDER COCKPIT
                    </div>

                    {/* BUY / SELL toggle */}
                    <div style={{
                        display: 'grid', gridTemplateColumns: '1fr 1fr',
                        borderRadius: '10px', overflow: 'hidden',
                        border: `1px solid rgba(255,255,255,0.06)`,
                    }}>
                        {(['BUY', 'SELL'] as const).map(a => (
                            <button key={a} onClick={() => setAction(a)} style={{
                                padding: '12px', border: 'none', cursor: 'pointer',
                                fontFamily: 'var(--font-mono)', fontWeight: 800,
                                fontSize: '14px', letterSpacing: '3px',
                                transition: 'all 0.25s ease',
                                background: action === a
                                    ? (a === 'BUY' ? `linear-gradient(135deg, ${C.lime}22, ${C.blue}11)` : `linear-gradient(135deg, ${C.pink}22, ${C.purple}11)`)
                                    : 'rgba(0,0,0,0.3)',
                                color: action === a
                                    ? (a === 'BUY' ? C.lime : C.pink)
                                    : 'var(--text-muted)',
                                textShadow: action === a ? `0 0 12px currentColor` : 'none',
                                borderRight: a === 'BUY' ? `1px solid rgba(255,255,255,0.06)` : 'none',
                            }}>
                                {a === 'BUY' ? <TrendingUp size={13} style={{ display: 'inline', marginRight: 6 }} /> : <TrendingDown size={13} style={{ display: 'inline', marginRight: 6 }} />}
                                {a}
                            </button>
                        ))}
                    </div>

                    {/* Symbol selector */}
                    <div>
                        <label style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '6px' }}>
                            SYMBOL
                        </label>
                        <div style={{ position: 'relative' }}>
                            <button onClick={() => setShowSymPicker(!showSymPicker)} style={{
                                width: '100%', padding: '10px 14px',
                                background: 'rgba(0,180,255,0.06)',
                                border: `1px solid ${C.blue}40`,
                                borderRadius: '8px', color: 'var(--text-primary)',
                                fontFamily: 'var(--font-mono)', fontWeight: 700,
                                fontSize: '13px', cursor: 'pointer',
                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                transition: 'all 0.2s',
                            }}>
                                <span style={{ color: C.blue }}>{symbol}</span>
                                <ChevronDown size={14} color={C.blue} style={{ transform: showSymPicker ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                            </button>
                            {showSymPicker && (
                                <div style={{
                                    position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0,
                                    background: '#080818', border: `1px solid ${C.blue}30`,
                                    borderRadius: '8px', zIndex: 999, overflow: 'hidden',
                                    boxShadow: `0 8px 32px rgba(0,0,0,0.8), 0 0 20px ${C.blue}10`,
                                }}>
                                    <div style={{ padding: '8px' }}>
                                        <input
                                            placeholder="Search by name or symbol…"
                                            value={customSym}
                                            onChange={e => setCustomSym(e.target.value.toUpperCase())}
                                            onKeyDown={e => { if (e.key === 'Enter' && customSym) handleSymbolSelect(customSym.includes('.') ? customSym : customSym + '.NS'); }}
                                            style={{
                                                width: '100%', background: 'rgba(0,180,255,0.05)',
                                                border: `1px solid ${C.blue}30`, borderRadius: '6px',
                                                color: 'var(--text-primary)', padding: '7px 10px', fontSize: '12px',
                                                fontFamily: 'var(--font-mono)', outline: 'none',
                                                boxSizing: 'border-box',
                                            }}
                                        />
                                    </div>
                                    <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
                                        {allSymbols
                                            .filter(s => s.symbol.includes(customSym) || s.label.toUpperCase().includes(customSym))
                                            .map(s => (
                                            <button key={s.symbol} onClick={() => handleSymbolSelect(s.symbol)} style={{
                                                width: '100%', padding: '8px 14px', background: 'none',
                                                border: 'none', color: s.symbol === symbol ? C.blue : 'var(--text-secondary)',
                                                fontFamily: 'var(--font-mono)', fontSize: '11px',
                                                fontWeight: s.symbol === symbol ? 700 : 400,
                                                cursor: 'pointer', textAlign: 'left',
                                                borderTop: '1px solid rgba(255,255,255,0.03)',
                                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            }}>
                                                <span style={{ color: 'var(--text-muted)', fontSize: '10px', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '8px' }}>{s.label}</span>
                                                <span style={{ color: s.symbol === symbol ? C.blue : C.chrome, fontWeight: 700, fontSize: '11px', flexShrink: 0 }}>{s.symbol.replace('.NS','')}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Live price — READ ONLY, locked to market */}
                    <div style={{
                        padding: '14px 16px',
                        background: priceError ? 'rgba(255,48,64,0.06)' : 'rgba(255,184,0,0.05)',
                        borderRadius: '10px',
                        border: `1px solid ${priceError ? C.red + '40' : C.amber + '40'}`,
                        position: 'relative', overflow: 'hidden',
                    }}>
                        {/* Shimmer while fetching */}
                        {isFetchingPrice && (
                            <div style={{
                                position: 'absolute', inset: 0,
                                background: 'linear-gradient(90deg, transparent 0%, rgba(255,184,0,0.08) 50%, transparent 100%)',
                                animation: 'shimmer 1.2s infinite',
                                pointerEvents: 'none',
                            }} />
                        )}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                                <div style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                    MARKET PRICE
                                    <span style={{ fontSize: '8px', color: C.lime, background: `${C.lime}15`, padding: '1px 5px', borderRadius: '3px', border: `1px solid ${C.lime}30` }}>LOCKED</span>
                                </div>
                                {isFetchingPrice ? (
                                    <div style={{ fontSize: '22px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontWeight: 800 }}>—</div>
                                ) : priceError ? (
                                    <div style={{ fontSize: '13px', color: C.red, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Price unavailable</div>
                                ) : (
                                    <div style={{ fontSize: '26px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: C.amber, textShadow: `0 0 16px ${C.amber}80`, lineHeight: 1 }}>
                                        ₹{livePrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                    </div>
                                )}
                                {lastUpdated && !isFetchingPrice && (
                                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>updated {lastUpdated} · auto-refreshes every 30s</div>
                                )}
                            </div>
                            <button onClick={() => fetchPrice(symbol)} title="Refresh price" style={{
                                background: 'none', border: `1px solid rgba(255,255,255,0.08)`,
                                borderRadius: '6px', padding: '6px', cursor: 'pointer',
                                color: 'var(--text-muted)', display: 'flex',
                            }}>
                                <RefreshCw size={12} style={{ animation: isFetchingPrice ? 'spin 1s linear infinite' : 'none' }} />
                            </button>
                        </div>
                    </div>

                    {/* Quantity */}
                    <div>
                        <label style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '2px', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '6px' }}>
                            QUANTITY
                        </label>
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                            <button onClick={() => setQty(Math.max(1, qty - 1))} style={{
                                width: 36, height: 36, border: `1px solid rgba(255,255,255,0.1)`,
                                background: 'rgba(0,0,0,0.3)', borderRadius: '6px',
                                color: 'var(--text-primary)', cursor: 'pointer', fontSize: '18px',
                            }}>−</button>
                            <input
                                type="number" value={qty} min={1}
                                onChange={e => setQty(Math.max(1, parseInt(e.target.value) || 1))}
                                style={{
                                    flex: 1, background: 'rgba(0,0,0,0.3)',
                                    border: `1px solid rgba(255,255,255,0.1)`,
                                    borderRadius: '6px', color: 'var(--text-primary)',
                                    padding: '8px', textAlign: 'center',
                                    fontSize: '15px', fontFamily: 'var(--font-mono)', fontWeight: 800, outline: 'none',
                                }}
                            />
                            <button onClick={() => setQty(qty + 1)} style={{
                                width: 36, height: 36, border: `1px solid rgba(255,255,255,0.1)`,
                                background: 'rgba(0,0,0,0.3)', borderRadius: '6px',
                                color: 'var(--text-primary)', cursor: 'pointer', fontSize: '18px',
                            }}>+</button>
                        </div>
                        {/* Quick qty chips */}
                        <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                            {[1, 5, 10, 25, 50].map(n => (
                                <button key={n} onClick={() => setQty(n)} style={{
                                    flex: 1, padding: '4px', fontSize: '10px',
                                    fontFamily: 'var(--font-mono)', fontWeight: 700,
                                    background: qty === n ? `${C.blue}20` : 'transparent',
                                    border: `1px solid ${qty === n ? C.blue : 'rgba(255,255,255,0.06)'}`,
                                    borderRadius: '4px', color: qty === n ? C.blue : 'var(--text-muted)',
                                    cursor: 'pointer',
                                }}>{n}</button>
                            ))}
                        </div>
                    </div>

                    {/* Cost summary */}
                    <div style={{
                        padding: '10px 14px', borderRadius: '8px',
                        background: canAfford ? 'rgba(57,255,20,0.04)' : 'rgba(255,0,110,0.06)',
                        border: `1px solid ${canAfford ? C.lime + '30' : C.pink + '40'}`,
                        fontSize: '12px', fontFamily: 'var(--font-mono)',
                        display: 'flex', justifyContent: 'space-between',
                    }}>
                        <span style={{ color: 'var(--text-muted)' }}>EST. COST</span>
                        <span style={{ color: canAfford ? C.lime : C.pink, fontWeight: 700 }}>
                            ₹{estimatedCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </span>
                    </div>

                    {/* LAUNCH button */}
                    <button
                        onClick={placeOrder}
                        disabled={isLaunching || isLoadingOrder || !livePrice || !canAfford || priceError}
                        style={{
                            padding: '15px', borderRadius: '10px', border: 'none',
                            cursor: (isLaunching || !livePrice || !canAfford || priceError) ? 'not-allowed' : 'pointer',
                            fontFamily: 'var(--font-heading)', fontWeight: 800,
                            fontSize: '16px', letterSpacing: '4px',
                            opacity: (!livePrice || !canAfford || priceError) ? 0.4 : 1,
                            background: isLaunching ? 'rgba(0,0,0,0.5)'
                                : action === 'BUY'
                                    ? `linear-gradient(135deg, ${C.lime}cc, ${C.blue}cc)`
                                    : `linear-gradient(135deg, ${C.pink}cc, ${C.purple}cc)`,
                            color: '#000',
                            boxShadow: isLaunching ? 'none'
                                : action === 'BUY' ? `0 0 30px ${C.lime}50` : `0 0 30px ${C.pink}50`,
                            transition: 'all 0.3s',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                        }}
                    >
                        {isFetchingPrice ? (
                            <span style={{ color: 'var(--text-muted)' }}>FETCHING PRICE…</span>
                        ) : isLaunching ? (
                            <span style={{ color: action === 'BUY' ? C.lime : C.pink }}>◉ LAUNCHING…</span>
                        ) : (
                            <>
                                <Zap size={16} />
                                {isLoadingOrder ? 'PROCESSING…' : `${action} ${qty} × ${symbol.replace('.NS', '')} @ ₹${livePrice.toLocaleString('en-IN')}`}
                            </>
                        )}
                    </button>
                </div>

                {/* CENTRE — flex column: ship + info panels below */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', minHeight: 0 }}>

                    {/* Spaceship canvas */}
                    <div style={{
                        borderRadius: '16px', overflow: 'hidden', flex: 1, minHeight: '260px',
                        border: `1px solid rgba(155,48,255,0.2)`,
                        position: 'relative',
                        boxShadow: `inset 0 0 60px rgba(0,0,0,0.7), 0 0 40px ${C.purple}08`,
                    }}>
                        <SpaceCanvas
                            action={action}
                            launchCounter={launchCounter}
                            onLaunchComplete={() => setIsLaunching(false)}
                            balance={balance}
                            symbol={symbol}
                            livePrice={livePrice}
                        />
                        {orderFeedback && (
                            <div style={{
                                position: 'absolute', bottom: '12px', left: '50%', transform: 'translateX(-50%)',
                                padding: '9px 18px', borderRadius: '30px',
                                background: orderFeedback.ok ? `rgba(57,255,20,0.12)` : `rgba(255,0,110,0.12)`,
                                border: `1px solid ${orderFeedback.ok ? C.lime : C.pink}60`,
                                color: orderFeedback.ok ? C.lime : C.pink,
                                fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700,
                                letterSpacing: '1px', whiteSpace: 'nowrap',
                                boxShadow: `0 0 20px ${orderFeedback.ok ? C.lime : C.pink}30`,
                                animation: 'fadeInUp 0.3s ease',
                            }}>
                                {orderFeedback.msg}
                            </div>
                        )}
                    </div>

                    {/* end of centre column */}
                </div>
            </div>

            {/* ── Horizontal Info Panels ───────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                {/* Panel 1 — Portfolio Pie */}
                <div style={{ background: 'rgba(5,5,20,0.85)', borderRadius: '14px', border: `1px solid ${C.blue}18`, padding: '16px', display: 'flex', gap: '14px', alignItems: 'center' }}>
                    <div style={{ width: '90px', height: '90px', flexShrink: 0 }}><PortfolioPie positions={positions} /></div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '9px', color: C.blue, letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 800, marginBottom: '8px' }}>PORTFOLIO EXPOSURE</div>
                        {positions.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                {positions.slice(0, 4).map((p, i) => (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: PIE_COLORS[i % PIE_COLORS.length] }} />
                                            <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{p.symbol.replace('.NS','')}</span>
                                        </div>
                                        <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: PIE_COLORS[i % PIE_COLORS.length] }}>{p.quantity} sh</span>
                                    </div>
                                ))}
                            </div>
                        ) : <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>No positions</div>}
                    </div>
                </div>
                {/* Panel 2 — Oracle Signal */}
                <div style={{ background: 'rgba(5,5,20,0.85)', borderRadius: '14px', border: `1px solid ${C.purple}20`, padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontSize: '9px', color: C.purple, letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}><Brain size={10} /> ORACLE SIGNAL</div>
                        <button onClick={() => fetchOracleSignal(symbol)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 0 }}><RefreshCw size={9} style={{ animation: oracleLoading ? 'spin 1s linear infinite' : 'none' }} /></button>
                    </div>
                    {oracleLoading ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>Scanning…</div>
                    ) : oracleSignal ? (
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                            <div style={{ padding: '8px 14px', borderRadius: '8px', textAlign: 'center', flexShrink: 0, background: oracleSignal['CURRENT SIGNAL'] === 'BUY' ? `${C.lime}18` : oracleSignal['CURRENT SIGNAL'] === 'SELL' ? `${C.pink}18` : 'rgba(255,255,255,0.04)', border: `1px solid ${oracleSignal['CURRENT SIGNAL'] === 'BUY' ? C.lime : oracleSignal['CURRENT SIGNAL'] === 'SELL' ? C.pink : 'rgba(255,255,255,0.08)'}40` }}>
                                <div style={{ fontSize: '18px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: oracleSignal['CURRENT SIGNAL'] === 'BUY' ? C.lime : oracleSignal['CURRENT SIGNAL'] === 'SELL' ? C.pink : C.amber }}>{oracleSignal['CURRENT SIGNAL'] || '—'}</div>
                                <div style={{ fontSize: '9px', color: C.purple, fontFamily: 'var(--font-mono)' }}>{oracleSignal['ORACLE CONFIDENCE'] || ''}</div>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                                {[['RSI (14)', oracleSignal['RSI (14)']], ['VWAP', oracleSignal['VWAP LEVEL']], ['MACD', oracleSignal['MACD DIRECTION']]].map(([k, v]) => (
                                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                                        <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{v ?? '—'}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>No signal. Click ↻ to scan.</div>}
                </div>
                {/* Panel 3 — Trade Calculator */}
                <div style={{ background: 'rgba(5,5,20,0.85)', borderRadius: '14px', border: `1px solid ${C.amber}18`, padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '9px', color: C.amber, letterSpacing: '2px', fontFamily: 'var(--font-mono)', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}><Calculator size={10} /> TRADE CALCULATOR</div>
                    {livePrice > 0 ? (() => {
                        const maxShares = Math.floor(balance / livePrice);
                        const tradeVal = livePrice * qty;
                        const portPct = balance > 0 ? (tradeVal / balance * 100) : 0;
                        const q25 = Math.floor(balance * 0.25 / livePrice);
                        const q50 = Math.floor(balance * 0.5 / livePrice);
                        const q10 = Math.floor(balance * 0.10 / livePrice);
                        return (
                            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '4px 8px', background: 'rgba(255,184,0,0.05)', borderRadius: '6px' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Max Shares</span>
                                        <span style={{ color: C.amber, fontWeight: 800 }}>{maxShares.toLocaleString()}</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>This Trade</span>
                                        <span style={{ color: portPct > 50 ? C.pink : portPct > 25 ? C.amber : C.lime, fontWeight: 700 }}>{portPct.toFixed(1)}% of wallet</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Trade Value</span>
                                        <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>₹{tradeVal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                                    </div>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
                                    {[['10%', q10], ['25%', q25], ['50%', q50]].map(([label, shares]) => (
                                        <button key={String(label)} onClick={() => setQty(Number(shares) || 1)} style={{ padding: '5px 6px', border: `1px solid ${C.amber}30`, background: 'rgba(255,184,0,0.06)', borderRadius: '5px', cursor: 'pointer', textAlign: 'center' }}>
                                            <div style={{ fontSize: '8px', color: C.amber, fontFamily: 'var(--font-mono)', fontWeight: 800 }}>{label}</div>
                                            <div style={{ fontSize: '8px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{String(shares)}sh</div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        );
                    })() : <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>Awaiting price…</div>}
                </div>
            </div>

            {/* ── Mission Log (full width bottom) ──────────────────── */}
            <div style={{ background: 'rgba(5,5,20,0.85)', border: `1px solid ${C.purple}20`, borderRadius: '16px', padding: '16px', backdropFilter: 'blur(20px)', boxShadow: `inset 0 0 30px rgba(0,0,0,0.5)` }}>
                <div style={{ fontSize: '10px', color: C.purple, letterSpacing: '3px', fontFamily: 'var(--font-mono)', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}><Zap size={12} /> MISSION LOG</div>
                <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
                    {logs.length === 0 ? (
                        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '16px' }}>
                            No missions launched yet.&nbsp;<span style={{ color: C.pink }}>Place your first trade.</span>
                        </div>
                    ) : logs.map((log, i) => (
                        <div key={i} style={{ padding: '10px 14px', borderRadius: '8px', minWidth: '160px', flexShrink: 0, background: log.action === 'BUY' ? 'rgba(57,255,20,0.04)' : 'rgba(255,0,110,0.04)', border: `1px solid ${log.action === 'BUY' ? C.lime + '20' : C.pink + '20'}`, animation: i === 0 ? 'fadeInUp 0.4s ease' : 'none' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: log.action === 'BUY' ? C.lime : C.pink }}>{log.action}</span>
                                <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{log.time}</span>
                            </div>
                            <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontWeight: 700 }}>{log.symbol.replace('.NS', '')}</div>
                            <div style={{ fontSize: '10px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', marginTop: '3px' }}>{log.qty} shares · ₹{log.price.toLocaleString('en-IN')}</div>
                            <div style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: C.lime, marginTop: '4px', letterSpacing: '1px' }}>◉ {log.status}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

