# import yfinance as yf (Removed)
import pandas as pd
import pandas_ta as ta
import time
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from broker_adapter import get_broker_adapter

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Initialize Broker Adapter
broker = get_broker_adapter(mode="research")

# Configure Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# --- CONFIGURATION (The Scout's Mission Parameters) ---
SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LICI.NS",
    "HINDUNILVR.NS", "TATASTEEL.NS", "BAJFINANCE.NS", "ADANIENT.NS",
    "SUNPHARMA.NS", "MARUTI.NS", "TITAN.NS", "AXISBANK.NS", "ASIANPAINT.NS",
    "ULTRACEMCO.NS", "WIPRO.NS", "POWERGRID.NS", "NTPC.NS", "M&M.NS",
    "HCLTECH.NS", "JSWSTEEL.NS", "TATASTEELL.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "ONGC.NS", "GRASIM.NS", "BAJAJFINSV.NS", "TECHM.NS", "HINDALCO.NS",
    "LT.NS", "NESTLEIND.NS", "DIVISLAB.NS", "DRREDDY.NS", "CIPLA.NS",
    "TATAMOTORS.NS", "BEL.NS", "HAL.NS", "INDUSINDBK.NS", "BPCL.NS",
    "HEROMOTOCO.NS", "EICHERMOT.NS", "APOLLOHOSP.NS", "SBILIFE.NS",
    "BRITANNIA.NS", "TATACONSUM.NS", "ADANIPOWER.NS", "VGUARD.NS", "NHPC.NS",
    "LODHA.NS", "DLF.NS", "OBEROIRLTY.NS", "GODREJPROP.NS", "PHOENIXLTD.NS",
    "PRESTIGE.NS", "BRIGADE.NS", "SOBHA.NS", "BOSCHLTD.NS", "MRF.NS", "PAGEIND.NS",
    "ABB.NS", "SIEMENS.NS", "TRENT.NS", "ZOMATO.NS", "PAYTM.NS", "NYKAA.NS",
    "POLICYBZR.NS", "DELHIVERY.NS", "MOTHERSON.NS", "TVSMOTOR.NS", "CHOLAFIN.NS",
    "SHRIRAMFIN.NS", "BAJAJHLDNG.NS", "ICICIGI.NS", "HDFCLIFE.NS",
    "MAXHEALTH.NS", "SYNGENE.NS", "PIIND.NS", "UPL.NS", "SRF.NS", "NAVINFLUOR.NS",
    "DEXUS.NS", "ETERNAL.NS"
]

def analyze_stock(symbol, lenient=False):
    """
    The Scout's Eyes: Checks Sovereign Rules (SMA200 + RSI).
    Returns a dictionary of data if a match is found, else None.
    """
    try:
        # Use Broker Adapter to fetch data
        df = broker.fetch_data(symbol)
        
        if len(df) < 200: return None
        
        # Calculate Sovereign Indicators
        # Adapter handles MultiIndex cleaning
        
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last_row = df.iloc[-1]
        price = last_row['Close']
        sma = last_row['SMA200']
        rsi = last_row['RSI']
        
        # Strategy: Bullish Trend (Price > SMA200) + Pullback (RSI 40-50)
        if lenient:
            # Loosened requirements to guarantee mandatory trades: Price > SMA*0.95 and RSI 35-65
            condition = (price > sma * 0.95) and (35 <= rsi <= 65)
        else:
            condition = (price > sma) and (40 <= rsi <= 50)
            
        # Note: We return the FULL DF because the Oracle needs history for features.
        if condition:
            return {
                "symbol": symbol,
                "price": round(price, 2),
                "rsi": round(rsi, 2),
                "timestamp": str(datetime.now()),
                "data": df  # Pass the full dataframe for the Oracle
            }
        return None
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None

def fetch_and_scan(lenient=False):
    """
    The Scout's Mission: Scans all symbols and yields candidates.
    If lenient is True, widens scan parameters to find more candidates.
    """
    mode_text = "LENIENT" if lenient else "STRICT"
    print(f"SCOUT: Starting market scan... ({mode_text} MODE)")
    candidates = []
    
    for s in SYMBOLS:
        try:
            res = analyze_stock(s, lenient=lenient)
            if res:
                print(f"SCOUT: Match found - {s} (RSI: {res['rsi']})")
                logging.info(f"match found for {s} - {mode_text}")
                candidates.append(res)
            
            # Rate limit to be polite
            time.sleep(0.5)
            
        except Exception as e:
            print(f"SCOUT: Failed on {s}: {e}")
            logging.error(f"Error processing {s}: {e}")
            
    print(f"SCOUT: Mission Complete. Found {len(candidates)} candidates.")
    return candidates

if __name__ == "__main__":
    # Test Run
    fetch_and_scan()
