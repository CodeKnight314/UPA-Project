from broker_api import AlpacaBroker
import alpaca_trade_api as tradeapi
import os
import time

class UPA():
    def __init__(self, output_dir: str, config_json: str):
        self.broker = AlpacaBroker(config_json=config_json)

        self.output_dir = output_dir
        self.output_logs = os.path.join(self.output_dir, "UPA_TransactionLogs.txt")

        self.ticker = ['DOCU', 'FSLY', 'GOCO', 'MDB', 'NET', 'PLTR', 'PTON', 'ROKU', 'SHOP', 'SNOW', 'SQ', 'TDOC', 'TTD', 'TWLO', 'NVDA']

        stock_prices = [self.broker.get_prices(ticker) for ticker in self.ticker]

        self.yester_close = [ticker[0] for ticker in stock_prices]
        self.today_close = [ticker[1] for ticker in stock_prices]
        self.price_change = [ticker[2] for ticker in stock_prices]

        self.current_qty = [float(self.broker.positions[ticker][0]) if ticker in self.broker.positions else 0 
                            for ticker in self.ticker]
        self.current_value = [price * qty for price, qty in zip(self.today_close, self.current_qty)]
        self.current_price = self.today_close
        self.weights = [value / self.broker.portfolio_value if self.broker.portfolio_value != 0 else 0 for value in self.current_value]

    def weight_allocation(self):
        if os.path.isfile(self.output_logs):
            with open(self.output_logs, 'r') as f:
                line = f.readline().split(" ")
            weights = [float(stock) for stock in line]
        else:
            weights = [1 / len(self.ticker) for _ in range(len(self.ticker))]

        return weights

    def weight_adjustment(self):
        self.weights = [value / self.broker.portfolio_value if self.broker.portfolio_value != 0 else 0 for value in self.current_value]
        new_weights = []
        sum_val = 0.0

        for weight, price_ratio in zip(self.weights, self.price_change):
            new_weight = weight * price_ratio
            new_weights.append(new_weight)
            sum_val += new_weight

        new_weights = [new_weight / sum_val for new_weight in new_weights]
        portfolio_value = self.broker.portfolio_value
        self.target_value = [weight * portfolio_value for weight in new_weights]

        sell_value = sum([(target - current) for target, current in zip(self.target_value, self.current_value) if target < current])

        buy_value = 0
        operation = []
        for target, current, price in zip(self.target_value, self.current_value, self.current_price):
            if target > current:
                op = (target - current) / price
                buy_value += op * price
                operation.append(op)
            else:
                operation.append((target - current) / price)

        buying_power = float(self.broker.get_bp())
        if buy_value > buying_power:
            if buy_value <= sell_value:
                print("[INFO] Buying power is sufficient after selling assets.")
            else:
                print("[WARNING] Insufficient buying power!")
                print("[INFO] Scaling down buy orders to match buying power.")
                scaling_factor = buying_power / buy_value
                operation = [op * scaling_factor if op > 0 else op for op in operation]
        else:
            print("[INFO] Buying power is sufficient.")

        MIN_ORDER_VALUE = 1.0
        
        for i, (ticker, op, price) in enumerate(zip(self.ticker, operation, self.current_price)):
            order_value = abs(op) * price
            if 0 < order_value < MIN_ORDER_VALUE:
                operation[i] = 0

        for ticker, op in zip(self.ticker, operation):
            if op > 0:
                self.broker.buy_order(ticker, abs(op))
            elif op < 0:
                self.broker.sell_order(ticker, abs(op))
            else:
                print(f"[INFO] {ticker} does not require any trades")

if __name__ == "__main__":
    model = UPA("Fuck", "/Users/richardtang/Desktop/UPA-Project/configs.json")
    while(True):
        if(model.broker.is_market_open()):
            model.weight_adjustment()
        time.sleep(60 * 60 * 3.5)