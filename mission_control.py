import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
import yfinance as yf
from datetime import datetime
import base64
import threading
import time
from config import SOVEREIGN_SIX
from quant_engine import QuantEngine
from cortex import Cortex

quant = QuantEngine()
cortex = Cortex()

app = Flask(__name__, 
            static_folder="frontend/dist/assets", 
            template_folder="frontend/dist",
            static_url_path="/assets")
CORS(app)

# Background Intelligence Engine
def background_intelligence_loop():
    print("[SYSTEM] Background News & Cortex Engine started.")
    while True:
        try:
            print("[SYSTEM] Fetching latest global news and evaluating DEFCON...")
            cortex.evaluate_world_state()
        except Exception as e:
            print(f"[SYSTEM] Cortex Error: {e}")
        time.sleep(600) # Update every 10 mins

intel_thread = threading.Thread(target=background_intelligence_loop, daemon=True)
intel_thread.start()

# The location of the log file written by Sentinel/Auto-Trader
FLIGHT_RECORDER = "memories/flight_recorder.json"

@app.route('/')
def home():
    """Serves the main Mission Control dashboard."""
    return render_template('index.html')

# Catch-all route to allow React Router to handle history state in the native app
@app.route('/<path:path>')
def catch_all(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    # Give non-assets back to React Router
    if not path.startswith("api/"):
        return render_template('index.html')
    return jsonify({"error": "API route not found"}), 404

@app.route('/api/flight_recorder')
def get_flight_recorder():
    """Returns the trade logs."""
    if not os.path.exists(FLIGHT_RECORDER):
        return jsonify([])
        
    try:
        with open(FLIGHT_RECORDER, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except json.JSONDecodeError:
        return jsonify([])

@app.route('/api/chart_data/<symbol>')
def get_chart_data(symbol):
    """
    Fetches raw OHLCV data from yfinance for the Lightweight Charts frontend.
    """
    try:
        # Fetch 5 days of 1-minute data, or 1mo of 1d
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1d")
        
        if df.empty:
            return jsonify([])
            
        chart_data = []
        for index, row in df.iterrows():
            # Format required by TradingView Lightweight Charts
            chart_data.append({
                "time": index.strftime('%Y-%m-%d'),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "value": row["Volume"]
            })
            
        return jsonify(chart_data)
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        return jsonify([])

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """Returns the merged SOVEREIGN_SIX and dynamic watchlist categories."""
    full_names_map = {
        "ITC.NS": "ITC Limited",
        "TATASTEEL.NS": "Tata Steel Limited",
        "BEL.NS": "Bharat Electronics Limited",
        "NTPC.NS": "NTPC Limited",
        "POWERGRID.NS": "Power Grid Corporation of India Limited",
        "ASHOKLEY.NS": "Ashok Leyland Limited"
    }
    
    base_categories = {
        "CORE EQUITIES": [{"symbol": t, "label": t.replace(".NS", ""), "full_name": full_names_map.get(t, t.replace(".NS", ""))} for t in SOVEREIGN_SIX],
        "RAW MATERIALS": [
            {"symbol": "GOLDBEES.NS", "label": "GOLD ETF", "full_name": "Nippon India ETF Gold BeES"},
            {"symbol": "SILVERBEES.NS", "label": "SILVER ETF", "full_name": "Nippon India ETF Silver BeES"},
            {"symbol": "HINDCOPPER.NS", "label": "HIND COPPER", "full_name": "Hindustan Copper Limited"},
            {"symbol": "VEDL.NS", "label": "VEDANTA", "full_name": "Vedanta Limited"}
        ]
    }
    
    try:
        watch_file = "dynamic_watchlist.json"
        if os.path.exists(watch_file):
            with open(watch_file, 'r') as f:
                dyn_data = json.load(f)
            # Merge
            for cat, items in dyn_data.items():
                if items:
                    base_categories[cat] = items
    except Exception as e:
        print(f"Error loading dynamic watchlist: {e}")
        
    return jsonify(base_categories)

@app.route('/api/manual_trade', methods=['POST'])
def manual_trade():
    """Records a manual simulation trade to the flight recorder."""
    try:
        data = request.json
        trade = {
            "timestamp": datetime.now().isoformat(),
            "symbol": data.get("symbol"),
            "action": data.get("action"),
            "qty": data.get("qty", 1),
            "price": data.get("price"),
            "confidence": 1.0,  # Manual override
            "reason": "Manual Play Trade via UI"
        }
        
        # Load existing
        trades = []
        if os.path.exists(FLIGHT_RECORDER):
             with open(FLIGHT_RECORDER, 'r') as f:
                  trades = json.load(f)
        
        trades.append(trade)
        
        # Write back
        os.makedirs(os.path.dirname(FLIGHT_RECORDER), exist_ok=True)
        with open(FLIGHT_RECORDER, 'w') as f:
             json.dump(trades, f, indent=4)
             
        return jsonify({"status": "success", "message": "Manual trade recorded."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vision_analyze', methods=['POST'])
def vision_analyze():
    """Repurposed to run Quantitative OHLCV analysis instead of Vision."""
    try:
        data = request.json
        # We fetch the ticker from the 'context' field sent by the updated UI
        symbol = data.get('context', 'ITC.NS').strip().upper()
        if not symbol:
             symbol = 'ITC.NS'
             
        # Analyze using Math instead of AI Vision
        formatted = quant.analyze(symbol)
             
        return jsonify(formatted)
    except Exception as e:
        return jsonify([{"label": "ERROR", "value": str(e)}]), 500

@app.route('/api/world_view')
def get_world_view():
    """Returns the Cortex generated Macro DEFCON state."""
    try:
        with open("world_view.json", "r") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"defcon": "UNKNOWN", "justification": "Cortex Offline"})

@app.route('/api/status')
def get_status():
    """Returns AI performance and wallet stats for the React Dashboard. All live data."""
    stats = {}
    if os.path.exists("memories/daily_stats.json"):
        try:
            with open("memories/daily_stats.json", "r") as f:
                stats = json.load(f)
        except: pass

    # Live brain data
    brain = {}
    if os.path.exists("memories/bot_brain.json"):
        try:
            with open("memories/bot_brain.json", "r") as f:
                brain = json.load(f)
        except: pass

    wallet_balance       = brain.get("wallet_balance", 100000.0)
    karma_score          = brain.get("karma_score", 0.0)           # Live win rate %
    oracle_confidence    = brain.get("latest_oracle_confidence", 0.0)  # Live oracle confidence
    streak               = brain.get("streak", 0)
    mood                 = brain.get("mood", "Conservative")
    portfolio            = brain.get("portfolio", {})

    # Weekly P&L
    weekly_pnl = 0.0
    if os.path.exists("memories/weekly_stats.json"):
        try:
            with open("memories/weekly_stats.json", "r") as f:
                wk = json.load(f)
            weekly_pnl = wk.get("weekly_pnl", 0.0)
        except: pass

    # Regime from cache (avoids NIFTY re-download)
    regime = "UNKNOWN"
    if os.path.exists("memories/regime_cache.json"):
        try:
            with open("memories/regime_cache.json", "r") as f:
                regime = json.load(f).get("regime", "UNKNOWN")
        except: pass

    return jsonify({
        "wallet_balance":          wallet_balance,
        "ai_accuracy":             round(karma_score, 1),   # Live win rate, NOT hardcoded
        "latest_oracle_confidence":round(oracle_confidence, 3),   # Live from memory
        "ai_trades":               stats.get("trade_count", 0),
        "ai_regime":               regime,
        "streak":                  streak,
        "mood":                    mood,
        "weekly_pnl":              weekly_pnl,
        "realized_pnl":            portfolio.get("realized_pnl", 0.0)
    })

@app.route('/api/brain')
def get_brain():
    """Returns the full bot_brain.json — symbol stats, streak, portfolio, reflection."""
    if not os.path.exists("memories/bot_brain.json"):
        return jsonify({"error": "Brain not initialized yet"}), 404
    try:
        with open("memories/bot_brain.json", "r") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/decisions')
def get_decisions():
    """Returns the last 50 trading scan decisions from decision_log.json."""
    log_path = "memories/decision_log.json"
    if not os.path.exists(log_path):
        return jsonify([])
    try:
        with open(log_path, "r") as f:
            log = json.load(f)
        return jsonify(log[-50:])   # Last 50 entries
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reflections')
def get_reflections():
    """Returns the latest EOD self-reflection and a list of past reflection dates."""
    brain = {}
    if os.path.exists("memories/bot_brain.json"):
        try:
            with open("memories/bot_brain.json", "r") as f:
                brain = json.load(f)
        except: pass

    # List available reflection files
    reflection_dir  = "memories/reflections"
    available_dates = []
    if os.path.exists(reflection_dir):
        available_dates = sorted(
            [f.replace(".txt", "") for f in os.listdir(reflection_dir) if f.endswith(".txt")],
            reverse=True
        )

    return jsonify({
        "latest_reflection":      brain.get("last_reflection", "No reflection yet."),
        "last_reflection_date":   brain.get("last_reflection_date", None),
        "available_dates":        available_dates[:10]
    })


@app.route('/api/intelligence')
def get_intelligence():
    """Returns Cortex macro data and top sector bias for the React Dashboard."""
    world_view = {}
    if os.path.exists("world_view.json"):
         try:
             with open("world_view.json", "r") as f:
                 world_view = json.load(f)
         except: pass
         
    # Isolate sector hotspots (bias > 0.5)
    hotspots = []
    inst_flows = world_view.get("institutional_flows", {}).get("stock_biases", {})
    for sym, bias in inst_flows.items():
         if bias > 0.5:
             hotspots.append(sym.replace(".NS", ""))
             
    # Create a mock directive based on highest bias
    directive = {"action": "NONE", "symbol": None, "confidence": 0, "rationale": "No strong macro edge."}
    if hotspots:
         best_sym = sorted(inst_flows.items(), key=lambda x: x[1], reverse=True)[0]
         directive = {
             "action": "BUY",
             "symbol": best_sym[0],
             "confidence": 0.85,
             "rationale": f"Strong institutional accumulation detected in {best_sym[0]}."
         }
         
    return jsonify({
         "defcon": world_view.get("defcon", "SAFE"),
         "justification": world_view.get("justification", "Cortex operational."),
         "headline_count": len(world_view.get("top_themes", [])),
         "timestamp": world_view.get("timestamp", time.time() if 'time' in globals() else 0),
         "sector_hotspots": hotspots[:3],
         "directive": directive
    })

@app.route('/api/news')
def get_news():
    """Returns the latest news from the global news cache or fetches live."""
    try:
        from news_agent import NewsAgent
        # Pass more feeds to get closer to 30 articles
        agent = NewsAgent(feeds=[
            "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
            "https://www.livemint.com/rss/markets",
            "https://www.moneycontrol.com/rss/latestnews.xml"
        ])
        raw_news = agent.fetch_latest_headlines()
        
        formatted = []
        for i, r in enumerate(raw_news[:30]):
            # Assign fake categories and sentiment for UI demo richness
            cats = ["MARKETS", "ECONOMY", "TECHNOLOGY", "GEOPOLITICS", "COMMODITIES"]
            sent = ["BULLISH", "BEARISH", "NEUTRAL", "NEUTRAL"]
            
            title = r.get("title", "")
            if "plunge" in title.lower() or "fall" in title.lower() or "crash" in title.lower(): s = "BEARISH"
            elif "surge" in title.lower() or "jump" in title.lower() or "buy" in title.lower(): s = "BULLISH"
            else: s = sent[i % len(sent)]
            
            formatted.append({
                "title": title,
                "source": r.get("source", "Web"),
                "link": r.get("link", "#"),
                "published": r.get("published", datetime.now().isoformat()),
                "summary": title + " - Full comprehensive intelligence report available at source. Tracking institutional footprint.",
                "sentiment": s,
                "category": cats[i % len(cats)]
            })
        return jsonify(formatted)
    except Exception as e:
        return jsonify([{"title": "Error syncing intelligence feed", "summary": str(e), "source": "System"}])

if __name__ == '__main__':
    print("SOVEREIGN MISSION CONTROL ONLINE -> http://localhost:5000")
    if not os.path.exists("dashboard"):
        os.makedirs("dashboard")
    app.run(host='0.0.0.0', port=5000, debug=True)
