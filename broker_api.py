import os
import alpaca_trade_api as tradeapi
import json
import datetime
import pytz
from datetime import timedelta
import yfinance as yf

def get_recent_weekdays():
        today = datetime.datetime.today().date()
        if today.weekday() == 5:
            today = today - timedelta(days=1)
            yesterday = today - timedelta(days=1)
        elif today.weekday() == 6:
            today = today - timedelta(days=2)
            yesterday = today - timedelta(days=1)
        elif today.weekday() == 0:
            yesterday = today - timedelta(days=3)
        else:
            yesterday = today - timedelta(days=1)

        return today, yesterday

class AlpacaBroker(): 
    def __init__(self, config_json : str): 
        with open(config_json, 'r') as file: 
            configs = json.load(file)
        
        self.url = configs['URL']
        self.api_key = configs['KEYS']
        self.secret_keys = configs['SECRET']
        
        self.api = tradeapi.REST(self.api_key, self.secret_keys, self.url, api_version='v2')
        
        self.positions = self.get_positons()
        self.portfolio_value = 0.0
        self.buying_power = self.get_bp()

        self.market_open_time = datetime.time(hour=9, minute=30)
        self.market_close_time = datetime.time(hour=16, minute=0)

    def is_market_open(self):
        current_time_utc = datetime.datetime.now(pytz.utc)
        
        us_eastern = pytz.timezone("US/Eastern")
        current_time_et = current_time_utc.astimezone(us_eastern).time()

        return self.market_open_time <= current_time_et <= self.market_close_time

    def buy_order(self, ticker: str, qty: float):
        if self.is_market_open():
            try:
                self.api.submit_order(
                    symbol=ticker,
                    qty=qty,
                    side="buy",
                    type="market",
                    time_in_force='gtc'
                )
                print(f"[INFO] Successfully purchased {qty} shares of {ticker}")
            except Exception as e:
                print(f"[ERROR] Failed to purchase {qty} shares of {ticker}: {e}")
        else:
            print("[INFO] Market is closed. Unable to execute buy order.")
    
    def sell_order(self, ticker : str, qty : float): 
        if self.is_market_open():
            try:
                self.api.submit_order(
                    symbol=ticker, 
                    qty=qty, 
                    side="sell", 
                    type="market", 
                    time_in_force="gtc"
                )
                print(f"[INFO] Successfully sold {qty} shares of {ticker}")
            except Exception as e:
                print(f"[ERROR] Failed to sell {qty} shares of {ticker}: {e}")
        else:
            print("[INFO] Market is closed. Unable to execute sell order.")

    def get_positons(self): 
        current_position = {}
        
        positions = self.api.list_positions()
        for position in positions: 
            current_position[position.symbol] = [position.qty, position.avg_entry_price, position.current_price, position.market_value]
            self.portfolio_value += float(position.market_value)
        return current_position
    
    def get_bp(self): 
        return self.api.get_account().buying_power

    def get_prices(self, ticker: str):
        """
        Retrieves yesterday's closing price and today's current price using yfinance.
        """
        today, yesterday = get_recent_weekdays()

        ticker_data = yf.Ticker(ticker)
        data = ticker_data.history(start=yesterday, end=today + timedelta(days=1))

        if len(data) < 2:
            print(f"[ERROR] Not enough data for {ticker}")
            return None, None

        yesterday_close = data['Close'].iloc[-2]
        today_close = data['Close'].iloc[-1]

        return yesterday_close, today_close, today_close/yesterday_close