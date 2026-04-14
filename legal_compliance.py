import datetime

class ComplianceOfficer:
    """
    The Compliance Officer: Enforces regulatory limits and internal safety rules.
    Primary Rule: KILL SWITCH - Max 3 trades per day.
    """
    MAX_DAILY_TRADES = 3

    @staticmethod
    def check_daily_limits(todays_trade_count):
        """
        Checks if the bot has exceeded the maximum allowed trades for the day.
        Returns: True if safe to trade, False if limit reached.
        """
        if todays_trade_count >= ComplianceOfficer.MAX_DAILY_TRADES:
            print(f"COMPLIANCE ALERT: Daily Limit Reached ({todays_trade_count}/{ComplianceOfficer.MAX_DAILY_TRADES}). STOPPING.")
            return False
        
        return True

    @staticmethod
    def is_market_open():
        """
        Checks if the current time is within market hours (9:15 AM - 3:30 PM).
        (Optional for now, but good for future strictness)
        """
        now = datetime.datetime.now().time()
        market_start = datetime.time(9, 15)
        market_end = datetime.time(15, 30)
        return market_start <= now <= market_end
