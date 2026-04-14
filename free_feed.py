import asyncio
import traceback
import json
import yfinance as yf
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

# In-memory track of active websocket connections per ticker
active_connections: dict[str, list[WebSocket]] = {}

async def register_connection(websocket: WebSocket, ticker: str):
    await websocket.accept()
    if ticker not in active_connections:
        active_connections[ticker] = []
    active_connections[ticker].append(websocket)
    print(f"[LIVE FEED] Client Connected to {ticker} pipeline.")
    
    # Immediately send the last 5 days of 5-minute intraday history 
    # as the foundation for the chart
    try:
        data = yf.download(ticker, period="5d", interval="5m", progress=False)
        history = []
        
        # yfinance returns a MultiIndex if multiple tickers, but we request one
        # Handle the DataFrame structure
        for index, row in data.iterrows():
            history.append({
                "time": int(index.timestamp()),
                "open": float(row['Open'].iloc[0]) if hasattr(row['Open'], 'iloc') else float(row['Open']),
                "high": float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High']),
                "low": float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low']),
                "close": float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close']),
            })
            
        await websocket.send_json({
            "type": "history",
            "data": history
        })
        print(f"[LIVE FEED] Sent {len(history)} historical candles for {ticker}.")
        
    except Exception as e:
        print(f"[LIVE FEED ERROR] Failed to fetch initial history for {ticker}: {e}")
        traceback.print_exc()

async def unregister_connection(websocket: WebSocket, ticker: str):
    if ticker in active_connections:
        try:
            active_connections[ticker].remove(websocket)
            print(f"[LIVE FEED] Client disconnected from {ticker}.")
        except ValueError:
            pass

async def stream_live_data():
    """
    Background worker that runs continuously.
    It simulates a high-frequency websocket feed by pulling the latest
    intraday minute data from yfinance and pushing it to all connected React clients.
    """
    print("[LIVE FEED] God-Level Websocket engine initialized.")
    while True:
        try:
            if not active_connections:
                await asyncio.sleep(2)
                continue
                
            # Iterate through all tickers that have active watchers
            for ticker, clients in list(active_connections.items()):
                if not clients:
                    continue
                    
                # Fetch the absolutely latest 1-minute candle
                data = yf.download(ticker, period="1d", interval="1m", progress=False)
                if not data.empty:
                    latest = data.iloc[-1]
                    
                    tick_payload = {
                        "type": "tick",
                        "data": {
                            "time": int(data.index[-1].timestamp()),
                            "open": float(latest['Open'].iloc[0]) if hasattr(latest['Open'], 'iloc') else float(latest['Open']),
                            "high": float(latest['High'].iloc[0]) if hasattr(latest['High'], 'iloc') else float(latest['High']),
                            "low": float(latest['Low'].iloc[0]) if hasattr(latest['Low'], 'iloc') else float(latest['Low']),
                            "close": float(latest['Close'].iloc[0]) if hasattr(latest['Close'], 'iloc') else float(latest['Close']),
                        }
                    }
                    
                    # Push directly to React
                    disconnected_clients = []
                    for client in clients:
                        try:
                            await client.send_json(tick_payload)
                        except WebSocketDisconnect:
                            disconnected_clients.append(client)
                        except Exception as e:
                            print(f"[LIVE FEED] Error sending tick: {e}")
                            disconnected_clients.append(client)
                            
                    # Clean up strictly disconnected clients
                    for c in disconnected_clients:
                        await unregister_connection(c, ticker)
                        
            # Wait 5 seconds before checking the market again
            # Note: yfinance free data only updates about once a minute in reality,
            # but this effectively mimics a real-time WebSocket connection to the front end.
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[LIVE FEED ERROR] Main loop crashed: {e}")
            await asyncio.sleep(5)
