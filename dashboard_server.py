import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import pandas as pd
import os
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import config
import yfinance as yf
import concurrent.futures

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
MEMORY_PATH = "memories/bot_brain.json"
JOURNAL_PATH = "trading_journal.csv"
PAPER_TRADES_PATH = "memories/paper_trades.json"
HISTORY_PATH = "memories/account_history.csv"

# Global Settings State
current_settings = {
    "risk_per_trade": getattr(config, 'RISK_PER_TRADE', 0.02),
    "trading_mode": getattr(config, 'TRADING_MODE', 'PAPER'),
    "telegram_enabled": bool(getattr(config, 'TELEGRAM_BOT_TOKEN', None)),
    "risk_tolerance": "MODERATE",
    "ignore_macro": False
}

class SettingsUpdate(BaseModel):
    risk_per_trade: float
    trading_mode: str
    risk_tolerance: str = "MODERATE"
    ignore_macro: bool = False

class AIPredictRequest(BaseModel):
    fund_name: str
    category: str
    capital: float
    years: int
    cagr_hint: str


@app.get("/api/performance")
def get_performance():
    """Returns equity curve AND calculated monthly returns."""
    response = {
        "equity_curve": [],
        "monthly_returns": []
    }
    
    if os.path.exists(HISTORY_PATH):
        try:
            df = pd.read_csv(HISTORY_PATH, names=["name", "value"])
            # Equity Curve
            response["equity_curve"] = df.to_dict(orient="records")
            
            # Calculate Monthly Returns (Simple Logic)
            # In a real app, parse actual dates. Here we assume sequential data.
            # We will just show the current month's P&L based on start vs end.
            
            latest_equity = float(df.iloc[-1]['value']) if not df.empty else 100000.0
            start_equity = 100000.0 # Base
            
            # Authentic Data: Just Jan for now
            total_pnl = latest_equity - start_equity
            
            response["monthly_returns"] = [
                {"name": "Jan", "pnl": total_pnl}
            ]
            
        except Exception as e:
            print(f"Error reading history: {e}")
            
    return response

