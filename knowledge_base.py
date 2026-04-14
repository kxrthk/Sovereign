# ═══════════════════════════════════════════════════════════════════
# knowledge_base.py — Deep Financial Knowledge for Local AI
# ═══════════════════════════════════════════════════════════════════
# STATIC knowledge that rarely changes. Ingested into ChromaDB once.
# This is what makes a 3.8B model punch above its weight —
# it doesn't need to "know" finance, it just needs to READ this.
# ═══════════════════════════════════════════════════════════════════

import logging
import os

logger = logging.getLogger("KnowledgeBase")

# ─────────────────────────────────────────────────────────────────
# CATEGORY 1: TRADING STRATEGIES (STATIC — update quarterly)
# ─────────────────────────────────────────────────────────────────
STRATEGY_KNOWLEDGE = [
    {
        "id": "momentum_strategy",
        "text": """MOMENTUM TRADING STRATEGY: Buy assets that have shown strong recent price increases, sell those that have dropped. 
Key rules: RSI > 60 signals upward momentum. Volume must be above 20-day average (confirms conviction). 
Enter when price breaks above 20-day EMA with volume surge. Exit when RSI crosses below 50 or price drops below 20-day EMA.
Risk: Momentum reversal. Always set 2-3% stop loss. Best in TRENDING regime. AVOID in CHOPPY or CRASH regime.
Indian context: Works well with mid-cap stocks like Zomato, HAL, Trent during bull phases."""
    },
    {
        "id": "mean_reversion_strategy", 
        "text": """MEAN REVERSION STRATEGY: Buy when price drops significantly below its average, expecting it to revert.
Key rules: Buy when RSI < 30 (oversold) AND price is >2 standard deviations below 50-day SMA.
Enter in small positions. Scale in if price drops further. Exit at 50-day SMA.
Risk: Value traps — stock may be falling for fundamental reasons. Always check news sentiment before buying dips.
Best in RANGING/CHOPPY regime. AVOID in CRASH regime (falling knives). Works well with large-cap Indian stocks like Reliance, HDFC Bank."""
    },
    {
        "id": "breakout_strategy",
        "text": """BREAKOUT TRADING STRATEGY: Enter when price breaks above resistance or below support with high volume.
Key rules: Identify consolidation zone (20+ days of tight range). Wait for close above resistance with 1.5x average volume.
Enter on the breakout candle. Stop loss just below the breakout level. Target: measure the consolidation range and project upward.
Risk: False breakouts. Volume MUST confirm. Low volume breakouts fail 60% of the time.
Indian context: BSE/NSE stocks often consolidate around round numbers (₹500, ₹1000, ₹2000). Breakout above these levels are psychologically significant."""
    },
    {
        "id": "sector_rotation_strategy",
        "text": """SECTOR ROTATION STRATEGY: Move capital between sectors based on economic cycle phase.
Early Recovery: Buy Financials, Consumer Discretionary. Mid Cycle: Buy IT, Industrials. 
Late Cycle: Buy Energy, Materials, Defence. Recession: Buy FMCG, Pharma, Utilities (defensive).
Indian sectors: NIFTY Bank leads in early recovery. NIFTY IT leads in mid-cycle with USD strength.
NIFTY Metal and Energy lead in late cycle. NIFTY Pharma and FMCG are defensive havens.
Key indicator: Track NIFTY sector index 3-month momentum. Rotate into top 2 performing sectors."""
    },
    {
        "id": "risk_management_rules",
        "text": """SOVEREIGN RISK MANAGEMENT DOCTRINE:
1. Never risk more than 1-2% of capital per trade.
2. Maximum 5 open positions at any time. 
3. Daily loss limit: -20% of capital → kill switch activated.
4. Loss streak limit: 5 consecutive losses → enter DEFENSIVE mode (reduce position size by 50%).
5. Always use stop losses. No exceptions.
6. Trade cooldown: Wait 30 minutes before re-entering same symbol.
7. Avoid trading first 15 minutes after market open (noise) and last 15 minutes before close (manipulation).
8. In CRASH regime: reduce all position sizes to 25% of normal. In CHOPPY: reduce to 50%.
9. Weekly loss limit: ₹1000. If breached, pause all trading until next Monday.
10. Paper trade new strategies for minimum 30 trades before going live."""
    },
]

