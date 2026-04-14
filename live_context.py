# ═══════════════════════════════════════════════════════════════════
# live_context.py — Real-Time Awareness Layer for SovereignBrain
# ═══════════════════════════════════════════════════════════════════
# Assembles the CURRENT state of the world into a compact text block
# that is injected into every AI inference call.
# This is what makes a small model "situationally aware."
# ═══════════════════════════════════════════════════════════════════

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger("LiveContext")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename: str) -> Optional[Dict]:
    """Safely load a JSON file, return None if missing/corrupt."""
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_latest_headlines(max_count: int = 15) -> str:
    """Returns the most recent news headlines as a formatted text block."""
    # Try cached raw news first (written by global_intelligence heartbeat)
    news = _load_json("memories/latest_news_raw.json")
    if not news:
        return "No recent news available."

    # Take latest headlines
    headlines = news[:max_count] if isinstance(news, list) else []
    if not headlines:
        return "No recent headlines."

    lines = []
    for h in headlines:
        source = h.get("source", "Unknown")
        title = h.get("title", "")
        if title:
            lines.append(f"  [{source}] {title}")

    return "\n".join(lines)


def get_market_snapshot() -> str:
    """Returns current market state: regime, NIFTY level, sector performance."""
    parts = []

    # Market regime
    regime_data = _load_json("memories/regime_cache.json")
    if regime_data:
        parts.append(f"Market Regime: {regime_data.get('regime', 'UNKNOWN')}")
        parts.append(f"NIFTY Volatility: {regime_data.get('volatility', 'N/A')}")

    # World view (intelligence report)
    world = _load_json("world_view.json")
    if world:
        parts.append(f"DEFCON Level: {world.get('defcon', 'UNKNOWN')}")
        justification = world.get("justification", "")
        if justification:
            parts.append(f"Macro Context: {justification}")
        hotspots = world.get("sector_hotspots", [])
        if hotspots:
            parts.append(f"Hot Sectors: {', '.join(hotspots)}")

    # Sector performance from harvested data
    sector_data = _load_json("data/sector_summary.json")
    if sector_data:
        sector_lines = []
        for name, info in sector_data.items():
            ret = info.get("1y_return_pct", 0)
            sector_lines.append(f"  {name}: {ret:+.1f}% (1Y)")
        if sector_lines:
            parts.append("Sector Returns:\n" + "\n".join(sector_lines))

    return "\n".join(parts) if parts else "Market data not available."


def get_trading_context() -> str:
    """Returns recent trading performance context."""
    brain_data = _load_json("bot_brain.json")
    if not brain_data:
        return "No trading history available."

    parts = []
    stats = brain_data.get("stats", {})
    if stats:
        parts.append(f"Total Trades: {stats.get('total_trades', 0)}")
        parts.append(f"Win Rate: {stats.get('win_rate', 0):.1f}%")
        parts.append(f"Current Streak: {stats.get('current_streak', 0)}")

    regime = brain_data.get("regime", "UNKNOWN")
    parts.append(f"Current Regime: {regime}")

    return "\n".join(parts) if parts else "No trading context."


def assemble_live_context() -> str:
    """
    The master function. Assembles ALL real-time context into a single
    compact text block that gets injected into the AI's system prompt.

    This is called BEFORE every brain.think() call to make the small
    model aware of the current state of the world.

    Returns a ~500-800 word context block.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M IST")

    context = f"""═══ SOVEREIGN LIVE INTELLIGENCE BRIEFING ═══
Timestamp: {now}

── MARKET STATE ──
{get_market_snapshot()}

── LATEST NEWS HEADLINES ──
{get_latest_headlines(15)}

── TRADING PERFORMANCE ──
{get_trading_context()}

── ANALYSIS DIRECTIVES ──
- Cross-reference news with sector performance before making predictions.
- If a headline sounds extreme, satirical, or too sensational, FLAG IT and do not factor it into financial analysis.
- Prioritize actionable financial events (earnings, policy changes, FII flows) over political noise.
- Indian market hours: 9:15 AM - 3:30 PM IST. Outside hours, focus on global cues.
═══════════════════════════════════════════"""

    return context