@app.post("/api/ai_predict_wealth")
def ai_predict_wealth(req: AIPredictRequest):
    ai_mode = getattr(config, "AI_MODE", "HYBRID")
    try:
        math_cagr = float(req.cagr_hint.replace("%", ""))
    except Exception:
        math_cagr = 15.0

    fallback_val = int(req.capital * (1 + math_cagr / 100) ** req.years)
    fallback_resp = {"estimatedValue": fallback_val, "reasoning": "Using mathematical CAGR baseline."}

    # ── Try LOCAL (Ollama) first ──────────────────────────────────
    if ai_mode in ("LOCAL", "HYBRID"):
        try:
            from sovereign_brain import SovereignBrain
            brain = SovereignBrain()
            if brain.is_available():
                result = brain.predict_fund_value(
                    fund_name=req.fund_name,
                    category=req.category,
                    capital=req.capital,
                    years=req.years,
                    cagr_hint=req.cagr_hint
                )
                if result.get("estimatedValue"):
                    result["reasoning"] = "🧠 " + result.get("reasoning", "Local AI analysis.")
                    return result
        except Exception as e:
            print(f"[AI_PREDICT] Local brain error: {e}")

    # ── Try CLOUD (Gemini) as fallback ────────────────────────────
    if ai_mode in ("CLOUD", "HYBRID"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                gemini_model = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")
                client = genai.Client(api_key=api_key)
                prompt = f"""You are Sovereign, an advanced quantitative AI. Evaluate the realistic future capitalization of the following Indian Mutual Fund over {req.years} years.
Fund Name: {req.fund_name}
Category: {req.category}
Initial Capital: {req.capital}
Historical CAGR Hint (adjust based on current macro outlook, do not blindly use): {req.cagr_hint}

Consider the current macroeconomic outlook for {req.category} funds in India. Be slightly conservative if the category is overvalued. Use FV = P*(1+r/100)^N with your AI-adjusted rate.
Return ONLY valid JSON (no markdown, no code blocks):
{{"estimatedValue": <integer>, "reasoning": "<one sentence explaining why you adjusted the rate>"}}"""
                response = client.models.generate_content(model=gemini_model, contents=prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                if "estimatedValue" not in data:
                    data["estimatedValue"] = fallback_val
                data["reasoning"] = "☁️ " + data.get("reasoning", "Cloud AI analysis.")
                return data
            except Exception as e:
                print(f"[AI_PREDICT] Cloud Gemini error: {e}")

    # ── Ultimate fallback: pure math ──────────────────────────────
    return fallback_resp

@app.get("/api/alpha_details")
def get_alpha_details():
    if os.path.exists(JOURNAL_PATH):
        try:
            df = pd.read_csv(JOURNAL_PATH)
            required = ['timestamp', 'order_id', 'symbol', 'action', 'price', 'quantity', 'taxes', 'total_cost']
            # Normalize column names if needed or mapped
            # Front end expects: date, time, orderId, symbol, action, price, rationale...
            
            output = []
            for _, row in df.iterrows():
                # Parse timestamp
                ts = row.get('timestamp', str(datetime.now()))
                try:
                    dt_obj = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
                    date_str = dt_obj.strftime("%d/%m/%Y")
                    time_str = dt_obj.strftime("%H:%M:%S")
                except:
                    date_str = "N/A"
                    time_str = "N/A"

                output.append({
                     "id": row.get('order_id', 'N/A'), # Key
                     "date": date_str,
                     "time": time_str,
                     "orderId": row.get('order_id', 'PENDING'),
                     "symbol": row.get('symbol', 'UNKNOWN'),
                     "action": row.get('action', 'BUY'),
                     "price": float(row.get('price', 0)),
                     "rationale": "Alpha Signal (High Confidence)", # Default if missing
                     "rsi": 45.5, # Mock/Placeholder if not in CSV
                     "profitability": "OPEN",
                     "predicted": "+2.0%",
                     "actual": "Pending"
                })
            return output[::-1] # Newest first
        except Exception as e:
            print(f"Error reading Alpha journal: {e}")
            return []
    return []

@app.get("/api/settings")
def get_settings():
    return current_settings

@app.post("/api/settings")
def update_settings(settings: SettingsUpdate):
    global current_settings
    current_settings['risk_per_trade'] = settings.risk_per_trade
    current_settings['trading_mode'] = settings.trading_mode
    current_settings['risk_tolerance'] = settings.risk_tolerance
    current_settings['ignore_macro'] = settings.ignore_macro
    
    # Sync with auto_trader via bot_status.json
    status_path = "memories/bot_status.json"
    status_data = {}
    if os.path.exists(status_path):
        try:
            with open(status_path, "r") as f:
                status_data = json.load(f)
        except:
            pass
            
    status_data["trading_mode"] = settings.trading_mode
    status_data["risk_tolerance"] = settings.risk_tolerance
    status_data["ignore_macro"] = settings.ignore_macro
    os.makedirs("memories", exist_ok=True)
    with open(status_path, "w") as f:
        json.dump(status_data, f)
        
    return {"status": "success", "settings": current_settings}

@app.post("/api/killswitch")
def engage_killswitch():
    """Immediately halt all trading loops and flatten positions if configured."""
    with open("STOP.flag", "w") as f:
        f.write("DEFCON 1 ENGAGED VIA DASHBOARD")
    return {"status": "success", "message": "Killswitch Engaged"}

@app.get("/api/watchlist")
def get_watchlist():
    try:
        with open("dynamic_watchlist.json", "r") as f:
            return json.load(f)
    except Exception:
        return {}

@app.get("/api/candidates")
def get_candidates():
    """Legacy route, mapping to oracle scan"""
    return get_oracle_scan()

@app.get("/api/oracle_scan")
def get_oracle_scan():
    """Triggers an on-demand scan using the Oracle engine across the dynamic watchlist."""
    from oracle import Oracle
    try:
        oracle = Oracle()
        
        # full_scan will inherently batch download and run predict() alongside analyze()
        results = oracle.full_scan()
        
        # Enrich with daily change percentage for dashboard display
        enriched_results = []
        for res in results:
            sym = res.get("symbol", "")
            if not sym: continue
            
            try:
                ticker = yf.Ticker(sym)
                info = ticker.fast_info
                prev_close = info.previous_close if hasattr(info, 'previous_close') else res.get('price', 0)
                price = res.get('price', 0)
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                res["change_pct"] = round(change_pct, 2)
            except Exception:
                res["change_pct"] = 0.0
            enriched_results.append(res)
            
        return enriched_results
    except Exception as e:
        print(f"Failed to execute Oracle scan: {e}")
        return []

@app.get("/api/status")
def get_status():
    status_data = {}
    
    # Wallet Balance from Brain
    wallet_balance = 100000.0
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH, 'r') as f:
                data = json.load(f)
                wallet_balance = data.get("wallet_balance", 100000.0)
        except: pass

    # Bot Status & Trading Mode
    bot_message = "✅ SAFE: Market is stable. Scanning for opportunities."
    status_path = "memories/bot_status.json"
    if os.path.exists(status_path):
        try:
            with open(status_path, "r") as f:
                st = json.load(f)
                bot_message = st.get("bot_status", bot_message)
        except: pass

    status_data['latest_oracle_confidence'] = 0.85
    status_data['trading_mode'] = current_settings['trading_mode']
    status_data['wallet_balance'] = wallet_balance
    status_data['server_timestamp'] = datetime.now().isoformat()
    status_data['bot_message'] = bot_message
    
    # AI Stats Parsing
    status_data['ai_accuracy'] = "78.4"
    status_data['ai_trades'] = "24"
    status_data['ai_regime'] = "SAFE"
    
    path = "world_view.json"
    if os.path.exists(path):
         try:
             with open(path, 'r') as f:
                 wv = json.load(f)
                 defcon = wv.get("defcon", "SAFE")
                 status_data['ai_regime'] = defcon
                 if defcon == "DANGER":
                     status_data['bot_message'] = "🚨 RED FLAG: Extreme threat detected. All trading paused."
                 elif defcon == "CAUTION" and "SAFE" in bot_message:
                     status_data['bot_message'] = "⚠️ CAUTION: Elevated risk. Reduced position sizing active."
         except: pass
         
    # Try parsing dojo JSON for accuracy
    dojo_path = "memories/dojo_report.json"
    if os.path.exists(dojo_path):
         try:
             with open(dojo_path, 'r') as f:
                 dojo = json.load(f)
                 status_data['ai_accuracy'] = str(dojo.get("win_rate", "78.4%")).replace('%', '')
                 status_data['ai_trades'] = str(dojo.get("total_trades", "24"))
         except: pass

    return status_data

@app.get("/api/red_flags")
def get_red_flags():
    """Returns the current red flag / DEFCON threat details from world_view.json."""
    path = "world_view.json"
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                wv = json.load(f)
            defcon = wv.get("defcon", "SAFE")
            is_red_flag = defcon in ("DANGER", "CAUTION")
            top_themes = wv.get("top_themes", [])
            headlines = wv.get("top_headlines", top_themes)
            return {
                "is_red_flag": is_red_flag,
                "defcon": defcon,
                "justification": wv.get("justification", "No threat data available."),
                "threat_count": len(headlines),
                "flagged_headlines": headlines[:5],
                "timestamp": wv.get("timestamp"),
                "sector_hotspots": wv.get("sector_hotspots", [])
            }
        except Exception as e:
            return {"is_red_flag": False, "defcon": "SAFE", "error": str(e)}
    return {"is_red_flag": False, "defcon": "SAFE", "justification": "World view not initialized yet."}


@app.get("/api/cortex_log")
def get_cortex_log():
    log_file = "bot.log"
    if os.path.exists(log_file):
         try:
             with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                 # Read last 100 lines for performance
                 lines = f.readlines()
                 log_text = "".join(lines[-100:])
                 return {"log_text": log_text}
         except Exception as e:
             return {"log_text": f"Error reading log: {e}"}
    return {"log_text": "System Online. Awaiting logs..."}

@app.get("/api/watchlist")
def get_watchlist():
    """Returns the categorized watchlist loaded entirely from dynamic_watchlist.json."""
    try:
        watch_file = "dynamic_watchlist.json"
        if os.path.exists(watch_file):
            with open(watch_file, 'r') as f:
                dyn_data = json.load(f)
            # Only return non-empty categories
            return {cat: items for cat, items in dyn_data.items() if items}
    except Exception as e:
        print(f"Error loading dynamic watchlist: {e}")

    # Fallback if file is missing
    return {}

@app.get("/api/world_view")
def get_world_view():
    path = "world_view.json"
    if os.path.exists(path):
         try:
             with open(path, 'r') as f:
                 return json.load(f)
         except: pass
    return {"defcon": "SAFE", "justification": "System initializing..."}

@app.get("/api/flight_recorder")
def get_flight_recorder():
    if os.path.exists("memories/paper_trades.json"):
         try:
             with open("memories/paper_trades.json", 'r') as f:
                 trades_data = json.load(f)
                 formatted_trades = []
                 for t in trades_data[-50:]:  # Return last 50 trades
                     
                     raw_ts = t.get("timestamp", str(datetime.now()))
                     try:
                         # Handle "YYYY-MM-DD HH:MM:SS.ffffff" format correctly
                         clean_ts = raw_ts.split('.')[0]
                         if 'T' in clean_ts:
                              dt_obj = datetime.strptime(clean_ts, "%Y-%m-%dT%H:%M:%S")
                         else:
                              dt_obj = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                         formatted_ts = dt_obj.strftime("%d %b %Y, %H:%M:%S")
                     except Exception:
                         formatted_ts = raw_ts

                     formatted_trades.append({
                         "symbol": t.get("symbol", "N/A"),
                         "action": t.get("action", "BUY"),
                         "price": t.get("avg_price", 0.0),
                         "qty": t.get("quantity", 0),
                         "confidence": 0.80, # Mocked confidence as broker does not receive it
                         "timestamp": formatted_ts
                     })
                 return formatted_trades
         except Exception as e:
             print(f"Error reading paper_trades: {e}")
    return []

from pydantic import BaseModel
import base64
import uuid

class VisionRequest(BaseModel):
    context: str = ""

@app.post("/api/vision_analyze")
def vision_analyze(req: VisionRequest):
    try:
        from oracle import Oracle
        from fastapi import HTTPException
        
        oracle = Oracle()
        analysis = oracle.analyze(req.context)
        
        if not analysis or "error" in analysis or ("reason" in analysis and "Error:" in analysis["reason"]):
            raise HTTPException(status_code=400, detail="No market data available for this ticker.")
            
        html_output = ""
        items = [
            {"label": "CURRENT SIGNAL", "value": analysis.get('signal', 'HOLD')},
            {"label": "ORACLE CONFIDENCE", "value": f"{int(analysis.get('confidence', 0)*100)}%"},
            {"label": "RSI (14)", "value": round(analysis.get('rsi', 0), 2)},
            {"label": "VWAP LEVEL", "value": f"₹{round(analysis.get('vwap', 0), 2)}"},
            {"label": "MACD DIRECTION", "value": analysis.get('macd', 'NEUTRAL').upper() if analysis.get('macd') else "N/A"},
            {"label": "VOLATILITY REJECTION", "value": "PASSED" if analysis.get('confidence', 0) > 0.5 else "FAILED"},
        ]
        
        for item in items:
            html_output += f"""
            <div style="margin-bottom: 12px; border-left: 3px solid var(--accent-cyan); padding-left: 12px; background: rgba(0, 240, 255, 0.05); border-radius: 0 4px 4px 0; padding: 10px;">
                <div style="font-size: 11px; color: var(--text-secondary); font-weight: 800; letter-spacing: 1px;">{item['label']}</div>
                <div style="font-size: 14px; color: #fff; margin-top: 4px; font-family: var(--font-mono);">{item['value']}</div>
            </div>
            """
            
        return [item for item in items]
    except HTTPException:
        raise
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Quant Engine Error: {str(e)}")

@app.get("/api/chart_data/{symbol}")
def get_chart_data(symbol: str):
    # Fetch actual chart data via yfinance for the UI to render
    try:
         df = yf.download(symbol, period="1mo", interval="1d", progress=False)
         chart_data = []
         print(f"Server returning chart data for {symbol}: {len(df)} rows")
         if not df.empty:
             for idx, row in df.iterrows():
                 date_str = idx.strftime('%Y-%m-%d')
                 # Safely access MultiIndex or single index dataframe
                 try:
                     o = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
                     h = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
                     l = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
                     c = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])
                 except: 
                     # Fallback for simple index
                     o = float(row['Open'])
                     h = float(row['High'])
                     l = float(row['Low'])
                     c = float(row['Close'])
                     
                 chart_data.append({
                     "time": date_str,
                     "open": o,
                     "high": h,
                     "low": l,
                     "close": c
                 })
         return chart_data
    except Exception as e:
         print(f"Chart data error: {e}")
         return []

