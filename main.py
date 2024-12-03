from broker_api import AlpacaBroker
import time
from datetime import datetime, timedelta
import pytz

def main():
    """
    Runs the main trading loop.

    This function initializes the Alpaca broker, checks if the market is open, 
    and adjusts the portfolio accordingly. If the market is closed, it calculates 
    the time until the next market opening and sleeps until then.
    """
    broker = AlpacaBroker("configs.json")
    if broker.is_market_open():
        broker.get_positons()
        broker.adjust_portfolio()
        
    desired_time = broker.market_open_time
    current_time_utc = datetime.now(pytz.utc)
    us_eastern = pytz.timezone("US/Eastern")
    current_time_et = current_time_utc.astimezone(us_eastern).time()
    
    time_diff = datetime.combine(datetime.today(), desired_time) - datetime.combine(datetime.today(), current_time_et)
    if time_diff.days < 0: 
        time_diff += timedelta(days=1)
        
    print(f"[INFORMATIOn] Sleeping until {time_diff}.")
    time.sleep(time_diff.total_seconds())

if __name__ == "__main__": 
    main()