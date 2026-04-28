"""
global_intelligence.py - The God-Level Global News Intelligence Engine
============================================================================
Runs every 3 minutes via a background asyncio loop inside dashboard_server.py.

Architecture:
  1. Scrapes 20+ global news RSS feeds spanning geopolitics, markets, war, tech.
  2. Batches headlines into Gemini-2.0-Flash with a structured analysis prompt.
  3. Outputs a JSON `IntelligenceReport` with a DEFCON level and a trading directive.
  4. Persists the report to `world_view.json` for the Dashboard UI.
  5. If the directive has an `action` (BUY/SELL), it fires a signal into the auto-trader.

Free. Student-friendly. Powered by free RSS and Gemini API.
"""

import asyncio
import feedparser
import logging
import json
import os
from datetime import datetime

try:
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = "gemini-2.5-flash"  # Fallback if config not found

logger = logging.getLogger("GlobalIntelligence")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INTEL] %(message)s")

# ─────────────────────────────────────────────────────────────────────────────
# 25+ Free Global RSS News Feeds — covering ALL required domains
# ─────────────────────────────────────────────────────────────────────────────
GLOBAL_FEEDS = [
    # Geopolitics & War
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.cnn.com/rss/edition_world.rss",

    # Business & Markets
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.theguardian.com/business/rss",
    "https://finance.yahoo.com/rss/topstories",
    "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    "https://economictimes.indiatimes.com/news/rssfeeds/1977021501.cms",  # ET Economy

    # International Trade & Resources
    "https://www.tradewindsnews.com/rss",     # Global Shipping & Trade
    "https://gcaptain.com/feed/",             # Maritime incidents & Shipping
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.livemint.com/rss/economy",

    # Technology
    "https://feeds.feedburner.com/TechCrunch",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",

    # Indian Politics & Policy
    "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeeds/1715249553.cms",
    "https://www.thehindu.com/feeder/default.rss",

    # International Politics
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://feeds.bbci.co.uk/news/politics/rss.xml",

    # Gold, Oil, Commodities
    "https://www.theguardian.com/environment/rss",
    "https://economictimes.indiatimes.com/commodities/rssfeeds/2146899.cms",

    # Earnings / Stocks
    "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "https://money.rediff.com/money/rss/news/rss.aspx",

    # Central Bank / Macro
    "https://feeds.bbci.co.uk/news/business/economy/rss.xml",
]


def fetch_all_headlines(max_per_feed: int = 5) -> list[dict]:
    """Scrapes all configured RSS feeds and aggregates headlines."""
    all_headlines = []
    logger.info(f"Scanning {len(GLOBAL_FEEDS)} global intel feeds...")

    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for url in GLOBAL_FEEDS:
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}, timeout=5, verify=False)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:max_per_feed]:
                all_headlines.append({
                    "source": getattr(feed.feed, "title", url),
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:300],  # cap length
                    "link": entry.get("link", ""),
                    "published": entry.get("published", datetime.now().isoformat()),
                })
        except Exception as e:
            # We don't need a huge traceback for one bad RSS feed
            logger.warning(f"Feed parse error [{url}]: {type(e).__name__} - {str(e)[:50]}...")

    logger.info(f"Total headlines scraped: {len(all_headlines)}")
    return all_headlines


