import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import numpy as np
import time
import logging
import json
import os
from risk_manager import RiskManager

logger = logging.getLogger("Oracle")

# ─── DYNAMIC WATCHLIST LOADER ──────────────────────────────────────
def _load_dynamic_watchlist() -> list:
    """
    Loads ALL unique symbols from dynamic_watchlist.json.
    Falls back to SOVEREIGN_SIX from config.py if file is missing.
    """
    wl_path = os.path.join(os.path.dirname(__file__), "dynamic_watchlist.json")
    if os.path.exists(wl_path):
        try:
            with open(wl_path, "r") as f:
                data = json.load(f)
            symbols = []
            seen = set()
            for category, items in data.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    sym = item.get("symbol", item) if isinstance(item, dict) else item
                    if sym and sym not in seen:
                        symbols.append(sym)
                        seen.add(sym)
            if symbols:
                logger.info(f"[ORACLE] Loaded {len(symbols)} symbols from dynamic_watchlist.json")
                return symbols
        except Exception as e:
            logger.warning(f"[ORACLE] Failed to load dynamic watchlist: {e}")

    # Fallback to config
    try:
        from config import SOVEREIGN_SIX
        return SOVEREIGN_SIX
    except ImportError:
        return ['ITC.NS', 'TATASTEEL.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BEL.NS']


