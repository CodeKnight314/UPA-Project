import os
import datetime
from broker_api import AlpacaBroker

class UPA():
    def __init__(self, output_dir: str, config_json: str):
        self.broker = AlpacaBroker(config_json=config_json)
        self.output_dir = output_dir
        self.output_logs = os.path.join(self.output_dir, "UPA_TransactionLogs.txt")
        self.ticker = ['DOCU', 'FSLY', 'GOCO', 'MDB', 'NET', 'PLTR', 'PTON', 'ROKU', 'SHOP', 'SNOW', 'SQ', 'TDOC', 'TTD', 'TWLO', 'NVDA']

        # Create output directory if it does not exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.load_initial_state()

    def load_initial_state(self):
        stock_prices = [self.broker.get_prices(ticker) for ticker in self.ticker]
        self.yester_close = [ticker[0] for ticker in stock_prices]
        self.today_close = [ticker[1] for ticker in stock_prices]
        self.price_change = [ticker[2] for ticker in stock_prices]
        self.current_qty = [float(self.broker.positions[ticker][0]) if ticker in self.broker.positions else 0 for ticker in self.ticker]
        self.current_value = [price * qty for price, qty in zip(self.today_close, self.current_qty)]
        self.current_price = self.today_close
        self.weights = [value / self.broker.portfolio_value if self.broker.portfolio_value != 0 else 0 for value in self.current_value]

    def check_if_rebalanced_today(self):
        today = datetime.datetime.now().date()
        if os.path.isfile(self.output_logs):
            with open(self.output_logs, 'r') as f:
                first_line = f.readline().strip()
                if first_line:
                    last_rebalance_date = datetime.datetime.strptime(first_line, "%Y-%m-%d").date()
                    if last_rebalance_date == today:
                        print("[INFO] Rebalancing has already been performed today.")
                        return True
        return False

    def weight_adjustment(self):
        if self.check_if_rebalanced_today():
            return

        # Update weights based on price change ratio
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

        sell_value = sum([abs((target - current)) for target, current in zip(self.target_value, self.current_value) if target < current])
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
                print(f"[WARNING] Insufficient buying power! Required: {buy_value}")
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

        # Log trades and execute orders
        today = datetime.datetime.now().date()
        with open(self.output_logs, 'a') as f:
            f.write(f"{today} - Trades:\n")
            for ticker, op in zip(self.ticker, operation):
                if op > 0:
                    self.broker.buy_order(ticker, abs(op))
                    f.write(f"BUY {ticker}: {abs(op)} shares\n")
                elif op < 0:
                    self.broker.sell_order(ticker, abs(op))
                    f.write(f"SELL {ticker}: {abs(op)} shares\n")
                else:
                    print(f"[INFO] {ticker} does not require any trades")

        # Update log file with today's date and new weights
        with open(self.output_logs, 'a') as f:
            f.write(f"{today}\n")
            f.write(" ".join(map(str, new_weights)) + "\n")