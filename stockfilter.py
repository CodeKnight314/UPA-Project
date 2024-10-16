import argparse
from tqdm import tqdm
import yfinance as yf
import pandas as pd


def get_tech_stocks(stocks):
    tech_stocks = []
    for stock in tqdm(stocks, desc="Filtering for tech stocks: "):
        try:
            ticker = yf.Ticker(stock)
            info = ticker.info
            if 'sector' in info and info['sector'] == 'Technology':
                tech_stocks.append(stock)
        except Exception as e:
            print(f"Could not retrieve information for {stock}: {e}")
    return tech_stocks


def calculate_correlation_matrix(stocks, start_date="2020-01-01", end_date="2024-01-01"):
    data = yf.download(stocks, start=start_date, end=end_date)['Adj Close']
    correlation_matrix = data.corr()
    return correlation_matrix


def get_uncorrelated_tech_stocks(stocks, correlation_threshold=0.75):
    # Step 1: Filter the tech stocks
    tech_stocks = get_tech_stocks(stocks)
    
    # Step 2: Calculate the correlation matrix
    if len(tech_stocks) < 2:
        return tech_stocks  # Not enough tech stocks to compare correlation
    
    correlation_matrix = calculate_correlation_matrix(tech_stocks)
    
    # Step 3: Identify uncorrelated stocks
    uncorrelated_stocks = []
    for stock in tqdm(tech_stocks, desc="Filtering for uncorrelated stocks: "):
        is_uncorrelated = True
        for selected_stock in uncorrelated_stocks:
            if abs(correlation_matrix.loc[stock, selected_stock]) > correlation_threshold:
                is_uncorrelated = False
                break
        if is_uncorrelated:
            uncorrelated_stocks.append(stock)
    
    return uncorrelated_stocks


def filter_volatile_stocks(nasdaq_csv: str):
    df = pd.read_csv(nasdaq_csv)
    volatile_stocks = []
    valid_stocks = df['Symbol'].tolist()

    for stock in tqdm(valid_stocks, desc="Filtering for volatile stocks: "):
        try:
            ticker_yahoo = yf.Ticker(stock)
            data = ticker_yahoo.history(start="2023-01-01", end="2024-10-10")

            if data.empty:
                continue

            std = data['Close'].std()
            price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
            if price_change > 0 and std < data['Close'].mean() * 0.5 and std > 0.5:
                volatile_stocks.append(stock)
        except Exception as e: 
            continue

    return volatile_stocks

def main(csv_path: str, output_file: str):
    # Filter for volatile stocks
    volatile_stocks = filter_volatile_stocks(csv_path)
    
    # Filter for tech stocks and uncorrelated stocks
    uncorrelated_stocks = get_uncorrelated_tech_stocks(volatile_stocks)
    
    # Save the volatile stocks to a CSV file
    df_volatile = pd.DataFrame({'Volatile Stocks': uncorrelated_stocks})
    df_volatile.to_csv(output_file, index=False) 
    print(f"Volatile stocks saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter volatile and uncorrelated tech stocks.")
    parser.add_argument('csv_path', type=str, help="Path to the NASDAQ CSV file containing stock symbols.")
    parser.add_argument('output_file', type=str, help="Path to save the filtered volatile tech stocks.")
    args = parser.parse_args()

    main(args.csv_path, args.output_file)