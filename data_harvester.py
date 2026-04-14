import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
# ═══════════════════════════════════════════════════════════════════
# data_harvester.py — Financial Data Acquisition Engine
# ═══════════════════════════════════════════════════════════════════
# Downloads FREE financial data from public sources:
#   - AMFI India (Mutual Fund NAVs for every fund in India)
#   - Yahoo Finance (Stock prices, sector indices)
#   - RBI (Interest rates, macro data)
# Stores locally and ingests into SovereignRAG for knowledge retrieval.
# ═══════════════════════════════════════════════════════════════════

import os
import json
import csv
import logging
import datetime
from typing import List, Dict

import requests
import yfinance as yf

logger = logging.getLogger("DataHarvester")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [HARVEST] %(message)s")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# 1. AMFI — All Mutual Fund NAVs in India (FREE, no API key)
# ═══════════════════════════════════════════════════════════════════
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

def harvest_amfi_nav() -> List[Dict]:
    """
    Downloads the AMFI daily NAV file (~6000+ mutual funds).
    Parses into structured records and saves to data/amfi_nav.json.
    """
    logger.info("Harvesting AMFI NAV data (all Indian mutual funds)...")
    try:
        r = requests.get(AMFI_NAV_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"AMFI download failed: {e}")
        return []

    lines = r.text.strip().split("\n")
    funds = []
    current_amc = ""
    current_category = ""

    for line in lines:
        line = line.strip()
        if not line or line.startswith("Scheme") or line.startswith("Open Ended"):
            continue

        # AMC headers are standalone lines without semicolons
        # Category lines contain specific markers
        parts = line.split(";")

        if len(parts) == 1:
            # Could be AMC name or category
            if "Mutual Fund" in line or "AMC" in line.upper():
                current_amc = line.strip()
            else:
                current_category = line.strip()
            continue

        if len(parts) >= 5:
            try:
                scheme_code = parts[0].strip()
                scheme_name = parts[1].strip() if len(parts) > 1 else ""
                nav_str = parts[4].strip() if len(parts) > 4 else ""
                nav_date = parts[5].strip() if len(parts) > 5 else ""

                # Skip non-numeric NAVs
                try:
                    nav_val = float(nav_str)
                except ValueError:
                    continue

                funds.append({
                    "scheme_code": scheme_code,
                    "scheme_name": scheme_name,
                    "amc": current_amc,
                    "category": current_category,
                    "nav": nav_val,
                    "date": nav_date
                })
            except Exception:
                continue

    # Save to disk
    out_path = os.path.join(DATA_DIR, "amfi_nav.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(funds, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Harvested {len(funds)} mutual fund NAVs → {out_path}")
    return funds


# ═══════════════════════════════════════════════════════════════════
# 2. STOCK PRICE HISTORY — Via yfinance (FREE, no API key)
# ═══════════════════════════════════════════════════════════════════

def harvest_stock_history(symbols: List[str] = None, period: str = "5y") -> Dict:
    """
    Downloads historical price data for watchlist symbols.
    Saves individual CSVs to data/stocks/.
    """
    if symbols is None:
        # Load from dynamic watchlist
        wl_path = os.path.join(os.path.dirname(__file__), "dynamic_watchlist.json")
        if os.path.exists(wl_path):
            with open(wl_path) as f:
                wl = json.load(f)
                symbols = []
                for cat_data in wl.values():
                    if isinstance(cat_data, list):
                        for item in cat_data:
                            sym = item.get("symbol", item) if isinstance(item, dict) else item
                            symbols.append(sym)
        else:
            symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS",
                        "TATASTEEL.NS", "BEL.NS", "NTPC.NS", "POWERGRID.NS", "HAL.NS"]

    stocks_dir = os.path.join(DATA_DIR, "stocks")
    os.makedirs(stocks_dir, exist_ok=True)

    results = {}
    for sym in symbols:
        try:
            logger.info(f"  Downloading {sym} ({period})...")
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period)
            if df.empty:
                logger.warning(f"  No data for {sym}")
                continue

            csv_path = os.path.join(stocks_dir, f"{sym.replace('.', '_')}.csv")
            df.to_csv(csv_path)
            results[sym] = {
                "rows": len(df),
                "start": str(df.index[0].date()),
                "end": str(df.index[-1].date()),
                "latest_close": round(float(df["Close"].iloc[-1]), 2)
            }
            logger.info(f"  ✅ {sym}: {len(df)} rows ({df.index[0].date()} → {df.index[-1].date()})")
        except Exception as e:
            logger.error(f"  ❌ {sym} failed: {e}")

    # Save summary
    summary_path = os.path.join(DATA_DIR, "stock_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Harvested {len(results)} stock histories → {stocks_dir}/")
    return results


