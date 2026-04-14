# tax_engine.py
# Updated for Indian Union Budget 2025-26

# --- GOVERNMENT & EXCHANGE RATES ---
STT_RATE = 0.001          # 0.1% on Buy & Sell (Equity Delivery)
STAMP_DUTY_RATE = 0.00015 # 0.015% on Buy only
EXCHANGE_TXN_NSE = 0.0000345 # 0.00345% (NSE Transaction Charge)
SEBI_TURNOVER_FEE = 0.000001 # 0.0001% (SEBI Fee)
GST_RATE = 0.18           # 18% GST on Svc Charges (Not on Capital)
STCG_TAX_RATE = 0.20      # 20% Tax on Net Profit

# --- BROKER SPECIFIC (Dhan / Discount Brokers) ---
DP_CHARGE_SELL = 12.50    # Approx ₹12.50 + GST per Sell Order (CDSL/NSDL)
BROKERAGE = 0.0           # Zero Brokerage for Delivery

def calculate_taxes(buy_price, sell_price, qty):
    """
    Returns a breakdown of all taxes and net profit.
    """
    turnover_buy = buy_price * qty
    turnover_sell = sell_price * qty
    
    # 1. Securities Transaction Tax (STT) - 0.1% on Both
    stt = (turnover_buy * STT_RATE) + (turnover_sell * STT_RATE)
    
    # 2. Stamp Duty - 0.015% on Buy Only
    stamp_duty = turnover_buy * STAMP_DUTY_RATE
    
    # 3. Exchange Transaction Charges
    txn_charge = (turnover_buy + turnover_sell) * EXCHANGE_TXN_NSE
    
    # 4. SEBI Turnover Fees
    sebi_fee = (turnover_buy + turnover_sell) * SEBI_TURNOVER_FEE
    
    # 5. GST (18% on Txn Charge + SEBI Fee + Brokerage)
    # Note: STT and Stamp Duty are exempt from GST
    gst = (txn_charge + sebi_fee + BROKERAGE) * GST_RATE
    
    # 6. DP Charges (Applied only on Sell side)
    # Applied only if selling (turnover_sell > 0)
    dp_charge_with_gst = 0.0
    if turnover_sell > 0:
        dp_charge_with_gst = DP_CHARGE_SELL * 1.18
    
    total_charges = stt + stamp_duty + txn_charge + sebi_fee + gst + dp_charge_with_gst
    
    # --- PROFIT CALCULATION ---
    gross_profit = turnover_sell - turnover_buy
    net_realized_profit = gross_profit - total_charges
    
    # 7. Income Tax (STCG) - 20% only if we made a profit
    tax_bill = 0.0
    if net_realized_profit > 0:
        tax_bill = net_realized_profit * STCG_TAX_RATE
        final_pocket_profit = net_realized_profit - tax_bill
    else:
        final_pocket_profit = net_realized_profit # Loss remains loss
        
    return {
        "gross_profit": round(gross_profit, 2),
        "total_charges": round(total_charges, 2),
        "net_profit_pre_tax": round(net_realized_profit, 2),
        "stcg_tax": round(tax_bill, 2),
        "final_money_in_hand": round(final_pocket_profit, 2)
    }

def get_breakeven_price(buy_price, qty):
    """
    Finds the minimum sell price to not lose money.
    """
    if qty <= 0: return buy_price # Avoid infinite loop or errors
    
    # Simple iteration to find price where net_profit_pre_tax >= 0
    sell_price = buy_price * 1.001 # Start at 0.1% gain
    
    # Limit iterations to avoid infinite loop
    max_iter = 10000
    for _ in range(max_iter):
        res = calculate_taxes(buy_price, sell_price, qty)
        if res['net_profit_pre_tax'] > 0:
            return round(sell_price, 2)
        sell_price += 0.05 # Increment by 5 paise
        
    return round(sell_price, 2) # Return best guess if loop exhausts

def get_target_price(buy_price, qty, target_net_percent=0.05):
    """
    Finds the exact Sell Price needed to achieve a Net Profit of X% on Capital.
    Formula: Net Profit (Pocket) = (Buy * Qty) * target_net_percent
    """
    if qty <= 0 or buy_price <= 0: return 0
    
    invested_capital = buy_price * qty
    desired_net_profit = invested_capital * target_net_percent
    
    # Start search from a reasonable point (Buy + Desired% + Approx Tax Buffer)
    # Taxes are around 0.2% turnover + 20% profit tax.
    # Gross gain needed is roughly Desired / 0.8 (to cover 20% tax) + small friction
    
    start_price = buy_price * (1 + target_net_percent/0.8) 
    sell_price = start_price
    
    # Iterate with precision
    max_iter = 10000
    step = 0.05 # 5 paise
    
    for _ in range(max_iter):
        res = calculate_taxes(buy_price, sell_price, qty)
        if res['final_money_in_hand'] >= desired_net_profit:
            return round(sell_price, 2)
        sell_price += step
        
    return round(sell_price, 2)