def build_gemini_prompt(headlines: list[dict], watchlist: list[str]) -> str:
    """Composes a highly structured Gemini prompt for macro-level intelligence."""
    headline_block = "\n".join(
        [f"- [{h['source']}] {h['title']}" for h in headlines[:40]]  # top 40
    )
    return f"""
You are SOVEREIGN's Global Intelligence Cortex — a quantitative macro AI with the acuity of a top hedge fund analyst.
You have been given a live feed of the latest {len(headlines)} global news headlines across geopolitics, markets, war, resources, and economics.

NEWS FEED (LIVE — {datetime.now().strftime('%Y-%m-%d %H:%M')} IST):
{headline_block}

Watchlist Tickers: {watchlist}

Your task:
1. Analyze the collective event landscape with EXTREME prejudice towards these key macro drivers:
   - Global Oil & Energy Markets (supply shocks, refineries, energy plants)
   - International Trade & Tariffs (import/export duties, trade wars, sanctions)
   - Maritime Infrastructure & Logistics (ships, docks, chokepoint blockades)
   - Artificial Intelligence & Tech (AI breakthroughs, major AI company announcements, silicon supply chains)
   - Narrative Warfare & Geopolitics (state-sponsored propaganda, escalation, central bank signals)
2. Assess the resulting macro state for Indian markets based on the above.
3. Generate a trading directive if there is a clear asymmetric opportunity or risk event.

OUTPUT STRICTLY VALID JSON ONLY — no markdown, no explanation:
{{
  "defcon": "SAFE" | "CAUTION" | "DANGER",
  "justification": "One-sentence macro context summary.",
  "daily_insight": "A 3-4 sentence comprehensive insight summarizing the most critical news, their predicted impact on the upcoming trading session, and previous market activities.",
  "sector_hotspots": ["ENERGY", "DEFENCE", "BANKING", ...],
  "watchlist_updates": [
    {{"symbol": "ADANIPORTS.NS", "label": "ADANI PORTS", "full_name": "Adani Ports and Special Economic Zone Limited", "category": "SHIPPING"}}
  ],
  "directive": {{
    "action": "BUY" | "SELL" | "HOLD" | "NONE",
    "symbol": "TICKER.NS or null",
    "confidence": 0.0 to 1.0,
    "rationale": "Why this trade makes sense given current macro context."
  }}
}}
"""


def run_gemini_analysis(headlines: list[dict], watchlist: list[str]) -> dict:
    """
    Analyzes headlines using SovereignBrain (local Ollama) first.
    Gemini code preserved below as backup but bypassed when AI_MODE=LOCAL.
    """
    try:
        from config import AI_MODE
    except ImportError:
        AI_MODE = "LOCAL"

    # ── LOCAL BRAIN (Ollama Phi-3.5) ─────────────────────────────
    if AI_MODE in ("LOCAL", "HYBRID"):
        try:
            from sovereign_brain import SovereignBrain
            brain = SovereignBrain()
            if brain.is_available():
                prompt = build_gemini_prompt(headlines, watchlist)
                logger.info("Submitting intel to LOCAL SovereignBrain (Phi-3.5)...")
                result = brain.think_json(
                    prompt=prompt,
                    temperature=0.2,
                    fallback=_default_report()
                )
                if result.get("defcon"):
                    result["timestamp"] = datetime.now().isoformat()
                    result["headline_count"] = len(headlines)
                    result["ai_source"] = "LOCAL"
                    logger.info(f"Intelligence Report (LOCAL) — DEFCON: {result.get('defcon')} | Directive: {result.get('directive', {}).get('action')}")
                    return result
        except Exception as e:
            logger.warning(f"Local brain analysis failed: {e}")

    # ── CLOUD BACKUP (Gemini) — PRESERVED BUT NOT ACTIVE ────────
    if AI_MODE == "CLOUD":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — Global Intelligence offline.")
            return _default_report()

        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            prompt = build_gemini_prompt(headlines, watchlist)

            logger.info("Submitting intel to Gemini 2.5 Flash...")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=prompt
                    )
                    break
                except Exception as e:
                    if "503" in str(e) or "429" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Transient error {e}. Retrying in 5 seconds...")
                            import time
                            time.sleep(5)
                            continue
                    raise e
                    
            raw = response.text.strip().replace("```json", "").replace("```", "").strip()
            report = json.loads(raw)
            report["timestamp"] = datetime.now().isoformat()
            report["headline_count"] = len(headlines)
            report["ai_source"] = "CLOUD"
            logger.info(f"Intelligence Report (CLOUD) — DEFCON: {report.get('defcon')}")
            return report

        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                logger.warning("Gemini Rate Limit Exceeded (429). Falling back.")
            else:
                logger.error(f"Gemini Intel Analysis failed: {e}")
            return _default_report()

    # ── DEEP DIVE VERIFICATION (works with any AI source) ────────
    # Moved to the heartbeat function to keep this function clean
    return _default_report()