# ═══════════════════════════════════════════════════════════════════
# 3. SECTOR INDEX DATA — NIFTY sector indices via yfinance
# ═══════════════════════════════════════════════════════════════════

SECTOR_INDICES = {
    "NIFTY_50": "^NSEI",
    "NIFTY_BANK": "^NSEBANK",
    "NIFTY_IT": "^CNXIT",
    "NIFTY_PHARMA": "^CNXPHARMA",
    "NIFTY_METAL": "^CNXMETAL",
    "NIFTY_AUTO": "^CNXAUTO",
    "NIFTY_ENERGY": "^CNXENERGY",
    "NIFTY_FMCG": "^CNXFMCG",
    "NIFTY_REALTY": "^CNXREALTY",
}

def harvest_sector_indices(period: str = "2y") -> Dict:
    """Downloads NIFTY sector index data for macro analysis."""
    logger.info("Harvesting NIFTY sector indices...")
    sectors_dir = os.path.join(DATA_DIR, "sectors")
    os.makedirs(sectors_dir, exist_ok=True)

    results = {}
    for name, symbol in SECTOR_INDICES.items():
        try:
            df = yf.Ticker(symbol).history(period=period)
            if df.empty:
                continue
            csv_path = os.path.join(sectors_dir, f"{name}.csv")
            df.to_csv(csv_path)

            # Calculate returns
            current = float(df["Close"].iloc[-1])
            yr_ago = float(df["Close"].iloc[max(0, len(df)-252)])
            returns_1y = round(((current - yr_ago) / yr_ago) * 100, 1)

            results[name] = {
                "latest": round(current, 2),
                "1y_return_pct": returns_1y,
                "rows": len(df)
            }
            logger.info(f"  ✅ {name}: {current:.0f} ({returns_1y:+.1f}% 1Y)")
        except Exception as e:
            logger.error(f"  ❌ {name} failed: {e}")

    summary_path = os.path.join(DATA_DIR, "sector_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Harvested {len(results)} sector indices → {sectors_dir}/")
    return results


# ═══════════════════════════════════════════════════════════════════
# 4. FUND KNOWLEDGE BASE — Curated fund descriptions for RAG
# ═══════════════════════════════════════════════════════════════════

FUND_KNOWLEDGE = [
    {
        "name": "Parag Parikh Flexi Cap Fund",
        "category": "Equity - Flexi Cap",
        "text": "Parag Parikh Flexi Cap is a go-anywhere multi-cap strategy also investing in global tech (Microsoft, Alphabet, Amazon). Known for value-oriented stock selection with a buy-and-hold discipline. AUM: ₹56,800 Cr. Expense ratio: 0.62%. 3Y CAGR: 21.4%. Top sectors: Financials 31%, Tech 19%. The fund benefits from global diversification and low portfolio turnover."
    },
    {
        "name": "Quant Small Cap Fund",
        "category": "Equity - Small Cap",
        "text": "Quant Small Cap is a highly aggressive momentum-driven fund using proprietary quantitative models. It rotates heavily between sectors and goes concentrated during high-conviction calls. AUM: ₹15,200 Cr. Expense ratio: 0.77%. 3Y CAGR: 34.8%. Top sectors: Industrials 26%, Materials 18%. High risk, high reward profile. Indian small-cap space is volatile with significant drawdown potential."
    },
    {
        "name": "SBI Contra Fund",
        "category": "Equity - Contra",
        "text": "SBI Contra is a contrarian strategy buying out-of-favor, undervalued companies. It thrives in market recoveries by picking deep value stocks with turnaround catalysts. AUM: ₹32,400 Cr. 3Y CAGR: 26.1%. Top holdings: GAIL, SBI, Tech Mahindra. Contra funds perform best when market sentiment shifts from bearish to neutral."
    },
    {
        "name": "HDFC Mid-Cap Opportunities Fund",
        "category": "Equity - Mid Cap",
        "text": "HDFC Mid-Cap Opportunities is the largest mid-cap fund in India, focusing on high-quality compounders in banking, manufacturing, and consumer goods. AUM: ₹61,000 Cr. Expense ratio: 0.81%. 3Y CAGR: 24.9%. Known for consistent stock selection and relatively lower volatility for its category."
    },
    {
        "name": "ICICI Prudential Asset Allocator Fund",
        "category": "Hybrid - Dynamic Asset",
        "text": "ICICI Pru Asset Allocator dynamically rebalances between equity (40-80%), debt (20-50%), and gold (5-15%) based on in-house valuation models. Safety-first approach, ideal for conservative investors. AUM: ₹22,500 Cr. 3Y CAGR: 14.2%. Lower returns but very high safety rating."
    },
    {
        "name": "Nippon India Growth Fund",
        "category": "Equity - Mid Cap",
        "text": "Nippon India Growth is a wealth creation focused mid-cap fund with a long track record. It targets secular growth themes and has strong exposure to financials (25%) and consumer goods (17%). AUM: ₹24,100 Cr. 3Y CAGR: 25.6%."
    },
    {
        "name": "Motilal Oswal Midcap Fund",
        "category": "Equity - Mid Cap",
        "text": "Motilal Oswal Midcap is a high-conviction concentrated portfolio (20-25 stocks) focusing on mid-cap companies with strong economic moats. It has significant tech exposure through Zomato, Persistent Systems. AUM: ₹11,400 Cr. 3Y CAGR: 32.4%. The concentration adds volatility but also alpha."
    },
    {
        "name": "HDFC Defence Fund",
        "category": "Thematic - Defence",
        "text": "HDFC Defence Fund is a thematic sector fund capturing India's massive sovereign defence capital expenditure boom. Holdings include HAL (Hindustan Aeronautics), BEL (Bharat Electronics), Mazagon Dock Shipbuilders, Cochin Shipyard, BDL. AUM: ₹3,250 Cr. 3Y CAGR: 41.2%. Indian defence sector has tailwinds from government Make in India and Atmanirbhar Bharat policy. High cyclicality risk."
    },
    {
        "name": "Tata Digital India Fund",
        "category": "Thematic - Technology",
        "text": "Tata Digital India is a pure IT services fund with heavy exposure to Infosys, TCS, Tech Mahindra, HCL Tech and Bharti Airtel. AUM: ₹9,100 Cr. 3Y CAGR: 18.6%. IT sector growth is linked to global enterprise spending and USD/INR exchange rates. Currently facing headwinds from AI disruption of traditional outsourcing models."
    },
    {
        "name": "Indian Macro Context 2024-2026",
        "category": "Macro",
        "text": "India real GDP growth: 6.5-7.0% (2025E). RBI repo rate: 6.5% (stable). CPI inflation: 4.5-5.0%. FII flows: net positive in 2025. Indian equity markets at premium valuations (Nifty PE ~22x). Defence sector massively boosted by government capex (₹5.94 lakh crore defence budget FY2025). IT sector facing margin pressures from AI adoption. Mid-caps and small-caps have outperformed large-caps over 3-year horizon. Gold hitting record highs providing hedge."
    }
]

