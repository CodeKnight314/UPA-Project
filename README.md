# UPA-Project

## Overview
This is an educational repoistory on the implementation of Universal Portfolio Algorithm in combination with Alpaca Trading API. The `main.py` is designed to run fully automatically and executes trades based on the two most recent closing prices of given stock. It can be modified to take other stocks as investment targets. The account can be initilizaed after investing in the account. The broker will distribute funds across the defined stocks then calculate the desired distribution as well as submit buy/sell orders necessary to reach desired distribution. After executing trade, `main.py` sleeps until the instant the U.S trade market opens. 

Ideally, the investment account should have sizable buying power as the UPA algorithm executes on average small percentage trades that culiminate to larger returns over time. This does not provide immeidate returns and is not guaranteed as a financial instrument. Please use or deploy at your own discretion. Results of algorithm implementation on Alpaca will be posted after trial runs (January ~ Feburary)

## Functionality 
Currently, the UPA model can only automate trading and is not developed yet for dynamic scenarios, including but not limited to: 
- Smoothing order sizes that are too small to execute 
- Daily trading logs
- Proper Stock filtering and searching for optimal investment candidates
- and more...

More improvements will come in the future as the project develops.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/CodeKnight314/UPA-Project.git
    ```

2. Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv upa-env
    source upa-env/bin/activate
    ```

3. cd to project directory: 
    ```bash 
    cd UPA-project/
    ```

4. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
Use the `main.py` script to initialize the automatic trading

**Example:**
```bash
python main.py
```