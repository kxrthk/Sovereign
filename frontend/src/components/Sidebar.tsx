import { NavLink } from 'react-router-dom';
import { LayoutDashboard, LineChart, History, TerminalSquare, Eye, Settings, ShieldCheck, Newspaper, Radar, Activity, Briefcase, Brain, Rocket, LayoutGrid, BookOpen, Calendar } from 'lucide-react';

interface NavItem {
    to: string;
    label: string;
    icon: React.ElementType;
    badge?: string;
    badgeColor?: string;
}

const SECTIONS: { title: string; items: NavItem[] }[] = [
    {
        title: 'COMMAND',
        items: [
            { to: '/overview', label: 'Overview', icon: LayoutDashboard },
            { to: '/oracle', label: 'Oracle Cortex', icon: Brain, badge: 'CORE', badgeColor: 'var(--accent-purple)' },
            { to: '/technicals', label: 'Technicals', icon: LineChart },
            { to: '/scanner', label: 'Alpha Scanner', icon: Radar, badge: 'NEW', badgeColor: 'var(--accent-green)' },
            { to: '/pilot', label: 'Pilot Mode', icon: Rocket, badge: 'HOT', badgeColor: '#FF006E' },
            { to: '/funds', label: 'Mutual Funds', icon: Briefcase },
        ],
    },
    {
        title: 'INTELLIGENCE',
        items: [
            { to: '/news', label: 'NewsRoom', icon: Newspaper, badge: 'LIVE', badgeColor: 'var(--accent-cyan)' },
            { to: '/vision', label: 'Vision Center', icon: Eye },
        ],
    },
    {
        title: 'ANALYTICS',
        items: [
            { to: '/heatmap', label: 'Portfolio Heatmap', icon: LayoutGrid, badge: 'NEW', badgeColor: 'var(--accent-cyan)' },
            { to: '/journal', label: 'Trade Journal', icon: BookOpen },
            { to: '/calendar', label: 'Eco Calendar', icon: Calendar },
        ],
    },
    {
        title: 'SYSTEM',
        items: [
            { to: '/ledger', label: 'Ledger', icon: History },
            { to: '/config', label: 'System Config', icon: Settings },
        ],
    },
];

export default function Sidebar() {
    return (
        <nav className="sidebar" style={{ width: '240px', minWidth: '240px', borderRight: '1px solid var(--border-light)', padding: '20px 16px', display: 'flex', flexDirection: 'column', background: 'var(--bg-surface)', overflowY: 'auto' }}>
            {/* Logo */}
            <div className="logo-area" style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '36px' }}>
                <div className="logo-icon" style={{ width: '44px', height: '44px', background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000', boxShadow: '0 0 20px var(--border-glow-cyan)', flexShrink: 0 }}>
                    <ShieldCheck size={26} />
                </div>
                <div className="logo-text">
                    <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, letterSpacing: '3px', background: 'linear-gradient(to right, var(--text-primary), var(--accent-cyan))', WebkitBackgroundClip: 'text', backgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>SOVEREIGN</h1>
                    <span className="version-badge" style={{ fontSize: '9px', fontWeight: 700, color: 'var(--accent-cyan)', background: 'rgba(0, 240, 255, 0.1)', padding: '2px 6px', borderRadius: '4px', letterSpacing: '2px', border: '1px solid rgba(0, 240, 255, 0.2)' }}>V3.0 REACT</span>
                </div>
            </div>

            {/* Nav sections */}
            <div style={{ flex: 1 }}>
                {SECTIONS.map((section) => (
                    <div key={section.title} style={{ marginBottom: '28px' }}>
                        <h3 style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '2px', marginBottom: '10px', fontWeight: 800, textTransform: 'uppercase', paddingLeft: '12px' }}>
                            {section.title}
                        </h3>
                        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                            {section.items.map((item) => (
                                <li key={item.to}>
                                    <NavLink
                                        to={item.to}
                                        style={({ isActive }) => ({
                                            display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', marginBottom: '4px',
                                            borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s ease', textDecoration: 'none',
                                            fontSize: '13px', fontWeight: 600, border: '1px solid transparent',
                                            ...(isActive
                                                ? { background: 'linear-gradient(90deg, rgba(0, 240, 255, 0.15) 0%, transparent 100%)', color: 'var(--accent-cyan)', borderLeft: '3px solid var(--accent-cyan)', borderTop: '1px solid rgba(0, 240, 255, 0.1)', borderBottom: '1px solid rgba(0, 240, 255, 0.1)' }
                                                : { color: 'var(--text-secondary)' }
                                            )
                                        })}
                                    >
                                        <item.icon size={16} style={{ flexShrink: 0 }} />
                                        <span style={{ flex: 1 }}>{item.label}</span>
                                        {item.badge && (
                                            <span style={{ fontSize: '8px', fontWeight: 800, letterSpacing: '1px', color: item.badgeColor, background: `${item.badgeColor}18`, padding: '2px 5px', borderRadius: '3px', border: `1px solid ${item.badgeColor}40` }}>
                                                {item.badge}
                                            </span>
                                        )}
                                    </NavLink>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>

            {/* System status footer */}
            <div style={{ padding: '14px 16px', background: 'rgba(0, 240, 255, 0.04)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--accent-cyan)', boxShadow: '0 0 8px var(--accent-cyan)' }} className="glow-pulse" />
                    <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '1px' }}>SYSTEM ONLINE</span>
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Activity size={9} /> React Build // Vite
                </div>
            </div>
        </nav>
    );
}