# ─────────────────────────────────────────────────────────────────
# CATEGORY 2: MUTUAL FUND DEEP ANALYSIS (SEMI-STATIC — update monthly)
# ─────────────────────────────────────────────────────────────────
FUND_DEEP_KNOWLEDGE = [
    {
        "id": "fund_valuation_framework",
        "text": """HOW TO EVALUATE A MUTUAL FUND:
1. CAGR alone is misleading. A fund with 30% CAGR in a 40% bull market underperformed.
2. Compare against benchmark: Flexi-cap → NIFTY 500. Mid-cap → NIFTY Midcap 150. 
3. Sharpe Ratio > 1.0 = good risk-adjusted return. Below 0.5 = poor.
4. Expense Ratio: Below 0.5% = excellent. 0.5-1.0% = acceptable. Above 1.5% = expensive.
5. AUM: Very large AUM (>50,000 Cr) may struggle in small/mid-cap due to liquidity constraints.
6. Fund Manager Track Record: Check their history across market cycles (minimum 5 years).
7. Portfolio Overlap: If you hold 2 funds with >40% overlap, you're paying double fees for same exposure.
8. For prediction: Historical returns regress toward long-term mean. A fund showing 40% CAGR will likely normalize to 20-25% over 5+ years."""
    },
    {
        "id": "indian_mf_categories",
        "text": """INDIAN MUTUAL FUND CATEGORIES AND EXPECTED LONG-TERM RETURNS:
Large Cap: Expected 10-14% CAGR long-term. Lower risk. Benchmark: NIFTY 50.
Mid Cap: Expected 14-20% CAGR long-term. Moderate risk. Can drop 30-40% in corrections.
Small Cap: Expected 16-25% CAGR long-term. High risk. Can drop 50-60% in bear markets.
Flexi Cap: Expected 12-18% CAGR. Manager decides allocation. Best for passive investors.
Thematic/Sector: Expected 15-30% CAGR during favorable cycles. CAN UNDERPERFORM for years during unfavorable cycles.
Defence Thematic: Exceptional 35-45% returns currently due to government capex, BUT expected to normalize to 18-22% as base effect kicks in.
IT Thematic: Currently in headwind (AI disruption fears, global spending cuts). Expected to recover in 2-3 years.
Debt/Hybrid: Expected 7-10% CAGR. Safety-first approach."""
    },
    {
        "id": "sip_projection_rules",
        "text": """SIP AND LUMPSUM PREDICTION METHODOLOGY:
For SIP projection: Use XIRR, not simple CAGR. SIP returns are typically 2-3% lower than lumpsum CAGR because money enters gradually.
For lumpsum: FV = P × (1 + r/100)^N where r = AI-adjusted CAGR.
AI-ADJUSTMENT RULES for small model:
- If category has shown >35% CAGR over 3 years: Apply regression factor. Predict 60-70% of that rate going forward.
- If category has shown <10% CAGR over 3 years: Apply recovery factor. Predict 120-140% of that rate going forward.
- If Indian GDP growth is strong (>6.5%): Add 1-2% to equity fund projections.
- If RBI is cutting rates: Add 1-2% to debt fund projections.
- If FII flows are positive: Add 1% to large-cap projections.
- ALWAYS project conservatively. Underestimating is better than overestimating for user trust."""
    },
]

# ─────────────────────────────────────────────────────────────────
# CATEGORY 3: INDIAN MARKET STRUCTURE (STATIC)
# ─────────────────────────────────────────────────────────────────
MARKET_KNOWLEDGE = [
    {
        "id": "indian_market_basics",
        "text": """INDIAN STOCK MARKET STRUCTURE:
NSE (National Stock Exchange): Primary exchange. NIFTY 50 is the benchmark index.
BSE (Bombay Stock Exchange): Older exchange. SENSEX (BSE 30) is its benchmark.
Trading hours: 9:15 AM - 3:30 PM IST, Monday-Friday. Pre-open session: 9:00-9:15 AM.
T+1 settlement: Trades settle next business day.
Circuit breakers: 10% drop → 45 min halt. 15% drop → 1h45m halt. 20% drop → market closed for day.
FII (Foreign Institutional Investors): Biggest market movers. Net FII buying is bullish.
DII (Domestic Institutional Investors): Mutual funds, insurance cos. Usually buy when FII sell.
Retail investors: Tend to buy at tops and sell at bottoms (contrarian indicator)."""
    },
    {
        "id": "indian_macro_indicators",
        "text": """KEY INDIAN MACROECONOMIC INDICATORS TO TRACK:
1. RBI Repo Rate: Currently 6.5%. Rate cuts = bullish for equities and debt.
2. CPI Inflation: Target 4% ±2%. Above 6% = hawkish RBI = bearish.
3. GDP Growth: India at 6.5-7.0% — strong. Supports equity markets.
4. USD/INR: Weak rupee hurts importers (oil companies) but helps IT exporters.
5. Crude Oil Price: India imports 80% of oil. High crude = high inflation = bearish.
6. FII/DII Net Flows: Available daily on NSE website. FII selling streak > 10 days = caution.
7. India VIX: Below 13 = low volatility (complacent). Above 20 = high fear. Above 30 = panic.
8. 10-Year Government Bond Yield: Rising yields = money moving from equity to debt."""
    },
]

# ═══════════════════════════════════════════════════════════════════
# INGESTION FUNCTION
# ═══════════════════════════════════════════════════════════════════
def ingest_all_knowledge():
    """Ingest all static knowledge into SovereignRAG ChromaDB."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [KB] %(message)s")
    
    try:
        from sovereign_rag import SovereignRAG
        rag = SovereignRAG()
    except Exception as e:
        logger.error(f"Cannot initialize RAG: {e}")
        return

    all_docs = [
        ("research_papers", STRATEGY_KNOWLEDGE),
        ("market_intelligence", FUND_DEEP_KNOWLEDGE),
        ("market_intelligence", MARKET_KNOWLEDGE),
    ]

    total = 0
    for collection, docs in all_docs:
        for doc in docs:
            try:
                count = rag.ingest_text(
                    text=doc["text"],
                    metadata={"source": f"knowledge_base_{doc['id']}", "type": "static_knowledge"},
                    collection=collection
                )
                total += count
                logger.info(f"  Ingested: {doc['id']} ({count} chunks)")
            except Exception as e:
                logger.error(f"  Failed: {doc['id']}: {e}")

    logger.info(f"Total knowledge ingested: {total} chunks across {sum(len(d) for _, d in all_docs)} documents.")


if __name__ == "__main__":
    ingest_all_knowledge()
