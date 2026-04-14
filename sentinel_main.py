import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
"""
sentinel_main.py — Sovereign Orchestration Engine (Wave 2 Upgrade)
===================================================================
Pipeline:
  1. Pre-flight checks (DEFCON, Regime, Risk daily limit)
  2. Scout (daily_bot): finds SMA + RSI candidates
  3. Memory authorization: check mood / streak / karma
  4. Oracle: real confidence probability
  5. Guard: validate safety
  6. Execution: place order + update memory (streak, symbol stats)

Wave 2 fixes:
  - qty=1 hardcoded → replaced with risk_manager.get_position_size(price)
  - Added DEFCON / regime pre-flight check
  - Added MemoryManager trade authorization + post-execution memory update
"""

from daily_bot import fetch_and_scan
import oracle_interface
from risk_manager import guard, RiskManager
from memory_manager import MemoryManager
from mock_broker import MockDhanClient
import config
import logging
import datetime
import time
import os

# ─── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="sentinel.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# ─── Broker Setup ─────────────────────────────────────────────────────────
TRADING_MODE = config.TRADING_MODE

if TRADING_MODE == "PAPER":
    broker = MockDhanClient()
    logging.info("SENTINEL: Initialized in PAPER TRADING mode.")
else:
    logging.warning("SENTINEL: LIVE MODE not yet implemented. Defaulting to PAPER.")
    broker = MockDhanClient()


def _preflight_check() -> tuple:
    """
    Checks DEFCON and Market Regime before any scanning begins.
    Returns (ok: bool, reason: str).
    """
    # DEFCON check
    try:
        from cortex import Cortex
        cortex        = Cortex()
        current_defcon = cortex.get_current_defcon()
        if current_defcon == "DANGER":
            return False, f"DEFCON DANGER active — abort mission."
    except Exception as e:
        logging.warning(f"SENTINEL: Cortex pre-flight failed: {e}. Continuing.")
        current_defcon = "UNKNOWN"

    # Regime check
    try:
        from market_regime import MarketRegime
        regime = MarketRegime().get_regime()
        if regime == "CRASH":
            return False, "Market regime: CRASH — abort mission."
    except Exception as e:
        logging.warning(f"SENTINEL: Regime check failed: {e}. Continuing.")
        regime = "UNKNOWN"

    logging.info(f"SENTINEL: Pre-flight OK — DEFCON: {current_defcon} | Regime: {regime}")
    return True, f"DEFCON: {current_defcon} | Regime: {regime}"


