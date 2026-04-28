import { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, CandlestickSeries, ColorType } from 'lightweight-charts';
import type { IChartApi } from 'lightweight-charts';
import axios from 'axios';
import { Target, TrendingUp, Activity, Pin, PinOff, Grid, Maximize2, Coins, Layers } from 'lucide-react';

const DEFAULT_CATEGORIES = [
    {
        name: 'INDICES',
        icon: <Target size={13} />,
        color: 'var(--accent-cyan)',
        tickers: [
            { symbol: '^NSEI', label: 'NIFTY 50' },
            { symbol: '^NSEBANK', label: 'BANK NIFTY' },
            { symbol: '^BSESN', label: 'SENSEX' },
        ],
    }
];

// Distinct color palette — one per category, no repeats
const CATEGORY_COLORS: Record<string, { color: string; icon: React.ReactElement }> = {
    'INDICES':                   { color: 'var(--accent-cyan)',  icon: <Target size={13} /> },
    'CORE SECTOR':               { color: '#a78bfa',             icon: <Layers size={13} /> },
    'BANKING & FINANCE':         { color: '#34d399',             icon: <Coins size={13} /> },
    'PHARMA & HEALTH':           { color: '#f472b6',             icon: <Activity size={13} /> },
    'ENERGY':                    { color: '#fbbf24',             icon: <Activity size={13} /> },
    'RAW MATERIALS':             { color: '#f59e0b',             icon: <Coins size={13} /> },
    'AUTO':                      { color: '#60a5fa',             icon: <TrendingUp size={13} /> },
    'FMCG & CONSUMER':           { color: '#fb923c',             icon: <Layers size={13} /> },
    'IT & TECH':                 { color: '#38bdf8',             icon: <Activity size={13} /> },
    'CONSTRUCTION & ENGINEERING':{ color: '#d97706',             icon: <Target size={13} /> },
    'TEXTILES':                  { color: '#e879f9',             icon: <Layers size={13} /> },
    'SHIPPING':                  { color: '#00b4d8',             icon: <Target size={13} /> },
    'DEFENCE':                   { color: '#4ade80',             icon: <Target size={13} /> },
    'AI_DISCOVERED':             { color: '#f72585',             icon: <Target size={13} /> },
};

// Fallback: deterministic color from name hash so future categories are never gray
const FALLBACK_PALETTE = [
    '#7dd3fc','#86efac','#fca5a5','#fcd34d','#c4b5fd',
    '#fdba74','#6ee7b7','#f9a8d4','#a5f3fc','#d4d4aa',
];
function hashColor(name: string): string {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) & 0xffff;
    return FALLBACK_PALETTE[hash % FALLBACK_PALETTE.length];
}

function getCategoryTheme(name: string) {
    if (CATEGORY_COLORS[name]) return CATEGORY_COLORS[name];
    return { color: hashColor(name), icon: <Layers size={13} /> };
}


// ─── Chart data layer: 30s TTL cache + WebSocket live ticks ─────────────────
const chartCache: Record<string, { data: any[]; ts: number }> = {};
const CACHE_TTL_MS = 30_000; // 30 seconds

async function fetchChartData(ticker: string): Promise<any[]> {
    const cached = chartCache[ticker];
    if (cached && Date.now() - cached.ts < CACHE_TTL_MS) return cached.data;

    try {
        const res = await axios.get(`/api/chart_data/${encodeURIComponent(ticker)}`, { timeout: 10000 });
        const data = (res.data || [])
            .map((d: any) => ({
                time: d.time as number,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close,
            }))
            .sort((a: any, b: any) => a.time - b.time);
        chartCache[ticker] = { data, ts: Date.now() };
        return data;
    } catch {
        return chartCache[ticker]?.data || [];
    }
}

