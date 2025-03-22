import matplotlib
matplotlib.use('Agg')
import pandas as pd
import mplfinance as mpf
import requests
import os
import random
import pickle
import time
from datetime import datetime

# Create necessary directories
os.makedirs("static/crypto", exist_ok=True)
os.makedirs("static/equities", exist_ok=True)
os.makedirs("cache", exist_ok=True)

# Asset mappings for API calls
CRYPTO_ASSETS = {
    "btc": {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC"},
    "eth": {"id": "ethereum", "name": "Ethereum", "symbol": "ETH"},
    "sol": {"id": "solana", "name": "Solana", "symbol": "SOL"},
    "bnb": {"id": "binancecoin", "name": "Binance Coin", "symbol": "BNB"}
}

EQUITY_ASSETS = {
    "nvda": {"symbol": "NVDA", "name": "Nvidia"},
    "aapl": {"symbol": "AAPL", "name": "Apple"},
    "tsla": {"symbol": "TSLA", "name": "Tesla"},
    "gld": {"symbol": "GLD", "name": "Gold"}
}
# Initialize bias test data


# Fetch data for cryptocurrencies using CoinGecko
def fetch_crypto_data(asset_id="bitcoin", days=365):
    cache_file = f"cache/crypto_{asset_id}_data.pkl"
    
    # Check if cached data is available and recent (less than 24 hours old)
    if os.path.exists(cache_file):
        cache_time = os.path.getmtime(cache_file)
        current_time = time.time()
        time_diff_hours = (current_time - cache_time) / 3600
        
        if time_diff_hours < 24:  # Use cache if less than 24 hours old
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            print(f"Loaded {asset_id} data from cache (CoinGecko)")
            return data
    
    print(f"Fetching fresh data for {asset_id} from CoinGecko")
    
    # Add API key if you have one
    headers = {"x-cg-demo-api-key": "CG-X9rKSiVeFyMS6FPbUCaFw4Lc"}
    
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data_json = response.json()
            
            if "prices" not in data_json:
                print(f"Error: Invalid data format from CoinGecko: {data_json}")
                return None
                
            prices = data_json["prices"]
            
            # Create DataFrame with Open, High, Low, Close
            data = pd.DataFrame(prices, columns=["Date", "Close"])
            data["Date"] = pd.to_datetime(data["Date"], unit="ms")
            data.set_index("Date", inplace=True)
            
            # If available, use volume data
            if "total_volumes" in data_json:
                volumes = data_json["total_volumes"]
                volume_df = pd.DataFrame(volumes, columns=["Date", "Volume"])
                volume_df["Date"] = pd.to_datetime(volume_df["Date"], unit="ms")
                volume_df.set_index("Date", inplace=True)
                data = data.join(volume_df)
            
            # Create OHLC data
            # We'll shift Close to get Open, and estimate High and Low
            # In production, you'd want more accurate OHLC data
            data["Open"] = data["Close"].shift(1)
            
            if "high" not in data_json and "low" not in data_json:
                # Estimate High and Low
                data["High"] = data["Close"] * 1.02  # Simulate High as 2% above Close
                data["Low"] = data["Close"] * 0.98   # Simulate Low as 2% below Close
            
            data = data.dropna()
            
            # Save to cache
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"Saved {asset_id} data to cache (CoinGecko)")
            return data
        else:
            print(f"Error fetching {asset_id} data from CoinGecko: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Exception fetching {asset_id} data from CoinGecko: {str(e)}")
        return None

# Fetch data for equities using Alpha Vantage
def fetch_equity_data(symbol="NVDA", days=365):
    cache_file = f"cache/equity_{symbol}_data.pkl"
    
    # Check if cached data is available and recent
    if os.path.exists(cache_file):
        cache_time = os.path.getmtime(cache_file)
        current_time = time.time()
        time_diff_hours = (current_time - cache_time) / 3600
        
        if time_diff_hours < 24:  # Use cache if less than 24 hours old
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            print(f"Loaded {symbol} data from cache (Alpha Vantage)")
            return data
    
    print(f"Fetching fresh data for {symbol} from Alpha Vantage")
    
    api_key = "QRL7874F7OJAGJHY"  # Replace with your API key
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            json_data = response.json()
            
            if "Time Series (Daily)" not in json_data:
                error_msg = json_data.get('Error Message', json_data.get('Information', 'Unknown error'))
                print(f"Error fetching {symbol} data from Alpha Vantage: {error_msg}")
                return None
            
            time_series = json_data["Time Series (Daily)"]
            data = pd.DataFrame.from_dict(time_series, orient="index")
            data = data.rename(columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            })
            
            data.index = pd.to_datetime(data.index)
            data = data.astype(float)
            data = data.sort_index()
            data = data.tail(days)
            
            # Save to cache
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"Saved {symbol} data to cache (Alpha Vantage)")
            return data
        else:
            print(f"Error fetching {symbol} data from Alpha Vantage: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Exception fetching {symbol} data from Alpha Vantage: {str(e)}")
        return None

