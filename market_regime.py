import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
import logging
import time
import json
import os

try:
    import yfinance as yf
    import pandas as pd
    import pandas_ta as ta
    PANDAS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MarketRegime: Could not import pandas/yfinance: {e}")
    PANDAS_AVAILABLE = False

REGIME_CACHE_PATH = "memories/regime_cache.json"
REGIME_CACHE_TTL  = 300   # 5 minutes — don't re-download NIFTY data every scan tick


class MarketRegime:
    """
    The Market Weather Station — upgraded to 3-tier regime classification.
    
    Regimes:
      TRENDING — Low volatility, directional move. Best for trend-following trades.
      NORMAL   — Standard conditions. All strategies valid.
      CHOPPY   — Elevated noise. Reduce position sizes, raise confidence threshold.
      CRASH    — Extreme spike (>2× avg). All trading halted immediately.
    
    Performance: Results cached for 5 minutes in memories/regime_cache.json
    to avoid redundant yfinance downloads during rapid scan loops.
    """
    def __init__(self, ticker="^NSEI", window=14, crash_multiplier=2.0, choppy_multiplier=1.3, trending_multiplier=0.7):
        self.ticker            = ticker
        self.window            = window
        self.crash_multiplier  = crash_multiplier    # vol > avg*2.0 → CRASH
        self.choppy_multiplier = choppy_multiplier   # vol > avg*1.3 → CHOPPY
        self.trending_multiplier = trending_multiplier  # vol < avg*0.7 → TRENDING (calm, directional)

    def _load_cache(self):
        """Returns cached regime if still fresh, else None."""
        try:
            if os.path.exists(REGIME_CACHE_PATH):
                with open(REGIME_CACHE_PATH, 'r') as f:
                    cache = json.load(f)
                if time.time() - cache.get("timestamp", 0) < REGIME_CACHE_TTL:
                    logging.info(f"MarketRegime: Using cached regime — {cache['regime']} (expires in {int(REGIME_CACHE_TTL - (time.time() - cache['timestamp']))}s)")
                    return cache["regime"]
        except Exception:
            pass
        return None

    def _save_cache(self, regime: str):
        """Saves current regime to the cache file."""
        try:
            os.makedirs("memories", exist_ok=True)
            with open(REGIME_CACHE_PATH, 'w') as f:
                json.dump({"regime": regime, "timestamp": time.time()}, f)
        except Exception as e:
            logging.warning(f"MarketRegime: Could not write cache: {e}")

    def get_regime(self) -> str:
        """
        Classifies the current market regime from NIFTY 50 data.
        Returns: TRENDING | NORMAL | CHOPPY | CRASH
        Uses 5-min TTL cache to prevent redundant API calls.
        """
        if not PANDAS_AVAILABLE:
            logging.warning("MarketRegime: Pandas unavailable. Defaulting to NORMAL.")
            return "NORMAL"

        # Check cache first
        cached = self._load_cache()
        if cached:
            return cached

        try:
            nifty = yf.download(self.ticker, period="1mo", progress=False)

            if nifty.empty:
                logging.warning(f"MarketRegime: No data for {self.ticker}. Defaulting to NORMAL.")
                return "NORMAL"

            # Flatten MultiIndex if needed (yfinance v0.2+)
            if isinstance(nifty.columns, pd.MultiIndex):
                try:
                    nifty.columns = nifty.columns.droplevel(1)
                except Exception:
                    pass

            # Daily percentage returns
            nifty['Return'] = nifty['Close'].pct_change()

            # Rolling std dev (volatility)
            hist_vol    = nifty['Return'].rolling(window=self.window).std()
            current_vol = float(hist_vol.iloc[-1])
            avg_vol     = float(hist_vol.iloc[-self.window:-1].mean())

            if pd.isna(current_vol) or pd.isna(avg_vol) or avg_vol == 0:
                return "NORMAL"

            vol_ratio = current_vol / avg_vol
            logging.info(f"MarketRegime: Vol={current_vol:.5f} | Avg={avg_vol:.5f} | Ratio={vol_ratio:.2f}")

            # ── Regime classification (4 tiers) ───────────────────────
            if vol_ratio > self.crash_multiplier:
                regime = "CRASH"
                logging.critical(f"🚨 MarketRegime: EXTREME VOLATILITY ({vol_ratio:.2f}x avg). CRASH declared.")
            elif vol_ratio > self.choppy_multiplier:
                regime = "CHOPPY"
                logging.warning(f"⚠️ MarketRegime: Elevated noise ({vol_ratio:.2f}x avg). CHOPPY market.")
            elif vol_ratio < self.trending_multiplier:
                regime = "TRENDING"
                logging.info(f"📈 MarketRegime: Low volatility ({vol_ratio:.2f}x avg). TRENDING conditions.")
            else:
                regime = "NORMAL"
                logging.info(f"✅ MarketRegime: Standard conditions ({vol_ratio:.2f}x avg). NORMAL.")

            self._save_cache(regime)
            return regime

        except Exception as e:
            logging.error(f"MarketRegime Error: {e}")
            return "NORMAL"   # Safe fallback (was STRICT — now NORMAL for less disruption)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mr = MarketRegime()
    print(f"Current Regime: {mr.get_regime()}")
    print(f"Cached Regime:  {mr.get_regime()}")   # Should hit cache
