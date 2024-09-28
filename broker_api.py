import os
import alpaca_trade_api as tradeapi
import json
import datetime
import pytz

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

        self.market_open_time = datetime.time(9, 30)
        self.market_close_time = datetime.time(16, 0)

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
        
    def get_ticker_price(self, ticker: str):
        try:
            trade = self.api.get_latest_trade(ticker)
            return trade.price
        except Exception as e:
            print(f"Failed to get ticker price for {ticker}: {e}")
    
    def get_positons(self): 
        current_position = []
        
        positions = self.api.list_positions()
        for position in positions: 
            current_position.append([position.symbol, position.qty, position.avg_entry_price, position.current_price, position.market_value])
            self.portfolio_value += float(position.market_value)
        return current_position
    
    def get_bp(self): 
        return self.api.get_account().buying_power
