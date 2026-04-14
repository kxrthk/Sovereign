import yfinance as yf
import pandas as pd
import pandas_ta as ta

class QuantEngine:
    """
    100% Mathematical OHLCV Engine.
    Computes Fibonacci retracements, Bollinger Bands, RSI, and MACD strictly from raw market data.
    ZERO AI HALLUCINATION.
    """
    def __init__(self):
        pass

    def analyze(self, symbol: str, period="1mo", interval="1d") -> list:
        try:
            # Ensure valid Indian ticker format if missing
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol += '.NS'

            df = yf.download(symbol, period=period, interval=interval, progress=False, show_errors=False)
            if df.empty:
                return [{"label": "ERROR", "value": f"No Market Data found for {symbol}"}]
                
            # Flatten MultiIndex Columns (yfinance v0.2+)
            if isinstance(df.columns, pd.MultiIndex):
                try: 
                    df.columns = df.columns.droplevel(1)
                except: 
                    pass
                
            # -------------------------------
            # 1. Core Price Metrics
            # -------------------------------
            close_price = df['Close'].iloc[-1]
            high_max = df['High'].max()
            low_min = df['Low'].min()
            
            # -------------------------------
            # 2. Fibonacci Retracements
            # -------------------------------
            diff = high_max - low_min
            fib_236 = high_max - 0.236 * diff
            fib_382 = high_max - 0.382 * diff
            fib_500 = high_max - 0.5 * diff
            fib_618 = high_max - 0.618 * diff
            fib_786 = high_max - 0.786 * diff
            
            # -------------------------------
            # 3. Bollinger Bands (Volatility)
            # -------------------------------
            bb = ta.bbands(df['Close'], length=20, std=2)
            if bb is not None and not bb.empty:
                df = pd.concat([df, bb], axis=1)
                lower_bb = float(df[bb.columns[0]].iloc[-1])
                mid_bb = float(df[bb.columns[1]].iloc[-1])
                upper_bb = float(df[bb.columns[2]].iloc[-1])
            else:
                lower_bb, mid_bb, upper_bb = 0, 0, 0
            
            # -------------------------------
            # 4. Momentum (RSI & MACD)
            # -------------------------------
            df['RSI'] = ta.rsi(df['Close'], length=14)
            rsi = float(df['RSI'].iloc[-1]) if pd.notna(df['RSI'].iloc[-1]) else 50.0
            
            macd = ta.macd(df['Close'])
            if macd is not None and not macd.empty:
                df = pd.concat([df, macd], axis=1)
                macd_val = float(df[macd.columns[0]].iloc[-1])
                macd_sig = float(df[macd.columns[2]].iloc[-1])
            else:
                macd_val, macd_sig = 0, 0

            # -------------------------------
            # 5. Synthesis & Formatting
            # -------------------------------
            setup_type = "Swing Trade (Daily Data)" if interval == "1d" else "Intraday Scalp"
            
            vibe = "Neutral"
            if rsi > 70: 
                vibe = "Overbought (Bearish Bias)"
            elif rsi < 30: 
                vibe = "Oversold (Bullish Bias)"
            elif macd_val > macd_sig and close_price > mid_bb: 
                vibe = "Strong Bullish Momentum"
            elif macd_val < macd_sig and close_price < mid_bb: 
                vibe = "Strong Bearish Momentum"
            
            # Strategy Suggestion
            advice = "Hold and monitor."
            entry = 0.0
            target = 0.0
            stop = 0.0

            if rsi < 30 or close_price <= lower_bb:
                advice = "Deep value territory. High probability bounce setup."
                entry = close_price
                target = fib_500
                stop = low_min * 0.98
            elif rsi > 70 or close_price >= upper_bb:
                advice = "Overextended. High risk of mean-reversion pullback."
                entry = 0.0
                target = 0.0
            elif macd_val > macd_sig:
                advice = "Momentum is accelerating upwards. Trend following setup."
                entry = close_price
                target = upper_bb
                stop = fib_618
            
            return [
                {"label": "Analyzed Asset", "value": f"{symbol.upper()} @ INR {float(close_price):.2f}"},
                {"label": "Play Style", "value": setup_type},
                {"label": "Current Vibe", "value": f"{vibe} | RSI: {rsi:.1f}"},
                {"label": "Fibonacci Box (0.5 - 0.618)", "value": f"INR {fib_618:.2f} - INR {fib_500:.2f}"},
                {"label": "Volatility Bounds", "value": f"Floor: INR {lower_bb:.2f} | Ceiling: INR {upper_bb:.2f}"},
                {"label": "Mathematical Output", "value": advice}
            ]
            
        except Exception as e:
            return [{"label": "QUANT ERROR", "value": str(e)}]

if __name__ == "__main__":
    quant = QuantEngine()
    res = quant.analyze("ITC.NS")
    for r in res:
        print(f"{r['label']}: {r['value']}")