def _default_report() -> dict:
    return {
        "defcon": "SAFE",
        "justification": "Global intelligence offline. Operating on technical signals only.",
        "daily_insight": "Sovereign is booting up. First comprehensive market insight will be available in ~10 minutes.",
        "sector_hotspots": [],
        "directive": {"action": "NONE", "symbol": None, "confidence": 0.0, "rationale": "N/A"},
        "timestamp": datetime.now().isoformat(),
        "headline_count": 0,
    }


def persist_report(report: dict, path: str = "world_view.json"):
    """Writes the IntelligenceReport to world_view.json for the Dashboard UI."""
    try:
        # Enrich with top headlines (already in report from Gemini analysis)
        # Ensure top_headlines key exists for dashboard consumption
        if "top_headlines" not in report:
            report["top_headlines"] = []

        # Inject current regime from cache for cross-module consistency
        try:
            if os.path.exists("memories/regime_cache.json"):
                with open("memories/regime_cache.json", "r") as f:
                    rc = json.load(f)
                report["regime"] = rc.get("regime", "UNKNOWN")
        except Exception:
            report["regime"] = "UNKNOWN"

        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Intelligence report persisted to {path} (regime: {report.get('regime')}, headlines: {len(report.get('top_headlines', []))}).")
    except Exception as e:
        logger.error(f"Failed to save intel report: {e}")


def fire_trading_directive(report: dict):
    """
    If Gemini has emitted a confident trading directive, forward it to
    the auto_trading pipeline for execution.
    """
    directive = report.get("directive", {})
    action = directive.get("action", "NONE")
    symbol = directive.get("symbol")
    confidence = directive.get("confidence", 0.0)

    if action in ("BUY", "SELL") and symbol and confidence >= 0.75:
        logger.info(f"[DIRECTIVE FIRE] Macro-driven {action} on {symbol} (confidence: {confidence:.0%})")
        try:
            # Delegate to the auto_trader via a shared flag file
            # (Decoupled communication to avoid circular imports)
            signal = {
                "symbol": symbol,
                "action": action,
                "source": "GLOBAL_INTEL",
                "confidence": confidence,
                "rationale": directive.get("rationale", ""),
                "timestamp": report.get("timestamp"),
            }
            with open("intel_signal.json", "w") as f:
                json.dump(signal, f, indent=2)
            logger.info(f"[DIRECTIVE] Signal written to intel_signal.json — {action} {symbol}")
        except Exception as e:
            logger.error(f"Directive fire failed: {e}")
    else:
        logger.info(f"[INTEL] No actionable directive this cycle. (action={action}, confidence={confidence:.0%})")


async def intelligence_heartbeat(interval_seconds: int = 180):
    """
    Continuous async loop — fires the full global intelligence pipeline every 3 minutes.
    Integrated into FastAPI startup events in dashboard_server.py.
    """
    try:
        from config import SOVEREIGN_SIX as watchlist
    except ImportError:
        watchlist = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "TATASTEEL.NS"]

    logger.info(f"Global Intelligence Heartbeat armed — firing every {interval_seconds // 60} minutes.")
    while True:
        try:
            headlines = await asyncio.to_thread(fetch_all_headlines)
            try:
                os.makedirs("memories", exist_ok=True)
                with open("memories/latest_news_raw.json", "w") as f:
                    json.dump(headlines, f)
            except Exception as e:
                logger.error(f"Failed to cache news: {e}")
            report = await asyncio.to_thread(run_gemini_analysis, headlines, watchlist)
            persist_report(report)
            fire_trading_directive(report)
        except Exception as e:
            logger.error(f"Heartbeat cycle error: {e}")

        logger.info(f"Heartbeat sleeping for {interval_seconds // 60} minutes...")
        await asyncio.sleep(interval_seconds)