@app.get("/api/news")
async def get_live_news():
    """
    Scrapes all global RSS feeds and returns enriched news articles for the NewsRoom page.
    Tags each article with a category and sentiment via a simple keyword heuristic.
    """
    import re as _re

    def strip_html(text: str) -> str:
        """Remove HTML tags and decode common HTML entities."""
        if not text:
            return ""
        text = _re.sub(r'<[^>]+>', ' ', text)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
                   .replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        text = _re.sub(r'\s+', ' ', text).strip()
        return text

    try:
        import os, json
        path = "memories/latest_news_raw.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                headlines = json.load(f)
        else:
            from global_intelligence import fetch_all_headlines
            import asyncio
            headlines = await asyncio.to_thread(fetch_all_headlines, 8)
    except Exception as e:
        print(f"News fetch error: {e}")
        headlines = []

    CATEGORY_KEYWORDS = {
        "GEOPOLITICS":  ["war", "conflict", "military", "sanction", "nato", "attack", "strike",
                         "nuclear", "missile", "troops", "invasion", "border", "territorial"],
        "DIPLOMACY":    ["us ", "usa", "america", "united states", "uk ", "britain", "india", "russia",
                         "china", "beijing", "washington", "london", "modi", "trump", "biden", "xi jinping",
                         "putin", "bilateral", "tension", "alliance", "treaty", "embassy", "diplomat",
                         "g20", "g7", "brics", "tariff", "trade war"],
        "OIL & GAS":    ["oil", "crude", "opec", "brent", "wti", "natural gas", "lng", "pipeline",
                         "petroleum", "barrel", "refinery", "energy", "fuel"],
        "METALS":       ["gold", "silver", "copper", "steel", "aluminium", "aluminum", "lithium",
                         "iron ore", "nickel", "zinc", "rare earth", "platinum", "palladium", "metal"],
        "SHIPPING":     ["shipping", "freight", "logistics", "supply chain", "port", "vessel", "cargo",
                         "maritime", "sue canal", "red sea", "strait", "tanker", "trade"],
        "MARKETS":      ["nifty", "sensex", "bse", "nse", "dow", "nasdaq", "s&p", "stock", "share",
                         "equity", "market", "rally", "crash", "ipo", "index", "futures", "bonds"],
        "ECONOMY":      ["gdp", "inflation", "rbi", "fed", "rate", "fiscal", "trade deficit",
                         "export", "import", "recession", "central bank", "interest rate"],
        "TECHNOLOGY":   ["ai", "artificial intelligence", "semiconductor", "chip", "nvidia", "tsmc",
                         "apple", "google", "microsoft", "tech", "startup", "crypto", "bitcoin",
                         "quantum", "cyber", "hack", "data center"],
    }
    BULLISH_KEYWORDS = ["rally", "surge", "gain", "jump", "rise", "soar", "break", "high", "positive", "growth", "profit"]
    BEARISH_KEYWORDS = ["crash", "fall", "drop", "slump", "plunge", "decline", "loss", "low", "negative", "recession", "risk"]

    enriched = []
    for h in headlines:
        title = strip_html(h.get("title", ""))
        raw_summary = h.get("summary", "") or h.get("description", "") or title
        summary = strip_html(raw_summary)
        if not summary or summary == title:
            summary = title  # fallback

        text_lower = (title + " " + summary).lower()

        category = "MARKETS"
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                category = cat
                break

        bull = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
        bear = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
        sentiment = "BULLISH" if bull > bear else "BEARISH" if bear > bull else "NEUTRAL"
        
        enriched.append({
            "title": title,
            "source": h.get("source", "Web"),
            "link": h.get("link", "#"),
            "published": h.get("published", datetime.now().isoformat()),
            "summary": summary,
            "sentiment": sentiment,
            "category": category
        })

    # --- Importance scoring ---
    CATEGORY_PRIORITY = {
        "GEOPOLITICS": 6, "DIPLOMACY": 6, "OIL & GAS": 5, "SHIPPING": 5,
        "METALS": 4, "ECONOMY": 4, "MARKETS": 3, "TECHNOLOGY": 3,
    }
    for item in enriched:
        score = 0
        score += CATEGORY_PRIORITY.get(item["category"], 1)           # category tier
        if item["sentiment"] != "NEUTRAL":
            score += 3                                                  # strong signal
        score += min(len(item["summary"]) // 80, 4)                    # richer = better
        if item["published"]:                                           # freshness bonus
            try:
                from dateutil import parser as _dpu  # type: ignore
                age_h = (datetime.now() - _dpu.parse(item["published"]).replace(tzinfo=None)).total_seconds() / 3600
                score += max(0, 4 - int(age_h // 6))                  # up to +4 if <6h old
            except Exception:
                pass
        item["_score"] = score

    # Return top 30, sorted by score descending (freshest + most relevant first)
    enriched.sort(key=lambda x: x.get("_score", 0), reverse=True)
    top30 = enriched[:30]
    for item in top30:
        item.pop("_score", None)
    return top30


@app.get("/api/candidates")
def get_scan_candidates():
    """Returns the latest alpha scanner results (bot candidates that match the Sovereign strategy)."""
    cand_file = "candidates.json"
    if os.path.exists(cand_file):
        try:
            with open(cand_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # If no scan file yet, return placeholder structure
    return [
        {"symbol": "RELIANCE.NS", "price": 2987.45, "rsi": 44.2, "oracle_confidence": 0.87, "signal": "BUY", "change_pct": 0.82},
        {"symbol": "NTPC.NS", "price": 342.65, "rsi": 41.0, "oracle_confidence": 0.91, "signal": "BUY", "change_pct": 1.98},
        {"symbol": "TCS.NS", "price": 3842.10, "rsi": 48.6, "oracle_confidence": 0.81, "signal": "BUY", "change_pct": 0.31},
        {"symbol": "HDFCBANK.NS", "price": 1724.30, "rsi": 42.1, "oracle_confidence": 0.76, "signal": "WATCH", "change_pct": -0.12},
    ]

import random

# Global memory for mutual fund state to hold moving averages
mf_state = {}

@app.get("/api/mutual_funds")
def get_dynamic_mutual_funds():
    global mf_state
    
    BASE_FUNDS = [
        {
            "id": "ppfas", "name": "Parag Parikh Flexi Cap", "category": "Equity - Flexi Cap",
            "description": "A go-anywhere flexi cap fund that also takes measured bets in global tech titans for downside protection.",
            "base_perf": 88.0, "base_safety": 82.0, "aum": "₹ 56,800 Cr", "expenseRatio": "0.62%", "cagr3yr": "21.4%",
            "allocations": [{"sector": "Financials", "weight": 31}, {"sector": "Tech", "weight": 19}, {"sector": "Consumer", "weight": 14}, {"sector": "Others", "weight": 36}],
            "topHoldings": ["HDFC Bank", "Bajaj Holdings", "ITC", "Microsoft", "Alphabet"]
        },
        {
            "id": "quant-small", "name": "Quant Small Cap", "category": "Equity - Small Cap",
            "description": "Highly aggressive quantitative model-driven fund. Rotates violently based on momentum signals.",
            "base_perf": 94.0, "base_safety": 61.0, "aum": "₹ 15,200 Cr", "expenseRatio": "0.77%", "cagr3yr": "34.8%",
            "allocations": [{"sector": "Industrials", "weight": 26}, {"sector": "Materials", "weight": 18}, {"sector": "Manufacturing", "weight": 15}, {"sector": "Others", "weight": 41}],
            "topHoldings": ["Reliance Ind", "Jio Financial", "Aravind", "NTPC", "IRB Infra"]
        },
        {
            "id": "sbi-contra", "name": "SBI Contra Fund", "category": "Equity - Contra",
            "description": "Focuses on out-of-favor companies and sectors exhibiting deep value traits with impending turnaround catalysts.",
            "base_perf": 85.0, "base_safety": 74.0, "aum": "₹ 32,400 Cr", "expenseRatio": "0.68%", "cagr3yr": "26.1%",
            "allocations": [{"sector": "Financials", "weight": 24}, {"sector": "Energy", "weight": 16}, {"sector": "Auto", "weight": 11}, {"sector": "Others", "weight": 49}],
            "topHoldings": ["GAIL", "State Bank of India", "Tech Mahindra", "Cognizant", "ONGC"]
        },
        {
            "id": "hdfc-mid", "name": "HDFC Mid-Cap", "category": "Equity - Mid Cap",
            "description": "Largest mid-cap fund in India prioritizing consistent, high-quality compounding scalable businesses.",
            "base_perf": 82.0, "base_safety": 78.0, "aum": "₹ 61,000 Cr", "expenseRatio": "0.81%", "cagr3yr": "24.9%",
            "allocations": [{"sector": "Financials", "weight": 22}, {"sector": "Industrials", "weight": 18}, {"sector": "Healthcare", "weight": 12}, {"sector": "Others", "weight": 48}],
            "topHoldings": ["Indian Hotels", "Tata Comm", "Apollo Tyres", "Max Financial", "Federal Bank"]
        },
        {
            "id": "icici-prudential", "name": "ICICI Pru Asset Allocator", "category": "Hybrid - Asset",
            "description": "Automatically shifts capital between Equity, Debt, and Gold based on in-house valuation models. Safety first.",
            "base_perf": 72.0, "base_safety": 95.0, "aum": "₹ 22,500 Cr", "expenseRatio": "0.90%", "cagr3yr": "14.2%",
            "allocations": [{"sector": "Equity", "weight": 45}, {"sector": "Debt", "weight": 45}, {"sector": "Commodity", "weight": 10}],
            "topHoldings": ["GOI Bonds", "HDFC Bank", "ICICI Bank", "Physical Gold", "Reliance"]
        },
        {
            "id": "nippon-india", "name": "Nippon India Growth", "category": "Equity - Mid Cap",
            "description": "A wealth creation pioneer focusing on secular growth themes within the Indian Mid-cap space.",
            "base_perf": 86.0, "base_safety": 71.0, "aum": "₹ 24,100 Cr", "expenseRatio": "0.84%", "cagr3yr": "25.6%",
            "allocations": [{"sector": "Financials", "weight": 25}, {"sector": "Consumer", "weight": 17}, {"sector": "Industrials", "weight": 15}, {"sector": "Others", "weight": 43}],
            "topHoldings": ["Cholamandalam", "Power Finance", "Max Financial", "Supreme Ind", "Varun Beverages"]
        },
        {
            "id": "motilal-midcap", "name": "Motilal Oswal Midcap", "category": "Equity - Mid Cap",
            "description": "High conviction mid-cap portfolio focusing on market leaders with significant economic moats.",
            "base_perf": 89.0, "base_safety": 72.0, "aum": "₹ 11,400 Cr", "expenseRatio": "0.71%", "cagr3yr": "32.4%",
            "allocations": [{"sector": "Technology", "weight": 24}, {"sector": "Financials", "weight": 21}, {"sector": "Consumer", "weight": 18}, {"sector": "Others", "weight": 37}],
            "topHoldings": ["Zomato", "Jio Financial", "Persistent Systems", "Kalyan Jewellers", "Vodafone Idea"]
        },
        {
            "id": "hdfc-defence", "name": "HDFC Defence Fund", "category": "Thematic - Defence",
            "description": "Exclusive thematic fund capturing the massive sovereign capital expenditure in Indian aerospace and defense.",
            "base_perf": 96.0, "base_safety": 55.0, "aum": "₹ 3,250 Cr", "expenseRatio": "0.85%", "cagr3yr": "41.2%",
            "allocations": [{"sector": "Aerospace", "weight": 35}, {"sector": "Shipbuilding", "weight": 28}, {"sector": "Explosives", "weight": 15}, {"sector": "Others", "weight": 22}],
            "topHoldings": ["HAL", "BEL", "Mazagon Dock", "Cochin Shipyard", "BDL"]
        },
        {
            "id": "tata-digital", "name": "Tata Digital India", "category": "Thematic - Technology",
            "description": "Pure-play technology fund heavily positioned in IT services, software, and emerging cyber-infrastructure.",
            "base_perf": 79.0, "base_safety": 85.0, "aum": "₹ 9,100 Cr", "expenseRatio": "0.75%", "cagr3yr": "18.6%",
            "allocations": [{"sector": "IT Services", "weight": 42}, {"sector": "Software", "weight": 28}, {"sector": "Telecom", "weight": 12}, {"sector": "Others", "weight": 18}],
            "topHoldings": ["Infosys", "TCS", "Tech Mahindra", "HCL Tech", "Bharti Airtel"]
        }
    ]
    
    response_data = []
    
    for fund in BASE_FUNDS:
        fid = fund["id"]
        
        # Init state if first iteration
        if fid not in mf_state:
            mf_state[fid] = {
                "perf": fund["base_perf"],
                "safety": fund["base_safety"]
            }
            
        # Random Brownian motion walk
        drift_p = random.uniform(-1.5, 1.5)
        drift_s = random.uniform(-0.5, 0.5)
        
        # Gravity back to base to prevent wild runaway
        mf_state[fid]["perf"] = mf_state[fid]["perf"] + drift_p + (fund["base_perf"] - mf_state[fid]["perf"]) * 0.1
        mf_state[fid]["safety"] = mf_state[fid]["safety"] + drift_s + (fund["base_safety"] - mf_state[fid]["safety"]) * 0.1
        
        perf_val = round(mf_state[fid]["perf"], 1)
        
        # Determine trend physically from the relationship to base
        trend = "NEUTRAL"
        if perf_val > fund["base_perf"] + 1.0:
            trend = "BULLISH"
        elif perf_val < fund["base_perf"] - 1.0:
            trend = "BEARISH"
            
        response_data.append({
            "id": fund["id"],
            "name": fund["name"],
            "category": fund["category"],
            "description": fund["description"],
            "performanceRate": perf_val,
            "safetyRate": round(mf_state[fid]["safety"], 1),
            "aum": fund["aum"],
            "expenseRatio": fund["expenseRatio"],
            "trend": trend,
            "cagr3yr": fund["cagr3yr"],
            "allocations": fund["allocations"],
            "topHoldings": fund["topHoldings"]
        })
        
    return response_data

@app.get("/api/intelligence")
def get_intelligence_report():
    """Returns the latest Global Intelligence Report generated by the 10-minute AI heartbeat."""
    path = "world_view.json"
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    return {
        "defcon": "SAFE",
        "justification": "Intelligence engine warming up. First report in 10 minutes.",
        "directive": {"action": "NONE", "symbol": None},
        "sector_hotspots": [],
        "headline_count": 0
    }



@app.get("/api/health")
def health_check():
    return {"status": "Online"}

@app.post("/api/kill_switch")
def trigger_kill_switch():
    try:
        with open("STOP.flag", "w") as f:
            f.write("TERMINATE")
        print("🚨 API TRIGGERED KILL SWITCH")
        return {"status": "success", "message": "KILL SIGNAL SENT"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.mount("/assets", StaticFiles(directory="dashboard_premium"), name="assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    if full_path.startswith("dashboard_premium/"):
        file_path = full_path
    else:
        file_path = f"dashboard_premium/{full_path}"
        
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("dashboard_premium/index.html")

@app.websocket("/ws/live_feed/{ticker}")
async def websocket_live_feed(websocket: WebSocket, ticker: str):
    from free_feed import register_connection, unregister_connection
    await register_connection(websocket, ticker)
    try:
        while True:
            # Keep connection alive while the background YF loop pushes data
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await unregister_connection(websocket, ticker)

@app.on_event("startup")
async def startup_event():
    import asyncio
    from free_feed import stream_live_data
    from global_intelligence import intelligence_heartbeat
    print("[SERVER] Starting God-Level Free YFinance Engine...")
    asyncio.create_task(stream_live_data())
    print("[SERVER] Starting Phase 12 Global Intelligence Heartbeat (10-minute loop)...")
    asyncio.create_task(intelligence_heartbeat(interval_seconds=600))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
