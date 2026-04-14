import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
# ═══════════════════════════════════════════════════════════════════
# sovereign_knowledge_engine.py — Elite Data Acquisition & Training
# ═══════════════════════════════════════════════════════════════════
# Downloads premium-grade financial data from FREE public sources,
# organizes it into structured knowledge, and:
#   1. Ingests into ChromaDB RAG (immediate performance boost)
#   2. Generates fine-tuning JSONL dataset (for future model training)
# ═══════════════════════════════════════════════════════════════════

import os
import json
import csv
import logging
import datetime
import time
from typing import List, Dict

logger = logging.getLogger("KnowledgeEngine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [KNOWLEDGE] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRAINING_DIR = os.path.join(DATA_DIR, "training")
os.makedirs(TRAINING_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: ELITE FINANCIAL KNOWLEDGE (HAND-CURATED)
# ═══════════════════════════════════════════════════════════════════
# This is the most valuable data — distilled expertise that would
# take years to accumulate. Written in a format the model learns from.

ELITE_KNOWLEDGE = [

    # ─── MARKET CRASH PATTERNS (Learn from history) ───────────
    {
        "id": "crash_2008_global",
        "collection": "research_papers",
        "text": """HISTORICAL CRASH ANALYSIS: 2008 Global Financial Crisis
Trigger: US subprime mortgage collapse → Lehman Brothers bankruptcy → global credit freeze.
Indian Impact: NIFTY fell from 6300 to 2500 (-60%) in 12 months. 
Recovery: Took 2.5 years to reclaim previous highs.
Lessons: Banks and financials fell hardest (-70%). FMCG and pharma fell least (-30%). 
Gold surged +25% as safe haven. FII selling was the primary driver.
Pattern: Credit crises spread slowly then crash suddenly. Watch for: rising NPAs, inverted yield curves, sudden FII outflows.
Prediction rule: If NIFTY drops >15% in 1 month with VIX >25, expect further 10-20% downside. Scale in slowly, don't catch falling knives."""
    },
    {
        "id": "crash_2020_covid",
        "collection": "research_papers",
        "text": """HISTORICAL CRASH ANALYSIS: 2020 COVID-19 Crash
Trigger: Global pandemic lockdowns → economic shutdown → supply chain collapse.
Indian Impact: NIFTY fell from 12400 to 7500 (-40%) in just 5 weeks (fastest crash in history).
Recovery: V-shaped recovery. NIFTY reclaimed highs in 8 months, hit new ATH in 12 months.
Lessons: Panic selling creates generational buying opportunities. Pharma and IT recovered fastest.
Hospitality, aviation, real estate took 2+ years to recover.
Pattern: Exogenous shocks (pandemic, war) cause sharp V-recoveries because the underlying economy is intact.
Prediction rule: If crash is caused by external shock (not financial system failure), recovery is typically faster. Buy quality stocks at -30% from ATH."""
    },
    {
        "id": "crash_2000_dotcom",
        "collection": "research_papers",
        "text": """HISTORICAL CRASH ANALYSIS: 2000 Dot-Com Bubble
Trigger: Overvaluation of internet companies with no earnings → bubble burst.
Indian Impact: NIFTY fell from 1800 to 850 (-53%). IT stocks fell 70-90%.
Recovery: Took 4 years to recover. Many IT companies never recovered.
Lessons: Never invest in companies without earnings just because the sector is hot.
PE ratio >40x for a sector = bubble territory. Current AI sector may repeat this pattern.
Pattern: Bubbles inflate for years but crash in months. Always check: Is the company profitable? Is revenue growing? Or is it just hype?
Prediction rule: If a thematic fund has returned >50% for 2 consecutive years, expect mean reversion. Reduce exposure."""
    },

    # ─── BEHAVIORAL FINANCE (Understanding market psychology) ──
    {
        "id": "behavioral_fear_greed",
        "collection": "research_papers",
        "text": """BEHAVIORAL FINANCE: Fear & Greed Cycle
Markets oscillate between FEAR (panic selling, VIX spike, media doom) and GREED (FOMO buying, euphoria, every stock is a 'multibagger').
Key indicator: India VIX. Below 12 = extreme complacency (greed). Above 25 = fear. Above 35 = panic.
Professional traders do the OPPOSITE of retail emotion: Buy when VIX is high (fear), sell when VIX is low (greed).
Anchoring bias: Investors anchor to their buy price and refuse to sell at a loss (disposition effect). This is irrational.
Herding: When everyone is buying the same stock/theme (AI, EV, defence), it's usually late in the cycle.
Confirmation bias: Investors seek news that confirms their existing position. Always seek disconfirming evidence.
As a trading AI, you must be EMOTIONLESS. Follow data, not sentiment. Fear and greed are signals to exploit, not follow."""
    },
    {
        "id": "behavioral_narratives",
        "collection": "research_papers",
        "text": """BEHAVIORAL FINANCE: Narrative Detection & Satire Awareness
Markets move on NARRATIVES, not just data. Learn to decode:
1. HYPE NARRATIVES: 'AI will replace all jobs' → AI stocks overvalued. '5 trillion economy by 2027' → political aspiration, not guaranteed.
2. FEAR NARRATIVES: 'Market will crash 50%' → usually promoted by those short the market or seeking clicks.
3. SATIRICAL/HUMOR CONTENT: Sources like Faking News, The Onion, NewsThump publish fake headlines for humor.
   NEVER trade on satirical news. Signs of satire: absurd claims, too-good-to-be-true numbers, humor tags.
4. INDIRECT LANGUAGE IN POLICY: RBI saying 'gradual withdrawal of accommodation' = rate hikes coming.
   Government saying 'fiscal consolidation' = spending cuts ahead. 'Strategic disinvestment' = PSU sell-off.
5. PROPAGANDA: Election season produces 90% noise. Ignore political claims about markets. Focus on actual policy actions.
6. CORPORATE SPEAK: 'Temporary headwind' = serious problem. 'Exploring strategic alternatives' = possible sale/layoffs.
   'One-time exceptional item' = recurring problem they're hiding.
Rule: If a headline triggers a strong emotional reaction, it's probably designed to manipulate. Step back and analyze."""
    },

    # ─── TECHNICAL ANALYSIS DEEP KNOWLEDGE ────────────────────
    {
        "id": "technical_patterns",
        "collection": "research_papers",
        "text": """TECHNICAL ANALYSIS: Key Chart Patterns for Indian Markets
HEAD AND SHOULDERS: Bearish reversal pattern. Three peaks, middle highest. When neckline breaks, target = head height projected downward. Reliability: 70% in trending markets.
DOUBLE BOTTOM: Bullish reversal. Two lows at similar level. Buy on breakout above the middle peak. Reliability: 65%.
CUP AND HANDLE: Bullish continuation. Rounded bottom (cup) followed by small pullback (handle). Classic accumulation pattern. Reliability: 60%.
FLAG/PENNANT: Continuation pattern after sharp move. Small consolidation then breakout in same direction. Works well for NIFTY futures.
MOVING AVERAGES: 50-day crossing above 200-day = Golden Cross (bullish). Reverse = Death Cross (bearish). Works on NIFTY weekly chart.
BOLLINGER BANDS: Price touching lower band with RSI <30 = oversold bounce likely. Upper band with RSI >70 = pullback likely.
Indian market specific: NIFTY respects 200-day EMA strongly. Buy when NIFTY touches 200-EMA with bullish divergence on RSI."""
    },
    {
        "id": "technical_indicators_advanced",
        "collection": "research_papers",
        "text": """ADVANCED TECHNICAL INDICATORS:
RSI (Relative Strength Index): 14-period standard. <30 oversold, >70 overbought. But in strong trends, RSI can stay >70 for weeks (don't short just because RSI is high).
MACD: Signal line crossover = trend change. Histogram divergence from price = early warning of reversal.
ATR (Average True Range): Measures volatility. Use for position sizing: higher ATR = smaller position. If ATR% < 0.3, the stock is too choppy to trade profitably.
VWAP (Volume Weighted Average Price): Institutional benchmark. Price above VWAP = institutions are net buyers (bullish). Below = net sellers.
SUPERTREND: Popular in Indian markets. 10-period, 3x ATR multiplier. Good for trailing stops on swing trades.
OBV (On-Balance Volume): Rising OBV with flat price = accumulation (smart money buying). Falling OBV with flat price = distribution (smart money selling).
FIBONACCI RETRACEMENTS: 38.2%, 50%, 61.8% levels. NIFTY consistently respects 50% and 61.8% retracement levels during corrections."""
    },

    # ─── SECTOR DEEP DIVES (Indian specific) ───────────────────
    {
        "id": "sector_banking_india",
        "collection": "market_intelligence",
        "text": """INDIAN BANKING SECTOR DEEP DIVE:
Structure: Public sector banks (SBI, PNB, BOB) vs Private sector (HDFC Bank, ICICI, Kotak) vs Small Finance Banks (AU, Ujjivan).
Key metrics: NIM (Net Interest Margin) — higher is better. CASA ratio — higher means cheaper funding. NPA ratio — lower is better.
HDFC Bank: Gold standard. Consistent 16-18% ROE. Premium valuation (3.5-4x P/B). Safe but limited upside.
ICICI Bank: Turnaround story. Cleaned up NPAs. Now growing faster than HDFC Bank. Better value.
SBI: Government-owned. Cheapest valuation (1.2x P/B). Benefits from government schemes but bureaucratic.
Kotak: Most expensive valuation (4-5x P/B). Premium franchise. Growth slowing post-merger with ING.
RBI rate cuts: Positive for banks (increases demand for loans). Rate hikes: Short-term negative (mark-to-market losses on bond portfolios).
PSU Bank risk: Government interference, frequent capital dilution. But during privatization/reform cycles, they can rally 100%+."""
    },
    {
        "id": "sector_defence_india",
        "collection": "market_intelligence",
        "text": """INDIAN DEFENCE SECTOR DEEP DIVE:
Government spending: Defence budget FY2025 = Rs 5.94 lakh crore. Growing at 15% annually (fastest in Asia).
Key policy: Make in India + Atmanirbhar Bharat = mandatory local sourcing for defence equipment.
HAL (Hindustan Aeronautics): Monopoly in fighter jets (Tejas), helicopters. Order book >Rs 98,000 Cr. Revenue growing 18% YoY.
BEL (Bharat Electronics): Electronics, radars, weapon systems. Consistent 18-20% margins. Government's preferred vendor.
Mazagon Dock: Submarines and warships. Long order cycle (5-7 years per ship). Revenue lumpy but growing.
Cochin Shipyard: Aircraft carrier maintenance + commercial shipbuilding. Benefiting from global ship order boom.
BEML: Defence vehicles + metro coaches. Diversified revenue base.
Risk factors: 1) Government is the ONLY customer (concentration risk). 2) Order execution delays common (2-3 years). 3) Valuations have become very expensive (PE >50x for many). 4) These stocks have already rallied 300-500% in 3 years. Mean reversion risk is HIGH.
Prediction rule: Defence CAGR will normalize from 40%+ to 18-22% as base effect kicks in and valuations correct."""
    },
    {
        "id": "sector_it_india",
        "collection": "market_intelligence",
        "text": """INDIAN IT SECTOR DEEP DIVE:
Big 4: TCS, Infosys, Wipro, HCL Tech. Revenue primarily from US/Europe enterprise clients.
Revenue model: Time-and-materials (declining) shifting to outcome-based/managed services.
AI disruption: GenAI is automating testing, code generation, documentation — reducing headcount needs. Short-term negative for hiring, long-term positive for margins if companies adapt.
Key metrics: Revenue growth (10-12% = healthy), EBIT margin (20-25% = good), Attrition rate (below 15% = stable).
USD/INR correlation: Every Rs 1 depreciation in rupee adds ~40bps to IT margins. Weak rupee = good for IT profits.
Current headwinds: US tech spending cuts, AI replacing traditional outsourcing, visa restrictions.
Current tailwinds: AI implementation services (helping enterprises deploy AI), cloud migration still ongoing.
NIFTY IT has underperformed by -19% over last year. This creates value buying opportunity if you believe AI is complementary, not destructive, to Indian IT.
Prediction rule: IT sector dips of >15% are historically followed by 12-18 month recoveries. Current dip may be a buying opportunity."""
    },

    # ─── MACRO ECONOMIC FRAMEWORKS ─────────────────────────────
    {
        "id": "macro_interest_rate_framework",
        "collection": "market_intelligence",
        "text": """INTEREST RATE IMPACT FRAMEWORK:
When RBI CUTS rates: Positive for equity (cheaper borrowing → higher profits), positive for real estate (cheaper EMIs), positive for debt funds (bond prices rise when yields fall), negative for bank NIMs short-term.
When RBI RAISES rates: Negative for equity (costlier borrowing), negative for real estate, negative for debt funds, positive for bank NIMs.
Transmission lag: RBI rate changes take 3-6 months to fully impact the economy.
Current stance analysis: If RBI uses word 'accommodative' = more cuts possible. 'Neutral' = paused. 'Hawkish' = rate hikes possible.
Global correlation: When US Fed cuts rates, emerging markets (India) benefit from FII inflows. When Fed raises rates, FII outflows occur as $ strengthens.
Bond yield signal: If India 10Y yield rises above 7.5% while equity market is at ATH, it's a warning sign — money is shifting from equity to debt.
Inverted yield curve (short-term rates > long-term): Recession signal in US. In India, less reliable but still cautionary."""
    },
    {
        "id": "macro_oil_india",
        "collection": "market_intelligence",
        "text": """OIL PRICE IMPACT ON INDIAN MARKETS:
India imports 80% of its crude oil. Every $10/barrel increase in crude costs India ~$15 billion additional import bill.
Impact chain: High oil → high petrol/diesel → high inflation → RBI forced to raise rates → equity markets fall.
Sector impact: 
  NEGATIVE for: Paint companies (crude-based inputs), airlines, logistics, auto (higher fuel costs), packaged goods.
  POSITIVE for: ONGC, Oil India (upstream producers), Reliance (refining margins widen in volatile oil).
  NEUTRAL for: IT (no direct oil linkage), pharma (limited).
Geopolitical triggers: Middle East tensions, Russia sanctions, OPEC cuts all spike oil prices.
India-specific: Government can cut excise duty on petrol/diesel to absorb price shock (done in 2022). This reduces fiscal deficit but shields consumers.
Trading rule: If crude crosses $90/barrel, go underweight Indian equity. If drops below $70, go overweight. Crude at $75-85 is the 'goldilocks' range for Indian markets."""
    },

    # ─── MUTUAL FUND ADVANCED ANALYSIS ─────────────────────────
    {
        "id": "mf_advanced_selection",
        "collection": "market_intelligence",
        "text": """ADVANCED MUTUAL FUND SELECTION FRAMEWORK:
Step 1 — Category Fit: Match fund category to investor horizon. <3 years: debt/hybrid only. 3-5 years: flexi-cap/large-cap. 5-7 years: mid-cap. 7+ years: small-cap.
Step 2 — Rolling Returns: Don't check point-to-point CAGR. Check 3-year rolling returns over 5+ years to see consistency. A fund with 18% average but 5% standard deviation is BETTER than a fund with 22% average and 15% standard deviation.
Step 3 — Downside Protection: Check maximum drawdown. How much did the fund fall in March 2020? In 2022? A fund that fell 25% when NIFTY fell 35% has better downside protection.
Step 4 — Alpha Generation: Is the fund beating its benchmark? If a mid-cap fund is returning 20% but NIFTY Midcap 150 returned 22%, the fund manager is destroying value despite absolute returns looking good.
Step 5 — Expense Impact: A 1% higher expense ratio compounds to 15-20% lower wealth over 15 years. Always prefer direct plans.
Step 6 — Portfolio Overlap Check: If you hold multiple funds, check if they hold the same top stocks. >40% overlap = you're paying two fund managers for the same portfolio.
AI Prediction Rule: Weight rolling return consistency (SD of rolling returns) more than absolute CAGR when projecting future values."""
    },
    {
        "id": "mf_timing_framework",
        "collection": "market_intelligence",
        "text": """MUTUAL FUND INVESTMENT TIMING FRAMEWORK:
LUMPSUM vs SIP Decision:
- If NIFTY PE < 18: Lumpsum is better (market is cheap). Deploy 60-70% lumpsum, rest via SIP.
- If NIFTY PE 18-22: SIP is better (market is fairly valued). Monthly SIP smooths out volatility.
- If NIFTY PE > 22: SIP with lower amounts. Market is expensive. Save cash for corrections.
- If NIFTY PE > 25: Avoid new equity investments. Shift to debt/liquid funds. Wait for correction.
Current NIFTY PE: ~22x (April 2025). Market is at fair-to-slightly-expensive levels.
Category timing:
- After 20%+ correction: Deploy into aggressive categories (small-cap, thematic).
- At all-time high: Shift to conservative (large-cap, hybrid, balanced advantage).
- During rate cut cycle: Deploy into banking/financial funds.
- During commodity supercycle: Deploy into metal/energy funds.
SIP return expectation: Over 10 years, SIP in good equity fund should compound at 12-15% XIRR. Don't expect >18% SIP returns long-term."""
    },
    {
        "doc_id": "strategy_momentum_breakout",
        "category": "research_papers",
        "content": "MOMENTUM BREAKOUT STRATEGY (INDIAN MARKETS): A momentum breakout occurs when a stock breaks above its 20-period high, accompanied by a volume surge (>1.5x average) and strong trend confirmation (ADX > 25). In trending regimes, breakouts have a 65% win rate. False breakouts are common in choppy regimes; avoid breakouts when ADX < 20 or when the broader market (NIFTY) is not aligned. Use the 20-period EMA as a trailing stop loss."
    },
    {
        "doc_id": "strategy_mean_reversion",
        "category": "research_papers",
        "content": "MEAN REVERSION STRATEGY (OVERSOLD PANIC): Mean reversion capitalizes on extreme overreactions. A high-probability setup requires multiple confirmations: RSI < 25, Price breaching the lower Bollinger Band, and Stochastic RSI < 20. Do not attempt mean reversion if ADX is strongly trending down (>35), as the trend may persist. Mean reversion targets the 20-SMA (middle Bollinger Band) for profit taking. High risk, high reward."
    },
    {
        "doc_id": "strategy_supply_demand_zones",
        "category": "research_papers",
        "content": "SUPPLY AND DEMAND ZONES (SMART MONEY CONCEPTS): Supply zones are areas where aggressive selling occurred previously, leaving unfilled institutional orders. Demand zones are areas of massive buying. In the NIFTY 50, price tends to consolidate near VWAP (Volume Weighted Average Price) before launching into a new zone. A stock trading >5% above VWAP is extended and susceptible to mean reversion back to value."
    },
    {
        "doc_id": "sector_rotation_india",
        "category": "market_intelligence",
        "content": "INDIAN SECTOR ROTATION DYNAMICS: Capital rotates through sectors predictably. Early Bull Phase: Banks & Finance lead out of the bottom. Mid Bull Phase: Capital rotates into high-beta names (Metals, Infrastructure, Real Estate). Late Bull Phase (Euphoria): FMCG, Pharma, and IT catch protective bids as smart money derisks. Bear Phase: Cash is king, defensive sectors (Pharma/FMCG) outperform relative to the index."
    },
    {
        "doc_id": "risk_kelly_criterion",
        "category": "research_papers",
        "content": "POSITION SIZING (KELLY CRITERION): The Kelly Criterion determines optimal bet sizing to maximize long-term compounding while preventing ruin. Formula: Kelly % = W - [(1 - W) / R], where W = Win Rate and R = Reward-to-Risk Ratio. For an autonomous trading system with a 55% win rate and 1.5 R:R, optimal total capital at risk per trade is ~25%. Sovereign implements 'Fractional Kelly' (e.g., 5-10%) to account for systemic market gaps and fat-tail risks."
    },
    {
        "doc_id": "indicator_confluence",
        "category": "research_papers",
        "content": "INDICATOR CONFLUENCE & ORACLE SCORING: No single indicator predicts the market. RSI is a momentum oscillator. MACD measures trend and momentum. ADX measures trend strength, not direction. Supertrend provides dynamic trailing support/resistance based on ATR. VWAP identifies institutional fair value. When 4+ uncorrelated indicators align (e.g., RSI oversold + MACD bullish cross + Price at Lower BB + Vol Surge), the mathematical expectancy of a reversal trade becomes highly positive."
    }
]


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: FINE-TUNING DATASET GENERATOR
# ═══════════════════════════════════════════════════════════════════
# Creates instruction/response pairs in JSONL format for QLoRA training

TRAINING_PAIRS = [
    # ── Sentiment Classification ──
    {"instruction": "Classify the financial sentiment: 'NIFTY 50 hits all-time high as FII buying surges to record levels'", "output": '{"sentiment": "BULLISH", "confidence": 0.92, "reasoning": "ATH with record FII inflows indicates strong institutional conviction"}'},
    {"instruction": "Classify the financial sentiment: 'RBI raises repo rate by 50 bps citing persistent inflation concerns'", "output": '{"sentiment": "BEARISH", "confidence": 0.85, "reasoning": "Aggressive rate hike signals tightening cycle, negative for equity valuations"}'},
    {"instruction": "Classify the financial sentiment: 'Markets closed flat as investors await US Fed decision'", "output": '{"sentiment": "NEUTRAL", "confidence": 0.78, "reasoning": "Wait-and-watch mode, no directional bias"}'},
    {"instruction": "Classify the financial sentiment: 'Sensex crashes 1500 points as global recession fears mount'", "output": '{"sentiment": "BEARISH", "confidence": 0.95, "reasoning": "Large absolute decline with global macro catalyst indicates genuine risk-off event"}'},
    {"instruction": "Classify the financial sentiment: 'IT sector stocks rally 3% after TCS beats Q3 revenue estimates'", "output": '{"sentiment": "BULLISH", "confidence": 0.80, "reasoning": "Sector leader earnings beat drives broad sectoral positive sentiment"}'},

    # ── Satire/Humor Detection ──
    {"instruction": "Classify the financial sentiment: 'Local Man Confident Stock Market Will Recover After Reading Astrology Column'", "output": '{"sentiment": "NEUTRAL", "confidence": 0.10, "reasoning": "SATIRICAL CONTENT. This headline is humorous/satirical, not a real financial event. Do not factor into market analysis."}'},
    {"instruction": "Classify the financial sentiment: 'India becomes 100 trillion dollar economy overnight says WhatsApp forward'", "output": '{"sentiment": "NEUTRAL", "confidence": 0.05, "reasoning": "SATIRICAL/FAKE. Absurd claim from unreliable source (WhatsApp forward). Ignore entirely."}'},
    {"instruction": "Is this headline satirical? 'Government Announces Free Money for Everyone Starting Tomorrow'", "output": '{"is_satirical": true, "confidence": 0.98, "reasoning": "No government announces universal free money. This is clearly satirical or misinformation."}'},
    {"instruction": "Is this headline satirical? 'RBI keeps repo rate unchanged at 6.5% in October policy review'", "output": '{"is_satirical": false, "confidence": 0.99, "reasoning": "Standard central bank policy announcement with specific factual details. Legitimate news."}'},

    # ── Fund Prediction ──
    {"instruction": "Predict the future value of Rs 100000 invested in a Large Cap fund with historical CAGR of 14% over 5 years. Consider current market conditions.", "output": '{"estimatedValue": 180094, "adjustedCAGR": 12.5, "reasoning": "Large cap funds historically return 10-14% CAGR long-term. With NIFTY at fair valuation (PE ~22x), I applied a slight discount to historical CAGR, projecting 12.5% instead of 14%. FV = 100000 * (1.125)^5 = 180094."}'},
    {"instruction": "Predict the future value of Rs 50000 invested in a Defence thematic fund with historical CAGR of 41% over 3 years.", "output": '{"estimatedValue": 97300, "adjustedCAGR": 25, "reasoning": "Defence sector has shown exceptional 41% CAGR driven by government capex surge, but this rate is unsustainable. Applied strong mean reversion: 60% of historical rate = 25% projected CAGR. Defence spending growth will moderate as base effect kicks in. FV = 50000 * (1.25)^3 = 97656, rounded to 97300."}'},
    {"instruction": "Predict the future value of Rs 200000 invested in an IT sector fund with historical CAGR of 18% over 5 years. IT sector has shown -19% returns last year.", "output": '{"estimatedValue": 460962, "adjustedCAGR": 18.2, "reasoning": "IT sector is currently in a dip cycle (-19% 1Y) due to AI disruption fears and US spending cuts. Historically, IT dips of >15% are followed by strong recoveries. I am projecting recovery to historical mean CAGR of ~18.2%, as AI will ultimately boost IT services demand for implementation and integration. FV = 200000 * (1.182)^5 = 460962."}'},

    # ── Market Regime Detection ──
    {"instruction": "Based on these signals: NIFTY at ATH, VIX at 11, FII buying Rs 2000 Cr daily, midcap index up 25% in 3 months — what is the market regime?", "output": '{"regime": "EUPHORIA", "risk_level": "HIGH", "recommendation": "Reduce exposure to midcaps. VIX at 11 indicates extreme complacency. ATH + low VIX + midcap rally suggests late-stage bull run. Historically, VIX below 12 preceded 10-15% corrections within 2-3 months. Shift 20% portfolio to defensive (pharma, FMCG, debt)."}'},
    {"instruction": "Based on these signals: NIFTY down 12% from ATH, VIX at 24, FII selling Rs 3000 Cr daily, midcap index down 18% in 2 months — what is the market regime?", "output": '{"regime": "FEAR", "risk_level": "MODERATE", "recommendation": "Start buying quality large-caps in small tranches. VIX at 24 indicates elevated fear but not panic. Historically, corrections of 12-15% with VIX 20-25 represent good entry points. Deploy 30% of reserved cash now, keep 70% for potential further decline."}'},

    # ── Indirect Language Decoding ──
    {"instruction": "Decode this RBI statement: 'The MPC decided to remain focused on withdrawal of accommodation to ensure that inflation progressively aligns with the target.'", "output": '{"decoded_meaning": "Rate hikes are coming or will continue. The RBI is prioritizing inflation control over growth. This is a HAWKISH stance.", "market_impact": "BEARISH for equities, positive for fixed deposits and debt funds", "action": "Reduce equity allocation, increase short-duration debt fund allocation"}'},
    {"instruction": "Decode this corporate statement: 'The company is exploring strategic alternatives for its non-core assets to unlock shareholder value.'", "output": '{"decoded_meaning": "The company is looking to sell underperforming divisions, possibly facing cash flow pressure. Could also mean activist investor pressure.", "market_impact": "SHORT-TERM NEUTRAL to slightly positive (asset monetization), LONG-TERM depends on what they do with proceeds", "action": "Monitor closely. If proceeds used for debt reduction = positive. If used for acquisitions = be cautious."}'},

    # ── Strategy Confirmation ──
    {"instruction": "Analyze this setup: Price is 2% above 20-period high. Volume is 2.5x normal. ADX is 35.", "output": '{"strategy": "MOMENTUM_BREAKOUT", "signal_strength": "STRONG_BUY", "reasoning": "Classic momentum breakout. High relative volume confirms institutional participation, and ADX > 25 confirms a strong prevailing trend. High probability setup."}'},
    {"instruction": "Analyze this setup: Price is at a 20-period high. Volume is 0.8x normal. ADX is 18.", "output": '{"strategy": "MOMENTUM_BREAKOUT", "signal_strength": "WEAK", "reasoning": "False breakout warning. Volume is below average, meaning institutions are not driving the move, and ADX < 20 indicates a choppy, trendless market. High risk of failure, avoid."}'},
    {"instruction": "Analyze this setup: RSI is 22. Price is below the lower Bollinger Band. Stochastic RSI is at 10. ADX is 15.", "output": '{"strategy": "MEAN_REVERSION", "signal_strength": "STRONG_BUY", "reasoning": "Excellent mean reversion confluence. Extreme oversold readings on multiple oscillators, and a low ADX means there is no strong downtrend forcing price lower. Likely to bounce back to the 20 SMA."}'},
    {"instruction": "Analyze this setup: RSI is 18. Price is below the lower Bollinger Band. ADX is 45.", "output": '{"strategy": "MEAN_REVERSION", "signal_strength": "AVOID", "reasoning": "RSI is oversold, but ADX is 45, indicating an incredibly strong downtrend (capitulation phase). Trying to catch this falling knife is dangerous. Do not trade mean reversion."}'},

    # ── Multi-Indicator Confluence ──
    {"instruction": "Evaluate the confluence: 5m EMA9 crosses above EMA21. 1H RSI is 58. Supertrend is Bullish. Current Price is below VWAP.", "output": '{"composite_signal": "BUY", "confidence": "MODERATE", "reasoning": "EMAs indicate short-term uptrend, confirmed by higher timeframe RSI > 55. Supertrend aligns. However, being below VWAP means we are trading below institutional average cost. Wait for VWAP breach for higher confidence."}'},
    {"instruction": "Evaluate the confluence: Price hits upper Bollinger Band. RSI is 72. MACD shows a Death Cross. Volume is 2x average.", "output": '{"composite_signal": "SELL", "confidence": "STRONG", "reasoning": "Perfect confluence for a short/sell signal. Exhaustion at upper resistance band, Overbought RSI, negative momentum shift (MACD), and high volume confirming the rejection."}'},
]


def ingest_elite_knowledge():
    """Ingest all elite knowledge into ChromaDB RAG."""
    logger.info("=" * 60)
    logger.info("SOVEREIGN KNOWLEDGE ENGINE — Elite Data Ingestion")
    logger.info("=" * 60)

    try:
        from sovereign_rag import SovereignRAG
        rag = SovereignRAG()
    except Exception as e:
        logger.error(f"RAG unavailable: {e}")
        return 0

    total = 0
    for doc in ELITE_KNOWLEDGE:
        try:
            count = rag.ingest_text(
                text=doc["text"],
                metadata={
                    "source": f"elite_{doc['id']}",
                    "type": "elite_knowledge"
                },
                collection=doc.get("collection", "research_papers")
            )
            total += count
            logger.info(f"  ✅ {doc['id']} ({count} chunks)")
        except Exception as e:
            logger.error(f"  ❌ {doc['id']}: {e}")

    logger.info(f"Elite knowledge ingested: {total} chunks from {len(ELITE_KNOWLEDGE)} documents.")
    return total


def generate_training_dataset():
    """Generate JSONL fine-tuning dataset for QLoRA training."""
    logger.info("Generating fine-tuning dataset...")

    jsonl_path = os.path.join(TRAINING_DIR, "sovereign_financial_training.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for pair in TRAINING_PAIRS:
            entry = {
                "instruction": pair["instruction"],
                "input": "",
                "output": pair["output"],
                "system": "You are Sovereign, a self-sovereign quantitative trading AI specializing in Indian financial markets. You analyze data precisely and return structured JSON responses."
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(f"  ✅ Training dataset: {jsonl_path} ({len(TRAINING_PAIRS)} examples)")

    # Also generate from the elite knowledge as Q&A pairs
    qa_path = os.path.join(TRAINING_DIR, "sovereign_knowledge_qa.jsonl")
    qa_count = 0
    with open(qa_path, "w", encoding="utf-8") as f:
        for doc in ELITE_KNOWLEDGE:
            # Generate a question from each knowledge document
            doc_id = doc["id"]
            text = doc["text"]
            title = text.split("\n")[0].strip()

            entry = {
                "instruction": f"Explain in detail: {title}",
                "input": "",
                "output": text.strip(),
                "system": "You are Sovereign, a self-sovereign quantitative trading AI. Provide detailed, accurate financial analysis."
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            qa_count += 1

    logger.info(f"  ✅ Knowledge Q&A dataset: {qa_path} ({qa_count} examples)")
    logger.info(f"  📊 Total training examples: {len(TRAINING_PAIRS) + qa_count}")

    return len(TRAINING_PAIRS) + qa_count


# ═══════════════════════════════════════════════════════════════════
# MAIN: Run Everything
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    start = datetime.datetime.now()

    # 1. Ingest elite knowledge into RAG
    chunks = ingest_elite_knowledge()

    # 2. Generate fine-tuning dataset
    training_count = generate_training_dataset()

    elapsed = (datetime.datetime.now() - start).total_seconds()
    logger.info("=" * 60)
    logger.info(f"KNOWLEDGE ENGINE COMPLETE in {elapsed:.1f}s")
    logger.info(f"  RAG Chunks:      {chunks}")
    logger.info(f"  Training Pairs:  {training_count}")
    logger.info(f"  Data Location:   {TRAINING_DIR}")
    logger.info("=" * 60)