// ─── WebSocket URL helper ────────────────────────────────────────────────────
function getWsUrl(ticker: string): string {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/ws/live_feed/${encodeURIComponent(ticker)}`;
}

// ─── Single chart component with LIVE WebSocket updates ─────────────────────
function MiniChart({ ticker, label }: { ticker: string; label: string; color: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<any>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [loading, setLoading] = useState(true);
    const [livePrice, setLivePrice] = useState<number | null>(null);
    const [prevClose, setPrevClose] = useState<number | null>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        const isHellenic = document.documentElement.classList.contains('theme-greek');
        const textColor = isHellenic ? '#2B2520' : 'rgba(255,255,255,0.85)';
        const gridColor = isHellenic ? 'rgba(99, 90, 79, 0.15)' : 'rgba(255,255,255,0.04)';
        const borderColor = isHellenic ? 'rgba(99, 90, 79, 0.2)' : 'rgba(255,255,255,0.12)';
        const crosshairColor = isHellenic ? 'rgba(178,82,51,0.5)' : 'rgba(0,240,255,0.4)';
        const crosshairBg = isHellenic ? '#B25233' : '#00F0FF';

        const chart = createChart(containerRef.current, {
            autoSize: true,
            layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor },
            grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } },
            rightPriceScale: {
                borderColor: borderColor,
                visible: true,
                minimumWidth: 80,
            },
            timeScale: { borderColor: borderColor, timeVisible: true, secondsVisible: false },
            crosshair: {
                vertLine: { color: crosshairColor, labelBackgroundColor: crosshairBg },
                horzLine: { color: crosshairColor, labelBackgroundColor: crosshairBg },
            },
        });

        const candleUp = isHellenic ? '#4A6B44' : '#00FF66';
        const candleDown = isHellenic ? '#8A3333' : '#FF003C';
        const series = chart.addSeries(CandlestickSeries, {
            upColor: candleUp, downColor: candleDown,
            borderVisible: false, wickUpColor: candleUp, wickDownColor: candleDown,
        });

        chartRef.current = chart;
        seriesRef.current = series;

        // ── Load initial historical data via HTTP ────────────────────────────
        fetchChartData(ticker).then((data) => {
            if (data.length > 0) {
                series.setData(data);
                chart.timeScale().fitContent();
                const lastCandle = data[data.length - 1];
                setLivePrice(lastCandle.close);
                // Find previous day's close for change% calc
                const now = lastCandle.time;
                const oneDayAgo = now - 86400;
                const prevDayCandle = [...data].reverse().find(c => c.time <= oneDayAgo);
                if (prevDayCandle) setPrevClose(prevDayCandle.close);
            }
            setLoading(false);
        });

        // ── Connect to WebSocket for live tick updates ───────────────────────
        let reconnectTimer: ReturnType<typeof setTimeout>;
        function connectWs() {
            try {
                const ws = new WebSocket(getWsUrl(ticker));
                wsRef.current = ws;

                ws.onmessage = (event) => {
                    try {
                        const msg = JSON.parse(event.data);
                        if (msg.type === 'history' && Array.isArray(msg.data)) {
                            // Full history push from backend on connect
                            const sorted = msg.data.sort((a: any, b: any) => a.time - b.time);
                            series.setData(sorted);
                            chart.timeScale().fitContent();
                            if (sorted.length > 0) {
                                setLivePrice(sorted[sorted.length - 1].close);
                            }
                        } else if (msg.type === 'tick' && msg.data) {
                            // Live candle update
                            series.update(msg.data);
                            setLivePrice(msg.data.close);
                        }
                    } catch { /* ignore malformed frames */ }
                };

                ws.onclose = () => {
                    // Auto-reconnect after 3s
                    reconnectTimer = setTimeout(connectWs, 3000);
                };

                ws.onerror = () => ws.close();
            } catch { /* WebSocket unavailable — rely on polling */ }
        }
        connectWs();

        // ── Polling fallback: refresh chart data every 30s ───────────────────
        const pollTimer = setInterval(() => {
            fetchChartData(ticker).then((data) => {
                if (data.length > 0 && seriesRef.current) {
                    seriesRef.current.setData(data);
                    setLivePrice(data[data.length - 1].close);
                }
            });
        }, 30_000);

        // ── Resize handler ───────────────────────────────────────────────────
        const handleResize = () => chart.timeScale().fitContent();
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            clearInterval(pollTimer);
            clearTimeout(reconnectTimer);
            if (wsRef.current) { try { wsRef.current.close(); } catch {} }
            chart.remove();
        };
    }, [ticker]);

    // Live price change %
    const changePct = (livePrice && prevClose) ? ((livePrice - prevClose) / prevClose * 100) : null;
    const isUp = changePct !== null && changePct >= 0;

    return (
        <div className="glass-panel" style={{ padding: '0', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* Chart header with live price */}
            <div style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-light)' }}>
                <div>
                    <div style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>{label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{ticker}</div>
                </div>
                {livePrice !== null && (
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                            ₹{livePrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        {changePct !== null && (
                            <div style={{
                                fontSize: '11px', fontWeight: 700, fontFamily: 'var(--font-mono)',
                                color: isUp ? 'var(--accent-green)' : 'var(--accent-danger)',
                            }}>
                                {isUp ? '▲' : '▼'} {Math.abs(changePct).toFixed(2)}%
                            </div>
                        )}
                    </div>
                )}
            </div>
            {/* Chart area */}
            <div style={{ flex: 1, position: 'relative' }}>
                {loading && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 5 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                            <div className="spinner" style={{ width: '28px', height: '28px', border: '2px solid rgba(0,240,255,0.15)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>LOADING</span>
                        </div>
                    </div>
                )}
                <div ref={containerRef} style={{ width: '100%', height: '280px' }} />
            </div>
        </div>
    );
}

// ─── Main Technicals page ────────────────────────────────────────────────────
import { ChevronDown, ChevronRight } from 'lucide-react';

export default function Technicals() {
    const [pinnedTickers, setPinnedTickers] = useState<{ symbol: string; label: string; color: string }[]>([
        { symbol: '^NSEI', label: 'NIFTY 50', color: 'var(--accent-cyan)' },
    ]);
    const [singleMode, setSingleMode] = useState(false);
    const [dynamicCategories, setDynamicCategories] = useState<any[]>(DEFAULT_CATEGORIES);
    const [expandedCategory, setExpandedCategory] = useState<string>('INDICES');
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            const sym = searchQuery.trim().toUpperCase();
            // Automatically pin the requested ticker and give it a cyan label
            togglePin(sym, sym, 'var(--accent-cyan)');
            setSearchQuery('');
        }
    };

    useEffect(() => {
        // Fetch the dynamic watchlist from the backend
        axios.get('/api/watchlist').then(res => {
            if (res.data) {
                const fetched = Object.entries(res.data).map(([catName, tickers]) => {
                    const theme = getCategoryTheme(catName);
                    return {
                        name: catName,
                        icon: theme.icon,
                        color: theme.color,
                        tickers: tickers
                    };
                });
                // Merge Default Indices with Backend Data
                setDynamicCategories([...DEFAULT_CATEGORIES, ...fetched]);
            }
        }).catch(err => console.error("Failed to load dynamic watchlist", err));
    }, []);

    const togglePin = useCallback((symbol: string, label: string, color: string) => {
        setPinnedTickers((prev) => {
            const exists = prev.find((p) => p.symbol === symbol);
            if (exists) return prev.filter((p) => p.symbol !== symbol);
            if (prev.length >= 4) return prev; // max 4 charts
            return [...prev, { symbol, label, color }];
        });
    }, []);

    const isPinned = useCallback((symbol: string) => pinnedTickers.some((p) => p.symbol === symbol), [pinnedTickers]);

    // Grid layout based on number of pinned charts
    const gridCols = pinnedTickers.length === 1 ? '1fr' : pinnedTickers.length <= 2 ? '1fr 1fr' : '1fr 1fr';

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: '17px', color: 'var(--text-primary)', letterSpacing: '2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TrendingUp size={18} className="neon-cyan" /> REAL-TIME TECHNICALS
                </h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        onClick={() => setSingleMode(!singleMode)}
                        title={singleMode ? "Grid view" : "Single view"}
                        style={{ background: 'var(--sub-panel-bg)', border: '1px solid var(--border-light)', color: 'var(--text-muted)', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                    >
                        {singleMode ? <Grid size={14} /> : <Maximize2 size={14} />}
                    </button>
                </div>
            </div>

            {/* Main Content Area (Sidebar + Grid) */}
            <div style={{ display: 'flex', flex: 1, gap: '16px', overflow: 'hidden' }}>

                {/* Scrollable vertical accordion menu */}
                <div className="glass-panel" style={{ width: '220px', padding: '10px 0', display: 'flex', flexDirection: 'column', overflowY: 'auto', scrollbarWidth: 'thin', scrollbarColor: 'rgba(148,163,184,0.2) transparent' }}>
                    {/* Native Search Input */}
                    <div style={{ padding: '0 12px 12px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
                            <input 
                                type="text"
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                placeholder="Search asset (e.g. BTC-USD)"
                                style={{ flex: 1, background: 'var(--sub-panel-bg)', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-primary)', fontSize: '11px', padding: '8px 10px', borderRadius: '4px', outline: 'none', fontFamily: 'var(--font-mono)' }}
                            />
                        </form>
                    </div>

                    {dynamicCategories.map((category) => {
                        const isExpanded = expandedCategory === category.name;
                        return (
                            <div key={category.name} style={{ display: 'flex', flexDirection: 'column', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                {/* Category Header (Click to expand) */}
                                <div
                                    onClick={() => setExpandedCategory(isExpanded ? '' : category.name)}
                                    style={{
                                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                        padding: '12px 16px', cursor: 'pointer', transition: 'background 0.2s',
                                        background: isExpanded ? 'var(--sub-panel-bg)' : 'transparent'
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: category.color, fontSize: '11px', fontWeight: 800, letterSpacing: '1.5px' }}>
                                        {category.icon} {category.name}
                                    </div>
                                    {isExpanded ? <ChevronDown size={12} color="var(--text-muted)" /> : <ChevronRight size={12} color="var(--text-muted)" />}
                                </div>

                                {/* Asset buttons (collapsible) */}
                                {isExpanded && (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '8px 16px 12px' }}>
                                        {category.tickers.map((t: any) => {
                                            const pinned = isPinned(t.symbol);
                                            return (
                                                <button
                                                    key={t.symbol}
                                                    onClick={() => togglePin(t.symbol, t.label, category.color)}
                                                    title={pinned ? 'Unpin chart' : `${t.full_name || t.label}\nPrimary Market: ${category.name}`}
                                                    style={{
                                                        background: pinned ? `${category.color}18` : 'var(--sub-panel-bg)',
                                                        border: pinned ? `1px solid ${category.color}` : '1px solid rgba(255,255,255,0.05)',
                                                        color: pinned ? 'var(--text-primary)' : 'var(--text-secondary)',
                                                        padding: '8px 12px',
                                                        borderRadius: '6px',
                                                        cursor: 'pointer',
                                                        fontSize: '12px',
                                                        fontFamily: 'var(--font-mono)',
                                                        fontWeight: pinned ? 700 : 500,
                                                        transition: 'all 0.15s ease',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '8px',
                                                        width: '100%',
                                                        textAlign: 'left'
                                                    }}
                                                >
                                                    {pinned ? <Pin size={10} color={category.color} /> : <PinOff size={10} style={{ opacity: 0.4 }} />}
                                                    {t.label}
                                                </button>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Chart grid — lazy loads each pinned chart independently */}
                <div style={{ display: 'grid', gridTemplateColumns: singleMode ? '1fr' : gridCols, gap: '16px', flex: 1, overflowY: 'auto' }}>
                    {pinnedTickers.length === 0 ? (
                        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', gridColumn: '1/-1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                            <Pin size={28} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                            <div style={{ fontFamily: 'var(--font-mono)', letterSpacing: '2px' }}>PIN AN ASSET FROM THE LEFT TO VIEW ITS CHART</div>
                        </div>
                    ) : (
                        pinnedTickers.map((p) => (
                            <MiniChart key={p.symbol} ticker={p.symbol} label={p.label} color={p.color} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
