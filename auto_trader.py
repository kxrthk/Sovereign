import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
from oracle import Oracle
from mock_broker import MockDhanClient
from risk_manager import RiskManager
import config
import time
import datetime
import random
import os
import sys
import json


TRADE_COOLDOWN_SECONDS = 30 * 60   # 30 minutes between re-entry on the same symbol

def run_auto_pilot():
    print("\n[AUTO-PILOT] Engaging Autonomous Trading Systems...")
    print("--------------------------------------------------")
    
    oracle = Oracle()
    broker = MockDhanClient()
    risk_manager = RiskManager()
    
    watchlist = oracle.watchlist
    print(f"[AUTO-PILOT] Monitoring {len(watchlist)} assets across all sectors.")
    
    from market_regime import MarketRegime
    from cortex import Cortex
    import requests
    regime_monitor = MarketRegime()
    cortex_engine  = Cortex()

    decision_log = []   # Accumulated each cycle, flushed to disk below
    
    try:
        trades_executed_today = 0
        last_trade_date = datetime.date.today()
        
        while True:
            # ── DAILY QUOTA CHECK ──────────────────────────────────────
            if datetime.date.today() != last_trade_date:
                trades_executed_today = 0
                last_trade_date = datetime.date.today()
                
            # ── BOT STATUS SYNC ─────────────────────────────────────────
            trading_mode = "AUTO_PILOT"
            risk_tolerance = "MODERATE"
            ignore_macro = False
            status_path = "memories/bot_status.json"
            if os.path.exists(status_path):
                try:
                    with open(status_path, "r") as f:
                        status_data = json.load(f)
                        trading_mode = status_data.get("trading_mode", "AUTO_PILOT")
                        risk_tolerance = status_data.get("risk_tolerance", "MODERATE")
                        ignore_macro = status_data.get("ignore_macro", False)
                except: pass
                
            def set_status(msg):
                st_data = {}
                if os.path.exists(status_path):
                    try:
                        with open(status_path, "r") as f:
                            st_data = json.load(f)
                    except: pass
                st_data["trading_mode"] = trading_mode
                st_data["risk_tolerance"] = risk_tolerance
                st_data["ignore_macro"] = ignore_macro
                st_data["bot_status"] = msg
                
                os.makedirs("memories", exist_ok=True)
                with open(status_path, "w") as f:
                    json.dump(st_data, f)
                    
            if trading_mode == "MANUAL":
                set_status("⏸️ Offline: Autonomous Execution Disabled")
                print("\n[AUTO-PILOT] Offline (MANUAL mode). Sleeping...")
                time.sleep(15)
                continue

            # ── SAFETY CHECK 1: Kill Switch ────────────────────────────
            if os.path.exists("STOP.flag"):
                print("\n🚨 KILL SIGNAL DETECTED. AUTO-PILOT TERMINATING IMMEDIATELY.")
                sys.exit()

            # ── SAFETY CHECK 2: Network Shield (Ping Google DNS) ───────
            try:
                requests.get("https://8.8.8.8", timeout=3)
            except requests.ConnectionError:
                sleep_time = random.randint(7, 13)
                print(f"[SHIELD] Network unreachable. Sleeping {sleep_time}s to prevent Crash Loops...")
                time.sleep(sleep_time)
                continue

            # ── SAFETY CHECK 3: Global Macro Cortex (DEFCON OVERRIDE) ──
            if ignore_macro:
                current_defcon = "SAFE"
                print("   [OVERRIDE] Ignore Macro Events is ACTIVE. Bypassing Cortex DEFCON.")
            else:
                current_defcon = cortex_engine.get_current_defcon()
                if current_defcon == "DANGER":
                    print("\n[CORTEX OVERRIDE] DEFCON DANGER ACTIVE. Suspended all trading due to Verified Macro Threats.")
                    time.sleep(300)
                    continue

            # ── SAFETY CHECK 4: Market Regime (Weather Station) ─────────
            try:
                regime = regime_monitor.get_regime()
            except Exception as e:
                print(f"[SHIELD] Failed to fetch market regime: {e}. Defaulting to CHOPPY.")
                regime = "CHOPPY"
                
            if regime == "CRASH":
                print("\n[STORM WARNING] Volatility spike detected! Halting all trades to protect capital.")
                time.sleep(300)
                continue

            # ── RISK CHECK (Stateful) ───────────────────────────────────
            if not risk_manager.can_trade():
                print("[WAIT] Risk Manager Halted Trading.")
                time.sleep(60)
                continue

            # ── GLOBAL INTELLIGENCE DIRECTIVE ──────────────────────────
            # If global_intelligence.py fired a macro-driven signal, act on it immediately
            intel_signal_path = "intel_signal.json"
            if os.path.exists(intel_signal_path):
                if ignore_macro:
                    os.remove(intel_signal_path)
                else:
                    try:
                        with open(intel_signal_path, 'r') as f:
                            intel = json.load(f)
                    except Exception as e:
                        print(f"   [INTEL] Failed to process intel signal: {e}")
                        intel = {}
                        
                    # Only act if the signal is fresh (< 10 minutes old)
                    ts_str = intel.get('timestamp', '1970-01-01T00:00:00')
                    signal_age = time.time() - datetime.datetime.fromisoformat(ts_str).timestamp()
                    if signal_age < 600 and intel.get('action') in ('BUY', 'SELL') and intel.get('confidence', 0) >= 0.75:
                        sym  = intel.get('symbol', 'N/A')
                        act  = intel.get('action', 'BUY')
                        conf = intel.get('confidence', 0)
                        print(f"\n[INTEL DIRECTIVE] Macro {act} on {sym} (conf: {conf:.0%}) — {intel.get('rationale', '')}")
                        if sym != 'N/A':
                            price_info = oracle.analyze(sym)
                            price = price_info.get('price', 0.0)
                            if price > 0:
                                qty = risk_manager.get_position_size(price)
                                if qty > 0:
                                    result = broker.place_order(sym, qty, act, price)
                                    if result['status'] == 'success':
                                        print(f"   [INTEL] Order filled. ID: {result.get('order_id')}")
                                        risk_manager.update_pnl(0)
                    try:
                        os.remove(intel_signal_path)   # Consume the signal
                    except: pass
            # ───────────────────────────────────────────────────────────

            scan_start_time = time.time()
            print(f"\n[SCAN] {datetime.datetime.now().strftime('%H:%M:%S')} - Regime: {regime} | DEFCON: {current_defcon} | Scanning Markets...")
            
            # ── PRE-FETCH ALL DATA (Batch Download) ────────────────────
            print("   [BATCH] Pre-fetching live market data for all symbols...")
            oracle.prefetch_all()
            
            # ── SMART EXIT ENGINE: Manage Open Positions ───────────────
            net_positions = broker.get_net_positions()
            
            ts_path = "memories/trailing_stops.json"
            trailing_data = {}
            if os.path.exists(ts_path):
                try:
                    with open(ts_path, 'r') as f:
                        trailing_data = json.load(f)
                except: pass
                
            for symbol, pos in net_positions.items():
                qty       = pos['quantity']
                avg_price = pos['avg_price']
                
                try:
                    analysis      = oracle.analyze(symbol)
                    current_price = analysis.get('price', 0.0)
                except Exception:
                    continue
                    
                if current_price <= 0: continue
                
                td = trailing_data.get(symbol, {'highest_price': avg_price, 'partial_taken': False})
                
                if current_price > td['highest_price']:
                    td['highest_price'] = current_price
                    
                profit_pct    = (current_price - avg_price) / avg_price
                drop_from_peak= (td['highest_price'] - current_price) / max(td.get('highest_price', 1), 1)
                
                # 1. Partial Profit Taking (+5%)
                if profit_pct >= 0.05 and not td['partial_taken'] and qty > 1:
                    sell_qty = qty // 2
                    print(f"   💰 [SMART EXIT] {symbol} hit +5% profit! Securing partial gains. Selling {sell_qty} shares.")
                    res = broker.place_order(symbol, sell_qty, "SELL", current_price)
                    if res['status'] == 'success':
                        risk_manager.update_pnl((current_price - avg_price) * sell_qty)
                        td['partial_taken'] = True
                        qty -= sell_qty
                
                # 2. Trailing Stop Loss (-3% from peak)
                if drop_from_peak >= 0.03 and qty > 0:
                    print(f"   🛡️ [SMART EXIT] {symbol} hit trailing stop (Dropped 3% from peak). Liquidating.")
                    res = broker.place_order(symbol, qty, "SELL", current_price)
                    if res['status'] == 'success':
                        risk_manager.update_pnl((current_price - avg_price) * qty)
                        td['highest_price'] = 0
                        td['partial_taken'] = False
                        qty = 0
                
                # 3. Hard Stop Loss (-2% from entry)
                elif profit_pct <= -0.02 and qty > 0:
                    print(f"   🛑 [SMART EXIT] {symbol} hit Hard Stop Loss (-2%). Liquidating.")
                    res = broker.place_order(symbol, qty, "SELL", current_price)
                    if res['status'] == 'success':
                        risk_manager.update_pnl((current_price - avg_price) * qty)
                        td['highest_price'] = 0
                        td['partial_taken'] = False
                
                # Update trailing memory
                if td['highest_price'] > 0:
                    trailing_data[symbol] = td
                elif symbol in trailing_data:
                    del trailing_data[symbol]
                    
            os.makedirs("memories", exist_ok=True)
            with open(ts_path, 'w') as f:
                json.dump(trailing_data, f, indent=4)
            # ──────────────────────────────────────────────────────────
            
            base_min_conf = risk_manager.get_required_confidence()

            # Apply Risk Tolerance Configuration
            if risk_tolerance == "CONSERVATIVE":
                base_min_conf += 0.10
            elif risk_tolerance == "AGGRESSIVE":
                base_min_conf -= 0.10

            # Regime-smart confidence gate:
            # CHOPPY markets demand higher bar across the board
            if regime == "CHOPPY":
                base_min_conf = min(base_min_conf + 0.05, 0.95)  # +5%, cap at 95%
                
            # ── LEARNING QUOTA ──────────────────────────────────────────
            if trades_executed_today < 5:
                base_min_conf -= 0.15  # Loosen requirements to guarantee trades
                set_status(f"🧠 Learning Mode: Hunting for Trades ({trades_executed_today}/5)")
            else:
                set_status("✅ Active: Scanning for Opportunities")
            
            # Load World View & Sector Biases
            world_view = {}
            if os.path.exists("world_view.json"):
                try:
                    with open("world_view.json", "r") as f:
                        world_view = json.load(f)
                except: pass
                    
            # Build sector map dynamically from the watchlist categories
            sector_map = {}
            try:
                wl_path = "dynamic_watchlist.json"
                if os.path.exists(wl_path):
                    with open(wl_path, "r") as f:
                        wl_data = json.load(f)
                    for category, items in wl_data.items():
                        if isinstance(items, list):
                            for item in items:
                                sym = item.get("symbol", "") if isinstance(item, dict) else str(item)
                                if sym:
                                    sector_map[sym] = category.upper()
            except Exception:
                pass
            sentiment_data    = world_view.get("sentiment", {})
            sector_bias_data  = sentiment_data.get("sector_bias", {})

            # Load trade cooldowns
            cooldown_path = "memories/cooldowns.json"
            cooldowns = {}
            if os.path.exists(cooldown_path):
                try:
                    with open(cooldown_path, 'r') as f:
                        cooldowns = json.load(f)
                except: pass
            
            for symbol in watchlist:
                # Calculate dynamic min_conf based on sector bias
                symbol_sector = sector_map.get(symbol, 'UNKNOWN')
                bias          = sector_bias_data.get(symbol_sector, 0.0)
                min_conf      = base_min_conf
                if bias > 0.5:
                    min_conf -= 0.05    # Lower barrier for trending sectors

                # Double Safety Check inside loop
                if os.path.exists("STOP.flag") or cortex_engine.get_current_defcon() == "DANGER":
                    break

                # ── TRADE COOLDOWN CHECK ──────────────────────────────
                last_trade_ts = cooldowns.get(symbol, 0)
                elapsed = time.time() - last_trade_ts
                if elapsed < TRADE_COOLDOWN_SECONDS:
                    remaining_min = int((TRADE_COOLDOWN_SECONDS - elapsed) / 60)
                    print(f"   [COOL] {symbol}: Cooldown active. {remaining_min}m until re-entry allowed.")
                    continue
                # ─────────────────────────────────────────────────────

                # 1. Consult the Oracle (Robust Call)
                try:
                    analysis = oracle.analyze(symbol)
                except Exception as e:
                    print(f"      [ERR] Oracle failed for {symbol}: {e}. Skipping.")
                    continue
                
                signal     = analysis.get('signal', 'HOLD')
                confidence = analysis.get('confidence', 0.0)
                price      = analysis.get('price', 0.0)
                
                # 2. Decision Gate (Adaptive)
                if signal != "HOLD" and confidence >= min_conf:
                    print(f"   >>> SIGNAL DETECTED: {signal} {symbol} ({analysis.get('reason', 'N/A')})")
                    
                    # 3. Position Sizing (The Risk Check)
                    quantity = risk_manager.get_position_size(price)
                    
                    # 3.5 Dynamic Sizing based on Asset Sentiment
                    asset_sentiment = sentiment_data.get(symbol, 0.0)
                    if asset_sentiment >= 0.7:
                        quantity = int(quantity * 1.2)    # High confidence news = size up 20%
                    elif asset_sentiment <= -0.5:
                        quantity = int(quantity * 0.5)    # Bad news = cut position 50%
                    
                    executed = False
                    if quantity > 0:
                        # Regime-aware position sizing
                        if regime == "TRENDING":
                            quantity = int(quantity * 1.25)  # Size up in clean trending markets
                        elif regime == "CHOPPY":
                            quantity = int(quantity * 0.75)  # Size down in noisy markets
                            
                        # Apply Risk Tolerance scaling
                        if risk_tolerance == "CONSERVATIVE":
                            quantity = int(quantity * 0.5)
                        elif risk_tolerance == "AGGRESSIVE":
                            quantity = int(quantity * 1.5)
                            
                        quantity = max(1, quantity)          # Never drop below 1 share

                        print(f"   [EXEC] Placing Order: {signal} {quantity} {symbol} @ {price:.2f} [{regime}]...")
                        try:
                            result = broker.place_order(symbol, quantity, signal, price)
                            if result['status'] == 'success':
                                print(f"      [OK] ORDER FILLED. ID: {result.get('order_id', 'N/A')}")
                                risk_manager.update_pnl(0)
                                trades_executed_today += 1
                                # Set cooldown for this symbol
                                cooldowns[symbol] = time.time()
                                with open(cooldown_path, 'w') as f:
                                    json.dump(cooldowns, f, indent=4)
                                executed = True
                            else:
                                print(f"      [ERR] ORDER FAILED: {result.get('message', 'Unknown Error')}")
                        except Exception as e:
                            print(f"      [ERR] Broker connection failed: {e}")
                    else:
                        print(f"      [SKIP] {symbol} too expensive for risk profile (Max Trade: {config.MAX_TRADE_AMOUNT})")
                        
                else:
                    executed = False
                    print(f"   [WAIT] {symbol}: {signal} ({analysis.get('reason', 'N/A')})")

                # ── DECISION LOG — record every decision ──────────────
                decision_log.append({
                    "timestamp":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol":     symbol,
                    "signal":     signal,
                    "confidence": round(confidence, 3),
                    "reason":     analysis.get('reason', 'N/A'),
                    "rsi":        analysis.get('rsi', 'N/A'),
                    "regime":     regime,
                    "defcon":     current_defcon,
                    "executed":   (signal != "HOLD" and confidence >= min_conf)
                })
                # ─────────────────────────────────────────────────────
            
            # Dynamic sleep based on Regime
            if regime == "TRENDING":
                loop_sleep = 10    # Rapid scan during clean directional moves
            elif regime == "CHOPPY":
                loop_sleep = 60    # Slow down in noisy markets to reduce false signals
            elif regime == "CRASH":
                loop_sleep = 300   # Already handled above, but just in case
            else:
                loop_sleep = 30    # NORMAL default

            # Flush decision log to disk
            try:
                dec_log_path = "memories/decision_log.json"
                existing_log = []
                if os.path.exists(dec_log_path):
                    try:
                        with open(dec_log_path, 'r') as f:
                            existing_log = json.load(f)
                    except: pass
                existing_log.extend(decision_log)
                existing_log = existing_log[-500:]   # Rolling window: last 500 decisions
                with open(dec_log_path, 'w') as f:
                    json.dump(existing_log, f, indent=2)
                decision_log.clear()
            except Exception as e:
                print(f"[LOG] Decision log write failed: {e}")

            scan_duration = time.time() - scan_start_time
            print(f"[WAIT] Scan complete in {scan_duration:.1f}s. Cooling down for {loop_sleep} seconds...")
            time.sleep(loop_sleep)
            
    except KeyboardInterrupt:
        print("\n[AUTO-PILOT] Manual Disengage Sequence Initiated. Landing safely.")
    except Exception as e:
        print(f"\n[FATAL] Uncaught Auto-Pilot Error: {e}. Initiating emergency shutdown.")

if __name__ == "__main__":
    run_auto_pilot()
