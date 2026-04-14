import pandas as pd
import joblib
import os
import pandas_ta as ta
class Oracle:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        model_path = os.path.join(os.path.dirname(__file__), 'research', 'oracle_v1.pkl')
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print(f"Oracle model loaded from {model_path}")
            except Exception as e:
                print(f"Failed to load Oracle model: {e}")
        else:
            print(f"Oracle model not found at {model_path}")

    def get_oracle_prediction(self, stock_data):
        """
        Calculates features and returns the probability of UP (1).
        stock_data: DataFrame with columns ['Open', 'High', 'Low', 'Close']
        """
        if self.model is None:
            print("Oracle model not active.")
            return 0.0

        if len(stock_data) < 20: # Need enough data for SMA_10, RSI (14), Vol (10). Let's say 20 safe.
            print("Not enough data for Oracle features.")
            return 0.0

        # We need to calculate features for the LAST row to predict Tomorrow.
        # Features used in training: 'Open_Close', 'High_Low', 'SMA_5', 'SMA_10', 'RSI', 'Volatility'
        
        # Work on a copy to avoid SettingWithCopy warnings on the main df
        df = stock_data.copy()
        
        # Calculate Features
        df['Open_Close'] = df['Open'] - df['Close']
        df['High_Low'] = df['High'] - df['Low']
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['Volatility'] = df['Close'].rolling(window=10).std()
        df['Return'] = df['Close'].pct_change()
        df['Return_Lag1'] = df['Return']
        df['Return_Lag2'] = df['Return'].shift(1)

        # Get the last row (latest data)
        latest_data = df.iloc[[-1]][['Open_Close', 'High_Low', 'SMA_5', 'SMA_10', 'RSI', 'Volatility', 'Return_Lag1', 'Return_Lag2']]
        
        # Check if we have NaNs (e.g. if not enough data for SMA)
        if latest_data.isnull().values.any():
            return 0.0

        # Predict probability
        # classes_ are usually [0, 1]. So index 1 is 'Up'.
        try:
            probability = self.model.predict_proba(latest_data)[0][1]
        except Exception as e:
            print(f"Oracle prediction error: {e}")
            return 0.0
            
        return probability

# Global instance
oracle = Oracle()

def get_oracle_prediction(stock_data):
    return oracle.get_oracle_prediction(stock_data)
