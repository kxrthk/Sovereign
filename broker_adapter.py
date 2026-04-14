from abc import ABC, abstractmethod
import yfinance as yf
import pandas as pd

class BrokerAdapter(ABC):
    """
    Abstract Base Class for Broker Interactions.
    Ensures the Scout can switch between yfinance, SmartAPI, Dhan, etc.
    without changing the core logic.
    """
    @abstractmethod
    def fetch_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        pass

class YFinanceAdapter(BrokerAdapter):
    """
    Concrete implementation for Yahoo Finance (Research/Free Tier).
    """
    def fetch_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
        except Exception as e:
            print(f"YFinance Error on {symbol}: {e}")
            return pd.DataFrame()

# Factory to get the configured adapter
def get_broker_adapter(mode="research"):
    if mode == "research":
        return YFinanceAdapter()
    # elif mode == "smartapi":
    #     return SmartAPIAdapter()
    else:
        raise ValueError(f"Unknown Broker Mode: {mode}")
