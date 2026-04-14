import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
"""
watchlist_curator.py — Sovereign Self-Evolving Watchlist Engine
================================================================
Runs every Sunday via Windows Task Scheduler.

Ruleset (immutable law):
  1. NEVER delete or rename a category.
  2. NEVER remove a stock from any category.
  3. Every category must have a MINIMUM of 4 stocks at all times.
  4. Uses Gemini AI to determine which stocks to ADD when a category
     falls below the minimum, selecting the most relevant to that sector.
  5. Logs every change made to memories/watchlist_curator_log.txt.
"""

import os
import json
import datetime
import logging

# Load API keys from .env (same as every other Sovereign module)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

WATCHLIST_PATH = "dynamic_watchlist.json"
LOG_PATH       = "memories/watchlist_curator_log.txt"
MIN_STOCKS     = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CURATOR] %(message)s")
logger = logging.getLogger("WatchlistCurator")

try:
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = "gemini-2.5-flash"


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_watchlist() -> dict:
    """Load dynamic_watchlist.json. Always returns a dict."""
    if os.path.exists(WATCHLIST_PATH):
        try:
            with open(WATCHLIST_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt watchlist JSON: {e}. Aborting.")
            raise
    return {}


def save_watchlist(data: dict):
    """Save the watchlist atomically — write to temp then rename."""
    tmp = WATCHLIST_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, WATCHLIST_PATH)
    logger.info("Watchlist saved.")


