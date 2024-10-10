from upa_model import UPA
from upa_gui import UPA_DashApp
import datetime

if __name__ == "__main__":
    upa = UPA(output_dir="Trading_logs", config_json="configs.json")
    app = UPA_DashApp(upa)
    while True:
        current_time = datetime.datetime.now()
        market_open = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)

        if market_open <= current_time < market_close:
            upa.weight_adjustment()
            print("[INFO] Trades executed for the day. Waiting until next market open.")
        else:
            time_to_open = (market_open - current_time).seconds if current_time < market_open else (market_open + datetime.timedelta(days=1) - current_time).seconds
            print(f"[INFO] Waiting for market to open. Time remaining: {time_to_open // 3600} hours and {(time_to_open % 3600) // 60} minutes.")

        app.run()