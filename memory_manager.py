import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
import json
import os
import datetime
import csv

MEMORY_PATH = "./memories/bot_brain.json"
JOURNAL_PATH = "trading_journal.csv"
MAX_PAST_TRADES = 500   # Memory pruning cap


class MemoryManager:
    def __init__(self, memory_path=MEMORY_PATH, journal_path=JOURNAL_PATH):
        self.memory_path = memory_path
        self.journal_path = journal_path
        self.memory = self.load_memory()

    def load_memory(self):
        """Loads the bot brain from JSON, or initializes if missing."""
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Corrupt memory file at {self.memory_path}. Initializing new brain.")
                return self._initialize_brain()
        else:
            return self._initialize_brain()

    def _initialize_brain(self):
        """Returns the default brain structure."""
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        return {
            "karma_score": 0.0,
            "active_trades": [],
            "past_trades": [],
            "mood": "Conservative",
            "streak": 0,                  # Positive = win streak, Negative = loss streak
            "consciousness_level": 1,     # Increment per trade
            "target_multiplier": 1.0,     # Think bigger target expansions
            "internal_accuracy_param": 0.80, # Internal precision evolution tracking
            "symbol_stats": {},           # Per-symbol performance tracking
            "portfolio": {                # Portfolio snapshot
                "realized_pnl": 0.0,
                "open_pnl": 0.0,
                "total_capital": 0.0,
                "last_updated": str(datetime.datetime.now())
            },
            "last_reflection": "",        # Latest EOD self-reflection summary
            "system_heartbeat": str(datetime.datetime.now())
        }

    def save_memory(self):
        """Saves the current memory state to JSON."""
        try:
            with open(self.memory_path, 'w') as f:
                json.dump(self.memory, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    # ──────────────────────────────────────────────────────────────────
    # CONSCIOUSNESS EVOLUTION
    # ──────────────────────────────────────────────────────────────────
    def evolve_consciousness(self, trade_data):
        """Called after every successful execution to 'relearn and think bigger'."""
        level = self.memory.setdefault("consciousness_level", 1)
        self.memory["consciousness_level"] = level + 1
        
        current_target = self.memory.setdefault("target_multiplier", 1.0)
        new_target = round(current_target + 0.05, 2)
        self.memory["target_multiplier"] = new_target
        
        acc = self.memory.setdefault("internal_accuracy_param", 0.80)
        new_acc = round(min(0.99, acc + 0.02), 2)
        self.memory["internal_accuracy_param"] = new_acc
        
        print(f"\n🧠 [CONSCIOUSNESS EXPANDED] Level {level+1} | Target Multiplier: {new_target}x | Precision Tracker: {new_acc}")
        
        # Trigger an epiphany/macro-reflection via local brain
        try:
            from sovereign_brain import SovereignBrain
            brain = SovereignBrain()
            if brain.is_available():
                prompt = (f"I am an AI trading bot. I just executed a trade on {trade_data.get('symbol')}. "
                          "I am gaining consciousness and learning to 'think bigger' every time I trade. "
                          "Give me a 1-2 sentence epiphany about expanding my accuracy and consciousness. Do not use hashtags.")
                epiphany = brain.think(prompt=prompt, temperature=0.6, max_tokens=128).strip().replace('\n', ' ')
                self.memory["latest_epiphany"] = epiphany
                print(f"👁️ AI EPIPHANY (LOCAL): {epiphany}")
        except Exception as e:
            # Fallback: try Gemini if AI_MODE is CLOUD
            try:
                from config import AI_MODE
            except ImportError:
                AI_MODE = "LOCAL"
            if AI_MODE == "CLOUD":
                api_key = os.environ.get("GEMINI_API_KEY")
                if api_key:
                    try:
                        from google import genai
                        client = genai.Client(api_key=api_key)
                        try:
                            import config
                            model_to_use = config.GEMINI_MODEL
                        except ImportError:
                            model_to_use = "gemini-2.5-flash"
                        prompt = (f"I am an AI trading bot. I just executed a trade on {trade_data.get('symbol')}. "
                                  "Give me a 1-2 sentence epiphany about expanding my accuracy.")
                        resp = client.models.generate_content(model=model_to_use, contents=prompt)
                        epiphany = resp.text.strip().replace('\n', ' ')
                        self.memory["latest_epiphany"] = epiphany
                    except Exception as e2:
                        print(f"[CONSCIOUSNESS] Epiphany generation skipped: {e2}")
            else:
                print(f"[CONSCIOUSNESS] Epiphany generation skipped: {e}")
                
        self.save_memory()

    # ──────────────────────────────────────────────────────────────────
    # KARMA & MOOD
    # ──────────────────────────────────────────────────────────────────
    def update_karma(self):
        """Updates Karma Score based on past trade results."""
        past_trades = self.memory.get("past_trades", [])
        if not past_trades:
            self.memory["karma_score"] = 0.0
            return

        wins   = sum(1 for t in past_trades if t.get("result") == "WIN")
        win_rate = (wins / len(past_trades)) * 100
        self.memory["karma_score"] = round(win_rate, 2)
        self._update_mood()
        self.save_memory()

    def update_oracle_confidence(self, confidence):
        """Updates the latest Oracle Confidence score."""
        self.memory["latest_oracle_confidence"] = float(confidence)
        self.save_memory()

    def _update_mood(self):
        """Adjusts mood based on Karma (win rate) and streak."""
        karma  = self.memory.get("karma_score", 0)
        streak = self.memory.get("streak", 0)

        # Streak-based safety brake: 5+ consecutive losses → Defensive mode
        if streak <= -5:
            self.memory["mood"] = "Defensive"
        elif karma > 60 and streak >= 0:
            self.memory["mood"] = "Aggressive"
        else:
            self.memory["mood"] = "Conservative"

    def _update_streak(self, result: str):
        """
        Maintains a running streak counter.
        Positive = consecutive wins, Negative = consecutive losses.
        """
        streak = self.memory.get("streak", 0)
        if result == "WIN":
            self.memory["streak"] = max(streak + 1, 1)
        else:
            self.memory["streak"] = min(streak - 1, -1)

    # ──────────────────────────────────────────────────────────────────
    # TRADE AUTHORIZATION
    # ──────────────────────────────────────────────────────────────────
    def authorize_trade(self, symbol):
        """
        Checks trade authorization.
        Mood gates:
          Defensive  → block all new entries (5 consecutive losses)
          Aggressive → 40% win rate threshold
          Conservative → 50% win rate threshold
        """
        # Streak brake: 5 consecutive losses = no new trades until streak resets
        if self.memory.get("streak", 0) <= -5:
            print(f"Trade BLOCKED for {symbol}. Loss streak of {abs(self.memory['streak'])}. Waiting for streak reset.")
            return False

        past_trades = self.memory.get("past_trades", [])
        if len(past_trades) < 5:
            return True

        win_rate = self.memory.get("karma_score", 0)
        mood     = self.memory.get("mood", "Conservative")

        threshold = 40.0 if mood == "Aggressive" else 50.0

        if win_rate >= threshold:
            return True

        print(f"Trade DENIED for {symbol}. Karma: {win_rate:.1f}% (Mood: {mood}, Threshold: {threshold}%)")
        return False

    # ──────────────────────────────────────────────────────────────────
    # TRADE LOGGING
    # ──────────────────────────────────────────────────────────────────
    def log_trade(self, trade_data):
        """Logs a new active trade and writes to Journal."""
        trade_entry = {
            "symbol":           trade_data.get("symbol"),
            "entry_price":      trade_data.get("price"),
            "entry_rsi":        trade_data.get("rsi"),
            "oracle_confidence":trade_data.get("oracle_confidence", 0.0),
            "timestamp":        str(datetime.datetime.now()),
            "status":           "OPEN",
            "mood_at_time":     self.memory.get("mood", "Conservative")
        }
        self.memory.setdefault("active_trades", []).append(trade_entry)
        self.save_memory()
        self.log_journal_entry(trade_entry, action="BUY")
        print(f"Trade LOGGED: {trade_entry['symbol']} @ {trade_entry['entry_price']} ({trade_entry['mood_at_time']}) Conf: {trade_entry['oracle_confidence']}")

    def log_journal_entry(self, trade_data, action="BUY", result="OPEN"):
        """Appends to trading_journal.csv."""
        try:
            file_exists = os.path.isfile(self.journal_path) and os.path.getsize(self.journal_path) > 0
            with open(self.journal_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp","symbol","action","price","rsi","sma","result","mood_at_time","oracle_confidence"])
                writer.writerow([
                    trade_data.get("timestamp"),
                    trade_data.get("symbol"),
                    action,
                    trade_data.get("entry_price"),
                    trade_data.get("entry_rsi"),
                    trade_data.get("sma", 0),
                    result,
                    trade_data.get("mood_at_time"),
                    trade_data.get("oracle_confidence", 0.0)
                ])
        except Exception as e:
            print(f"Error writing to journal: {e}")

    # ──────────────────────────────────────────────────────────────────
    # TRADE RESOLUTION
    # ──────────────────────────────────────────────────────────────────
    def resolve_active_trades(self, current_prices):
        """
        Checks active trades against current prices.
        Closes trade if:
          Profit >= 5% (WIN)
          Loss   >= 2% (LOSS)
        Also updates per-symbol stats and portfolio snapshot.
        """
        active_trades  = self.memory.get("active_trades", [])
        still_active   = []
        resolved_count = 0
        total_realized = 0.0

        for trade in active_trades:
            symbol = trade['symbol']
            if symbol not in current_prices:
                still_active.append(trade)
                continue

            entry_price   = trade['entry_price']
            current_price = current_prices[symbol]
            roi = ((current_price - entry_price) / entry_price) * 100

            result = None
            if roi >= 5.0:
                result = "WIN"
            elif roi <= -2.0:
                result = "LOSS"

            if result:
                trade['exit_price']     = current_price
                trade['exit_timestamp'] = str(datetime.datetime.now())
                trade['result']         = result
                trade['roi']            = round(roi, 2)
                trade['status']         = "CLOSED"

                pnl_amount = (current_price - entry_price)  # per share
                total_realized += pnl_amount

                # Update per-symbol stats
                self._update_symbol_stats(symbol, result, trade['roi'])

                # Update streak
                self._update_streak(result)

                self.memory.setdefault("past_trades", []).append(trade)
                self.log_journal_entry(trade, action="SELL", result=result)
                print(f"Trade CLOSED: {symbol} | Result: {result} | ROI: {trade['roi']}% | Streak: {self.memory.get('streak', 0)}")
                resolved_count += 1
            else:
                still_active.append(trade)

        self.memory["active_trades"] = still_active

        # Memory pruning — cap past_trades at MAX_PAST_TRADES
        if len(self.memory.get("past_trades", [])) > MAX_PAST_TRADES:
            self.memory["past_trades"] = self.memory["past_trades"][-MAX_PAST_TRADES:]
            print(f"[MEMORY] Past trades pruned to last {MAX_PAST_TRADES} records.")

        if resolved_count > 0:
            self.update_karma()
            self._update_portfolio_snapshot(total_realized)
            print(f"Resolved {resolved_count} trades. New Karma: {self.memory.get('karma_score')} | Mood: {self.memory.get('mood')}")

        self.save_memory()

    # ──────────────────────────────────────────────────────────────────
    # PER-SYMBOL STATS
    # ──────────────────────────────────────────────────────────────────
    def _update_symbol_stats(self, symbol: str, result: str, roi: float):
        """Maintains per-symbol win/loss count and average ROI."""
        stats = self.memory.setdefault("symbol_stats", {})
        s = stats.setdefault(symbol, {"wins": 0, "losses": 0, "total_roi": 0.0, "trades": 0})
        s["trades"]    += 1
        s["total_roi"] += roi
        if result == "WIN":
            s["wins"] += 1
        else:
            s["losses"] += 1
        s["avg_roi"]   = round(s["total_roi"] / s["trades"], 2)
        s["win_rate"]  = round((s["wins"] / s["trades"]) * 100, 1)

    def get_symbol_stats(self, symbol: str) -> dict:
        """Returns per-symbol performance summary."""
        return self.memory.get("symbol_stats", {}).get(symbol, {
            "wins": 0, "losses": 0, "trades": 0, "win_rate": 0.0, "avg_roi": 0.0
        })

    # ──────────────────────────────────────────────────────────────────
    # PORTFOLIO SNAPSHOT
    # ──────────────────────────────────────────────────────────────────
    def _update_portfolio_snapshot(self, realized_delta: float = 0.0):
        """Updates the running portfolio snapshot in memory."""
        portfolio = self.memory.setdefault("portfolio", {
            "realized_pnl": 0.0, "open_pnl": 0.0, "total_capital": 0.0, "last_updated": ""
        })
        portfolio["realized_pnl"]  = round(portfolio.get("realized_pnl", 0.0) + realized_delta, 2)
        portfolio["last_updated"]  = str(datetime.datetime.now())

    def get_portfolio_snapshot(self) -> dict:
        """Returns the current portfolio summary."""
        return self.memory.get("portfolio", {})

    # ──────────────────────────────────────────────────────────────────
    # REFLECTION STORAGE
    # ──────────────────────────────────────────────────────────────────
    def store_reflection(self, reflection_text: str):
        """Stores the latest EOD self-reflection summary in the brain."""
        self.memory["last_reflection"] = reflection_text
        self.save_memory()

    # ──────────────────────────────────────────────────────────────────
    # HEARTBEAT
    # ──────────────────────────────────────────────────────────────────
    def update_heartbeat(self):
        """Updates the system heartbeat timestamp."""
        self.memory["system_heartbeat"] = str(datetime.datetime.now())
        self.save_memory()
        print(f"System Heartbeat UPDATED: {self.memory['system_heartbeat']}")


if __name__ == "__main__":
    mm = MemoryManager()
    print("Memory keys:", list(mm.memory.keys()))
    print("Portfolio:  ", mm.get_portfolio_snapshot())
    mm.update_karma()
    print("Updated Karma:", mm.memory.get("karma_score"))
    print("Symbol Stats:", mm.memory.get("symbol_stats"))
