import { useState, useEffect } from 'react';
import axios from 'axios';
import { Newspaper, TrendingUp, TrendingDown, Minus, RefreshCw, ExternalLink, Wifi } from 'lucide-react';

interface Article {
    title: string;
    source: string;
    link: string;
    published: string;
    summary: string;
    sentiment?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    category?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
    GEOPOLITICS: '#f97316',   // orange
    DIPLOMACY: '#f59e0b',   // amber-gold
    'OIL & GAS': '#ef4444',   // red
    METALS: '#94a3b8',   // silver-steel
    MARKETS: '#00f0ff',   // cyan
    ECONOMY: '#22c55e',   // green
    TECHNOLOGY: '#818cf8',   // indigo
    DEFAULT: '#6b7280',
};


function timeAgo(published: string): string {
    try {
        const d = new Date(published);
        const diff = Math.floor((Date.now() - d.getTime()) / 1000);
        if (diff < 60) return `${diff}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return d.toLocaleDateString('en-IN');
    } catch { return published; }
}

// Split summary into up to 2 paragraphs
function getParagraphs(summary: string): string[] {
    const sentences = summary.match(/[^.!?]+[.!?]*/g) || [summary];
    if (sentences.length <= 2) return [summary];
    const mid = Math.ceil(sentences.length / 2);
    return [
        sentences.slice(0, mid).join(' ').trim(),
        sentences.slice(mid).join(' ').trim(),
    ].filter(Boolean);
}

function SentimentIcon({ s }: { s?: string }) {
    if (s === 'BULLISH') return <TrendingUp size={11} color="#22c55e" />;
    if (s === 'BEARISH') return <TrendingDown size={11} color="#ef4444" />;
    return <Minus size={11} color="#6b7280" />;
}

function NewsCard({ article }: { article: Article }) {
    const catColor = CATEGORY_COLORS[article.category || 'DEFAULT'] || CATEGORY_COLORS.DEFAULT;
    const sentColor = article.sentiment === 'BULLISH' ? '#22c55e' : article.sentiment === 'BEARISH' ? '#ef4444' : '#6b7280';
    const paragraphs = getParagraphs(article.summary);

    return (
        <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderTop: `3px solid ${catColor}`,
            borderRadius: '12px',
            padding: '18px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            height: '290px',          /* fixed — all cards same size */
            boxSizing: 'border-box',
            overflow: 'hidden',
            transition: 'box-shadow 0.2s, transform 0.2s',
            flexShrink: 0,
        }}
            onMouseEnter={e => { e.currentTarget.style.boxShadow = `0 0 20px ${catColor}22`; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}
        >
            {/* Category + sentiment + time */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                <span style={{ fontSize: '9px', fontWeight: 800, letterSpacing: '1.5px', color: catColor, background: `${catColor}18`, padding: '3px 9px', borderRadius: '4px', border: `1px solid ${catColor}35` }}>
                    {article.category || 'MARKETS'}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '9px', fontWeight: 700, color: sentColor }}>
                        <SentimentIcon s={article.sentiment} /> {article.sentiment || 'NEUTRAL'}
                    </span>
                    <span style={{ fontSize: '10px', color: '#475569' }}>{timeAgo(article.published)}</span>
                </div>
            </div>

            {/* Headline */}
            <h3 style={{
                fontSize: '16px', fontWeight: 800, color: '#f1f5f9', lineHeight: 1.4, margin: 0, flexShrink: 0,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
            }}>
                {article.title}
            </h3>

            {/* Source */}
            <div style={{ fontSize: '12px', color: '#67e8f9', fontWeight: 700, flexShrink: 0 }}>{article.source}</div>

            {/* Up to 2 paragraphs, text clipped to available space */}
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: '7px' }}>
                {paragraphs.slice(0, 2).map((para, i) => (
                    <p key={i} style={{
                        fontSize: '14px', color: '#94a3b8', lineHeight: 1.65, margin: 0,
                        display: '-webkit-box', WebkitLineClamp: i === 0 ? 3 : 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
                    }}>
                        {para}
                    </p>
                ))}
            </div>

            {/* Read more */}
            <a href={article.link} target="_blank" rel="noreferrer"
                onClick={e => e.stopPropagation()}
                style={{
                    display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '13px', fontWeight: 700,
                    color: catColor, textDecoration: 'none', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '8px', flexShrink: 0
                }}>
                <ExternalLink size={13} /> Read Full Article
            </a>
        </div>
    );
}

export default function NewsRoom() {
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const fetchNews = async () => {
        try {
            const res = await axios.get('/api/news', { timeout: 20000 });
            setArticles(res.data || []);
            setLastUpdate(new Date());
        } catch (e) {
            console.error('News fetch error', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNews();
        const t = window.setInterval(fetchNews, 10 * 60 * 1000);
        return () => window.clearInterval(t);
    }, []);

    const Skeleton = () => (
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '12px', padding: '22px', display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
            <div style={{ height: '10px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', width: '40%' }} />
            <div style={{ height: '18px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }} />
            <div style={{ height: '18px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', width: '80%' }} />
            <div style={{ height: '12px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', marginTop: '4px' }} />
            <div style={{ height: '12px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px' }} />
            <div style={{ height: '12px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', width: '70%' }} />
        </div>
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '17px', color: '#f1f5f9', letterSpacing: '2px', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                        <Newspaper size={18} color="#00f0ff" /> NEWSROOM
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#22c55e', background: 'rgba(34,197,94,0.1)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(34,197,94,0.25)', letterSpacing: '1px' }}>TOP 6</span>
                    </h2>
                    <div style={{ fontSize: '11px', color: '#475569', marginTop: '5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Wifi size={10} color="#22c55e" />
                        AI-ranked by importance · Auto-refreshes every 10 min
                        {lastUpdate && <> · Updated {timeAgo(lastUpdate.toISOString())}</>}
                    </div>
                </div>
                <button
                    onClick={() => { setLoading(true); fetchNews(); }}
                    disabled={loading}
                    style={{ background: 'rgba(0,240,255,0.07)', border: '1px solid rgba(0,240,255,0.25)', color: '#00f0ff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700 }}
                >
                    <RefreshCw size={13} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} /> REFRESH
                </button>
            </div>

            {/* 3-column scrollable grid — 30 cards, same size, latest at top */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                paddingRight: '4px',
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(0,240,255,0.2) transparent',
            }}>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '14px',
                    alignItems: 'start',
                }}>
                    {loading
                        ? Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} />)
                        : articles.slice(0, 30).map((article, i) => (
                            <NewsCard key={i} article={article} />
                        ))
                    }
                </div>
            </div>
        </div>
    );
}
