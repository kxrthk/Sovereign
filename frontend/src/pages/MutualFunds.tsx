import { useState, useEffect } from 'react';
import axios from 'axios';
import { Briefcase, TrendingUp, ShieldCheck, PieChart as PieChartIcon, ArrowRight, X, BarChart2, CheckCircle2, Activity } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface AssetAllocation {
    sector: string;
    weight: number;
}

interface MutualFund {
    id: string;
    name: string;
    category: string;
    description: string;
    performanceRate: number; // 0-100
    safetyRate: number;      // 0-100
    aum: string;
    expenseRatio: string;
    trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    cagr3yr: string;
    allocations: AssetAllocation[];
    topHoldings: string[];
}

const BACKUP_FUNDS: MutualFund[] = [
    {
        id: 'ppfas', name: 'Parag Parikh Flexi Cap', category: 'Equity - Flexi Cap',
        description: 'A go-anywhere flexi cap fund that also takes measured bets in global tech titans for downside protection.',
        performanceRate: 88, safetyRate: 82, aum: '₹ 56,800 Cr', expenseRatio: '0.62%', trend: 'NEUTRAL', cagr3yr: '21.4%',
        allocations: [{ sector: 'Financials', weight: 31 }, { sector: 'Tech', weight: 19 }, { sector: 'Consumer', weight: 14 }, { sector: 'Others', weight: 36 }],
        topHoldings: ['HDFC Bank', 'Bajaj Holdings', 'ITC', 'Microsoft', 'Alphabet']
    },
    {
        id: 'quant-small', name: 'Quant Small Cap', category: 'Equity - Small Cap',
        description: 'Highly aggressive quantitative model-driven fund. Rotates violently based on momentum signals.',
        performanceRate: 94, safetyRate: 61, aum: '₹ 15,200 Cr', expenseRatio: '0.77%', trend: 'BULLISH', cagr3yr: '34.8%',
        allocations: [{ sector: 'Industrials', weight: 26 }, { sector: 'Materials', weight: 18 }, { sector: 'Manufacturing', weight: 15 }, { sector: 'Others', weight: 41 }],
        topHoldings: ['Reliance Ind', 'Jio Financial', 'Aravind', 'NTPC', 'IRB Infra']
    },
    {
        id: 'sbi-contra', name: 'SBI Contra Fund', category: 'Equity - Contra',
        description: 'Focuses on out-of-favor companies and sectors exhibiting deep value traits with impending turnaround catalysts.',
        performanceRate: 85, safetyRate: 74, aum: '₹ 32,400 Cr', expenseRatio: '0.68%', trend: 'NEUTRAL', cagr3yr: '26.1%',
        allocations: [{ sector: 'Financials', weight: 24 }, { sector: 'Energy', weight: 16 }, { sector: 'Auto', weight: 11 }, { sector: 'Others', weight: 49 }],
        topHoldings: ['GAIL', 'State Bank of India', 'Tech Mahindra', 'Cognizant', 'ONGC']
    },
    {
        id: 'hdfc-mid', name: 'HDFC Mid-Cap', category: 'Equity - Mid Cap',
        description: 'Largest mid-cap fund in India prioritizing consistent, high-quality compounding scalable businesses.',
        performanceRate: 82, safetyRate: 78, aum: '₹ 61,000 Cr', expenseRatio: '0.81%', trend: 'BULLISH', cagr3yr: '24.9%',
        allocations: [{ sector: 'Financials', weight: 22 }, { sector: 'Industrials', weight: 18 }, { sector: 'Healthcare', weight: 12 }, { sector: 'Others', weight: 48 }],
        topHoldings: ['Indian Hotels', 'Tata Comm', 'Apollo Tyres', 'Max Financial', 'Federal Bank']
    },
    {
        id: 'icici-prudential', name: 'ICICI Pru Asset Allocator', category: 'Hybrid - Asset',
        description: 'Automatically shifts capital between Equity, Debt, and Gold based on in-house valuation models. Safety first.',
        performanceRate: 72, safetyRate: 95, aum: '₹ 22,500 Cr', expenseRatio: '0.90%', trend: 'NEUTRAL', cagr3yr: '14.2%',
        allocations: [{ sector: 'Equity', weight: 45 }, { sector: 'Debt', weight: 45 }, { sector: 'Commodity', weight: 10 }],
        topHoldings: ['GOI Bonds', 'HDFC Bank', 'ICICI Bank', 'Physical Gold', 'Reliance']
    },
    {
        id: 'nippon-india', name: 'Nippon India Growth', category: 'Equity - Mid Cap',
        description: 'A wealth creation pioneer focusing on secular growth themes within the Indian Mid-cap space.',
        performanceRate: 86, safetyRate: 71, aum: '₹ 24,100 Cr', expenseRatio: '0.84%', trend: 'BULLISH', cagr3yr: '25.6%',
        allocations: [{ sector: 'Financials', weight: 25 }, { sector: 'Consumer', weight: 17 }, { sector: 'Industrials', weight: 15 }, { sector: 'Others', weight: 43 }],
        topHoldings: ['Cholamandalam', 'Power Finance', 'Max Financial', 'Supreme Ind', 'Varun Beverages']
    },
    {
        id: 'motilal-midcap', name: 'Motilal Oswal Midcap', category: 'Equity - Mid Cap',
        description: 'High conviction mid-cap portfolio focusing on market leaders with significant economic moats.',
        performanceRate: 89, safetyRate: 72, aum: '₹ 11,400 Cr', expenseRatio: '0.71%', trend: 'NEUTRAL', cagr3yr: '32.4%',
        allocations: [{ sector: 'Technology', weight: 24 }, { sector: 'Financials', weight: 21 }, { sector: 'Consumer', weight: 18 }, { sector: 'Others', weight: 37 }],
        topHoldings: ['Zomato', 'Jio Financial', 'Persistent Systems', 'Kalyan Jewellers', 'Vodafone Idea']
    },
    {
        id: 'hdfc-defence', name: 'HDFC Defence Fund', category: 'Thematic - Defence',
        description: 'Exclusive thematic fund capturing the massive sovereign capital expenditure in Indian aerospace and defense.',
        performanceRate: 96, safetyRate: 55, aum: '₹ 3,250 Cr', expenseRatio: '0.85%', trend: 'BULLISH', cagr3yr: '41.2%',
        allocations: [{ sector: 'Aerospace', weight: 35 }, { sector: 'Shipbuilding', weight: 28 }, { sector: 'Explosives', weight: 15 }, { sector: 'Others', weight: 22 }],
        topHoldings: ['HAL', 'BEL', 'Mazagon Dock', 'Cochin Shipyard', 'BDL']
    },
    {
        id: 'tata-digital', name: 'Tata Digital India', category: 'Thematic - Technology',
        description: 'Pure-play technology fund heavily positioned in IT services, software, and emerging cyber-infrastructure.',
        performanceRate: 79, safetyRate: 85, aum: '₹ 9,100 Cr', expenseRatio: '0.75%', trend: 'NEUTRAL', cagr3yr: '18.6%',
        allocations: [{ sector: 'IT Services', weight: 42 }, { sector: 'Software', weight: 28 }, { sector: 'Telecom', weight: 12 }, { sector: 'Others', weight: 18 }],
        topHoldings: ['Infosys', 'TCS', 'Tech Mahindra', 'HCL Tech', 'Bharti Airtel']
    }
];

