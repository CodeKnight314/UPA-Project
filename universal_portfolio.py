from broker_api import AlpacaBroker
import alpaca_trade_api as tradeapi
import os

class model():
    def __init__(self, output_dir : str, config_json : str):
        self.broker = AlpacaBroker(config_json=config_json)

        self.output_dir = output_dir
        self.output_logs = os.path.join(self.output_dir, "UPA_TransactionLogs.txt")
        
        self.ticker = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'TSLA', 'ADBE', 'CSCO', 'SQ', 'NET']
        
        stock_prices = [self.broker.get_prices(ticker) for ticker  in self.ticker]
        self.yester_close = [ticker[0] for ticker in stock_prices]
        self.today_close = [ticker[1] for ticker in stock_prices]
        self.price_change = [ticker[2] for ticker in stock_prices]
        self.current_value = [self.broker.positions[ticker][0] for ticker in self.ticker]
        
        self.weights = self.weight_allocation()
        
    def weight_allocation(self):
        if(os.path.isfile(self.output_logs)):
            with open(self.output_logs, 'r') as f:
                line = f.readline().split(" ")
            weights = [int(stock) for stock in line] 
        else:
            weights = [1/len(self.ticker) for _ in range(len(self.ticker))]
            
        return weights
    
    def weight_adjustment(self):
        new_weights = []
        sum = 0.0
        
        for weight, price_ratio in zip(self.weights, self.price_change):
            new_weight = weight * price_ratio
            new_weights.append(new_weight)
            sum+=new_weight
        
        new_weights = [round(new_weight/sum, 5) for new_weight in new_weights]
        
        portfolio_value = self.broker.portfolio_value
        
        self.target_value = [weight * portfolio_value for weight in new_weights]
        
        operation = [(target - current)/(current) for target, current in zip(self.target_value, self.current_value)]
        
        for ticker, op in zip(self.ticker, operation):
            if(op > 0):
                self.broker.buy(ticker, op)
            else: 
                self.broker.sell(ticker, op)
                
        file = open(self.output_logs, "w")
        for weight, ticker in zip(new_weights, self.ticker):
            file.write(f"{weight} ")
        file.close()
    
if __name__ == "__main__":
    upa = model("fuck", "/Users/richardtang/Desktop/UPA-Project/configs.json")
    print(upa.yester_close)
    print(upa.today_close)
    print(upa.weights)
    upa.weight_adjustment()
    print(upa.new_weights)
    