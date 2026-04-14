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


// ─── Lightweight chart data fetches exclusively over HTTP (fast, no WS delay) ──
const chartCache: Record<string, any[]> = {};

async function fetchChartData(ticker: string): Promise<any[]> {
    if (chartCache[ticker]) return chartCache[ticker]; // Instant from memory cache
    try {
        const res = await axios.get(`/api/chart_data/${encodeURIComponent(ticker)}`, { timeout: 8000 });
        const data = (res.data || [])
            .map((d: any) => ({
                time: d.time as string,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close,
            }))
            .sort((a: any, b: any) => (a.time > b.time ? 1 : -1));
        chartCache[ticker] = data;
        return data;
    } catch {
        return [];
    }
}

// ─── Single chart component ──────────────────────────────────────────────────
function MiniChart({ ticker, label }: { ticker: string; label: string; color: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!containerRef.current) return;

        const chart = createChart(containerRef.current, {
            autoSize: true,
            layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: 'rgba(255,255,255,0.85)' },
            grid: { vertLines: { color: 'rgba(255,255,255,0.04)' }, horzLines: { color: 'rgba(255,255,255,0.04)' } },
            rightPriceScale: {
                borderColor: 'rgba(255,255,255,0.12)',
                visible: true,
                minimumWidth: 80,
            },
            timeScale: { borderColor: 'rgba(255,255,255,0.08)', timeVisible: true },
            crosshair: {
                vertLine: { color: 'rgba(0,240,255,0.4)', labelBackgroundColor: '#00F0FF' },
                horzLine: { color: 'rgba(0,240,255,0.4)', labelBackgroundColor: '#00F0FF' },
            },
        });

        const series = chart.addSeries(CandlestickSeries, {
            upColor: '#00FF66', downColor: '#FF003C',
            borderVisible: false, wickUpColor: '#00FF66', wickDownColor: '#FF003C',
        });

        chartRef.current = chart;
        seriesRef.current = series;

        const handleResize = () => {
            // autoSize handles resize automatically — just trigger a fitContent on resize
            chart.timeScale().fitContent();
        };
        window.addEventListener('resize', handleResize);

        // Fetch data immediately
        fetchChartData(ticker).then((data) => {
            if (data.length > 0) {
                series.setData(data);
                chart.timeScale().fitContent();
            }
            setLoading(false);
        });

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [ticker]);

    return (
        <div className="glass-panel" style={{ padding: '0', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* Chart header */}
            <div style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-light)' }}>
                <div>
                    <div style={{ fontSize: '14px', fontWeight: 800, color: '#fff' }}>{label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{ticker}</div>
                </div>
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
                        style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-light)', color: 'var(--text-muted)', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
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
                                style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '11px', padding: '8px 10px', borderRadius: '4px', outline: 'none', fontFamily: 'var(--font-mono)' }}
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
                                        background: isExpanded ? 'rgba(0,0,0,0.2)' : 'transparent'
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
                                                        background: pinned ? `${category.color}18` : 'rgba(0,0,0,0.4)',
                                                        border: pinned ? `1px solid ${category.color}` : '1px solid rgba(255,255,255,0.05)',
                                                        color: pinned ? '#fff' : 'var(--text-secondary)',
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
