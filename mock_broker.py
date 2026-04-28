import json
import os
import datetime
import tax_engine
import uuid
import csv

MEMORY_PATH = "memories/bot_brain.json"
PAPER_TRADES_PATH = "memories/paper_trades.json"
JOURNAL_PATH = "trading_journal.csv"
HISTORY_PATH = "memories/account_history.csv"

class MockDhanClient:
    """
    Simulates the DhanHQ API for Paper Trading.
    Manages a virtual wallet and records fake trades.
    """
    def __init__(self):
        self._ensure_memory()
        
    def _ensure_memory(self):
        # 1. Ensure Paper Trades File
        if not os.path.exists(PAPER_TRADES_PATH):
            os.makedirs("memories", exist_ok=True)
            with open(PAPER_TRADES_PATH, 'w') as f:
                json.dump([], f)
                
        # 2. Ensure Bot Brain (Wallet)
        if not os.path.exists(MEMORY_PATH):
            os.makedirs("memories", exist_ok=True)
            with open(MEMORY_PATH, 'w') as f:
                json.dump({"wallet_balance": 100000.0}, f) # Start with 1L
        else:
            # Check if wallet exists, if not init
            with open(MEMORY_PATH, 'r+') as f:
                try:
                    data = json.load(f)
                except:
                    data = {}
                
                if "wallet_balance" not in data:
                    data["wallet_balance"] = 100000.0
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()

    def get_fund_balance(self):
        """Returns virtual wallet balance."""
        with open(MEMORY_PATH, 'r') as f:
            data = json.load(f)
        return data.get("wallet_balance", 0.0)

    def get_positions(self):
        """Returns list of all raw paper trades."""
        with open(PAPER_TRADES_PATH, 'r') as f:
            return json.load(f)

    def get_net_positions(self):
        """Returns aggregated open positions: {symbol: {'quantity': net_qty, 'avg_price': avg_price}}"""
        if not os.path.exists(PAPER_TRADES_PATH): return {}
        with open(PAPER_TRADES_PATH, 'r') as f:
             trades = json.load(f)
             
        pos = {}
        for t in trades:
             sym = t['symbol']
             if sym not in pos:
                 pos[sym] = {'quantity': 0, 'avg_price': 0.0, 'total_cost': 0.0}
                 
             qty = t.get('quantity', 0)
             price = t.get('avg_price', t.get('price', 0))
             if t.get('action') == 'BUY':
                 pos[sym]['total_cost'] += qty * price
                 pos[sym]['quantity'] += qty
             elif t.get('action') == 'SELL':
                 pos[sym]['total_cost'] -= qty * price
                 pos[sym]['quantity'] -= qty
                 
             if pos[sym]['quantity'] > 0:
                 pos[sym]['avg_price'] = pos[sym]['total_cost'] / pos[sym]['quantity']
             else:
                 pos[sym]['avg_price'] = 0.0
                 pos[sym]['total_cost'] = 0.0
                 
        return {k: v for k, v in pos.items() if v['quantity'] > 0}

    def place_order(self, symbol, quantity, action, price):
        """
        Simulates placing an order.
        Updates wallet balance and records trade.
        DEDUCTS TAXES (Realism Mode).
        """
        # Calculate Taxes
        if action == "BUY":
            # Buy Side Taxes (Sell Price=0)
            charges_breakdown = tax_engine.calculate_taxes(price, 0, quantity)
            total_charges = charges_breakdown['total_charges']
            
            stock_cost = quantity * price
            total_cost = stock_cost + total_charges
            
            # Load Memory
            with open(MEMORY_PATH, 'r') as f:
                brain = json.load(f)
            
            balance = brain.get("wallet_balance", 0.0)
            
            if balance >= total_cost:
                balance -= total_cost
                brain["wallet_balance"] = balance
                
                # Generate Digital Receipt (The Proof)
                order_id = f"ORD-{uuid.uuid4().hex[:4].upper()}-{symbol}"
                
                # Record Trade
                trade = {
                    "order_id": order_id,
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": price,
                    "action": "BUY",
                    "timestamp": str(datetime.datetime.now()),
                    "status": "OPEN",
                    "taxes_paid": total_charges
                }
                
                with open(PAPER_TRADES_PATH, 'r+') as tf:
                    trades = json.load(tf)
                    trades.append(trade)
                    tf.seek(0)
                    json.dump(trades, tf, indent=4)
                
                # Update Wallet
                with open(MEMORY_PATH, 'w') as bf:
                    json.dump(brain, bf, indent=4)

                # Log to Account History (Real-time Equity Curve)
                today_str = datetime.datetime.now().strftime("%b %d")
                hist_exists = os.path.isfile(HISTORY_PATH)
                with open(HISTORY_PATH, 'a', newline='') as hf:
                    writer = csv.writer(hf)
                    if not hist_exists:
                        writer.writerow(['date', 'equity'])
                    writer.writerow([today_str, balance])

                # Log to CSV (Permanent Record)
                file_exists = os.path.isfile(JOURNAL_PATH)
                with open(JOURNAL_PATH, 'a', newline='') as csvfile:
                    fieldnames = ['timestamp', 'order_id', 'symbol', 'action', 'price', 'quantity', 'taxes', 'total_cost']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow({
                        'timestamp': trade['timestamp'],
                        'order_id': order_id,
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': price,
                        'quantity': quantity,
                        'taxes': total_charges,
                        'total_cost': total_cost
                    })
                    
                print(f"MOCK BROKER: Bought {quantity} {symbol} @ {price}. Receipt: {order_id}")
                return {"status": "success", "message": "Paper Order Placed", "order_id": order_id}
            else:
                print(f"MOCK BROKER: Insufficient Funds ({balance} < {total_cost})")
                return {"status": "error", "message": f"Insufficient funds. Need ₹{total_cost:,.2f}, wallet has ₹{balance:,.2f}"}
        elif action == "SELL":
             # Sell Side Taxes
            charges_breakdown = tax_engine.calculate_taxes(price, price, quantity) # Simplified
            total_charges = charges_breakdown['total_charges']
            
            stock_value = quantity * price
            net_credit = stock_value - total_charges
            
            # Load Memory
            with open(MEMORY_PATH, 'r') as f:
                brain = json.load(f)
            
            balance = brain.get("wallet_balance", 0.0)
            balance += net_credit # Add to wallet
            brain["wallet_balance"] = balance
            
            # Digital Receipt
            order_id = f"ORD-{uuid.uuid4().hex[:4].upper()}-{symbol}"
            
            # Record Trade
            trade = {
                "order_id": order_id,
                "symbol": symbol,
                "quantity": quantity,
                "avg_price": price,
                "action": "SELL",
                "timestamp": str(datetime.datetime.now()),
                "status": "OPEN",
                "taxes_paid": total_charges
            }
            
            with open(PAPER_TRADES_PATH, 'r+') as tf:
                trades = json.load(tf)
                trades.append(trade)
                tf.seek(0)
                json.dump(trades, tf, indent=4)
            
            # Update Wallet
            with open(MEMORY_PATH, 'w') as bf:
                json.dump(brain, bf, indent=4)

            # Log to Account History
            today_str = datetime.datetime.now().strftime("%b %d")
            hist_exists = os.path.isfile(HISTORY_PATH)
            with open(HISTORY_PATH, 'a', newline='') as hf:
                writer = csv.writer(hf)
                if not hist_exists:
                    writer.writerow(['date', 'equity'])
                writer.writerow([today_str, balance])
                
            # Log to CSV
            file_exists = os.path.isfile(JOURNAL_PATH)
            with open(JOURNAL_PATH, 'a', newline='') as csvfile:
                fieldnames = ['timestamp', 'order_id', 'symbol', 'action', 'price', 'quantity', 'taxes', 'total_cost']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                     writer.writeheader()
                writer.writerow({
                    'timestamp': trade['timestamp'],
                    'order_id': order_id,
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': price,
                    'quantity': quantity,
                    'taxes': total_charges,
                    'total_cost': -net_credit # Negative cost = credit
                })
                
            print(f"MOCK BROKER: Sold {quantity} {symbol} @ {price}. Receipt: {order_id}")
            return {"status": "success", "message": "Paper Order Placed", "order_id": order_id}

        return {"status": "failure", "message": "Not Implemented"}
