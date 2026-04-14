import json
import os
import random
from datetime import datetime
import config

class SmartMoneyTracker:
    def __init__(self):
        self.data_file = "memories/smart_money.json"

    def fetch_institutional_flows(self):
        """
        Simulates fetching FII (Foreign Institutional) and DII (Domestic Institutional) flows.
        In a production environment, this would scrape NSE bulk deals or a financial API.
        """
        # Simulated recent flows (Positive = Buying, Negative = Selling in Crores INR)
        # We tie this to sectors roughly represented by the Sovereign Six
        simulated_flows = {
            "timestamp": str(datetime.now()),
            "FII_net": random.randint(-5000, 5000), # Net FII flow today
            "DII_net": random.randint(-5000, 5000), # Net DII flow today
            "sector_flows": {
                "FMCG": random.uniform(-1.0, 1.0),    # ITC
                "METALS": random.uniform(-1.0, 1.0),  # TATASTEEL
                "ENERGY": random.uniform(-1.0, 1.0),  # ONGC
                "POWER": random.uniform(-1.0, 1.0),   # NTPC, POWERGRID
                "DEFENCE": random.uniform(-1.0, 1.0), # BEL
                "AUTO": random.uniform(-1.0, 1.0)     # ASHOKLEY
            },
            "block_deals": self.simulate_block_deals()
        }
        
        self.save_flows(simulated_flows)
        return simulated_flows

    def simulate_block_deals(self):
        deals = []
        # Randomly generate 0-2 block deals for our watchlist today
        num_deals = random.randint(0, 2)
        watch_copy = list(config.SOVEREIGN_SIX)
        random.shuffle(watch_copy)
        
        for i in range(num_deals):
             if not watch_copy: break
             sym = watch_copy.pop()
             action = random.choice(["BUY", "SELL"])
             size = random.randint(500000, 5000000) # 500k to 5M shares
             deals.append({
                 "symbol": sym,
                 "entity": "Unknown Fund",
                 "action": action,
                 "quantity": size
             })
        return deals

    def save_flows(self, data):
        os.makedirs("memories", exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    def analyze_bias(self):
        """Returns the institutional bias for the market and specific assets."""
        flows = self.fetch_institutional_flows()
        
        net_flow = flows["FII_net"] + flows["DII_net"]
        market_bias = "BULLISH" if net_flow > 1000 else "BEARISH" if net_flow < -1000 else "NEUTRAL"
        
        # Calculate specific stock biases based on block deals
        stock_biases = {}
        for deal in flows["block_deals"]:
             score = 0.5 if deal["action"] == "BUY" else -0.5
             stock_biases[deal["symbol"]] = stock_biases.get(deal["symbol"], 0) + score
             
        # Add sector flow influence
        sector_map = {
            'ITC.NS': 'FMCG',
            'TATASTEEL.NS': 'METALS',
            'ONGC.NS': 'ENERGY',
            'NTPC.NS': 'POWER',
            'POWERGRID.NS': 'POWER',
            'BEL.NS': 'DEFENCE',
            'ASHOKLEY.NS': 'AUTO'
        }
        
        for sym in config.SOVEREIGN_SIX:
             sector = sector_map.get(sym)
             if sector:
                  sector_score = flows["sector_flows"].get(sector, 0)
                  # Sector score represents -1 to 1, let's scale it slightly
                  stock_biases[sym] = stock_biases.get(sym, 0) + (sector_score * 0.3)
                  
        return {
             "market_bias": market_bias,
             "net_flow_cr": net_flow,
             "stock_biases": stock_biases,
             "block_deals": flows["block_deals"]
        }

if __name__ == "__main__":
    tracker = SmartMoneyTracker()
    result = tracker.analyze_bias()
    print("SMART MONEY FLOWS:")
    print(json.dumps(result, indent=4))