def log_change(msg: str):
    """Appends a curator note to the log file."""
    os.makedirs("memories", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


# ── AI Stock Suggestion ───────────────────────────────────────────────────────

def ask_gemini_for_additions(category: str, existing_symbols: list[str], needed: int) -> list[dict]:
    """
    Suggests {needed} NSE-listed stocks for the given sector category.
    Uses local SovereignBrain first, Gemini as backup.
    """
    existing_str = ", ".join(existing_symbols) if existing_symbols else "none yet"
    prompt = f"""
You are a market analyst managing a curated Indian stock watchlist.

Category: "{category}"
Currently tracked symbols: {existing_str}

Task: Suggest exactly {needed} additional NSE-listed stocks for this category.
Rules:
- Must be listed on NSE (symbol ends in .NS)
- Must NOT be any of: {existing_str}
- Choose stocks that are most relevant to the "{category}" sector
- Use only well-known, liquid, NIFTY 500-class stocks
- Return a JSON array ONLY — no preamble, no markdown, no explanation

Format:
[
  {{"symbol": "SYMBOLNAME.NS", "label": "COMPANY SHORT NAME"}},
  ...
]
"""
    # ── LOCAL BRAIN (Primary) ─────────────────────────────────────
    try:
        from sovereign_brain import SovereignBrain
        brain = SovereignBrain()
        if brain.is_available():
            import json as _json
            raw = brain.think(prompt=prompt, json_mode=True, temperature=0.3)
            suggestions = _json.loads(raw)
            if isinstance(suggestions, list):
                valid = [
                    s for s in suggestions
                    if isinstance(s, dict)
                    and s.get("symbol", "").endswith(".NS")
                    and s["symbol"] not in existing_symbols
                ]
                if valid:
                    logger.info(f"Local brain suggested {len(valid)} stocks for '{category}'")
                    return valid[:needed]
    except Exception as e:
        logger.warning(f"Local brain suggestion failed for '{category}': {e}")

    # ── CLOUD BACKUP (Gemini) — preserved ─────────────────────────
    try:
        from config import AI_MODE
    except ImportError:
        AI_MODE = "LOCAL"
    if AI_MODE == "CLOUD":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set. Cannot auto-add stocks.")
            return []
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            suggestions = json.loads(raw.strip())
            if isinstance(suggestions, list):
                valid = [s for s in suggestions if isinstance(s, dict) and s.get("symbol", "").endswith(".NS") and s["symbol"] not in existing_symbols]
                return valid[:needed]
        except Exception as e:
            logger.error(f"Gemini suggestion failed for '{category}': {e}")

    return []


# ── Core Curation Logic ───────────────────────────────────────────────────────

def curate_watchlist():
    """
    Main curation pass:
    - For each category: ensure at least MIN_STOCKS are present.
    - If below minimum, call Gemini to recommend additions.
    - Never delete / rename categories or remove existing stocks.
    """
    logger.info("=" * 60)
    logger.info("  SOVEREIGN WATCHLIST CURATOR — Weekly Self-Edit Run")
    logger.info("=" * 60)

    watchlist = load_watchlist()
    if not watchlist:
        logger.warning("Watchlist is empty or missing. Nothing to curate.")
        return

    changed = False

    for category, stocks in watchlist.items():
        if category == "AI_DISCOVERED":
            # Skip the runtime AI-discovery bucket — it manages itself
            continue

        current_count = len(stocks)
        if current_count >= MIN_STOCKS:
            logger.info(f"  [{category}] OK — {current_count} stocks (min: {MIN_STOCKS})")
            continue

        shortfall = MIN_STOCKS - current_count
        existing_symbols = [s["symbol"] for s in stocks]

        logger.info(f"  [{category}] Only {current_count} stocks — need {shortfall} more. Asking Gemini...")
        print(f"\n[CURATOR] '{category}' has {current_count}/{MIN_STOCKS} stocks. Requesting {shortfall} AI additions...")

        additions = ask_gemini_for_additions(category, existing_symbols, shortfall)

        if additions:
            for stock in additions:
                watchlist[category].append(stock)
                msg = f"ADDED '{stock['symbol']}' ({stock['label']}) to [{category}]"
                logger.info(f"  + {msg}")
                print(f"  ✅ {msg}")
                log_change(msg)
            changed = True
        else:
            logger.warning(f"  [{category}] Could not get suggestions. Will retry next week.")
            log_change(f"SKIPPED [{category}] — AI suggestions unavailable. Still at {current_count} stocks.")

    if changed:
        save_watchlist(watchlist)
        log_change(f"CURATOR RUN COMPLETE — Watchlist saved with updates.")
        logger.info("\n✅ Watchlist updated and saved.")
    else:
        log_change(f"CURATOR RUN COMPLETE — No changes needed.")
        logger.info("\n✅ All categories are healthy. No changes made.")

    logger.info("=" * 60)


# ── Windows Task Scheduler Registration ──────────────────────────────────────

def register_on_startup():
    """
    Registers this curator to run automatically every time you log into Windows.
    Uses ONLOGON trigger — no fixed time needed.
    """
    import sys
    python_exe  = sys.executable
    script_path = os.path.abspath(__file__)
    task_name   = "SovereignWatchlistCurator_Startup"

    cmd = (
        f'schtasks /Create /F /TN "{task_name}" '
        f'/TR "\\"{python_exe}\\" \\"{script_path}\\"" '
        f'/SC ONLOGON /RL HIGHEST'
    )

    print(f"\n[CURATOR] Registering Startup Task: {task_name}")
    print(f"  Trigger  : Every time you log into Windows")
    print(f"  Script   : {script_path}")
    result = os.system(cmd)
    if result == 0:
        print(f"  ✅ Startup task registered! Curator will run on every login.")
    else:
        print(f"  ❌ Failed. Please run this script as Administrator.")


def register_weekly_task():
    """
    Registers this curator as a Windows Task Scheduler job running
    every Sunday at 06:00 AM, before market opens.
    """
    import sys
    python_exe  = sys.executable
    script_path = os.path.abspath(__file__)
    task_name   = "SovereignWatchlistCurator"

    cmd = (
        f'schtasks /Create /F /TN "{task_name}" '
        f'/TR "\\"{python_exe}\\" \\"{script_path}\\"" '
        f'/SC WEEKLY /D SUN /ST 14:00 /RL HIGHEST'
    )

    print(f"\n[CURATOR] Registering Windows Scheduled Task: {task_name}")
    print(f"  Schedule : Every Sunday at 14:00 (2:00 PM)")
    print(f"  Script   : {script_path}")
    result = os.system(cmd)
    if result == 0:
        print(f"  ✅ Task '{task_name}' registered successfully.")
    else:
        print(f"  ❌ Failed to register task. Run as Administrator for full access.")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--register":
        register_weekly_task()
    elif len(sys.argv) > 1 and sys.argv[1] == "--register-startup":
        register_on_startup()
    else:
        curate_watchlist()