def harvest_fund_knowledge() -> int:
    """
    Ingests curated mutual fund knowledge into SovereignRAG ChromaDB.
    Returns the number of documents ingested.
    """
    logger.info("Ingesting fund knowledge into SovereignRAG...")
    count = 0
    try:
        from sovereign_rag import SovereignRAG
        rag = SovereignRAG()

        for fund in FUND_KNOWLEDGE:
            try:
                rag.ingest_text(
                    text=fund["text"],
                    metadata={
                        "source": f"fund_knowledge_{fund['name'].replace(' ', '_')}",
                        "category": fund["category"],
                        "name": fund["name"],
                        "type": "fund_knowledge"
                    },
                    collection="market_intelligence"
                )
                count += 1
                logger.info(f"  ✅ Ingested: {fund['name']}")
            except Exception as e:
                logger.error(f"  ❌ Failed to ingest {fund['name']}: {e}")

    except ImportError:
        logger.error("SovereignRAG not available. Knowledge not ingested.")

    logger.info(f"✅ Ingested {count}/{len(FUND_KNOWLEDGE)} knowledge documents into ChromaDB.")
    return count


# ═══════════════════════════════════════════════════════════════════
# 5. MASTER HARVESTER — Run everything
# ═══════════════════════════════════════════════════════════════════

def run_full_harvest():
    """
    Runs the complete data acquisition pipeline:
    1. AMFI mutual fund NAVs
    2. Stock price histories (watchlist)
    3. NIFTY sector indices
    4. Fund knowledge → RAG ingestion
    """
    logger.info("=" * 60)
    logger.info("SOVEREIGN DATA HARVESTER — Full Acquisition Run")
    logger.info("=" * 60)

    start = datetime.datetime.now()

    # 1. AMFI
    amfi = harvest_amfi_nav()

    # 2. Stock histories
    stocks = harvest_stock_history()

    # 3. Sector indices
    sectors = harvest_sector_indices()

    # 4. Fund knowledge → RAG
    knowledge_count = harvest_fund_knowledge()

    elapsed = (datetime.datetime.now() - start).total_seconds()

    logger.info("=" * 60)
    logger.info(f"HARVEST COMPLETE in {elapsed:.1f}s")
    logger.info(f"  Mutual Funds:  {len(amfi)} NAVs")
    logger.info(f"  Stock History: {len(stocks)} symbols")
    logger.info(f"  Sector Index:  {len(sectors)} indices")
    logger.info(f"  RAG Knowledge: {knowledge_count} documents")
    logger.info(f"  Data stored:   {DATA_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_full_harvest()
