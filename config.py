# ═══════════════════════════════════════════════════════════════════
# SOVEREIGN BOT — FINANCIAL CONSTITUTION
# All key parameters live here. Change once, applies everywhere.
# ═══════════════════════════════════════════════════════════════════

# ─── AI ENGINE ────────────────────────────────────────────────────
# AI_MODE: "LOCAL" = Ollama (zero cloud), "CLOUD" = Gemini API, "HYBRID" = try local first, cloud fallback
AI_MODE              = "LOCAL"        # LOCKED: Sovereign runs fully local. Gemini code kept as backup only.
GEMINI_MODEL         = "gemini-2.5-flash"
OLLAMA_MODEL         = "phi3.5"           # Local model via Ollama (3.8B, fits in 4GB VRAM)
OLLAMA_URL           = "http://localhost:11434"


# ─── CAPITAL MANAGEMENT ───────────────────────────────────────────
TOTAL_CAPITAL        = 1500.0       # Real wallet balance (₹)
MAX_DAILY_LOSS       = 300.0        # Kill limit — halt when daily loss reaches this (-20%)
DAILY_PROFIT_TARGET  = 1500.0       # Strategy target (+100% gain)
MAX_TRADE_AMOUNT     = 500.0        # Max capital per single trade
RISK_PER_TRADE       = 0.01         # 1% of capital per trade (position sizing)

# ─── WATCHLIST ────────────────────────────────────────────────────
SOVEREIGN_SIX = ["ITC.NS", "TATASTEEL.NS", "BEL.NS", "NTPC.NS", "POWERGRID.NS", "ASHOKLEY.NS"]

# ─── TRADING BEHAVIOUR ────────────────────────────────────────────
TRADING_MODE         = 'PAPER'      # 'PAPER' | 'ADVISORY' | 'LIVE'
MIN_CONFIDENCE       = 0.80         # Minimum Oracle confidence to execute (Sniper Mode)
MAX_TRADES_PER_DAY   = 8            # Limit overtrading per session

# ─── RISK CONTROLS (Centralized — used by memory_manager, auto_trader) ────
LOSS_STREAK_LIMIT    = 5            # Consecutive losses before Defensive mode activates
TRADE_COOLDOWN_MIN   = 30           # Minutes between re-entry on same symbol
WEEKLY_LOSS_LIMIT    = 1000.0       # Maximum tolerable weekly loss (₹)

# ─── ORACLE SIGNAL ENGINE ────────────────────────────────────────
ATR_MIN_PCT          = 0.30         # Minimum ATR% threshold to trade (reject choppy low-vol)
VOLUME_SURGE_RATIO   = 1.5          # Volume must be 1.5× 20-period average for surge flag
RSI_OVERSOLD         = 30           # RSI below this = oversold (potential BUY trigger)
RSI_OVERBOUGHT       = 70           # RSI above this = overbought (potential SELL trigger)

# ─── MARKET REGIME ────────────────────────────────────────────────
REGIME_CACHE_TTL     = 300          # Seconds to cache NIFTY regime (avoid redundant downloads)
CRASH_VOL_MULTIPLIER = 2.0          # Vol > avg*2 = CRASH regime
CHOPPY_VOL_MULTIPLIER= 1.3          # Vol > avg*1.3 = CHOPPY regime
TRENDING_VOL_MULTIPLIER = 0.7       # Vol < avg*0.7 = TRENDING regime

# ─── MEMORY & PRUNING ─────────────────────────────────────────────
MAX_PAST_TRADES      = 500          # Maximum past_trades records in bot_brain.json
MAX_DECISION_LOG     = 500          # Maximum entries in decision_log.json

# ─── SMART EXIT ENGINE ────────────────────────────────────────────
PARTIAL_PROFIT_PCT   = 5.0          # Take 50% off at +5% profit
HARD_STOP_PCT        = 2.0          # Hard stop loss at -2%
TRAILING_STOP_PCT    = 3.0          # Trailing stop: close if drops 3% from peak

# ─── NOTIFICATIONS ────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN   = "mock_token"
TELEGRAM_CHAT_ID     = "mock_id"
PUBLIC_DASHBOARD_URL = "http://localhost:5000"

# ─── RAG ENGINE ──────────────────────────────────────────────────
RAG_ENABLED          = True           # Master switch for RAG knowledge retrieval
RAG_VECTOR_DB_PATH   = "./vector_db"  # Persistent ChromaDB storage
RAG_EMBEDDING_MODEL  = "all-MiniLM-L6-v2"  # Local embedding model (384-dim, ~80MB)
RAG_CHUNK_SIZE       = 512            # Tokens per chunk
RAG_CHUNK_OVERLAP    = 64             # Overlap tokens between chunks
RAG_TOP_K            = 5              # Default results per query
RAG_CACHE_SIZE       = 256            # LRU cache entries for repeat queries
