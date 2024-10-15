import os
import json
import datetime
import threading
from broker_api import AlpacaBroker
import time
import os

class UPA():
    def __init__(self, output_dir: str, config_json: str):
        self.broker = AlpacaBroker(config_json=config_json)
        self.output_dir = output_dir
        self.output_logs = os.path.join(self.output_dir, "UPA_TransactionLogs.json")
        self.ticker = ['DOCU', 'FSLY', 'GOCO', 'MDB', 'NET', 'PLTR', 'PTON', 'ROKU', 'SHOP', 'SNOW', 'SQ', 'TDOC', 'TTD', 'TWLO', 'NVDA']

        # Create output directory if it does not exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.load_initial_state()
        self.start_periodic_update()

    def load_initial_state(self):
        stock_prices = [self.broker.get_prices(ticker) for ticker in self.ticker]
        self.yester_close = [ticker[0] for ticker in stock_prices]
        self.today_close = [ticker[1] for ticker in stock_prices]
        self.price_change = [ticker[2] for ticker in stock_prices]
        self.current_qty = [float(self.broker.positions[ticker][0]) if ticker in self.broker.positions else 0 for ticker in self.ticker]
        self.current_value = [price * qty for price, qty in zip(self.today_close, self.current_qty)]
        self.current_price = self.today_close
        self.weights = [value / self.get_portfolio_value() if self.get_portfolio_value() != 0 else 0 for value in self.current_value]

    def get_portfolio_value(self):
        return self.broker.portfolio_value

    def check_if_rebalanced_today(self):
        today = datetime.datetime.now().date()
        if os.path.isfile(self.output_logs):
            with open(self.output_logs, 'r') as f:
                data = json.load(f)
                if 'last_rebalance_date' in data:
                    last_rebalance_date = datetime.datetime.strptime(data['last_rebalance_date'], "%Y-%m-%d").date()
                    if last_rebalance_date == today:
                        print("[INFO] Rebalancing has already been performed today.")
                        self.update_ui_last_rebalance_date(last_rebalance_date)
                        return True
        return False

    def update_ui_last_rebalance_date(self, last_rebalance_date):
        # This method could be used to update the UI with the last rebalance date information
        print(f"[UI UPDATE] Last rebalance date: {last_rebalance_date}")

    def weight_adjustment(self):
        if self.check_if_rebalanced_today():
            return

        # Clear the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

        # Update weights based on price change ratio
        self.weights = [value / self.get_portfolio_value() if self.get_portfolio_value() != 0 else 0 for value in self.current_value]
        new_weights = []
        sum_val = 0.0

        for weight, price_ratio in zip(self.weights, self.price_change):
            new_weight = weight * price_ratio
            new_weights.append(new_weight)
            sum_val += new_weight

        new_weights = [new_weight / sum_val for new_weight in new_weights]
        portfolio_value = self.get_portfolio_value()
        self.target_value = [weight * portfolio_value for weight in new_weights]

        # Generate sell orders to create liquidity
        sell_operations = []
        for ticker, target, current, price in zip(self.ticker, self.target_value, self.current_value, self.current_price):
            if target < current:
                op = (current - target) / price
                success = self.broker.sell_order(ticker, abs(op))  # Execute sell order here to generate liquidity
                if success:
                    sell_operations.append(op)
                else:
                    sell_operations.append(0)
            else:
                sell_operations.append(0)

        # Update buying power after selling
        buying_power = float(self.broker.get_bp())

        # Generate buy orders with updated buying power
        buy_operations = []
        for ticker, target, current, price in zip(self.ticker, self.target_value, self.current_value, self.current_price):
            if target > current:
                op = (target - current) / price
                if op * price <= buying_power:
                    success = self.broker.buy_order(ticker, abs(op))
                    if success and op > 0:
                        buy_operations.append(op)
                        buying_power -= op * price
                    else:
                        buy_operations.append(0)
                else:
                    print(f"[WARNING] Insufficient buying power for {ticker}, scaling down buy order.")
                    op = buying_power / price
                    if op > 0:
                        success = self.broker.buy_order(ticker, abs(op))
                    else:
                        success = False
                    if success and op > 0:
                        buy_operations.append(op)
                        buying_power = 0
                    else:
                        buy_operations.append(0)
            else:
                buy_operations.append(0)

        # Log and execute buy orders only if all orders were successful
        if any(sell_operations) or any(buy_operations):
            today = datetime.datetime.now().date()
            log_filename = os.path.join(self.output_dir, f"UPA_TransactionLogs_{today}.json")
            trade_log = {
                "date": str(today),
                "trades": []
            }
            for ticker, op in zip(self.ticker, buy_operations):
                if op > 0:
                    trade_log["trades"].append({"ticker": ticker, "action": "BUY", "quantity": abs(op)})
                elif op < 0:
                    trade_log["trades"].append({"ticker": ticker, "action": "SELL", "quantity": abs(op)})
                else:
                    trade_log["trades"].append({"ticker": ticker, "action": "NO TRADE"})

            # Update log file with today's date and new weights
            if os.path.isfile(log_filename):
                with open(log_filename, 'r') as f:
                    data = json.load(f)
            else:
                data = {}

            data['last_rebalance_date'] = str(today)
            data['weights'] = new_weights
            if 'trade_history' not in data:
                data['trade_history'] = []
            data['trade_history'].append(trade_log)

            with open(log_filename, 'w') as f:
                json.dump(data, f, indent=4)

    def get_recent_trade_history(self, days: int = 7):
        if not os.path.isfile(self.output_logs):
            print("[INFO] No trade history found.")
            return []

        with open(self.output_logs, 'r') as f:
            data = json.load(f)

        if 'trade_history' not in data:
            print("[INFO] No trade history found.")
            return []

        recent_trades = []
        today = datetime.datetime.now().date()
        for trade in data['trade_history']:
            trade_date = datetime.datetime.strptime(trade['date'], "%Y-%m-%d").date()
            if (today - trade_date).days <= days:
                recent_trades.append(trade)

        return recent_trades

    def start_periodic_update(self):
        def update():
            self.load_initial_state()
            threading.Timer(60, update).start()

        update()

    def get_current_state(self):
        # Method to extract current state for UI purposes
        current_state = []
        for ticker, qty, price, value in zip(self.ticker, self.current_qty, self.current_price, self.current_value):
            current_state.append({
                "ticker": ticker,
                "quantity": qty,
                "current_price": price,
                "current_value": value
            })
        formatted_state = "\n".join([f"Ticker: {state['ticker']}, Quantity: {state['quantity']}, Price: {state['current_price']}, Value: {state['current_value']}" for state in current_state])
        return formatted_state
    
def main():
    output_dir = "upa_logs/"
    config_json = "configs.json"

    upa = UPA(output_dir=output_dir, config_json=config_json)

    try:
        while True:
            upa.weight_adjustment()  # Run the rebalancing
            current_state = upa.get_current_state()  # Get the current state for UI or logging
            print(current_state)  # Print or use this data in your UI

            time.sleep(3600)
    except KeyboardInterrupt:
        print("Execution stopped by user.")

if __name__ == "__main__":
    main()