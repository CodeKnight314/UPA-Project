import os
import alpaca_trade_api as tradeapi
import json
import datetime
import pytz
from upa_model import UPA, get_recent_closing_prices
import numpy as np 
from datetime import datetime, time

class AlpacaBroker(): 
    def __init__(self, config_json : str): 
        with open(config_json, 'r') as file: 
            configs = json.load(file)
        
        self.url = configs['URL']
        self.api_key = configs['KEYS']
        self.secret_keys = configs['SECRET']
        
        self.api = tradeapi.REST(self.api_key, self.secret_keys, self.url, api_version='v2')
        
        self.portfolio_value = 0.0
        
        self.model = UPA()
                
        self.positions = self.get_positons()
        self.buying_power = self.get_bp()

        self.market_open_time = time(hour=9, minute=30)
        self.market_close_time = time(hour=16, minute=0)

    def is_market_open(self):
        """
        Checks if the US stock market is currently open.

        Returns:
            bool: True if the market is open, False otherwise.
        """
        current_time_utc = datetime.now(pytz.utc)
        
        us_eastern = pytz.timezone("US/Eastern")
        current_time_et = current_time_utc.astimezone(us_eastern).time()

        return self.market_open_time <= current_time_et <= self.market_close_time

    def buy_order(self, ticker: str, dollars: float):
        """
        Places a buy order for the specified ticker and dollar amount.

        Arguments:
            ticker (str): The stock ticker symbol.
            dollars (float): The dollar amount to invest.
        """
        try:
            order_type = "market"
            time_in_force = "day"
        
            self.api.submit_order(
                symbol=ticker,
                notional=dollars,
                side="buy",
                type=order_type,
                time_in_force=time_in_force
            )
            print(f"[INFO] Successfully placed buy order for ${dollars} of {ticker}")
        except Exception as e:
            print(f"[ERROR] Failed to purchase ${dollars} of {ticker}: {e}")
    
    def sell_order(self, ticker: str, dollars: float):
        """
        Places a sell order for the specified ticker and dollar amount.

        Arguments:
            ticker (str): The stock ticker symbol.
            dollars (float): The dollar amount to sell.
        """
        try:
            order_type = "market"
            time_in_force = "day"

            self.api.submit_order(
                symbol=ticker,
                notional=dollars,
                side="sell",
                type=order_type,
                time_in_force=time_in_force
            )
            print(f"[INFO] Successfully placed sell order for ${dollars} of {ticker}")
        except Exception as e:
            print(f"[ERROR] Failed to sell ${dollars} of {ticker}: {e}")

    def get_positons(self): 
        """
        Retrieves the current positions in the portfolio.

        Returns:
            dict: A dictionary of positions where keys are ticker symbols and 
                  values are lists containing quantity, average entry price, 
                  current price, and market value.
        """
        current_position = {}
        
        positions = self.api.list_positions()
        if len(positions) == 0 and float(self.api.get_account().cash) > 0:
            avg_investment_price = int(self.api.get_account().cash) / len(self.model.ticker)
            for ticker in self.model.ticker: 
                self.buy_order(ticker, avg_investment_price)
            positions = self.api.list_positions()

        for position in positions: 
            current_position[position.symbol] = [float(position.qty), float(position.avg_entry_price), float(position.current_price), float(position.market_value)]
            self.portfolio_value += float(position.market_value)        
                
        return current_position

    def get_price(self, ticker): 
        """
        Fetches the latest price for a given ticker.

        Arguments:
            ticker (str): The stock ticker symbol.

        Returns:
            float: The latest price of the stock.
        """
        return float(self.api.get_latest_trade(ticker).price)

    def adjust_portfolio(self): 
        """
        Adjusts the portfolio based on the UPA model's recommendations.

        This method calculates the desired portfolio weights using the UPA model,
        compares them to the current weights, and places buy/sell orders 
        to rebalance the portfolio accordingly.
        """
        current_position = self.get_positons()
        self.model.get_portfolio_weights(current_position)
        recent_prices, previous_prices = get_recent_closing_prices(self.model.ticker)
        old, new = self.model.adjust_portfolio_weights(recent_prices, previous_prices)
        
        diff = new - old
        for i, ticker in enumerate(self.model.ticker): 
            amount = abs(round(diff[i] * current_position[ticker][0] * self.get_price(ticker), 2))
            if amount < 1.0:
                amount = 0
                
            if(diff[i] < 0 and amount >= 1): 
                self.sell_order(ticker, amount)
            elif(diff[i] > 0 and amount >= 1): 
                self.buy_order(ticker, amount)
            else: 
                continue
            
        os.system('cls' if os.name == 'nt' else 'clear')
        now = datetime.now()
        formatted = now.strftime("%Y-%m-%d %H:%M:%S")
        print(formatted)
        print("\nPortfolio Weight Changes:")
        print("------------------------")
        for ticker, old_w, new_w in zip(self.model.ticker, old, new):
            change = (new_w - old_w) * 100
            print(f"{ticker}: {old_w:.4f} -> {new_w:.4f} (Change: {change:+.2f}%)")
        
        print("\nPortfolio Statistics:")
        print("-------------------")
        print(f"Sum of weights: {np.sum(new):.4f}")
        print(f"Min weight: {np.min(new):.4f}")
        print(f"Max weight: {np.max(new):.4f}")
        print(f"Std dev of weights: {np.std(new):.4f}")
    
    def get_bp(self): 
        return self.api.get_account().buying_power

    def get_portfolio_value(self):
        """
        Retrieves the most updated portfolio value.
        """
        self.portfolio_value = 0.0
        self.positions = self.get_positons()
        return self.portfolio_value
    
if __name__ == "__main__": 
    api = AlpacaBroker("configs.json")
    api.get_positons()
    api.adjust_portfolio()