# Generate chart images for a given asset and date
def generate_bias_charts(data, date_n, asset_symbol, asset_type="crypto", lookback=30):
    if data is None or data.empty:
        return None, None
    
    # Ensure date_n is a valid index in the data
    if date_n not in data.index:
        print(f"Date {date_n} not found in data for {asset_symbol}")
        return None, None
    
    # Get the next date available in the data
    next_dates = data.index[data.index > date_n]
    if len(next_dates) == 0:
        print(f"No next date available after {date_n} for {asset_symbol}")
        return None, None
    
    date_n_plus_1 = next_dates[0]
    
    # Generate file paths
    date_str = date_n.strftime('%Y-%m-%d')
    next_date_str = date_n_plus_1.strftime('%Y-%m-%d')
    
    setup_path = f"{asset_type}/{asset_symbol}_{date_str}_setup.png"
    outcome_path = f"{asset_type}/{asset_symbol}_{next_date_str}_outcome.png"
    
    full_setup_path = f"static/{setup_path}"
    full_outcome_path = f"static/{outcome_path}"
    
    # Check if files already exist
    if os.path.exists(full_setup_path) and os.path.exists(full_outcome_path):
        print(f"Chart images already exist for {asset_symbol} on {date_str}")
        return setup_path, outcome_path
    
    # Get data for setup and outcome charts
    setup_data = data.loc[:date_n].tail(lookback)
    outcome_data = data.loc[:date_n_plus_1].tail(lookback)
    
    # Plotting settings
    plot_kwargs = {
        'type': 'candle',
        'style': 'charles',
        'figscale': 1.5,
        'volume': 'Volume' in data.columns,
        'title': f"{asset_symbol.upper()} Chart"
    }
    
    # Generate the charts
    try:
        mpf.plot(setup_data, **plot_kwargs, savefig=full_setup_path)
        mpf.plot(outcome_data, **plot_kwargs, savefig=full_outcome_path)
        print(f"Generated charts for {asset_symbol} on {date_str}")
        return setup_path, outcome_path
    except Exception as e:
        print(f"Error generating charts for {asset_symbol} on {date_str}: {str(e)}")
        return None, None

# Get the sentiment (Bullish/Bearish) based on closing prices
def get_sentiment(data, date_n):
    next_dates = data.index[data.index > date_n]
    if len(next_dates) == 0:
        return "Unknown"
    
    date_n_plus_1 = next_dates[0]
    
    if data.loc[date_n_plus_1, "Close"] > data.loc[date_n, "Close"]:
        return "Bullish"
    else:
        return "Bearish"

# Prepare test data for a given asset
def prepare_bias_test(asset_code, asset_type="crypto", num_tests=5):
    """
    Prepare bias test data for a given asset.
    
    Args:
        asset_code (str): Asset code like 'btc', 'eth', 'nvda', etc.
        asset_type (str): Type of asset - 'crypto' or 'equities'
        num_tests (int): Number of test examples to prepare
        
    Returns:
        list: List of test data dictionaries with setup, outcome, etc.
    """
    if asset_type == "crypto":
        if asset_code not in CRYPTO_ASSETS:
            print(f"Unknown crypto asset: {asset_code}")
            return []
            
        asset = CRYPTO_ASSETS[asset_code]
        data = fetch_crypto_data(asset["id"])
        asset_symbol = asset_code
    else:  # equities
        if asset_code not in EQUITY_ASSETS:
            print(f"Unknown equity asset: {asset_code}")
            return []
            
        asset = EQUITY_ASSETS[asset_code]
        data = fetch_equity_data(asset["symbol"])
        asset_symbol = asset_code
    
    if data is None or data.empty:
        print(f"No data available for {asset_code}")
        return []
    
    # Get dates that have next-day data available
    valid_dates = [date for date in data.index[:-1] if date in data.index]
    
    if len(valid_dates) < num_tests:
        print(f"Not enough data points for {asset_code}. Needed {num_tests}, got {len(valid_dates)}")
        num_tests = len(valid_dates)
    
    # Select random dates for testing
    test_dates = random.sample(valid_dates, num_tests)
    test_dates.sort()
    
    tests = []
    for date_n in test_dates:
        setup_path, outcome_path = generate_bias_charts(data, date_n, asset_symbol, asset_type)
        
        if setup_path is None or outcome_path is None:
            continue
            
        sentiment = get_sentiment(data, date_n)
        
        # Get OHLC data for the test date
        ohlc = data.loc[date_n]
        
        tests.append({
            "setup": setup_path,
            "outcome": outcome_path,
            "correct": sentiment,
            "open": float(ohlc["Open"]),
            "high": float(ohlc["High"]),
            "low": float(ohlc["Low"]),
            "close": float(ohlc["Close"]),
            "volume": float(ohlc["Volume"]) if "Volume" in ohlc else None,
            "date": date_n.strftime('%Y-%m-%d')
        })
    
    print(f"Prepared {len(tests)} tests for {asset_code}")
    return tests

# Prepare all assets for testing
def prepare_all_bias_tests(num_tests=5):
    """
    Prepare test data for all supported assets.
    
    Returns:
        dict: Dictionary mapping asset codes to test data
    """
    all_tests = {}
    
    # Prepare crypto tests
    for asset_code in CRYPTO_ASSETS:
        all_tests[asset_code] = prepare_bias_test(asset_code, "crypto", num_tests)
    
    # Prepare equity tests
    for asset_code in EQUITY_ASSETS:
        all_tests[asset_code] = prepare_bias_test(asset_code, "equities", num_tests)
    
    return all_tests

# Get asset info
def get_asset_info(asset_code):
    """Get information about an asset"""
    if asset_code in CRYPTO_ASSETS:
        return {
            "type": "crypto",
            "name": CRYPTO_ASSETS[asset_code]["name"],
            "symbol": CRYPTO_ASSETS[asset_code]["symbol"],
            "code": asset_code
        }
    elif asset_code in EQUITY_ASSETS:
        return {
            "type": "equities", 
            "name": EQUITY_ASSETS[asset_code]["name"],
            "symbol": EQUITY_ASSETS[asset_code]["symbol"],
            "code": asset_code
        }
    return None