class Oracle:
    """
    The All-Seeing Eye — 10-Factor Signal Engine (v2).

    Factors:
      1. RSI (14)                — Oversold/Overbought
      2. MACD Crossover          — Momentum direction
      3. Bollinger Bands         — Squeeze / breach
      4. ATR Volatility Filter   — Reject noise (DYNAMIC threshold)
      5. Volume Surge            — Institutional participation
      6. EMA Crossover (9/21)    — Fast trend direction
      7. Stochastic RSI          — Momentum within the RSI
      8. ADX (14)                — Trend strength
      9. VWAP                    — Institutional price benchmark
     10. Supertrend (10, 3)      — Directional trailing indicator

    Strategies:
      A. Momentum Breakout       — Price breaks 20-period high + volume + ADX
      B. Mean Reversion          — Extreme oversold multi-indicator confluence
      C. EMA Compression Breakout— EMAs converge then expand with volume

    Performance:
      - Batch yfinance download (1 API call for all symbols)
      - Per-symbol indicator cache with TTL
      - Lazy higher-timeframe check (only for passing signals)
    """

    def __init__(self):
        self.risk_manager = RiskManager()
        self.watchlist = _load_dynamic_watchlist()
        self._price_cache = {}       # {symbol: (df, timestamp)}
        self._batch_cache = {}       # {interval: (multi_df, timestamp)}
        self._indicator_cache = {}   # {symbol: (indicators_dict, timestamp)}
        self._CACHE_TTL = 60         # seconds
        self._BATCH_TTL = 55         # slightly less than cache TTL to stay fresh
        self._failed_symbols = set() # Track symbols that consistently fail

        # Initialize RAG for research-augmented signals
        self._rag = None
        try:
            from config import RAG_ENABLED
            if RAG_ENABLED:
                from sovereign_rag import SovereignRAG
                self._rag = SovereignRAG()
                if self._rag.is_ready:
                    logger.info("[ORACLE] RAG Knowledge Engine linked.")
                else:
                    self._rag = None
        except ImportError:
            pass

        print(f"[ORACLE] 10-Factor Signal Engine ONLINE. Tracking {len(self.watchlist)} assets.")

    # ─────────────────────────────────────────────────────────────────
    # DATA LAYER — Batch Download + Per-Symbol Cache
    # ─────────────────────────────────────────────────────────────────
    def _batch_download(self, interval="5m", period="5d"):
        """Download all watchlist symbols in a single yfinance call."""
        cache_key = interval
        now = time.time()

        if cache_key in self._batch_cache:
            cached_df, ts = self._batch_cache[cache_key]
            if now - ts < self._BATCH_TTL:
                return cached_df

        try:
            symbols = [s for s in self.watchlist if s not in self._failed_symbols]
            if not symbols:
                return None
            df = yf.download(symbols, period=period, interval=interval,
                             progress=False, show_errors=False, group_by='ticker', threads=True)
            if df is not None and not df.empty:
                self._batch_cache[cache_key] = (df, now)
                return df
        except Exception as e:
            logger.warning(f"[ORACLE] Batch download failed ({interval}): {e}")
        return None

    def _extract_symbol_data(self, batch_df, symbol):
        """Extract a single symbol's OHLCV from a batch download DataFrame."""
        try:
            if batch_df is None:
                return None
            if isinstance(batch_df.columns, pd.MultiIndex):
                if symbol in batch_df.columns.get_level_values(0):
                    df = batch_df[symbol].copy()
                else:
                    return None
            else:
                df = batch_df.copy()

            # Drop rows where Close is NaN
            if 'Close' in df.columns:
                df = df.dropna(subset=['Close'])
            if df.empty:
                return None
            return df
        except Exception:
            return None

    def fetch_data(self, symbol, period="5d", interval="5m"):
        """Fetches data — tries batch cache first, then individual download."""
        cache_key = f"{symbol}_{interval}"
        now = time.time()

        # Check per-symbol cache
        if cache_key in self._price_cache:
            cached_df, ts = self._price_cache[cache_key]
            if now - ts < self._CACHE_TTL:
                return cached_df

        # Try batch cache
        batch_key = interval
        if batch_key in self._batch_cache:
            batch_df, ts = self._batch_cache[batch_key]
            if now - ts < self._BATCH_TTL:
                df = self._extract_symbol_data(batch_df, symbol)
                if df is not None:
                    self._price_cache[cache_key] = (df, now)
                    return df

        # Fallback: individual download
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                return None
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    df.columns = df.columns.droplevel(1)
                except Exception:
                    pass
            self._price_cache[cache_key] = (df, now)
            return df
        except Exception as e:
            logger.debug(f"[ORACLE] Data fetch failed for {symbol}: {e}")
            return None

    def invalidate_cache(self):
        """Clears all cached data."""
        self._price_cache.clear()
        self._batch_cache.clear()
        self._indicator_cache.clear()

    def prefetch_all(self):
        """Pre-download all symbols in batch for current scan cycle."""
        self._batch_download(interval="5m", period="5d")
        self._batch_download(interval="1h", period="5d")

    # ─────────────────────────────────────────────────────────────────
    # INDICATOR COMPUTATION (All 10 factors in one pass)
    # ─────────────────────────────────────────────────────────────────
    def _compute_indicators(self, df):
        """Compute all 10 technical indicators on a DataFrame. Returns dict of values."""
        if df is None or len(df) < 21:
            return None

        try:
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume'] if 'Volume' in df.columns else pd.Series(0, index=df.index)

            price = float(close.iloc[-1])
            if price <= 0:
                return None

            # ── Factor 1: RSI (14) ────────────────────────────────────
            rsi_series = ta.rsi(close, length=14)
            rsi = float(rsi_series.iloc[-1]) if rsi_series is not None and pd.notna(rsi_series.iloc[-1]) else 50.0

            # ── Factor 2: MACD (12, 26, 9) ────────────────────────────
            macd_df = ta.macd(close, fast=12, slow=26, signal=9)
            macd_val = 0.0
            macd_signal = 0.0
            macd_prev = 0.0
            macd_signal_prev = 0.0
            if macd_df is not None:
                mc = macd_df.get('MACD_12_26_9')
                ms = macd_df.get('MACDs_12_26_9')
                if mc is not None and ms is not None:
                    macd_val = float(mc.iloc[-1]) if pd.notna(mc.iloc[-1]) else 0.0
                    macd_signal = float(ms.iloc[-1]) if pd.notna(ms.iloc[-1]) else 0.0
                    macd_prev = float(mc.iloc[-2]) if len(mc) > 1 and pd.notna(mc.iloc[-2]) else 0.0
                    macd_signal_prev = float(ms.iloc[-2]) if len(ms) > 1 and pd.notna(ms.iloc[-2]) else 0.0

            # ── Factor 3: Bollinger Bands (20, 2) ─────────────────────
            bb = ta.bbands(close, length=20, std=2)
            bb_lower = bb_mid = bb_upper = price
            if bb is not None:
                bbl_cols = [c for c in bb.columns if 'BBL' in c]
                bbm_cols = [c for c in bb.columns if 'BBM' in c]
                bbu_cols = [c for c in bb.columns if 'BBU' in c]
                if bbl_cols and pd.notna(bb[bbl_cols[0]].iloc[-1]):
                    bb_lower = float(bb[bbl_cols[0]].iloc[-1])
                if bbm_cols and pd.notna(bb[bbm_cols[0]].iloc[-1]):
                    bb_mid = float(bb[bbm_cols[0]].iloc[-1])
                if bbu_cols and pd.notna(bb[bbu_cols[0]].iloc[-1]):
                    bb_upper = float(bb[bbu_cols[0]].iloc[-1])

            # ── Factor 4: ATR (14) — DYNAMIC threshold ────────────────
            atr_series = ta.atr(high, low, close, length=14)
            atr_val = float(atr_series.iloc[-1]) if atr_series is not None and pd.notna(atr_series.iloc[-1]) else 0.0
            atr_pct = (atr_val / price) * 100 if price > 0 else 0.0

            # Dynamic ATR: compute 20-period median ATR% for this stock
            atr_pct_series = (atr_series / close) * 100 if atr_series is not None else None
            atr_median = 0.3  # fallback
            if atr_pct_series is not None:
                recent_atr = atr_pct_series.iloc[-20:]
                atr_median = float(recent_atr.median()) if not recent_atr.empty and pd.notna(recent_atr.median()) else 0.3
            # Dynamic threshold = 50% of the stock's own median ATR%, with 0.1% floor
            atr_threshold = max(0.10, atr_median * 0.50)

            # ── Factor 5: Volume Surge ────────────────────────────────
            vol_cur = float(volume.iloc[-1]) if pd.notna(volume.iloc[-1]) else 0
            vol_avg = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else 0
            vol_ratio = (vol_cur / vol_avg) if vol_avg > 0 else 0
            vol_surge = vol_ratio > 1.5

            # ── Factor 6: EMA Crossover (9/21) ────────────────────────
            ema9 = ta.ema(close, length=9)
            ema21 = ta.ema(close, length=21)
            ema9_val = float(ema9.iloc[-1]) if ema9 is not None and pd.notna(ema9.iloc[-1]) else price
            ema21_val = float(ema21.iloc[-1]) if ema21 is not None and pd.notna(ema21.iloc[-1]) else price
            ema9_prev = float(ema9.iloc[-2]) if ema9 is not None and len(ema9) > 1 and pd.notna(ema9.iloc[-2]) else price
            ema21_prev = float(ema21.iloc[-2]) if ema21 is not None and len(ema21) > 1 and pd.notna(ema21.iloc[-2]) else price
            ema_bullish_cross = ema9_val > ema21_val and ema9_prev <= ema21_prev
            ema_bearish_cross = ema9_val < ema21_val and ema9_prev >= ema21_prev
            ema_bullish = ema9_val > ema21_val
            ema_bearish = ema9_val < ema21_val
            # EMA compression: EMAs within 0.1% of each other
            ema_gap_pct = abs(ema9_val - ema21_val) / max(ema21_val, 1) * 100
            ema_compressed = ema_gap_pct < 0.10

            # ── Factor 7: Stochastic RSI (14, 14, 3, 3) ──────────────
            stoch_rsi = ta.stochrsi(close, length=14, rsi_length=14, k=3, d=3)
            stoch_k = 50.0
            stoch_d = 50.0
            if stoch_rsi is not None:
                k_cols = [c for c in stoch_rsi.columns if 'STOCHRSIk' in c]
                d_cols = [c for c in stoch_rsi.columns if 'STOCHRSId' in c]
                if k_cols and pd.notna(stoch_rsi[k_cols[0]].iloc[-1]):
                    stoch_k = float(stoch_rsi[k_cols[0]].iloc[-1])
                if d_cols and pd.notna(stoch_rsi[d_cols[0]].iloc[-1]):
                    stoch_d = float(stoch_rsi[d_cols[0]].iloc[-1])

            # ── Factor 8: ADX (14) — Trend Strength ──────────────────
            adx_df = ta.adx(high, low, close, length=14)
            adx_val = 20.0
            plus_di = 0.0
            minus_di = 0.0
            if adx_df is not None:
                adx_col = [c for c in adx_df.columns if 'ADX' in c and 'DM' not in c]
                pdi_col = [c for c in adx_df.columns if 'DMP' in c]
                ndi_col = [c for c in adx_df.columns if 'DMN' in c]
                if adx_col and pd.notna(adx_df[adx_col[0]].iloc[-1]):
                    adx_val = float(adx_df[adx_col[0]].iloc[-1])
                if pdi_col and pd.notna(adx_df[pdi_col[0]].iloc[-1]):
                    plus_di = float(adx_df[pdi_col[0]].iloc[-1])
                if ndi_col and pd.notna(adx_df[ndi_col[0]].iloc[-1]):
                    minus_di = float(adx_df[ndi_col[0]].iloc[-1])

            # ── Factor 9: VWAP ────────────────────────────────────────
            vwap_val = price  # default
            try:
                vwap_series = ta.vwap(high, low, close, volume)
                if vwap_series is not None and pd.notna(vwap_series.iloc[-1]):
                    vwap_val = float(vwap_series.iloc[-1])
            except Exception:
                pass
            price_vs_vwap = ((price - vwap_val) / max(vwap_val, 1)) * 100  # % above/below VWAP

            # ── Factor 10: Supertrend (10, 3) ─────────────────────────
            supertrend_bullish = False
            try:
                st = ta.supertrend(high, low, close, length=10, multiplier=3)
                if st is not None:
                    st_dir_cols = [c for c in st.columns if 'SUPERTd' in c]
                    if st_dir_cols and pd.notna(st[st_dir_cols[0]].iloc[-1]):
                        supertrend_bullish = int(st[st_dir_cols[0]].iloc[-1]) == 1
            except Exception:
                pass

            # ── Derived: 20-period high/low for breakout detection ────
            high_20 = float(high.iloc[-20:].max()) if len(high) >= 20 else price
            low_20 = float(low.iloc[-20:].min()) if len(low) >= 20 else price

            return {
                "price": price,
                # Factor 1
                "rsi": rsi,
                # Factor 2
                "macd": macd_val, "macd_signal": macd_signal,
                "macd_prev": macd_prev, "macd_signal_prev": macd_signal_prev,
                "macd_golden_cross": macd_val > macd_signal and macd_prev <= macd_signal_prev,
                "macd_death_cross": macd_val < macd_signal and macd_prev >= macd_signal_prev,
                # Factor 3
                "bb_lower": bb_lower, "bb_mid": bb_mid, "bb_upper": bb_upper,
                # Factor 4
                "atr_pct": atr_pct, "atr_threshold": atr_threshold,
                # Factor 5
                "vol_surge": vol_surge, "vol_ratio": vol_ratio,
                # Factor 6
                "ema9": ema9_val, "ema21": ema21_val,
                "ema_bullish_cross": ema_bullish_cross, "ema_bearish_cross": ema_bearish_cross,
                "ema_bullish": ema_bullish, "ema_bearish": ema_bearish,
                "ema_compressed": ema_compressed, "ema_gap_pct": ema_gap_pct,
                # Factor 7
                "stoch_k": stoch_k, "stoch_d": stoch_d,
                # Factor 8
                "adx": adx_val, "plus_di": plus_di, "minus_di": minus_di,
                # Factor 9
                "vwap": vwap_val, "price_vs_vwap": price_vs_vwap,
                # Factor 10
                "supertrend_bullish": supertrend_bullish,
                # Derived
                "high_20": high_20, "low_20": low_20,
            }
        except Exception as e:
            logger.debug(f"[ORACLE] Indicator computation error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────
    # HIGHER TIMEFRAME COMPOSITE TREND
    # ─────────────────────────────────────────────────────────────────
    def _get_higher_tf_trend(self, symbol) -> str:
        """
        Composite trend from 1-hour chart:
        RSI direction + EMA9/21 position + ADX strength.
        Returns: BULLISH / BEARISH / NEUTRAL
        """
        try:
            df = self.fetch_data(symbol, period="5d", interval="1h")
            if df is None or len(df) < 21:
                return "NEUTRAL"

            close = df['Close']

            # RSI trend
            rsi = ta.rsi(close, length=14)
            rsi_val = float(rsi.iloc[-1]) if rsi is not None and pd.notna(rsi.iloc[-1]) else 50.0

            # EMA trend
            ema9 = ta.ema(close, length=9)
            ema21 = ta.ema(close, length=21)
            ema9_v = float(ema9.iloc[-1]) if ema9 is not None and pd.notna(ema9.iloc[-1]) else 0
            ema21_v = float(ema21.iloc[-1]) if ema21 is not None and pd.notna(ema21.iloc[-1]) else 0

            # ADX strength
            adx_df = ta.adx(df['High'], df['Low'], close, length=14)
            adx_val = 20.0
            if adx_df is not None:
                adx_col = [c for c in adx_df.columns if 'ADX' in c and 'DM' not in c]
                if adx_col and pd.notna(adx_df[adx_col[0]].iloc[-1]):
                    adx_val = float(adx_df[adx_col[0]].iloc[-1])

            # Composite scoring
            score = 0
            if rsi_val > 55: score += 1
            elif rsi_val < 45: score -= 1
            if ema9_v > ema21_v: score += 1
            elif ema9_v < ema21_v: score -= 1
            if adx_val > 25: score += (1 if score > 0 else -1 if score < 0 else 0)

            if score >= 2:
                return "BULLISH"
            elif score <= -2:
                return "BEARISH"
            return "NEUTRAL"
        except Exception:
            return "NEUTRAL"

    # ─────────────────────────────────────────────────────────────────
    # STRATEGY DETECTION
    # ─────────────────────────────────────────────────────────────────
    def _detect_strategy(self, ind: dict) -> tuple:
        """
        Detects predefined strategy patterns from computed indicators.
        Returns (strategy_name, signal, confidence, reason) or None.
        """
        # ── Strategy A: Momentum Breakout ─────────────────────────
        # Price breaks 20-period high + volume surge + strong trend (ADX > 25)
        if (ind["price"] >= ind["high_20"] * 0.998
                and ind["vol_surge"]
                and ind["adx"] > 25
                and ind["plus_di"] > ind["minus_di"]
                and ind["supertrend_bullish"]):
            conf = 0.55
            if ind["ema_bullish"]: conf += 0.10
            if ind["rsi"] < 70:    conf += 0.05
            return ("MOMENTUM_BREAKOUT", "BUY", conf,
                    f"Momentum Breakout (20H Break + Vol {ind['vol_ratio']:.1f}x + ADX {ind['adx']:.0f})")

        # ── Strategy B: Mean Reversion (Extreme Oversold) ─────────
        # RSI < 25 + price below BB lower + StochRSI < 20
        if (ind["rsi"] < 25
                and ind["price"] <= ind["bb_lower"]
                and ind["stoch_k"] < 20
                and ind["adx"] < 35):  # Not in a strong downtrend
            conf = 0.50
            if ind["vol_surge"]:        conf += 0.10
            if ind["supertrend_bullish"]: conf += 0.08
            return ("MEAN_REVERSION", "BUY", conf,
                    f"Mean Reversion (RSI {ind['rsi']:.0f} + BB Breach + StochRSI {ind['stoch_k']:.0f})")

        # ── Strategy C: EMA Compression Breakout ──────────────────
        # EMAs compressed (within 0.1%) then sudden expansion with volume
        if (ind["ema_compressed"] is False  # Not currently compressed (just broke out)
                and ind["ema_gap_pct"] < 0.5  # But still very close
                and ind["ema_bullish_cross"]
                and ind["vol_surge"]):
            conf = 0.48
            if ind["adx"] > 20: conf += 0.10
            return ("EMA_COMPRESSION", "BUY", conf,
                    f"EMA Compression Breakout (Gap {ind['ema_gap_pct']:.2f}% + Vol {ind['vol_ratio']:.1f}x)")

        # ── Bearish versions ──────────────────────────────────────
        # Breakdown from 20-period low
        if (ind["price"] <= ind["low_20"] * 1.002
                and ind["vol_surge"]
                and ind["adx"] > 25
                and ind["minus_di"] > ind["plus_di"]
                and not ind["supertrend_bullish"]):
            conf = 0.50
            if ind["ema_bearish"]: conf += 0.10
            if ind["rsi"] > 30:    conf += 0.05
            return ("MOMENTUM_BREAKDOWN", "SELL", conf,
                    f"Momentum Breakdown (20L Break + Vol {ind['vol_ratio']:.1f}x + ADX {ind['adx']:.0f})")

        return None

    # ─────────────────────────────────────────────────────────────────
    # PREDICTION ENGINE — Self-sufficient Technical Pattern Recognition
    # ─────────────────────────────────────────────────────────────────
    def predict(self, symbol):
        """
        Predicts a stock's likely next move using ONLY technical patterns.
        No news dependency. Pure price/volume/indicator pattern analysis.

        Returns: {prediction, strength (0-100), cycle_phase}
        """
        df = self.fetch_data(symbol)
        if df is None or len(df) < 30:
            return {"prediction": "NEUTRAL", "strength": 0, "cycle_phase": "UNKNOWN"}

        try:
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume'] if 'Volume' in df.columns else pd.Series(0, index=df.index)

            score = 0  # -100 to +100 scale

            # ── 1. TREND PERSISTENCE SCORE ─────────────────────────────
            # Rate of change of EMA9-EMA21 gap over last 5 candles
            ema9 = ta.ema(close, length=9)
            ema21 = ta.ema(close, length=21)
            if ema9 is not None and ema21 is not None:
                gap = ema9 - ema21
                gap_recent = gap.iloc[-5:]
                if len(gap_recent.dropna()) >= 3:
                    gap_slope = float(gap_recent.iloc[-1] - gap_recent.iloc[0])
                    price_val = float(close.iloc[-1])
                    gap_slope_pct = (gap_slope / max(price_val, 1)) * 100
                    score += max(-25, min(25, gap_slope_pct * 50))  # cap at ±25

            # ── 2. MOMENTUM CYCLE DETECTION ────────────────────────────
            rsi_series = ta.rsi(close, length=14)
            cycle_phase = "NEUTRAL"
            if rsi_series is not None:
                rsi_now = float(rsi_series.iloc[-1]) if pd.notna(rsi_series.iloc[-1]) else 50
                rsi_5ago = float(rsi_series.iloc[-5]) if len(rsi_series) >= 5 and pd.notna(rsi_series.iloc[-5]) else 50
                rsi_delta = rsi_now - rsi_5ago

                if rsi_now < 35 and rsi_delta > 0:
                    cycle_phase = "EARLY_BULL"
                    score += 20
                elif 35 <= rsi_now < 55 and rsi_delta > 2:
                    cycle_phase = "MID_BULL"
                    score += 15
                elif 55 <= rsi_now < 70 and rsi_delta > 0:
                    cycle_phase = "LATE_BULL"
                    score += 5
                elif rsi_now >= 70:
                    cycle_phase = "EXHAUSTION_TOP"
                    score -= 15
                elif rsi_now > 55 and rsi_delta < 0:
                    cycle_phase = "EARLY_BEAR"
                    score -= 20
                elif 35 <= rsi_now <= 55 and rsi_delta < -2:
                    cycle_phase = "MID_BEAR"
                    score -= 15
                elif rsi_now < 35 and rsi_delta < 0:
                    cycle_phase = "CAPITULATION"
                    score -= 5  # Actually contrarian bullish, so small negative
                else:
                    cycle_phase = "CONSOLIDATION"

            # ── 3. VOLUME PATTERN SCORE ────────────────────────────────
            # Accumulation: volume up on green candles, down on red
            if len(close) >= 10 and len(volume) >= 10:
                last_10_close = close.iloc[-10:]
                last_10_vol = volume.iloc[-10:]
                price_changes = last_10_close.diff()

                up_vol = 0.0
                down_vol = 0.0
                for i in range(1, len(price_changes)):
                    if pd.notna(price_changes.iloc[i]) and pd.notna(last_10_vol.iloc[i]):
                        v = float(last_10_vol.iloc[i])
                        if float(price_changes.iloc[i]) > 0:
                            up_vol += v
                        else:
                            down_vol += v

                if (up_vol + down_vol) > 0:
                    vol_ratio_ad = up_vol / max(down_vol, 1)
                    if vol_ratio_ad > 1.5:
                        score += 15  # Strong accumulation
                    elif vol_ratio_ad > 1.1:
                        score += 8
                    elif vol_ratio_ad < 0.7:
                        score -= 15  # Distribution
                    elif vol_ratio_ad < 0.9:
                        score -= 8

            # ── 4. SUPERTREND REGIME DURATION ──────────────────────────
            try:
                st = ta.supertrend(high, low, close, length=10, multiplier=3)
                if st is not None:
                    st_dir_cols = [c for c in st.columns if 'SUPERTd' in c]
                    if st_dir_cols:
                        st_dir = st[st_dir_cols[0]]
                        current_dir = int(st_dir.iloc[-1]) if pd.notna(st_dir.iloc[-1]) else 0
                        # Count consecutive candles in same direction
                        streak = 0
                        for i in range(len(st_dir) - 1, -1, -1):
                            if pd.notna(st_dir.iloc[i]) and int(st_dir.iloc[i]) == current_dir:
                                streak += 1
                            else:
                                break

                        if current_dir == 1:  # Bullish
                            if streak <= 20:
                                score += min(15, streak)
                            else:
                                score += 5  # Exhaustion risk
                        else:  # Bearish
                            if streak <= 20:
                                score -= min(15, streak)
                            else:
                                score -= 5
            except Exception:
                pass

            # ── 5. VWAP MOMENTUM ───────────────────────────────────────
            try:
                vwap_series = ta.vwap(high, low, close, volume)
                if vwap_series is not None and len(vwap_series) >= 5:
                    price_now = float(close.iloc[-1])
                    vwap_now = float(vwap_series.iloc[-1]) if pd.notna(vwap_series.iloc[-1]) else price_now
                    vwap_5ago = float(vwap_series.iloc[-5]) if pd.notna(vwap_series.iloc[-5]) else vwap_now

                    # Price distance from VWAP
                    dist_pct = ((price_now - vwap_now) / max(vwap_now, 1)) * 100

                    if dist_pct > 1.5:
                        score += 10  # Strong buyer control
                    elif dist_pct > 0.3:
                        score += 5
                    elif dist_pct < -1.5:
                        score -= 10  # Strong seller control
                    elif dist_pct < -0.3:
                        score -= 5
            except Exception:
                pass

            # ── Normalize to 0-100 ─────────────────────────────────────
            strength = max(0, min(100, 50 + score))
            prediction = "BULLISH" if score > 10 else "BEARISH" if score < -10 else "NEUTRAL"

            return {
                "prediction": prediction,
                "strength": round(strength),
                "cycle_phase": cycle_phase,
            }

        except Exception as e:
            logger.debug(f"[ORACLE] Prediction error for {symbol}: {e}")
            return {"prediction": "NEUTRAL", "strength": 50, "cycle_phase": "UNKNOWN"}

    # ─────────────────────────────────────────────────────────────────
    # MAIN ANALYZE — 10-Factor Weighted Scoring
    # ─────────────────────────────────────────────────────────────────
    def analyze(self, symbol):
        """
        Analyzes a single symbol with 10-factor weighted signal scoring.
        Returns a dict with signal, confidence, reason, and all indicator values.
        """
        # GATEKEEPER CHECK
        if not self.risk_manager.can_trade():
            return {"signal": "HOLD", "reason": "Risk Manager Halted", "confidence": 0.0}

        min_confidence = self.risk_manager.get_required_confidence()

        df = self.fetch_data(symbol)
        if df is None or df.empty or len(df) < 21:
            return {"signal": "HOLD", "reason": "Insufficient Data", "confidence": 0.0}

        # ── COMPUTE ALL INDICATORS ───────────────────────────────────
        ind = self._compute_indicators(df)
        if ind is None:
            return {"signal": "HOLD", "reason": "Indicator Error", "confidence": 0.0}

        price = ind["price"]

        # ── DYNAMIC ATR FILTER ───────────────────────────────────────
        if ind["atr_pct"] < ind["atr_threshold"]:
            return {
                "symbol": symbol, "price": price,
                "signal": "HOLD",
                "reason": f"ATR filter: Low vol ({ind['atr_pct']:.2f}% < {ind['atr_threshold']:.2f}%)",
                "confidence": 0.0,
                "required_confidence": min_confidence
            }

        # ── CHECK STRATEGY PATTERNS FIRST ────────────────────────────
        strategy = self._detect_strategy(ind)
        if strategy:
            strat_name, signal, confidence, reason = strategy
            reason = f"[{strat_name}] {reason}"
        else:
            # ── 10-FACTOR WEIGHTED SCORING ────────────────────────────
            signal = "HOLD"
            reason = "No clear edge"
            confidence = 0.0

            buy_score = 0.0
            sell_score = 0.0
            reasons_buy = []
            reasons_sell = []

            # F1: RSI (weight: 0.15)
            if ind["rsi"] < 30:
                buy_score += 0.15
                reasons_buy.append(f"RSI Oversold ({ind['rsi']:.0f})")
            elif ind["rsi"] > 70:
                sell_score += 0.15
                reasons_sell.append(f"RSI Overbought ({ind['rsi']:.0f})")

            # F2: MACD Crossover (weight: 0.12)
            if ind["macd_golden_cross"]:
                buy_score += 0.12
                reasons_buy.append("MACD Golden Cross")
            elif ind["macd_death_cross"]:
                sell_score += 0.12
                reasons_sell.append("MACD Death Cross")

            # F3: Bollinger Bands (weight: 0.10)
            if price <= ind["bb_lower"]:
                buy_score += 0.10
                reasons_buy.append("BB Lower Breach")
            elif price >= ind["bb_upper"]:
                sell_score += 0.10
                reasons_sell.append("BB Upper Breach")

            # F5: Volume Surge (weight: 0.08)
            if ind["vol_surge"]:
                if buy_score > sell_score:
                    buy_score += 0.08
                    reasons_buy.append(f"Vol Surge ({ind['vol_ratio']:.1f}x)")
                elif sell_score > buy_score:
                    sell_score += 0.08
                    reasons_sell.append(f"Vol Surge ({ind['vol_ratio']:.1f}x)")

            # F6: EMA Crossover (weight: 0.15)
            if ind["ema_bullish_cross"]:
                buy_score += 0.15
                reasons_buy.append("EMA 9/21 Golden Cross")
            elif ind["ema_bearish_cross"]:
                sell_score += 0.15
                reasons_sell.append("EMA 9/21 Death Cross")
            elif ind["ema_bullish"]:
                buy_score += 0.06
            elif ind["ema_bearish"]:
                sell_score += 0.06

            # F7: Stochastic RSI (weight: 0.12)
            if ind["stoch_k"] < 20 and ind["stoch_d"] < 20:
                buy_score += 0.12
                reasons_buy.append(f"StochRSI Oversold ({ind['stoch_k']:.0f})")
            elif ind["stoch_k"] > 80 and ind["stoch_d"] > 80:
                sell_score += 0.12
                reasons_sell.append(f"StochRSI Overbought ({ind['stoch_k']:.0f})")

            # F8: ADX Trend Strength (multiplier)
            adx_multiplier = 1.0
            if ind["adx"] > 30:
                adx_multiplier = 1.15
                if buy_score > sell_score:
                    reasons_buy.append(f"Strong Trend (ADX {ind['adx']:.0f})")
                else:
                    reasons_sell.append(f"Strong Trend (ADX {ind['adx']:.0f})")
            elif ind["adx"] < 20:
                adx_multiplier = 0.80

            if ind["plus_di"] > ind["minus_di"]:
                buy_score += 0.04
            elif ind["minus_di"] > ind["plus_di"]:
                sell_score += 0.04

            # F9: VWAP (weight: 0.10)
            if ind["price_vs_vwap"] > 0.3:
                buy_score += 0.10
                reasons_buy.append(f"Above VWAP (+{ind['price_vs_vwap']:.1f}%)")
            elif ind["price_vs_vwap"] < -0.3:
                sell_score += 0.10
                reasons_sell.append(f"Below VWAP ({ind['price_vs_vwap']:.1f}%)")

            # F10: Supertrend (weight: 0.12)
            if ind["supertrend_bullish"]:
                buy_score += 0.12
                reasons_buy.append("Supertrend Bullish")
            else:
                sell_score += 0.12
                reasons_sell.append("Supertrend Bearish")

            # ── DECISION ──────────────────────────────────────────────
            buy_score *= adx_multiplier
            sell_score *= adx_multiplier

            if buy_score > sell_score and buy_score >= 0.20:
                signal = "BUY"
                confidence = min(buy_score, 1.0)
                reason = " + ".join(reasons_buy) if reasons_buy else "Multi-factor BUY"
            elif sell_score > buy_score and sell_score >= 0.20:
                signal = "SELL"
                confidence = min(sell_score, 1.0)
                reason = " + ".join(reasons_sell) if reasons_sell else "Multi-factor SELL"

        # ── MULTI-TIMEFRAME FILTER (only for non-HOLD signals) ────────
        if signal != "HOLD":
            htf_trend = self._get_higher_tf_trend(symbol)
            if (signal == "BUY" and htf_trend == "BEARISH") or (signal == "SELL" and htf_trend == "BULLISH"):
                confidence *= 0.60
                reason += f" [HTF Conflict: {htf_trend}]"
            elif (signal == "BUY" and htf_trend == "BULLISH") or (signal == "SELL" and htf_trend == "BEARISH"):
                confidence += 0.08
                reason += f" [HTF Aligned: {htf_trend}]"

        # ── REGIME-AWARE ADJUSTMENT ───────────────────────────────────
        regime = "NORMAL"
        try:
            if os.path.exists("memories/regime_cache.json"):
                with open("memories/regime_cache.json", 'r') as f:
                    rc = json.load(f)
                regime = rc.get("regime", "NORMAL")
        except Exception:
            pass

        if signal != "HOLD":
            if regime == "TRENDING":
                confidence += 0.10
                reason += " [Regime: TRENDING+]"
            elif regime == "CHOPPY":
                confidence *= 0.85
                reason += " [Regime: CHOPPY-]"

        # ── NEWS SENTIMENT & SMART MONEY ─────────────────────────────
        sentiment_score = 0.0
        institutional_bias = 0.0
        try:
            if os.path.exists("world_view.json"):
                with open("world_view.json", 'r') as f:
                    view = json.load(f)
                    sentiment_score = view.get("sentiment", {}).get(symbol, 0.0)
                    institutional_bias = view.get("institutional_flows", {}).get("stock_biases", {}).get(symbol, 0.0)
        except Exception:
            pass

        total_bias = sentiment_score + institutional_bias
        if signal == "BUY":
            confidence += total_bias * 0.12
            reason += f" [Bias: {total_bias:+.2f}]"
        elif signal == "SELL":
            confidence -= total_bias * 0.12
            reason += f" [Bias: {-total_bias:+.2f}]"

        # Cap between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        # ── ADAPTIVE CONFIDENCE GATE ──────────────────────────────────
        if signal != "HOLD" and confidence < min_confidence:
            reason = f"{signal} rejected (Conf {confidence:.2f} < Req {min_confidence:.2f})"
            signal = "HOLD"
            confidence = 0.0

        # ── RAG RESEARCH AUGMENTATION ─────────────────────────────────
        research_insight = ""
        if self._rag and signal != "HOLD":
            try:
                query = f"{symbol} {reason} {regime} trading strategy"
                research_insight = self._rag.query_for_context(
                    query, top_k=2, max_chars=500
                )
                if research_insight:
                    reason += " [RAG: Research-backed]"
            except Exception as e:
                logger.debug(f"[ORACLE] RAG lookup failed: {e}")

        # ── PREDICTION (self-sufficient, no news required) ───────────
        pred = self.predict(symbol)

        return {
            "symbol":              symbol,
            "price":               ind["price"],
            "signal":              signal,
            "reason":              reason,
            "confidence":          round(confidence, 3),
            "required_confidence": min_confidence,
            # Core indicators for dashboard
            "rsi":                 round(ind["rsi"], 1),
            "atr_pct":             round(ind["atr_pct"], 2),
            "adx":                 round(ind["adx"], 1),
            "stoch_rsi":           round(ind["stoch_k"], 1),
            "ema9":                round(ind["ema9"], 2),
            "ema21":               round(ind["ema21"], 2),
            "vwap":                round(ind["vwap"], 2),
            "supertrend_bullish":  ind["supertrend_bullish"],
            "vol_surge":           ind["vol_surge"],
            "vol_ratio":           round(ind["vol_ratio"], 1),
            "research_insight":    research_insight,
            # Prediction data
            "prediction":          pred["prediction"],
            "prediction_strength": pred["strength"],
            "cycle_phase":         pred["cycle_phase"],
        }

    # ─────────────────────────────────────────────────────────────────
    # FULL SCAN — Returns analysis for ALL watchlist symbols
    # ─────────────────────────────────────────────────────────────────
    def full_scan(self):
        """
        Batch-analyzes all watchlist symbols. Used by /api/oracle_scan.
        Pre-fetches data, then runs analyze + predict for each symbol.
        Returns a list of result dicts.
        """
        self.prefetch_all()
        results = []
        for symbol in self.watchlist:
            try:
                result = self.analyze(symbol)
                # Ensure symbol is always present
                if "symbol" not in result:
                    result["symbol"] = symbol
                results.append(result)
            except Exception as e:
                logger.debug(f"[ORACLE] full_scan failed for {symbol}: {e}")
                results.append({
                    "symbol": symbol, "signal": "HOLD", "confidence": 0.0,
                    "reason": f"Error: {e}", "price": 0.0,
                })
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    oracle = Oracle()
    print("\nTesting 10-Factor Oracle Engine with Prediction...")
    print("Pre-fetching all symbols in batch...")
    oracle.prefetch_all()
    print("\nAnalyzing RELIANCE.NS...")
    result = oracle.analyze("RELIANCE.NS")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"\n  >>> PREDICTION: {result.get('prediction')} | Strength: {result.get('prediction_strength')}% | Phase: {result.get('cycle_phase')}")