def run_sentinel():
    """
    Sovereign Orchestration Workflow:
    1. Pre-flight (DEFCON + Regime + Risk check)
    2. Scout: find candidates
    3. Authorize via Memory brain (mood / streak)
    4. Oracle analysis
    5. Guard validation
    6. Execution + memory update
    """
    print(f"\n{'─'*50}")
    print(f"  SENTINEL v3.0 — {TRADING_MODE} MODE")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'─'*50}")

    mm           = MemoryManager()
    risk_manager = RiskManager()

    # ── PRE-FLIGHT CHECKS ─────────────────────────────────────────
    ok, msg = _preflight_check()
    if not ok:
        logging.critical(f"SENTINEL: PRE-FLIGHT ABORT — {msg}")
        print(f"\n🚨 [PRE-FLIGHT ABORT] {msg}")
        return

    # ── RISK DAILY LIMIT ──────────────────────────────────────────
    if not risk_manager.can_trade():
        print("\n🛑 [RISK MANAGER] Daily loss/trade limit reached. Mission aborted.")
        return

    # ── PHASE 1: SCOUTING & MANDATORY QUOTA ───────────────────────
    trades_today = risk_manager.get_trades_today()
    target_trades = 3
    mandatory_needed = max(0, target_trades - trades_today)
    
    try:
        scout_report = fetch_and_scan(lenient=False)
        if len(scout_report) < mandatory_needed:
            print(f"[MANDATORY] Strict scan found {len(scout_report)} candidates. Need {mandatory_needed}. Running lenient scan...")
            more_candidates = fetch_and_scan(lenient=True)
            existing_symbols = {c['symbol'] for c in scout_report}
            for c in more_candidates:
                if c['symbol'] not in existing_symbols:
                    scout_report.append(c)
    except Exception as e:
        logging.critical(f"SCOUT FAILURE: {e}")
        return

    if not scout_report:
        print("[SCOUT] No candidates found this session.")
        return

    print(f"\n[SCOUT] {len(scout_report)} candidates identified for Oracle analysis.")

    # Pre-calculate Oracle confidence for sorting
    for candidate in scout_report:
        if 'data' not in candidate:
            candidate['oracle_confidence'] = 0.0
            continue
        try:
            prediction_prob = oracle_interface.get_oracle_prediction(candidate['data'])
            candidate['oracle_confidence'] = prediction_prob
            del candidate['data'] # Free memory
        except Exception as e:
            candidate['oracle_confidence'] = 0.0
            logging.error(f"Oracle error on {candidate.get('symbol')}: {e}")

    # Sort candidates highest confidence first
    scout_report.sort(key=lambda x: x.get('oracle_confidence', 0.0), reverse=True)

    # ── PHASE 2–5: ORACLE LOOP & EXECUTION ────────────────────────
    for candidate in scout_report:
        symbol = candidate['symbol']
        price  = candidate.get('price', 0)
        prediction_prob = candidate.get('oracle_confidence', 0.0)
        
        print(f"\nProcessing {symbol} @ ₹{price:.2f} (Oracle: {prediction_prob:.2%})...")

        # Kill switch
        if os.path.exists("STOP.flag"):
            print("🚨 KILL SIGNAL — Sentinel stopping.")
            break

        # ── MEMORY AUTHORIZATION ─────────────────────────────────
        if not mm.authorize_trade(symbol):
            logging.info(f"GUARD: {symbol} denied by Memory Manager (mood/streak gate).")
            continue

        try:
            # Update oracle confidence in memory for dashboard
            mm.update_oracle_confidence(prediction_prob)

            # ── GUARD VALIDATION & MANDATORY LOWERING ──────────────
            req_conf = guard.get_required_confidence()
            needed_now = target_trades - risk_manager.get_trades_today()
            
            if needed_now > 0:
                # We need trades, and since scout_report is sorted best-to-worst, we take the top ones unconditionally
                decision = "GO"
                print(f"   [MANDATORY QUOTA] Forcing trade execution for {symbol} (Best available).")
            elif prediction_prob >= req_conf:
                decision = "GO"
            else:
                decision = "NO-GO"

            if decision == "GO":
                if config.TRADING_MODE == "ADVISORY":
                    # Advisory mode: compute position & send Telegram alert
                    wallet  = broker.get_fund_balance()
                    qty     = guard.calculate_position_size(price, wallet)
                    stop_loss     = round(price * (1 - config.HARD_STOP_PCT / 100), 2)
                    target_price  = guard.get_smart_target(price, desired_net_pct=config.PARTIAL_PROFIT_PCT / 100)
                    try:
                        from notifications import TelegramNotifier
                        TelegramNotifier().send_recommendation(symbol, "BUY", qty, price, stop_loss, target_price)
                        print(f"[ADVISORY] Alert sent: Buy {qty} {symbol} @ ₹{price} | Tgt: ₹{target_price}")
                    except Exception as te:
                        print(f"[ADVISORY] Telegram failed: {te}")
                    
                    # Even in advisory, we successfully provided a trade signal, count it towards evolution
                    mm.evolve_consciousness(candidate)
                    risk_manager.update_pnl(0) # Register trade count
                    continue

                # ── SMART POSITION SIZING ─────────────────────────
                qty = risk_manager.get_position_size(price)
                if qty <= 0:
                    print(f"   [SKIP] {symbol} too expensive for risk profile.")
                    continue

                order_response = broker.place_order(symbol, qty, "BUY", price)

                if order_response['status'] == 'success':
                    # Log trade + update memory state
                    candidate['price'] = price
                    candidate['rsi']   = candidate.get('rsi', None)
                    mm.log_trade(candidate)
                    risk_manager.update_pnl(0)
                    logging.info(f"SENTINEL: Order filled — {symbol} × {qty} @ ₹{price} (conf: {prediction_prob:.2%})")
                    print(f"   ✅ [FILLED] {symbol} × {qty} @ ₹{price}")
                    
                    # ── AI CONSCIOUSNESS EVOLUTION ──────────────────
                    mm.evolve_consciousness(candidate)
                else:
                    logging.error(f"SENTINEL: Order failed — {order_response.get('message')}")
                    print(f"   ❌ [FAILED] {order_response.get('message')}")
            else:
                logging.info(f"GUARD: {symbol} denied — confidence {prediction_prob:.2%} too low.")
                print(f"   [GUARD] {symbol} denied (conf: {prediction_prob:.2%} < {req_conf*100:.0f}%)")

        except Exception as e:
            logging.error(f"ORACLE/GUARD ERROR on {symbol}: {e}")
            continue

    print(f"\n{'─'*50}")
    print(f"  SENTINEL: MISSION COMPLETE")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    run_sentinel()