export default function MutualFunds() {
    const [funds, setFunds] = useState<MutualFund[]>([]);
    const [selectedFund, setSelectedFund] = useState<MutualFund | null>(null);
    const [loading, setLoading] = useState(true);
    
    // Future Predictor state
    const [calcAmount, setCalcAmount] = useState<number>(10000);
    const [calcYears, setCalcYears] = useState<number>(3);
    const [aiPrediction, setAiPrediction] = useState<number | null>(null);
    const [aiReasoning, setAiReasoning] = useState<string>('');
    const [predicting, setPredicting] = useState(false);
    const [lastPredicted, setLastPredicted] = useState<string>('');

    // Reset prediction when fund changes
    useEffect(() => {
        setAiPrediction(null);
        setAiReasoning('');
        setLastPredicted('');
    }, [selectedFund?.id]);

    // Explicit predict function — fires only on button click
    const runPrediction = async () => {
        if (!selectedFund || predicting) return;
        setPredicting(true);
        try {
            const res = await axios.post('/api/ai_predict_wealth', {
                fund_name: selectedFund.name,
                category: selectedFund.category,
                capital: calcAmount,
                years: calcYears,
                cagr_hint: selectedFund.cagr3yr
            });
            setAiPrediction(res.data.estimatedValue);
            setAiReasoning(res.data.reasoning || '');
        } catch {
            const cagr = parseFloat(selectedFund.cagr3yr) / 100;
            setAiPrediction(Math.round(calcAmount * Math.pow(1 + cagr, calcYears)));
            setAiReasoning('Using historical CAGR due to connection issue.');
        } finally {
            setPredicting(false);
            setLastPredicted(new Date().toLocaleTimeString());
        }
    };

    useEffect(() => {
        const fetchFunds = async () => {
            try {
                const res = await axios.get('/api/mutual_funds');
                setFunds(res.data);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch mutual funds API. Displaying static institutional parameters.", err);
                if (funds.length === 0) setFunds(BACKUP_FUNDS);
                setLoading(false);
            }
        };
        fetchFunds();
    }, []);

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '18px', color: 'var(--text-primary)', letterSpacing: '2px', display: 'flex', alignItems: 'center', gap: '10px', margin: 0 }}>
                        <Briefcase size={20} className="neon-cyan" /> SIP & MUTUAL FUNDS VAULT
                    </h2>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', letterSpacing: '1px' }}>
                        Institutional allocations, tracking performance mechanics and systemic safety ratings.
                    </div>
                </div>
            </div>

            {/* Fund Grid */}
            {loading ? (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                    <div className="spinner" style={{ width: '40px', height: '40px', border: '3px solid rgba(0,240,255,0.15)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '16px' }} />
                    <div style={{ fontSize: '13px', letterSpacing: '2px', fontFamily: 'var(--font-mono)' }}>CONNECTING TO INSTITUTIONAL FEED...</div>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
                    {funds.map(fund => (
                        <div 
                            key={fund.id}
                            className="glass-panel hover-glow"
                            style={{ padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', overflow: 'hidden' }}
                            onClick={() => setSelectedFund(fund)}
                        >
                            {/* Title Row */}
                            <div>
                                <div style={{ fontSize: '9px', fontWeight: 800, color: 'var(--accent-cyan)', letterSpacing: '1.5px', textTransform: 'uppercase', marginBottom: '4px' }}>
                                    {fund.category}
                                </div>
                                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.5px' }}>
                                    {fund.name}
                                </div>
                            </div>

                            {/* Circular Graphs Row */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', background: 'var(--sub-panel-bg)', padding: '12px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.03)' }}>
                                {/* Perf Graph */}
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                    <div style={{ height: '60px', width: '60px', position: 'relative' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie data={[{ value: fund.performanceRate }, { value: Math.max(0, 100 - fund.performanceRate) }]} cx="50%" cy="50%" innerRadius={22} outerRadius={30} dataKey="value" stroke="none">
                                                    <Cell fill="var(--accent-cyan)" />
                                                    <Cell fill="rgba(255,255,255,0.05)" />
                                                </Pie>
                                            </PieChart>
                                        </ResponsiveContainer>
                                        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                                            {fund.performanceRate}%
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px', marginTop: '4px' }}>PERFORMANCE</div>
                                </div>
                                {/* Safety Graph */}
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                    <div style={{ height: '60px', width: '60px', position: 'relative' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie data={[{ value: fund.safetyRate }, { value: Math.max(0, 100 - fund.safetyRate) }]} cx="50%" cy="50%" innerRadius={22} outerRadius={30} dataKey="value" stroke="none">
                                                    <Cell fill="var(--accent-green)" />
                                                    <Cell fill="rgba(255,255,255,0.05)" />
                                                </Pie>
                                            </PieChart>
                                        </ResponsiveContainer>
                                        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800, color: 'var(--accent-green)' }}>
                                            {fund.safetyRate}%
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px', marginTop: '4px' }}>SAFETY RATE</div>
                                </div>
                            </div>

                            {/* Footer details */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '4px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                                    <TrendingUp size={12} color="var(--accent-cyan)" /> 3Y CAGR: <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{fund.cagr3yr}</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)' }}>
                                    <ArrowRight size={14} />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Details Modal overlay */}
            {selectedFund && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(5, 10, 20, 0.8)', backdropFilter: 'blur(8px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={() => setSelectedFund(null)}>
                    {/* Modal Box */}
                    <div className="glass-panel" style={{ width: '100%', maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto', padding: '32px', position: 'relative', border: '1px solid var(--accent-cyan)' }} onClick={e => e.stopPropagation()}>
                        <button onClick={() => setSelectedFund(null)} style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                            <X size={24} />
                        </button>
                        <div style={{ marginBottom: '28px' }}>
                            <span style={{ background: 'var(--accent-cyan)', color: '#000', fontSize: '10px', fontWeight: 800, padding: '4px 8px', borderRadius: '4px', letterSpacing: '1px' }}>{selectedFund.category}</span>
                            <h2 style={{ fontSize: '24px', color: 'var(--text-primary)', margin: '12px 0 8px', letterSpacing: '1px' }}>{selectedFund.name}</h2>
                            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '85%' }}>{selectedFund.description}</p>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
                            <div style={{ background: 'var(--sub-panel-bg)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>CORE TREND</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', fontWeight: 800, color: selectedFund.trend === 'BULLISH' ? 'var(--accent-green)' : selectedFund.trend === 'BEARISH' ? 'var(--accent-danger)' : 'var(--text-primary)' }}>
                                    {selectedFund.trend === 'BULLISH' ? <TrendingUp size={16} /> : selectedFund.trend === 'BEARISH' ? <BarChart2 size={16} /> : <Activity size={16} />} 
                                    {selectedFund.trend}
                                </div>
                            </div>
                            <div style={{ background: 'var(--sub-panel-bg)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>FINANCIAL AUM</div>
                                <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)' }}>{selectedFund.aum}</div>
                            </div>
                            <div style={{ background: 'var(--sub-panel-bg)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>EXPENSE RATIO</div>
                                <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)' }}>{selectedFund.expenseRatio}</div>
                            </div>
                            <div style={{ background: 'var(--sub-panel-bg)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>3YR CAGR</div>
                                <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--accent-cyan)' }}>{selectedFund.cagr3yr}</div>
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                            <div style={{ background: 'var(--sub-panel-bg)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <h3 style={{ fontSize: '12px', color: 'var(--text-secondary)', letterSpacing: '1.5px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <PieChartIcon size={14} /> RELATIVE SECTOR WEIGHTS
                                </h3>
                                <div style={{ height: '140px', width: '100%', marginBottom: '16px' }}>
                                    <ResponsiveContainer>
                                        <PieChart>
                                            <Pie data={selectedFund.allocations} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="weight" stroke="none">
                                                {selectedFund.allocations.map((_, index) => (
                                                    <Cell key={`cell-${index}`} fill={['var(--accent-cyan)', 'var(--accent-green)', '#a78bfa', 'rgba(255,255,255,0.1)'][index % 4]} />
                                                ))}
                                            </Pie>
                                            <Tooltip contentStyle={{ background: 'rgba(15,23,42,0.9)', border: '1px solid rgba(0,240,255,0.3)', borderRadius: '8px', fontSize: '12px' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginBottom: '24px' }}>
                                    {selectedFund.allocations.map((a, i) => (
                                        <div key={a.sector} style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: ['var(--accent-cyan)', 'var(--accent-green)', '#a78bfa', 'rgba(255,255,255,0.1)'][i % 4] }} />
                                            {a.sector}
                                        </div>
                                    ))}
                                </div>

                                {/* Wealth Predictor Sub-Layout — AI Powered */}
                                <div style={{ background: 'rgba(0,240,255,0.05)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(0,240,255,0.15)', marginTop: 'auto' }}>
                                    <div style={{ fontSize: '10px', color: 'var(--accent-cyan)', letterSpacing: '1px', fontWeight: 700, marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <span>AI WEALTH PREDICTOR</span>
                                        {lastPredicted && <span style={{ fontSize: '8px', color: 'var(--text-muted)', fontWeight: 400 }}>Last: {lastPredicted}</span>}
                                    </div>
                                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '4px' }}>CAPITAL (₹)</div>
                                            <input 
                                                type="number" 
                                                value={calcAmount} 
                                                onChange={(e) => setCalcAmount(Math.max(0, Number(e.target.value)))}
                                                style={{ width: '100%', background: 'var(--sub-panel-bg)', border: '1px solid var(--border-light)', color: 'var(--text-primary)', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', fontFamily: 'var(--font-mono)', outline: 'none', boxSizing: 'border-box' }}
                                            />
                                        </div>
                                        <div style={{ flex: 0.5 }}>
                                            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '4px' }}>YEARS</div>
                                            <input 
                                                type="number" 
                                                value={calcYears} 
                                                onChange={(e) => setCalcYears(Math.max(1, Number(e.target.value)))}
                                                style={{ width: '100%', background: 'var(--sub-panel-bg)', border: '1px solid var(--border-light)', color: 'var(--text-primary)', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', fontFamily: 'var(--font-mono)', outline: 'none', boxSizing: 'border-box' }}
                                            />
                                        </div>
                                        <button
                                            onClick={runPrediction}
                                            disabled={predicting}
                                            style={{
                                                padding: '6px 14px', borderRadius: '6px', border: '1px solid var(--accent-cyan)',
                                                background: predicting ? 'rgba(0,240,255,0.05)' : 'rgba(0,240,255,0.15)',
                                                color: 'var(--accent-cyan)', cursor: predicting ? 'not-allowed' : 'pointer',
                                                fontSize: '10px', fontWeight: 800, letterSpacing: '1px',
                                                fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap',
                                                opacity: predicting ? 0.6 : 1, transition: 'all 0.2s'
                                            }}
                                        >
                                            {predicting ? 'ANALYZING...' : 'PREDICT'}
                                        </button>
                                    </div>
                                    {aiPrediction !== null && (
                                        <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(0,255,102,0.06)', borderRadius: '6px', border: '1px solid rgba(0,255,102,0.15)' }}>
                                            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '4px' }}>AI ESTIMATED VALUE</div>
                                            <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                                                ₹{aiPrediction.toLocaleString('en-IN')}
                                            </div>
                                        </div>
                                    )}
                                    {aiReasoning && (
                                        <div style={{ marginTop: '8px', fontSize: '9px', color: 'var(--text-muted)', lineHeight: 1.5, fontStyle: 'italic', borderTop: '1px solid rgba(0,240,255,0.08)', paddingTop: '8px' }}>
                                            🤖 {aiReasoning}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div style={{ background: 'var(--sub-panel-bg)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <h3 style={{ fontSize: '12px', color: 'var(--text-secondary)', letterSpacing: '1.5px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <ShieldCheck size={14} /> TOP MANAGED ASSETS
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                    {selectedFund.topHoldings.map((asset, i) => (
                                        <div key={asset} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px', background: 'var(--sub-panel-border)', borderRadius: '6px' }}>
                                            <div style={{ color: 'var(--accent-cyan)', fontSize: '11px', fontWeight: 800 }}>#{i + 1}</div>
                                            <div style={{ color: 'var(--text-primary)', fontSize: '13px', fontWeight: 600 }}>{asset}</div>
                                            <CheckCircle2 size={14} color="var(--accent-green)" style={{ marginLeft: 'auto', opacity: 0.6 }} />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
