"""
self_reflect.py — The Sovereign Daily Self-Reflection Engine
=============================================================
Runs at end of trading day (or on-demand).

What it does:
  1. Reads today's trading_journal.csv and memories/decision_log.json
  2. Feeds the raw data to Gemini for deep analysis
  3. Asks Gemini: "What worked? What failed? What should Sovereign do differently?"
  4. Saves the plain-English insight to memories/reflections/YYYY-MM-DD.txt
  5. Updates bot_brain.json with the 'last_reflection' key for dashboard display

Free. Zero extra dependencies. Powered by the same Gemini API key already configured.
"""

import os
import json
import csv
import datetime
import logging

try:
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = "gemini-2.5-flash"

logger = logging.getLogger("SelfReflect")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REFLECT] %(message)s")

REFLECTIONS_DIR = "memories/reflections"
BRAIN_PATH      = "memories/bot_brain.json"
JOURNAL_PATH    = "trading_journal.csv"
DECISION_LOG    = "memories/decision_log.json"
SHADOW_JOURNAL  = "memories/shadow_journal.json"


def _load_todays_trades() -> list:
    """Reads today's rows from trading_journal.csv."""
    today = datetime.date.today().isoformat()
    trades = []
    try:
        with open(JOURNAL_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = row.get("timestamp", "")
                if today in ts:
                    trades.append(row)
    except FileNotFoundError:
        logger.warning("Journal not found. No trades to reflect on.")
    return trades


def _load_todays_decisions() -> list:
    """Reads today's entries from the decision log."""
    today = datetime.date.today().isoformat()
    decisions = []
    try:
        with open(DECISION_LOG, 'r') as f:
            log = json.load(f)
        decisions = [d for d in log if today in d.get("timestamp", "")]
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Decision log not found or invalid.")
    return decisions


def _load_shadow_trades() -> list:
    """Reads today's shadow trades from aggressive learning mode."""
    today = datetime.date.today().isoformat()
    shadows = []
    try:
        with open(SHADOW_JOURNAL, 'r') as f:
            log = json.load(f)
        shadows = [s for s in log if today in s.get("timestamp", "")]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return shadows


def _get_rag_context(trades: list, decisions: list) -> str:
    """Query RAG for relevant past reflections and research papers."""
    try:
        from sovereign_rag import SovereignRAG
        from config import RAG_ENABLED
        if not RAG_ENABLED:
            return ""

        rag = SovereignRAG()
        if not rag.is_ready:
            return ""

        # Build a query from today's trading symbols and patterns
        symbols = list(set(t.get("symbol", "") for t in trades if t.get("symbol")))
        query = f"trading reflection analysis {' '.join(symbols)}"

        # Get past reflections
        past_reflections = rag.query_for_context(
            query, top_k=2, collection="trading_memory", max_chars=400
        )

        # Get relevant research
        research = rag.query_for_context(
            f"trading strategy performance analysis {' '.join(symbols)}",
            top_k=2, collection="research_papers", max_chars=400
        )

        context = ""
        if past_reflections:
            context += f"PAST REFLECTIONS (similar patterns):\n{past_reflections}\n\n"
        if research:
            context += f"RELEVANT RESEARCH:\n{research}\n\n"
        return context

    except (ImportError, Exception) as e:
        logger.debug(f"RAG context lookup skipped: {e}")
        return ""


def _build_reflection_prompt(trades: list, decisions: list, brain: dict) -> str:
    """Composes the Gemini reflection prompt, augmented with RAG context."""
    today_str    = datetime.date.today().strftime("%A, %B %d, %Y")
    karma        = brain.get("karma_score", 0.0)
    mood         = brain.get("mood", "Unknown")
    streak       = brain.get("streak", 0)
    symbol_stats = json.dumps(brain.get("symbol_stats", {}), indent=2)

    trades_block = json.dumps(trades, indent=2) if trades else "  No trades executed today."
    dec_block    = json.dumps(decisions[-30:], indent=2) if decisions else "  No decisions logged."

    # Shadow trades from aggressive learning mode
    shadow_trades = _load_shadow_trades()
    shadow_block  = ""
    if shadow_trades:
        executed_shadows = [s for s in shadow_trades if s.get('was_executed')]
        skipped_shadows  = [s for s in shadow_trades if not s.get('was_executed')]
        shadow_block = f"""
AGGRESSIVE LEARNING SHADOW LOG ({len(shadow_trades)} total signals):
  Executed: {len(executed_shadows)} trades (1 share each, learning mode)
  Skipped:  {len(skipped_shadows)} signals (below threshold or HOLD)
  Sample executed: {json.dumps(executed_shadows[:10], indent=2)}
  Sample skipped:  {json.dumps(skipped_shadows[:10], indent=2)}

IMPORTANT: Analyze the skipped signals especially. For each skipped signal that had a BUY/SELL
recommendation, determine if NOT executing was a good decision or a missed opportunity.
This is critical for improving the confidence threshold calibration.
"""

    # Get RAG-augmented context
    rag_context = _get_rag_context(trades, decisions)
    rag_section = ""
    if rag_context:
        rag_section = f"\nKNOWLEDGE BASE CONTEXT (from past reflections & research):\n{rag_context}"

    return f"""
You are Sovereign's introspective mind — a trading bot analyzing its own performance.
Today is {today_str}.

CURRENT STATE:
  Overall Karma (Win Rate): {karma:.1f}%
  Current Mood:             {mood}
  Current Streak:           {streak} (positive = win streak, negative = loss streak)

PER-SYMBOL STATISTICS:
{symbol_stats}

TODAY'S TRADES:
{trades_block}

TODAY'S SCAN DECISIONS (last 30):
{dec_block}
{rag_section}
{shadow_block}

YOUR TASK — Produce a structured self-reflection with these exact sections:

1. PERFORMANCE SUMMARY
   Briefly describe today's outcomes (wins, losses, P&L context).

2. WHAT WORKED
   Identify which strategies, symbols, or timing decisions were effective and why.

3. WHAT FAILED
   Be brutally honest. Identify missed signals, bad entries, or poor timing.

4. PATTERN RECOGNITION
   Are there recurring patterns in wins vs losses? (e.g., specific symbols, times of day, DEFCON levels)
   Cross-reference with the knowledge base context above if available.

5. TOMORROW'S DIRECTIVE
   Give 3 specific, actionable adjustments for tomorrow. Be precise (e.g., "Avoid TATASTEEL.NS on Mondays", "Raise min confidence to 0.85 in CHOPPY regime").

Keep the total response under 400 words. Be direct, analytical, not motivational.
"""


def run_reflection() -> str:
    """
    Main function: loads data, calls Gemini, saves reflection.
    Returns the reflection text.
    """
    logger.info("Starting EOD self-reflection...")

    trades    = _load_todays_trades()
    decisions = _load_todays_decisions()

    # Load brain
    brain = {}
    try:
        with open(BRAIN_PATH, 'r') as f:
            brain = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Brain file not found. Reflecting with minimal context.")

    # ── LOCAL BRAIN (Primary) ─────────────────────────────────────
    try:
        from config import AI_MODE
    except ImportError:
        AI_MODE = "LOCAL"

    if AI_MODE in ("LOCAL", "HYBRID"):
        try:
            from sovereign_brain import SovereignBrain
            brain = SovereignBrain()
            if brain.is_available():
                prompt = _build_reflection_prompt(trades, decisions, brain_data)
                reflection_text = brain.think(
                    prompt=prompt,
                    context_query="trading performance reflection self-improvement",
                    temperature=0.4,
                    max_tokens=2048
                )
                # Save to file
                os.makedirs(REFLECTIONS_DIR, exist_ok=True)
                date_str = datetime.date.today().isoformat()
                output_path = os.path.join(REFLECTIONS_DIR, f"{date_str}.txt")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"=== Sovereign Self-Reflection: {date_str} ===\n\n")
                    f.write(reflection_text)
                logger.info(f"Reflection saved to {output_path} (LOCAL)")

                # Update brain with summary
                try:
                    with open(BRAIN_PATH, 'r') as f:
                        brain_data = json.load(f)
                    brain_data["last_reflection"] = reflection_text[:500]
                    brain_data["last_reflection_date"] = date_str
                    with open(BRAIN_PATH, 'w') as f:
                        json.dump(brain_data, f, indent=4)
                    logger.info("Brain updated with latest reflection.")
                except Exception as e:
                    logger.error(f"Could not update brain with reflection: {e}")

                return reflection_text
        except Exception as e:
            logger.warning(f"Local brain reflection failed: {e}")

    # ── CLOUD BACKUP (Gemini) — preserved but not active ────────
    if AI_MODE == "CLOUD":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "GEMINI_API_KEY not set. Reflection skipped."
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = _build_reflection_prompt(trades, decisions, brain_data)
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            reflection_text = response.text.strip()
            os.makedirs(REFLECTIONS_DIR, exist_ok=True)
            date_str = datetime.date.today().isoformat()
            output_path = os.path.join(REFLECTIONS_DIR, f"{date_str}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Sovereign Self-Reflection: {date_str} ===\n\n")
                f.write(reflection_text)
            return reflection_text
        except Exception as e:
            logger.error(f"Gemini reflection failed: {e}")

    return "Reflection engine offline. Neither local nor cloud AI available."


if __name__ == "__main__":
    print("=" * 60)
    print("  SOVEREIGN EOD SELF-REFLECTION ENGINE")
    print("=" * 60)
    result = run_reflection()
    print("\n" + result)
