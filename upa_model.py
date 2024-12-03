import yfinance as yf
from typing import Union
import numpy as np

class UPA():
    def __init__(self):
        self.ticker = ["CCCS", "DSP", "ADEA", "RELY", "GDYN", "CLBT", "TTMI", "ACMR", "SATS", "GEN", "CRDO", "AOSL", "VERX", "TENB", "RMBS", "SCSC", "INTA", "ACIW", "CSCO", "NTNX"]

    def get_portfolio_weights(self, portfolio: Union[None, dict]):  
        if portfolio == None: 
            self.portfolio_weights = np.array([1/len(self.ticker) for _ in range(len(self.ticker))])
        else: 
            total_value = 0.0
            self.portfolio_weights = []
            for ticker in self.ticker: 
                total_value += portfolio[ticker][3]
                self.portfolio_weights.append(portfolio[ticker][3])
            self.portfolio_weights = np.array(self.portfolio_weights) / total_value
    
    def adjust_portfolio_weights(self, current_price: dict, last_price: dict): 
        """
        Adjust portfolio weights using Universal Portfolio Algorithm
        Implementation based on Cover's original paper using exponential gradient updates
        """
        old_weights = np.array(self.portfolio_weights)
        price_relatives = np.array([current_price[ticker]/last_price[ticker] for ticker in self.ticker])
        num_assets = len(self.ticker)
        
        log_returns = np.log(price_relatives)
        
        numerator = old_weights * np.exp(log_returns)
        new_weights = numerator / np.sum(numerator)
        
        epsilon = 1e-3
        new_weights = (1 - epsilon) * new_weights + epsilon * (1/num_assets)
        
        new_weights = np.maximum(new_weights, 0)
        new_weights = new_weights / np.sum(new_weights)
        
        self.portfolio_weights = new_weights
        return new_weights, old_weights

def get_recent_closing_prices(tickers):
    """
    Fetches the most recent and second most recent closing prices for a list of tickers.
    """
    recent_closing_prices = {}
    previous_closing_prices = {}

    for ticker in tickers:
        try:
            data = yf.download(ticker, period="5d")['Close']
            recent_closing_prices[ticker] = round(data.iloc[-1].item(), 3)
            previous_closing_prices[ticker] = round(data.iloc[-2].item(), 3)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    return recent_closing_prices, previous_closing_prices

if __name__ == "__main__":
    model = UPA()
    tickers = model.ticker
    model.get_portfolio_weights(None)
    recent_prices, previous_prices = get_recent_closing_prices(tickers)
    new, old = model.adjust_portfolio_weights(recent_prices, previous_prices)
    
    print("\nPortfolio Weight Changes:")
    print("------------------------")
    for ticker, old_w, new_w in zip(tickers, old, new):
        change = (new_w - old_w) * 100
        print(f"{ticker}: {old_w:.4f} -> {new_w:.4f} (Change: {change:+.2f}%)")
    
    print("\nPortfolio Statistics:")
    print("-------------------")
    print(f"Sum of weights: {np.sum(new):.4f}")
    print(f"Min weight: {np.min(new):.4f}")
    print(f"Max weight: {np.max(new):.4f}")
    print(f"Std dev of weights: {np.std(new):.4f}")