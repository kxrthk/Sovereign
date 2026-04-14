"""
daily_recap.py — Nightly AI Coach (Wave 2 Upgrade)
====================================================
Runs after market hours to evaluate the full day's performance.

Wave 2 fixes:
  - Reads correct CSV columns (price, action, result) — old code read 'total_cost'/'quantity'
    which don't exist in the current journal schema.
  - Analyzes BOTH winning and losing trades (not just losses).
  - Reads decision_log.json for scan-level pattern analysis.
  - Writes machine-readable daily summary to memories/daily_summaries/YYYY-MM-DD.json
"""

import json
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

try:
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = "gemini-2.5-flash"

JOURNAL_PATH     = "trading_journal.csv"
AI_JOURNAL_MD    = "trading_journal.md"
DECISION_LOG     = "memories/decision_log.json"
SUMMARIES_DIR    = "memories/daily_summaries"


class DailyRecap:
    """
    The Nightly AI Coach.
    Runs after market hours: reads journal + decision log → Gemini analysis → saves report.
    """
    def __init__(self):
        load_dotenv()
        # Local AI brain is primary — no API key needed
        self.brain = None
        try:
            from sovereign_brain import SovereignBrain
            self.brain = SovereignBrain()
            if self.brain.is_available():
                print("[AI COACH] SovereignBrain (LOCAL) connected.")
            else:
                print("[AI COACH] Local brain offline. Will try cloud fallback.")
                self.brain = None
        except Exception as e:
            print(f"[AI COACH] Local brain unavailable: {e}")

        # Cloud fallback (preserved but not primary)
        self.client = None
        try:
            from config import AI_MODE
        except ImportError:
            AI_MODE = "LOCAL"
        if AI_MODE == "CLOUD" and not self.brain:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    from google import genai
                    self.client = genai.Client(api_key=api_key)
                except ImportError:
                    pass

    def _parse_journal(self) -> tuple:
        """
        Reads trading_journal.csv using the CORRECT columns:
        timestamp, symbol, action, price, rsi, sma, result, mood_at_time, oracle_confidence

        Returns (winning_trades, losing_trades).
        """
        if not os.path.exists(JOURNAL_PATH):
            return [], []

        today     = datetime.now().strftime("%Y-%m-%d")
        wins      = []
        losses    = []

        try:
            with open(JOURNAL_PATH, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ts = row.get("timestamp", "")
                    if today not in ts:
                        continue

                    result = row.get("result", "OPEN").upper()
                    entry = {
                        "symbol":     row.get("symbol", "?"),
                        "action":     row.get("action", "?"),
                        "price":      row.get("price", 0),
                        "rsi":        row.get("entry_rsi", "N/A"),
                        "confidence": row.get("oracle_confidence", "N/A"),
                        "mood":       row.get("mood_at_time", "N/A"),
                        "result":     result
                    }

                    if result == "WIN":
                        wins.append(entry)
                    elif result == "LOSS":
                        losses.append(entry)
        except Exception as e:
            print(f"[RECAP] Journal parse error: {e}")

        return wins, losses

    def _load_todays_decisions(self) -> list:
        """Reads today's scan decisions from decision_log.json."""
        today     = datetime.now().strftime("%Y-%m-%d")
        decisions = []
        try:
            with open(DECISION_LOG, 'r') as f:
                log = json.load(f)
            decisions = [d for d in log if today in d.get("timestamp", "")]
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return decisions

    def _build_prompt(self, wins, losses, decisions) -> str:
        """Builds the Gemini post-mortem prompt covering wins, losses, and scan patterns."""
        today_str = datetime.now().strftime("%A, %B %d, %Y")
        executed = [d for d in decisions if d.get("executed")]
        skipped  = [d for d in decisions if not d.get("executed")]

        return f"""
You are an elite quantitative trading coach reviewing Sovereign Bot's performance today ({today_str}).

WINNING TRADES ({len(wins)}):
{json.dumps(wins, indent=2) if wins else "  None today."}

LOSING TRADES ({len(losses)}):
{json.dumps(losses, indent=2) if losses else "  None today."}

SCAN DECISIONS — Executed ({len(executed)}), Skipped ({len(skipped)}):
{json.dumps(decisions[-20:], indent=2) if decisions else "  No scan log available."}

Write a concise Post-Mortem with these sections:
**WINS ANALYSIS**: What patterns made these trades successful?
**LOSSES POST-MORTEM**: Why did these fail? Be brutal and specific.
**MISSED OPPORTUNITIES**: Were any good signals incorrectly skipped?
**TOMORROW'S DIRECTIVE**: 3 specific actionable improvements.

Under 350 words. Use bullet points. Start with a bold date header.
"""

    def run_nightly_recap(self):
        """Main method: parse journal, call Gemini, save results."""
        print(f"\n[AI COACH] Starting Nightly Review for {datetime.now().strftime('%Y-%m-%d')}...")

        wins, losses   = self._parse_journal()
        decisions      = self._load_todays_decisions()

        print(f"[AI COACH] Today: {len(wins)} wins, {len(losses)} losses, {len(decisions)} scan decisions")

        if not wins and not losses:
            msg = "No completed trades today. Capital preserved."
            print(f"[AI COACH] {msg}")
            self._write_to_journal(msg)
            self._save_machine_summary({"wins": 0, "losses": 0, "lesson": msg})
            return

        # ── LOCAL BRAIN (Primary) ─────────────────────────────────
        lesson = None
        if self.brain:
            try:
                prompt = self._build_prompt(wins, losses, decisions)
                lesson = self.brain.think(
                    prompt=prompt,
                    context_query="trading performance review analysis",
                    temperature=0.4,
                    max_tokens=1024
                )
                print("[AI COACH] Analysis complete (LOCAL brain).")
            except Exception as e:
                print(f"[AI COACH] Local brain failed: {e}")

        # ── CLOUD BACKUP (Gemini) ────────────────────────────────
        if not lesson and self.client:
            try:
                from config import GEMINI_MODEL as MODEL
            except ImportError:
                MODEL = GEMINI_MODEL
            try:
                prompt = self._build_prompt(wins, losses, decisions)
                response = self.client.models.generate_content(model=MODEL, contents=prompt)
                lesson = response.text
            except Exception as e:
                print(f"[ERR] Gemini API failed: {e}")

        if not lesson:
            lesson = (
                f"### {datetime.now().strftime('%Y-%m-%d')}\n"
                f"* Wins: {len(wins)} | Losses: {len(losses)}\n"
                f"* AI offline — raw data only.\n"
                f"* Wins: {json.dumps(wins)}\n"
                f"* Losses: {json.dumps(losses)}"
            )

        self._write_to_journal(lesson)

        # Machine-readable summary for dashboard
        self._save_machine_summary({
            "date":     datetime.now().strftime("%Y-%m-%d"),
            "wins":     len(wins),
            "losses":   len(losses),
            "decisions":len(decisions),
            "lesson":   lesson[:600],
            "win_rate": round(len(wins) / max(len(wins) + len(losses), 1) * 100, 1)
        })

        print("[AI COACH] Nightly recap complete. Journal and summary updated.")

    def _write_to_journal(self, text: str):
        with open(AI_JOURNAL_MD, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n{text}\n")

    def _save_machine_summary(self, data: dict):
        """Saves a structured JSON summary for dashboard consumption."""
        try:
            os.makedirs(SUMMARIES_DIR, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            path     = os.path.join(SUMMARIES_DIR, f"{date_str}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[AI COACH] Machine summary saved: {path}")
        except Exception as e:
            print(f"[AI COACH] Could not save machine summary: {e}")


if __name__ == "__main__":
    coach = DailyRecap()
    coach.run_nightly_recap()
