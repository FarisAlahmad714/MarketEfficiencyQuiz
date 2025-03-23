from flask import Flask, jsonify, render_template, request, redirect, url_for, make_response, session, flash
import os
import random
import time
import requests
from flask_session import Session
from quiz_data import quiz_topics
# Remove deleted file imports
# from btc_data import btc_candle_data
# from daily_candle_data import daily_candle_data
from prediction_validator import CandleAnalyzer
from charting_exam_data import swing_analysis_data
from study_content import study_content
from chart_generator import prepare_bias_test, get_asset_info, CRYPTO_ASSETS, EQUITY_ASSETS
import click
import glob
from datetime import datetime, timedelta
import pickle
import logging
import json


logging.basicConfig(level=logging.DEBUG)

validator = CandleAnalyzer('static')
app = Flask(__name__)
app.secret_key = "your_secret_key"
# Add this near the top of your app.py file after creating the app
print(f"Template folder path: {app.template_folder}")
# Set up Flask-Session for server-side sessions
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "flask_session"  # Folder to store sessions
os.makedirs("flask_session", exist_ok=True)  # Create the directory if it doesn't exist
Session(app)

# Application cache for chart data to avoid session bloat
app.config['CHART_DATA_CACHE'] = {}

# Create necessary directories
os.makedirs("static/crypto", exist_ok=True)
os.makedirs("static/equities", exist_ok=True)
os.makedirs("cache", exist_ok=True)


@app.context_processor
def inject_analytics_data():
    """Inject Google Analytics data into all templates."""
    return {
        'ga_tracking_id': 'G-1NOM6BVFW5',  # Your Google Analytics ID
        'ga_enabled': True  # You can set to False in development if needed
    }
# Create empty fallback data (to replace deleted modules)
btc_candle_data = []
daily_candle_data = []

symbol_map = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "BNBUSDT": "binancecoin",
    "SOLUSDT": "solana",
    "XRPUSDT": "ripple",
    "LTCUSDT": "litecoin",
    "LINKUSDT": "chainlink"
}

topic_descriptions = {
    "Swing Point Basics": "Learn to identify key swing highs and lows in price action",
    "Liquidity Concepts": "Understand how liquidity pools form and their significance",
    "Range Trading": "Master the art of trading within defined ranges",
    "Risk Management": "Learn proper risk:reward ratios and position sizing",
    "Stop/Target Orders": "Understand proper order placement and management"
}

charting_exam_descriptions = {
    'swing_analysis': {
        'title': 'Swing Points & Equal Highs/Lows',
        'description': 'Practice identifying swing points and equal/old levels through chart markup.',
        'sections': ['swing_points', 'equal_levels'],
        'tools_required': ['line', 'pointer', 'hline'],
        'instructions': 'Mark swing points and equal price levels on charts.'
    },
    "fibonacci": {
        "title": "Fibonacci Retracements",
        "description": "Learn to plot Fibonacci retracements from swing high to swing low",
        "sections": ["fib_retracement"],
        "tools_required": ["fibonacci"]
    },
    "gap_analysis": {
        "title": "Gap Analysis & FVG",
        "description": "Identify fair value gaps, volume imbalances, and consequent encroachment",
        "sections": ["fvg", "volume_imbalance", "gaps", "encroachment", "inversion"],
        "tools_required": ["box", "line"]
    },
    "order_blocks": {
        "title": "Order Block Formation",
        "description": "Complete order block analysis including liquidity, BOS, and order block identification",
        "sections": ["liquidity", "swing", "bos", "ob_identification", "reaction"],
        "tools_required": ["line", "pointer", "box"]
    }
}

# Add these new routes to your Flask app

@app.route('/get_available_assets')
def get_available_assets():
    """Return a list of all available assets for bias testing"""
    assets = list(CRYPTO_ASSETS.keys()) + list(EQUITY_ASSETS.keys())
    return jsonify({'assets': assets})

@app.route('/preload_asset_data/<asset_code>')
def preload_asset_data(asset_code):
    """Preload data for a specific asset and return a status"""
    if asset_code not in CRYPTO_ASSETS and asset_code not in EQUITY_ASSETS:
        return jsonify({'status': 'error', 'message': 'Invalid asset code'}), 400
    
    # Load the data for this asset if not already loaded
    asset_data = load_asset_data(asset_code)
    
    # Return a simple success response with count
    return jsonify({
        'status': 'success', 
        'asset': asset_code,
        'count': len(asset_data) if asset_data else 0
    })

# Replace your current load_asset_data function with this improved version
def load_asset_data(asset_code):
    """Load data for an asset only when needed with improved error handling and caching"""
    global BIAS_TEST_DATA
    
    # If data is already loaded, return it
    if asset_code in BIAS_TEST_DATA and BIAS_TEST_DATA[asset_code]:
        return BIAS_TEST_DATA[asset_code]
    
    try:
        if asset_code == 'random':
            # Generate random dataset from already loaded assets
            if not BIAS_TEST_DATA.get('random'):
                print("Creating new random test dataset...")
                BIAS_TEST_DATA['random'] = []
                
                # Force-load the primary assets first if they're not loaded
                primary_assets = ['btc', 'eth', 'sol']
                for code in primary_assets:
                    if code not in BIAS_TEST_DATA or not BIAS_TEST_DATA[code]:
                        try:
                            print(f"Force-loading primary asset {code} for random test")
                            asset_type = "crypto" if code in CRYPTO_ASSETS else "equities"
                            BIAS_TEST_DATA[code] = prepare_bias_test(code, asset_type, 5)
                        except Exception as e:
                            print(f"Error loading primary asset {code}: {str(e)}")
                
                # Use all loaded assets to create a random mix
                available_assets = []
                for code in list(BIAS_TEST_DATA.keys()):
                    if code != 'random' and BIAS_TEST_DATA[code]:
                        available_assets.append(code)
                
                print(f"Found {len(available_assets)} available assets for random test: {available_assets}")
                
                # Need at least 3 tests for a good random mix
                if len(available_assets) >= 2:
                    # Take one test from each available asset to ensure diversity
                    for code in available_assets:
                        # Create a deep copy to avoid reference issues
                        original_test = random.choice(BIAS_TEST_DATA[code])
                        test_copy = {k: v for k, v in original_test.items()}
                        
                        # Add asset identification
                        test_copy['asset_code'] = code
                        test_copy['asset_info'] = get_asset_info(code)
                        BIAS_TEST_DATA['random'].append(test_copy)
                    
                    random.shuffle(BIAS_TEST_DATA['random'])
                    print(f"Created random test with {len(BIAS_TEST_DATA['random'])} items")
                else:
                    # Fallback: If we don't have enough assets loaded, create a default set
                    print("Not enough assets loaded for random test, creating fallback tests")
                    fallback_assets = ['btc', 'eth', 'sol']
                    for code in fallback_assets:
                        asset_info = get_asset_info(code)
                        # Create a fallback test with static images if available
                        fallback_test = {
                            'asset_code': code,
                            'asset_info': asset_info,
                            'setup': f"crypto/{code}_setup_fallback.png",
                            'outcome': f"crypto/{code}_outcome_fallback.png",
                            'correct': 'bullish',  # Provide a default value
                            'open': 100,
                            'high': 110, 
                            'low': 95,
                            'close': 105,
                            'date': '2025-03-01'
                        }
                        BIAS_TEST_DATA['random'].append(fallback_test)
                    
                    random.shuffle(BIAS_TEST_DATA['random'])
                    print(f"Created fallback random test with {len(BIAS_TEST_DATA['random'])} items")
            
            return BIAS_TEST_DATA['random']
        
        # For a specific asset
        asset_type = "crypto" if asset_code in CRYPTO_ASSETS else "equities"
        BIAS_TEST_DATA[asset_code] = prepare_bias_test(asset_code, asset_type, 5)
        return BIAS_TEST_DATA[asset_code]
    except Exception as e:
        print(f"Error loading data for {asset_code}: {str(e)}")
        BIAS_TEST_DATA[asset_code] = []
        return []


# Initialize with empty dictionary - we'll load data lazily
BIAS_TEST_DATA = {}

@app.route('/')
def index():
    return render_template(
        'index.html',
        topics=list(quiz_topics.keys()),
        topic_descriptions=topic_descriptions,
        charting_exam_descriptions=charting_exam_descriptions
    )

@app.route('/get_homepage_chart_data/<symbol>/<interval>')
def get_homepage_chart_data(symbol, interval):
    symbol_map = {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "SOLUSDT": "solana"}
    coingecko_symbol = symbol_map.get(symbol, "bitcoin")
    limit = 100  # Fixed for homepage
    if interval == '1h':
        days = 1
    elif interval == '4h':
        days = 7
    elif interval == '1d':
        days = 30
    elif interval == '1w':
        days = 365
    else:
        days = 30

    url = f"https://api.coingecko.com/api/v3/coins/{coingecko_symbol}/ohlc?vs_currency=usd&days={days}"
    headers = {"x-cg-demo-api-key": "CG-X9rKSiVeFyMS6FPbUCaFw4Lc"}  # Replace with your actual API key
    print(f"Fetching homepage chart data for {coingecko_symbol} ({interval}, {days} days)")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"CoinGecko API response status: {response.status_code}")
        if response.status_code != 200:
            print(f"CoinGecko API error (homepage): {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to fetch chart data'}), 500
        data = response.json()
        print(f"Received {len(data)} candles from CoinGecko")
        candles_to_take = min(limit, len(data))
        candles = [
            {
                'time': int(candle[0]) // 1000,
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4])
            }
            for candle in data[-candles_to_take:]
        ]
        print(f"Returning {len(candles)} candles to homepage")
        return jsonify(candles)
    except requests.exceptions.RequestException as e:
        print(f"CoinGecko request failed (homepage): {str(e)}")
        return jsonify({'error': 'Request failed'}), 500
    
@app.route('/study')
def study_selection():
    """
    Render the study selection page, showing all available study topics
    """
    return render_template('study_selection.html', study_content=study_content)

@app.route('/study/<topic>')
def study_topic(topic):
    if topic in study_content:
        lessons = study_content[topic]
        return render_template('study_topic.html', topic=topic, lessons=lessons)
    return redirect(url_for('study_selection'))

@app.route('/quiz_selection')
def quiz_selection():
    return render_template('quiz_selection.html', quiz_topics=quiz_topics)

@app.route('/quiz/<topic>/<int:question_id>', methods=['GET', 'POST'])
def quiz(topic, question_id):
    if topic not in quiz_topics:
        return redirect(url_for('index'))
    if question_id >= len(quiz_topics[topic]):
        return redirect(url_for('results', topic=topic))
    
    question_data = quiz_topics[topic][question_id]
    
    if request.method == 'POST':
        user_answer = int(request.form.get('answer', 0))
        score = int(request.cookies.get(f'score_{topic}', 0))
        answers = request.cookies.get(f'answers_{topic}', '').split(',')
        if answers == ['']: answers = []
        answers.append(str(user_answer))
        
        if user_answer == question_data['correct_option']:
            score += 1
            
        response = redirect(url_for('quiz', topic=topic, question_id=question_id + 1))
        response.set_cookie(f'score_{topic}', str(score))
        response.set_cookie(f'answers_{topic}', ','.join(answers))
        return response

    image_url = url_for('static', filename=question_data['image']) if 'image' in question_data else None
    images_list = [url_for('static', filename=img) for img in question_data['images']] if 'images' in question_data else None

    return render_template(
        'quiz.html',
        topic=topic,
        question=question_data['question'],
        options=question_data['options'],
        image_url=image_url,
        images_list=images_list,
        question_id=question_id,
        total_questions=len(quiz_topics[topic])
    )

@app.route('/results/<topic>')
def results(topic):
    # Track quiz completion
    track_server_event(
        'quiz_completed',
        category='learning',
        label=topic,
        value=score
    )
    score = int(request.cookies.get(f'score_{topic}', 0))
    answers_str = request.cookies.get(f'answers_{topic}', '')
    
    response = make_response(render_template('results.html', 
                             topic=topic,
                             score=score,
                             total=len(quiz_topics[topic]),
                             questions=quiz_topics[topic],
                             user_answers=[int(x) for x in answers_str.split(',') if x]))
    
    if f'score_{topic}' in request.cookies:
        response.delete_cookie(f'score_{topic}')
        response.delete_cookie(f'answers_{topic}')
    
    return response

@app.route('/bias_test_selection')
def bias_test_selection():
    session.clear()  # Clear any existing test session
    return render_template('bias_test_selection.html')

@app.route('/daily_bias/<test_type>', methods=['GET', 'POST'])
def daily_bias(test_type):
    # Lazy-load data for this asset when needed
    if test_type in CRYPTO_ASSETS or test_type in EQUITY_ASSETS or test_type == 'random':
        data_source = load_asset_data(test_type)
        using_new_format = True
    else:
        # Fall back to old data format
        data_source = btc_candle_data if test_type == 'btc' else daily_candle_data
        using_new_format = False
    
    if request.method == 'POST':
        user_prediction = request.form.get('prediction', '').lower()
        current_index = session.get('current_index', 0)
        
        if 'data' not in session or current_index >= len(session['data']):
            return redirect(url_for('daily_bias_results', test_type=test_type))
        
        test_item = session['data'][current_index]
        
        if using_new_format and 'correct' in test_item:
            # New format with 'correct' property
            actual_outcome = test_item['correct'].lower()
        else:
            # Old format with validator
            actual_outcome = validator.validate_sequence(
                test_item['setup'],
                test_item['outcome']
            ).lower()
        
        if 'score' not in session:
            session['score'] = 0
        if user_prediction == actual_outcome:
            session['score'] += 1
            
        if 'user_answers' not in session:
            session['user_answers'] = []
        session['user_answers'].append(user_prediction)
        
        if 'correct_answers' not in session:
            session['correct_answers'] = []
        session['correct_answers'].append(user_prediction == actual_outcome)
        
        session['current_index'] = current_index + 1
        return redirect(url_for('daily_bias_feedback', test_type=test_type))
    
    # Initialize test data if needed
    if 'data' not in session:
        if using_new_format and data_source:
            # Get up to 5 tests from new format
            test_data = random.sample(data_source, min(5, len(data_source)))
        else:
            # Old format - take first 5 after shuffle
            if data_source:
                random.shuffle(data_source)
                test_data = data_source[:5]
            else:
                test_data = []
        
        session['data'] = test_data
        session['current_index'] = 0
        session['score'] = 0
        session['user_answers'] = []
        session['correct_answers'] = []
    
    current_index = session.get('current_index', 0)
    if current_index >= len(session['data']):
        return redirect(url_for('daily_bias_results', test_type=test_type))
    
    # Get asset info for display
    test_item = session['data'][current_index]
    
    # Asset name and info
    if test_type == 'random' and 'asset_info' in test_item:
        asset_info = test_item['asset_info']
        asset_name = f"{asset_info['name']} ({asset_info['symbol']})"
    else:
        try:
            asset_info = get_asset_info(test_type)
            asset_name = f"{asset_info['name']} ({asset_info['symbol']})" if asset_info else test_type.upper()
        except:
            asset_info = {'type': 'crypto', 'name': test_type.upper(), 'symbol': test_type.upper()}
            asset_name = test_type.upper()
    
    # Create OHLC data structure for templates
    ohlc_data = {
        'open': test_item.get('open', 0),
        'high': test_item.get('high', 0),
        'low': test_item.get('low', 0),
        'close': test_item.get('close', 0),
        'date': test_item.get('date', '')
    }
    
    return render_template(
        'daily_bias.html',
        candle_image=url_for('static', filename=test_item['setup']),
        progress=f"{current_index + 1}/{len(session['data'])}",
        score=session.get('score', 0),
        total=len(session.get('user_answers', [])),
        test_type=test_type,
        asset_name=asset_name,
        asset_info=asset_info,
        ohlc_data=ohlc_data
    )

@app.route('/daily_bias_feedback/<test_type>')
def daily_bias_feedback(test_type):
    current_index = session.get('current_index', 0)
    data = session.get('data', [])
    correct_answers = session.get('correct_answers', [])
    
    if current_index <= 0 or current_index > len(data):
        return redirect(url_for('daily_bias_results', test_type=test_type))

    # Get info about the previous question
    prev_index = current_index - 1
    prev_question = data[prev_index]
    
    # Get asset info for display
    if test_type == 'random' and 'asset_info' in prev_question:
        asset_info = prev_question['asset_info']
        asset_name = f"{asset_info['name']} ({asset_info['symbol']})"
    else:
        try:
            asset_info = get_asset_info(test_type)
            asset_name = f"{asset_info['name']} ({asset_info['symbol']})" if asset_info else test_type.upper()
        except:
            asset_info = {'type': 'crypto', 'name': test_type.upper(), 'symbol': test_type.upper()}
            asset_name = test_type.upper()
    
    # Determine correct prediction based on format
    if 'correct' in prev_question:
        correct_prediction = prev_question['correct'].lower()
    else:
        try:
            correct_prediction = validator.validate_sequence(
                prev_question['setup'],
                prev_question['outcome']
            ).lower()
        except Exception as e:
            print(f"Error validating sequence: {str(e)}")
            correct_prediction = "unknown"
        
    was_correct = correct_answers[-1] if correct_answers else False
    
    # If we've reached the end, don't show a next image
    if current_index >= len(data):
        next_image = None
    else:
        next_image = url_for('static', filename=data[current_index]['setup'])
    
    # Create OHLC data
    ohlc_data = {
        'open': prev_question.get('open', 0),
        'high': prev_question.get('high', 0),
        'low': prev_question.get('low', 0),
        'close': prev_question.get('close', 0),
        'date': prev_question.get('date', '')
    }
    
    return render_template(
        'daily_bias_feedback.html',
        question_image=url_for('static', filename=prev_question['setup']),
        answer_image=url_for('static', filename=prev_question['outcome']),
        correct_prediction=correct_prediction,
        user_prediction=session['user_answers'][-1] if session.get('user_answers') else '',
        score=session.get('score', 0),
        total=len(session.get('user_answers', [])),
        next_image=next_image,
        test_type=test_type,
        asset_name=asset_name,
        asset_info=asset_info,
        progress=f"{current_index}/{len(data)}",
        was_correct=was_correct,
        ohlc_data=ohlc_data
    )

@app.route('/daily_bias_results/<test_type>')
def daily_bias_results(test_type):
    # Get data from session
    score = session.get('score', 0)
    data = session.get('data', [])
    user_answers = session.get('user_answers', [])
    correct_answers = session.get('correct_answers', [])
    
    # Debug logging
    print(f"Results for {test_type}: Score={score}, Questions={len(data)}, Answers={len(user_answers)}")
    
    # Handle empty data case
    if not data or len(data) == 0:
        return render_template(
            'daily_bias_results.html',
            score=0,
            total=0,
            accuracy="N/A",
            results=[],
            test_type=test_type,
            asset=test_type.upper(),
            asset_symbol=test_type
        )
    
    # Format results with a flat structure (like standalone app)
    results = []
    for i, question in enumerate(data):
        if i >= len(user_answers):
            continue
            
        # Get correct prediction
        if 'correct' in question:
            correct_prediction = question['correct'].lower()
        else:
            try:
                correct_prediction = validator.validate_sequence(
                    question['setup'],
                    question['outcome']
                ).lower()
            except:
                correct_prediction = "unknown"
        
        was_correct = correct_answers[i] if i < len(correct_answers) else False
        
        # Create a FLAT result structure (not nested)
        result = {
            'setup': question['setup'],
            'outcome': question['outcome'],
            'user_answer': user_answers[i],
            'correct_answer': correct_prediction,
            # Flat OHLC data (no nested structure)
            'open': float(question.get('open', 0)),
            'high': float(question.get('high', 0)),
            'low': float(question.get('low', 0)),
            'close': float(question.get('close', 0)),
            'date': question.get('date', '')
        }
        
        results.append(result)
    
    # Get asset name for display
    if test_type == 'random':
        asset_name = "Multiple Assets"
    else:
        try:
            asset_info = get_asset_info(test_type)
            asset_name = f"{asset_info['name']} ({asset_info['symbol']})"
        except:
            asset_name = test_type.upper()
    
    # Create response before clearing session
    response = make_response(render_template(
        'daily_bias_results.html',
        score=score,
        total=len(results),
        accuracy=f"{(score / len(results)) * 100:.1f}%" if results else "0%",
        results=results,
        test_type=test_type,
        asset=asset_name,  # For compatibility with standalone app
        asset_symbol=test_type
    ))
    
    # Clear session after preparing response
    session.clear()
    
    return response

# ================== NEW/UPDATED FUNCTIONS FROM STANDALONE APP =================

def fetch_chart_data(coin=None, timeframe=None, limit=100):  # Set a reasonable limit to avoid session bloat
    """
    Fetch chart data from CoinGecko with improved reliability and data handling.
    Returns the full chart data but manages session storage more efficiently.
    """
    # Define available coins and timeframes
    all_coins = ['bitcoin', 'ethereum', 'binancecoin', 'solana', 'cosmos', 'ripple', 'litecoin', 'chainlink']
    hourly_coins = ['bitcoin', 'ethereum', 'binancecoin', 'solana']
    timeframes = {'1h': 2, '4h': 14, '1d': 60, '1w': 180}  # Kept for compatibility, but we'll fetch 365 days
    
    # Select timeframe if not provided
    timeframe = timeframe or random.choice(list(timeframes.keys()))
    logging.debug(f"Selected timeframe: {timeframe}")
    
    # Select coin based on timeframe restrictions
    if coin is None:
        if timeframe == '1h':
            coin = random.choice(hourly_coins)
            logging.debug(f"Selected coin for 1h timeframe: {coin}")
        else:
            coin = random.choice(all_coins)
            logging.debug(f"Selected coin for non-1h timeframe: {coin}")
    
    # Use caching to avoid repeated API calls
    cache_file = f"cache/{coin}_ohlc_365days.pkl"
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            raw_data = pickle.load(f)
        print(f"Loaded {coin} data from cache (CoinGecko OHLC)")
        logging.debug(f"Loaded {coin} data from cache")
    else:
        days = 365  # Fetch 365 days of data
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/ohlc?vs_currency=usd&days={days}"
        headers = {"x-cg-demo-api-key": "CG-X9rKSiVeFyMS6FPbUCaFw4Lc"}
        print(f"Fetching data for {coin} ({timeframe}) from {url} with days={days}")
        logging.info(f"Selected coin: {coin} for timeframe: {timeframe}")
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"API Response Status: {response.status_code}")
            logging.debug(f"API response status code: {response.status_code}")
            if response.status_code != 200:
                print(f"API Error: {response.status_code} - {response.text}")
                logging.error(f"API Error: {response.status_code} - {response.text}")
                return [], coin, timeframe
            
            raw_data = response.json()
            if not raw_data:
                print("No OHLC data received from CoinGecko")
                logging.error("No OHLC data received from CoinGecko")
                return [], coin, timeframe
            
            # Cache the raw 1-day OHLC data
            with open(cache_file, 'wb') as f:
                pickle.dump(raw_data, f)
            print(f"Saved {coin} data to cache (CoinGecko OHLC)")
            logging.debug(f"Saved {coin} data to cache")
        
        except requests.exceptions.RequestException as e:
            print(f"Exception fetching data: {e}")
            logging.error(f"Exception in fetch_chart_data: {e}")
            return [], coin, timeframe
    
    print(f"Received {len(raw_data)} daily candles from CoinGecko")
    logging.debug(f"Received {len(raw_data)} daily candles from CoinGecko")
    logging.debug(f"Sample of raw data: {raw_data[-5:]}")
    
    # Convert 1-day candles into the desired timeframe
    chart_data = []
    if timeframe == '1h':
        # Convert each 1-day candle into 24 hourly candles
        for row in raw_data:
            base_time = int(row[0] / 1000)  # Convert milliseconds to seconds
            open_price = float(row[1])
            close_price = float(row[4])
            high_price = float(row[2])
            low_price = float(row[3])
            
            # Linearly interpolate prices over 24 hours
            for hour in range(24):
                time = base_time + hour * 3600
                # Interpolate the price for this hour
                price_ratio = hour / 24
                interpolated_price = open_price + (close_price - open_price) * price_ratio
                # Scale high and low proportionally
                high = high_price * (1 + (hour / 24) * (close_price / open_price - 1)) if open_price != 0 else high_price
                low = low_price * (1 + (hour / 24) * (close_price / open_price - 1)) if open_price != 0 else low_price
                candle = {
                    'time': time,
                    'open': interpolated_price if hour == 0 else chart_data[-1]['close'],
                    'high': high,
                    'low': low,
                    'close': interpolated_price
                }
                chart_data.append(candle)
        logging.debug(f"Converted to 1h timeframe: {len(chart_data)} hourly candles")
    elif timeframe == '4h':
        # Convert each 1-day candle into 6 4-hourly candles
        for row in raw_data:
            base_time = int(row[0] / 1000)
            open_price = float(row[1])
            close_price = float(row[4])
            high_price = float(row[2])
            low_price = float(row[3])
            
            for segment in range(6):
                time = base_time + segment * 14400  # 4 hours = 14400 seconds
                price_ratio = segment / 6
                interpolated_price = open_price + (close_price - open_price) * price_ratio
                high = high_price * (1 + (segment / 6) * (close_price / open_price - 1)) if open_price != 0 else high_price
                low = low_price * (1 + (segment / 6) * (close_price / open_price - 1)) if open_price != 0 else low_price
                candle = {
                    'time': time,
                    'open': interpolated_price if segment == 0 else chart_data[-1]['close'],
                    'high': high,
                    'low': low,
                    'close': interpolated_price
                }
                chart_data.append(candle)
        logging.debug(f"Converted to 4h timeframe: {len(chart_data)} 4-hourly candles")
    elif timeframe == '1d':
        # Use the 1-day candles as-is
        for row in raw_data:
            candle = {
                'time': int(row[0] / 1000),
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4])
            }
            chart_data.append(candle)
        logging.debug(f"Using 1d timeframe: {len(chart_data)} daily candles")
    elif timeframe == '1w':
        # Aggregate 7 days into 1 weekly candle
        weekly_candles = {}
        for row in raw_data:
            timestamp = int(row[0] / 1000)
            week_start = timestamp - (timestamp % (7 * 86400))
            if week_start not in weekly_candles:
                weekly_candles[week_start] = {
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4])
                }
            else:
                candle = weekly_candles[week_start]
                candle['high'] = max(candle['high'], float(row[2]))
                candle['low'] = min(candle['low'], float(row[3]))
                candle['close'] = float(row[4])
        
        for week_start, candle in sorted(weekly_candles.items()):
            chart_data.append({
                'time': week_start,
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close']
            })
        logging.debug(f"Converted to 1w timeframe: {len(chart_data)} weekly candles")
    
    # Apply the limit but ensure we have at least 50 candles for a good view
    candles_to_take = min(max(50, limit), len(chart_data))
    chart_data = chart_data[-candles_to_take:]
    print(f"Limit: {limit}, Data length: {len(chart_data)}, Candles to take: {candles_to_take}")
    print(f"Fetched {len(chart_data)} candles for {coin} ({timeframe})")
    logging.debug(f"Final chart data length: {len(chart_data)}")
    
    # Validate the chart data before returning
    is_valid, message = validate_chart_data(chart_data, coin, timeframe)
    if not is_valid:
        logging.warning(f"Generated invalid chart data: {message}")
        return refresh_problem_chart()
    
    return chart_data, coin, timeframe

def validate_chart_data(data, coin, timeframe):
    """
    Validates chart data to ensure it's properly formed and contains enough candles.
    
    Args:
        data: The chart data to validate
        coin: The cryptocurrency being displayed
        timeframe: The timeframe of the chart
        
    Returns:
        tuple: (is_valid, message)
    """
    if not data or len(data) < 20:
        return False, f"Insufficient data for {coin} ({timeframe}): Only {len(data) if data else 0} candles."
    
    # Check for too many identical candles in a row (corrupted data)
    identical_candles = 0
    max_identical = 0
    
    for i in range(1, len(data)):
        if (data[i]['open'] == data[i-1]['open'] and 
            data[i]['high'] == data[i-1]['high'] and 
            data[i]['low'] == data[i-1]['low'] and 
            data[i]['close'] == data[i-1]['close']):
            identical_candles += 1
        else:
            identical_candles = 0
        
        max_identical = max(max_identical, identical_candles)
    
    if max_identical > 5:  # More than 5 identical candles in a row is suspicious
        return False, f"Chart data for {coin} ({timeframe}) may be corrupted (found {max_identical+1} identical candles)."
    
    return True, "Chart data is valid."

def refresh_problem_chart():
    """
    Force refresh of chart data when issues are detected.
    
    Returns:
        tuple: (new_chart_data, coin, timeframe)
    """
    # Try another coin if the current one has problems
    all_coins = ['bitcoin', 'ethereum', 'binancecoin', 'solana', 'cosmos', 'ripple', 'litecoin', 'chainlink']
    coin = random.choice(all_coins)
    timeframe = random.choice(['1d', '4h'])  # Use more reliable timeframes
    
    # Try to get data with more reliable settings
    for attempt in range(3):  # Try up to 3 times
        chart_data, selected_coin, selected_timeframe = fetch_chart_data(coin, timeframe)
        
        # Skip the validation call here to avoid infinite recursion
        if chart_data and len(chart_data) >= 20:
            return chart_data, selected_coin, selected_timeframe
            
        logging.warning(f"Attempt {attempt+1}: Failed to get valid chart data")
        coin = random.choice([c for c in all_coins if c != coin])  # Try a different coin
    
    # If we can't get good data after multiple attempts, return a simple synthetic chart
    logging.error("Unable to fetch valid chart data after multiple attempts. Using synthetic data.")
    
    # Create synthetic data as a last resort
    synthetic_data = []
    base_price = 100.0
    for i in range(100):
        price_change = (random.random() - 0.5) * 2.0  # Random movement
        open_price = base_price
        close_price = base_price + price_change
        high_price = max(open_price, close_price) + random.random() * 0.5
        low_price = min(open_price, close_price) - random.random() * 0.5
        
        synthetic_data.append({
            'time': int(datetime.now().timestamp()) - (100 - i) * 86400,  # One day apart
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price
        })
        
        base_price = close_price  # Next candle starts at previous close
    
    return synthetic_data, "SYNTHETIC", "1d"

def detect_swing_points(data, lookback=5, timeframe='4h', significance_threshold=0.01):
    """
    Improved swing point detection with dynamic lookback and significance thresholds.
    """
    lookback_map = {'1h': 8, '4h': 5, '1d': 3, '1w': 2}
    lookback = lookback_map.get(timeframe, 5)

    swing_points = {'highs': [], 'lows': []}
    price_range = max(c['high'] for c in data) - min(c['low'] for c in data) if data else 1
    min_price_diff = price_range * significance_threshold

    for i in range(lookback, len(data) - lookback):
        current = data[i]
        before = [c['high'] for c in data[i - lookback:i]]
        after = [c['high'] for c in data[i + 1:i + 1 + lookback]]
        if current['high'] > max(before) and current['high'] > max(after):
            window_lows = [c['low'] for c in data[i - lookback:i + 1 + lookback]]
            lowest_low = min(window_lows)
            price_diff = current['high'] - lowest_low
            if price_diff >= min_price_diff:
                swing_points['highs'].append({'time': current['time'], 'price': current['high']})

        before_lows = [c['low'] for c in data[i - lookback:i]]
        after_lows = [c['low'] for c in data[i + 1:i + 1 + lookback]]
        if current['low'] < min(before_lows) and current['low'] < min(after_lows):
            window_highs = [c['high'] for c in data[i - lookback:i + 1 + lookback]]
            highest_high = max(window_highs)
            price_diff = highest_high - current['low']
            if price_diff >= min_price_diff:
                swing_points['lows'].append({'time': current['time'], 'price': current['low']})

    print(f"Detected {len(swing_points['highs'])} swing highs and {len(swing_points['lows'])} swing lows")
    return swing_points

def determine_trend(data):
    """
    Determine the overall trend of the chart data.
    """
    if len(data) < 10:
        return 'sideways'
    
    recent_data = data[-10:]
    highs = [c['high'] for c in recent_data]
    lows = [c['low'] for c in recent_data]
    
    is_uptrend = all(highs[i] < highs[i + 1] for i in range(len(highs) - 1)) and \
                 all(lows[i] < lows[i + 1] for i in range(len(lows) - 1))
    
    is_downtrend = all(highs[i] > highs[i + 1] for i in range(len(highs) - 1)) and \
                   all(lows[i] > lows[i + 1] for i in range(len(lows) - 1))
    
    if is_uptrend:
        return 'uptrend'
    elif is_downtrend:
        return 'downtrend'
    else:
        return 'sideways'

def detect_fair_value_gaps(data, gap_type='bullish', min_gap_percent=0.005):
    """
    SIMPLE FVG detection that strictly follows the THREE CANDLE pattern.
    
    Bullish FVG:
    - THREE CANDLE pattern
    - FIRST candle high and THIRD candle low MUST NOT OVERLAP
    
    Bearish FVG:
    - THREE CANDLE pattern
    - FIRST candle low and THIRD candle high MUST NOT OVERLAP
    
    Args:
        data: List of candle data (OHLC)
        gap_type: 'bullish' or 'bearish'
    
    Returns:
        List of detected FVGs
    """
    if not data or len(data) < 3:
        return []
    
    gaps = []
    
    # Calculate minimum gap size for significance
    price_range = max(c['high'] for c in data) - min(c['low'] for c in data) if data else 1
    min_gap_size = price_range * min_gap_percent
    
    # Look for exactly THREE candle patterns
    for i in range(len(data) - 2):
        first_candle = data[i]
        middle_candle = data[i + 1]  # We need the middle candle as part of the pattern
        third_candle = data[i + 2]
        
        if gap_type == 'bullish':
            # FIRST candle high and THIRD candle low must NOT overlap
            gap_size = third_candle['low'] - first_candle['high']
            
            if gap_size > 0 and gap_size >= min_gap_size:  # No overlap
                logging.debug(f"Bullish FVG found at index {i}")
                
                gaps.append({
                    'startTime': first_candle['time'],
                    'endTime': third_candle['time'],
                    'topPrice': third_candle['low'],
                    'bottomPrice': first_candle['high'],
                    'type': 'bullish',
                    'size': gap_size,
                    'firstCandleIndex': i,
                    'thirdCandleIndex': i + 2
                })
        
        elif gap_type == 'bearish':
            # FIRST candle low and THIRD candle high must NOT overlap
            gap_size = first_candle['low'] - third_candle['high']
            
            if gap_size > 0 and gap_size >= min_gap_size:  # No overlap
                logging.debug(f"Bearish FVG found at index {i}")
                
                gaps.append({
                    'startTime': first_candle['time'],
                    'endTime': third_candle['time'],
                    'topPrice': first_candle['low'],
                    'bottomPrice': third_candle['high'],
                    'type': 'bearish',
                    'size': gap_size,
                    'firstCandleIndex': i,
                    'thirdCandleIndex': i + 2
                })
    
    # Sort gaps by size (largest first)
    gaps.sort(key=lambda x: x['size'], reverse=True)
    
    # Limit to the most significant gaps - at most 5 to avoid overcrowding
    result = gaps[:5]
    
    logging.debug(f"Detected {len(result)} {gap_type} FVGs")
    return result

def validate_fair_value_gaps(drawings, chart_data, interval, part):
    """
    Enhanced validation of user-identified FVGs with improved accuracy and reliability.
    Focused on the specific part of the exam (bullish or bearish).
    
    Args:
        drawings: User submitted FVG drawings
        chart_data: Chart candle data
        interval: Timeframe interval
        part: 1 for bullish, 2 for bearish
        
    Returns:
        Validation results
    """
    # Ensure we're only validating the correct FVG type for the current part
    gap_type = 'bullish' if part == 1 else 'bearish'
    
    # Validate chart data before proceeding
    if not chart_data or len(chart_data) < 20:
        return {
            'success': False,
            'message': 'Invalid chart data. Please try another chart.',
            'score': 0,
            'feedback': {
                'correct': [],
                'incorrect': [{
                    'type': 'error',
                    'advice': 'The chart data appears to be incomplete. Please click "Continue" to get a new chart.'
                }]
            },
            'totalExpectedPoints': 0,
            'expected': {'gaps': []}
        }
    
    # Use stricter minimum gap percentage to avoid false positives
    expected_gaps = detect_fair_value_gaps(chart_data, gap_type, min_gap_percent=0.005)
    
    if not expected_gaps:
        # Check if "No FVGs Found" was correctly identified
        if drawings and drawings[0].get('no_fvgs_found', False):
            return {
                'success': True,
                'message': f'Correct! No significant {gap_type} fair value gaps in this chart.',
                'score': 1,
                'feedback': {
                    'correct': [{
                        'type': 'no_gaps',
                        'advice': f'You correctly identified that there are no {gap_type} fair value gaps in this chart.'
                    }],
                    'incorrect': []
                },
                'totalExpectedPoints': 1,
                'expected': {'gaps': []}
            }
        
        return {
            'success': False,
            'message': f'No significant {gap_type} fair value gaps detected in this chart.',
            'score': 0,
            'feedback': {
                'correct': [],
                'incorrect': [{
                    'type': 'no_gaps',
                    'advice': f'There are no significant {gap_type} fair value gaps in this chart. Use the "No FVGs Found" button when appropriate.'
                }]
            },
            'totalExpectedPoints': 1,
            'expected': {'gaps': []}
        }
    
    # If user marked "No FVGs Found" but there are gaps, that's incorrect
    if drawings and drawings[0].get('no_fvgs_found', False):
        return {
            'success': False,
            'message': f'Incorrect. {len(expected_gaps)} {gap_type} fair value gaps were present in this chart.',
            'score': 0,
            'feedback': {
                'correct': [],
                'incorrect': [{
                    'type': 'missed_all_gaps',
                    'advice': f'You marked "No FVGs Found" but there are {len(expected_gaps)} {gap_type} fair value gaps in this chart.'
                }]
            },
            'totalExpectedPoints': len(expected_gaps),
            'expected': {'gaps': expected_gaps}
        }
    
    # Calculate tolerances based on chart range (smaller tolerance than before)
    price_range = max(c['high'] for c in chart_data) - min(c['low'] for c in chart_data) if chart_data else 1
    
    # More reasonable tolerance values
    tolerance_map = {'1h': 0.01, '4h': 0.015, '1d': 0.02, '1w': 0.025}
    price_tolerance = price_range * tolerance_map.get(interval, 0.015)
    
    time_increment = {'1h': 3600, '4h': 14400, '1d': 86400, '1w': 604800}.get(interval, 14400)
    time_tolerance = time_increment * 3
    
    matched_gaps = []
    feedback = {'correct': [], 'incorrect': []}
    used_gaps = set()
    
    # First, validate drawings against expected gaps
    for drawing in drawings:
        drawing_type = drawing.get('type', gap_type)
        if drawing_type != gap_type:
            feedback['incorrect'].append({
                'type': 'incorrect_type',
                'topPrice': drawing.get('topPrice'),
                'bottomPrice': drawing.get('bottomPrice'),
                'advice': f'You marked a {drawing_type} gap, but we\'re looking for {gap_type} gaps in this part.'
            })
            continue
        
        gap_matched = False
        
        for i, gap in enumerate(expected_gaps):
            if i in used_gaps:
                continue
            
            # Check if this is a horizontal line (h-line) drawing
            is_hline = abs(drawing.get('topPrice', 0) - drawing.get('bottomPrice', 0)) < price_tolerance / 10
            
            if is_hline:
                # For h-lines, check if line is in the gap area and near the median of the gap
                price = drawing.get('topPrice', 0)
                gap_median = (gap['topPrice'] + gap['bottomPrice']) / 2
                price_match = abs(price - gap_median) <= price_tolerance
                
                # Time should be within the FVG timeframe
                time_match = drawing.get('startTime', 0) >= gap['startTime'] - time_tolerance and \
                             drawing.get('startTime', 0) <= gap['endTime'] + time_tolerance
                
                if price_match and time_match:
                    matched_gaps.append(gap)
                    used_gaps.add(i)
                    gap_matched = True
                    feedback['correct'].append({
                        'type': gap_type,
                        'topPrice': gap['topPrice'],
                        'bottomPrice': gap['bottomPrice'],
                        'size': gap['size'],
                        'advice': f'Good job! You correctly identified this {gap_type} fair value gap with a horizontal line.'
                    })
                    break
            else:
                # For rectangle drawings, check both price and time boundaries more strictly
                price_match = (
                    abs(drawing.get('topPrice', 0) - gap['topPrice']) <= price_tolerance and
                    abs(drawing.get('bottomPrice', 0) - gap['bottomPrice']) <= price_tolerance
                )
                
                # Check time match - allow some flexibility but ensure general alignment
                time_match = (
                    abs(drawing.get('startTime', 0) - gap['startTime']) <= time_tolerance and
                    abs(drawing.get('endTime', 0) - gap['endTime']) <= time_tolerance
                )
                
                if price_match and time_match:
                    matched_gaps.append(gap)
                    used_gaps.add(i)
                    gap_matched = True
                    feedback['correct'].append({
                        'type': gap_type,
                        'topPrice': gap['topPrice'],
                        'bottomPrice': gap['bottomPrice'],
                        'size': gap['size'],
                        'advice': f'Excellent! You correctly identified this {gap_type} fair value gap.'
                    })
                    break
                
                # If close but not exact, check if it's at least overlapping significantly
                top_overlap = min(drawing.get('topPrice', 0), gap['topPrice'])
                bottom_overlap = max(drawing.get('bottomPrice', 0), gap['bottomPrice'])
                
                # Need sufficient overlap of the gap
                if top_overlap > bottom_overlap and (top_overlap - bottom_overlap) >= gap['size'] * 0.5:
                    # Time should roughly correspond to the gap period
                    if (drawing.get('startTime', 0) <= gap['endTime'] and 
                        drawing.get('endTime', 0) >= gap['startTime']):
                        matched_gaps.append(gap)
                        used_gaps.add(i)
                        gap_matched = True
                        feedback['correct'].append({
                            'type': gap_type,
                            'topPrice': gap['topPrice'],
                            'bottomPrice': gap['bottomPrice'],
                            'size': gap['size'],
                            'advice': f'You identified this {gap_type} fair value gap correctly, though the boundaries could be more precise.'
                        })
                        break
        
        if not gap_matched:
            # More detailed advice for incorrect markings
            feedback['incorrect'].append({
                'type': 'incorrect_gap',
                'topPrice': drawing.get('topPrice'),
                'bottomPrice': drawing.get('bottomPrice'),
                'advice': f'This is not a valid {gap_type} FVG. Remember: {gap_type.capitalize()} FVGs require the 1st candle to be {"bullish" if gap_type == "bearish" else "bearish"}, the 3rd candle to be {"bearish" if gap_type == "bearish" else "bullish"}, and NO OVERLAP between them.'
            })
    
    # Add missed gaps to feedback with specific education about the pattern
    for i, gap in enumerate(expected_gaps):
        if i not in used_gaps:
            first_candle_index = gap.get('firstCandleIndex')
            third_candle_index = gap.get('thirdCandleIndex')
            
            # Get the actual candles if indices are available
            first_candle_desc = ""
            third_candle_desc = ""
            
            if first_candle_index is not None and third_candle_index is not None:
                first_candle = chart_data[first_candle_index]
                third_candle = chart_data[third_candle_index]
                
                # Format dates for readability
                first_date = datetime.fromtimestamp(first_candle['time']).strftime('%Y-%m-%d %H:%M')
                third_date = datetime.fromtimestamp(third_candle['time']).strftime('%Y-%m-%d %H:%M')
                
                first_candle_desc = f" at {first_date}"
                third_candle_desc = f" at {third_date}"
            
            feedback['incorrect'].append({
                'type': 'missed_gap',
                'topPrice': gap['topPrice'],
                'bottomPrice': gap['bottomPrice'],
                'size': gap['size'],
                'advice': f'You missed a {gap_type} FVG from {gap["bottomPrice"]:.4f} to {gap["topPrice"]:.4f}. ' + 
                         f'This gap forms between the {"high" if gap_type == "bullish" else "low"} of the 1st candle{first_candle_desc} and ' +
                         f'the {"low" if gap_type == "bullish" else "high"} of the 3rd candle{third_candle_desc}.'
            })
    
    score = len(matched_gaps)
    total_expected = len(expected_gaps)
    success = score == total_expected and score > 0
    
    return {
        'success': success,
        'message': f"{gap_type.capitalize()} Fair Value Gaps: {score}/{total_expected} correctly identified!",
        'score': score,
        'feedback': feedback,
        'totalExpectedPoints': total_expected,
        'expected': {'gaps': expected_gaps},
        'next_part': 2 if part == 1 else None
    }

def validate_fibonacci_retracement(drawings, chart_data, interval, part):
    default_expected = {'start': {'time': 0, 'price': 0}, 'end': {'time': 0, 'price': 0}, 'direction': 'unknown'}

    logging.debug(f"Validate Fibonacci - Chart Data Length: {len(chart_data)}")
    if not chart_data or len(chart_data) < 10:
        logging.debug("Insufficient chart data in validate_fibonacci_retracement")
        return {
            'success': False,
            'message': 'Insufficient chart data for validation.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'No chart data available. Please try again with a different chart.'}]},
            'totalExpectedPoints': 0,
            'expected': default_expected
        }

    swing_points = detect_swing_points(chart_data, timeframe=interval)
    highs = swing_points['highs']
    lows = swing_points['lows']

    logging.debug(f"Validate Fibonacci - Detected {len(highs)} highs and {len(lows)} lows")

    if len(highs) < 1 or len(lows) < 1:
        logging.debug("Not enough significant swing points for a retracement")
        return {
            'success': False,
            'message': 'Not enough significant swing points for a retracement.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'This chart lacks clear swing points. Try another chart.'}]},
            'totalExpectedPoints': 0,
            'expected': default_expected
        }

    lows_with_subsequent_high = [low for low in lows if any(high['time'] > low['time'] for high in highs)]
    if lows_with_subsequent_high:
        uptrend_low = max(lows_with_subsequent_high, key=lambda x: x['time'])
        subsequent_highs = [high for high in highs if high['time'] > uptrend_low['time']]
        uptrend_high = max(subsequent_highs, key=lambda x: x['time']) if subsequent_highs else None
    else:
        uptrend_low = None
        uptrend_high = None

    highs_with_subsequent_low = [high for high in highs if any(low['time'] > high['time'] for low in lows)]
    if highs_with_subsequent_low:
        downtrend_high = max(highs_with_subsequent_low, key=lambda x: x['time'])
        subsequent_lows = [low for low in lows if low['time'] > downtrend_high['time']]
        downtrend_low = max(subsequent_lows, key=lambda x: x['time']) if subsequent_lows else None
    else:
        downtrend_high = None
        downtrend_low = None

    expected_retracement = (
        {'start': uptrend_low, 'end': uptrend_high, 'direction': 'uptrend'} if part == 1 and uptrend_low and uptrend_high else
        {'start': downtrend_high, 'end': downtrend_low, 'direction': 'downtrend'} if part == 2 and downtrend_high and downtrend_low else
        default_expected
    )

    logging.debug(f"Validate Fibonacci - Expected Retracement: {expected_retracement}")

    if expected_retracement == default_expected:
        logging.debug(f"No significant {'uptrend' if part == 1 else 'downtrend'} retracement found")
        return {
            'success': False,
            'message': f"No significant {'uptrend' if part == 1 else 'downtrend'} retracement found.",
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': f"Couldn't find a clear {'uptrend' if part == 1 else 'downtrend'} retracement. Try another chart."}]},
            'totalExpectedPoints': 2,
            'expected': expected_retracement
        }

    price_range = max(c['high'] for c in chart_data) - min(c['low'] for c in chart_data) if chart_data else 1
    tolerance_map = {'1h': 0.01, '4h': 0.02, '1d': 0.03, '1w': 0.04}
    price_tolerance = price_range * tolerance_map.get(interval, 0.02)
    time_increment = {'1h': 3600, '4h': 14400, '1d': 86400, '1w': 604800}.get(interval, 14400)
    time_tolerance = time_increment * 3

    total_credits = 2
    credits_earned = 0
    feedback = {'correct': [], 'incorrect': []}

    if not drawings:
        feedback['incorrect'].append({
            'type': 'missed_retracement',
            'direction': expected_retracement['direction'],
            'startPrice': expected_retracement['start']['price'],
            'endPrice': expected_retracement['end']['price'],
            'advice': f"You missed the {expected_retracement['direction']} retracement from {expected_retracement['start']['price']:.2f} to {expected_retracement['end']['price']:.2f}."
        })
    else:
        for fib in drawings:
            user_direction = 'uptrend' if fib['end']['price'] > fib['start']['price'] else 'downtrend'
            direction_matched = user_direction == expected_retracement['direction']

            if not direction_matched:
                feedback['incorrect'].append({
                    'type': 'incorrect_direction',
                    'direction': user_direction,
                    'startPrice': fib['start']['price'],
                    'endPrice': fib['end']['price'],
                    'advice': f"Direction incorrect: Expected {expected_retracement['direction']}, but you drew a {user_direction} from {fib['start']['price']:.2f} to {fib['end']['price']:.2f}."
                })
                continue

            start_exact = (abs(fib['start']['time'] - expected_retracement['start']['time']) < time_tolerance and
                           abs(fib['start']['price'] - expected_retracement['start']['price']) < price_tolerance)
            start_close = (abs(fib['start']['time'] - expected_retracement['start']['time']) < time_tolerance * 2 and
                           abs(fib['start']['price'] - expected_retracement['start']['price']) < price_tolerance * 2)
            
            start_credits = 1 if start_exact else 0.5 if start_close else 0
            credits_earned += start_credits

            end_exact = (abs(fib['end']['time'] - expected_retracement['end']['time']) < time_tolerance and
                         abs(fib['end']['price'] - expected_retracement['end']['price']) < price_tolerance)
            end_close = (abs(fib['end']['time'] - expected_retracement['end']['time']) < time_tolerance * 2 and
                         abs(fib['end']['price'] - expected_retracement['end']['price']) < price_tolerance * 2)
            
            end_credits = 1 if end_exact else 0.5 if end_close else 0
            credits_earned += end_credits

            feedback['correct'].append({
                'direction': user_direction,
                'startPrice': fib['start']['price'],
                'endPrice': fib['end']['price'],
                'startCredits': start_credits,
                'endCredits': end_credits,
                'advice': f"Start Price: {start_credits}/1 credit ({'Exact' if start_exact else 'Close' if start_close else 'Incorrect'}), End Price: {end_credits}/1 credit ({'Exact' if end_exact else 'Close' if end_close else 'Incorrect'})"
            })

        if credits_earned == 0:
            feedback['incorrect'].append({
                'type': 'missed_retracement',
                'direction': expected_retracement['direction'],
                'startPrice': expected_retracement['start']['price'],
                'endPrice': expected_retracement['end']['price'],
                'advice': f"You missed the {expected_retracement['direction']} retracement from {expected_retracement['start']['price']:.2f} to {expected_retracement['end']['price']:.2f}."
            })

    success = credits_earned > 0
    score = credits_earned

    return {
        'success': success,
        'message': f"{'Uptrend' if part == 1 else 'Downtrend'} retracement: {score}/{total_credits} credits earned!",
        'score': score,
        'feedback': feedback,
        'totalExpectedPoints': total_credits,
        'expected': expected_retracement,
        'next_part': 2 if part == 1 else None
    }

def validate_swing_points(drawings, chart_data, interval):
    if not chart_data or len(chart_data) < 10:
        return {
            'success': False,
            'message': 'Insufficient chart data for validation.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'No chart data available. Please try again with a different chart.'}]},
            'expected': {'highs': [], 'lows': []},
            'totalExpectedPoints': 0
        }

    swing_points = detect_swing_points(chart_data, timeframe=interval)
    highs = swing_points['highs']
    lows = swing_points['lows']
    expected = {'highs': highs, 'lows': lows}

    if len(highs) + len(lows) == 0:
        return {
            'success': False,
            'message': 'No significant swing points detected in this chart.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'This chart does not have any significant swing points. Try another chart.'}]},
            'expected': expected,
            'totalExpectedPoints': 0
        }

    price_range = max(c['high'] for c in chart_data) - min(c['low'] for c in chart_data) if chart_data else 1
    tolerance_map = {'1h': 0.005, '4h': 0.015, '1d': 0.025, '1w': 0.035}
    price_tolerance = price_range * tolerance_map.get(interval, 0.02)
    time_increment = {'1h': 3600, '4h': 14400, '1d': 86400, '1w': 604800}.get(interval, 14400)
    time_tolerance = time_increment * 3

    matched = 0
    feedback = {'correct': [], 'incorrect': []}
    used_points = set()

    for d in drawings:
        point_matched = False
        for i, point in enumerate(highs + lows):
            if i in used_points:
                continue
            if (abs(d['time'] - point['time']) < time_tolerance and
                abs(d['price'] - point['price']) < price_tolerance):
                matched += 1
                point_matched = True
                used_points.add(i)
                point_type = 'high' if point in highs else 'low'
                feedback['correct'].append({
                    'type': point_type,
                    'time': point['time'],
                    'price': point['price'],
                    'advice': f"Good job! You identified a significant swing {point_type} at price {point['price']:.2f}."
                })
                break
        if not point_matched:
            feedback['incorrect'].append({
                'type': d['type'],
                'time': d['time'],
                'price': d['price'],
                'advice': f"This point at price {d['price']:.2f} doesn't match a significant swing point."
            })

    for i, point in enumerate(highs + lows):
        if i not in used_points:
            point_type = 'high' if point in highs else 'low'
            feedback['incorrect'].append({
                'type': 'missed_point',
                'time': point['time'],
                'price': point['price'],
                'advice': f"You missed a significant swing {point_type} at price {point['price']:.2f}."
            })

    total_expected = len(highs) + len(lows)
    success = matched == total_expected
    score = matched

    return {
        'success': success,
        'message': 'All significant swing points identified correctly!' if success else 'Some swing points were missed or incorrect.',
        'score': score,
        'feedback': feedback,
        'totalExpectedPoints': total_expected,
        'expected': expected
    }

def validate_order_blocks(drawings):
    """
    Basic validation for order blocks. This function can be expanded based on the specific
    criteria for order block identification.
    
    Returns:
        A validation result object.
    """
    # Simple validation that just checks if any boxes were drawn
    if not drawings or len(drawings) == 0:
        return {
            'success': False,
            'message': 'No order blocks identified. Try again!',
            'score': 0,
            'feedback': {
                'correct': [],
                'incorrect': [{
                    'type': 'missing',
                    'advice': 'You need to identify at least one order block. Look for strong momentum candles.'
                }]
            },
            'totalExpectedPoints': 1,
            'expected': {}
        }
    else:
        # For now, consider any drawn box as a potential correct answer
        # This can be enhanced with more specific validation logic
        return {
            'success': True,
            'message': 'Order blocks identified!',
            'score': 1,
            'feedback': {
                'correct': [{
                    'type': 'order_block',
                    'advice': 'Good job! You identified potential order blocks.'
                }],
                'incorrect': []
            },
            'totalExpectedPoints': 1,
            'expected': {}
        }

@app.route('/charting_exam/swing_analysis', methods=['GET'])
def swing_analysis():
    """
    Specialized route for swing analysis exam.
    """
    if 'exam_data' not in session:
        session['exam_data'] = {
            'chart_count': 1,
            'scores': [],
            'chart_data': None,
            'coin': None,
            'timeframe': None
        }

    exam_data = session['exam_data']

    chart_data, coin, timeframe = fetch_chart_data()
    if not chart_data:
        return render_template(
            'charting_exams/swing_analysis.html',
            chart_data=[],
            progress={'chart_count': exam_data['chart_count']},
            symbol="ERROR",
            timeframe=timeframe,
            error="Failed to fetch chart data."
        )
    
    exam_data['chart_data'] = chart_data
    exam_data['coin'] = coin
    exam_data['timeframe'] = timeframe
    session['exam_data'] = exam_data

    return render_template(
        'charting_exams/swing_analysis.html',
        chart_data=chart_data,
        progress={'chart_count': exam_data['chart_count']},
        symbol=coin.upper(),
        timeframe=timeframe
    )

@app.route('/charting_exam/fibonacci_retracement', methods=['GET', 'POST'])
def fibonacci_retracement():
    """
    Specialized route for Fibonacci retracement exam.
    """
    # Check if reset is explicitly requested
    if request.args.get('reset') == 'true':
        session.pop('exam_data', None)

    # Important: Only initialize if exam_data doesn't exist or is not a Fibonacci exam
    if 'exam_data' not in session or session['exam_data'].get('type') != 'fibonacci':
        session['exam_data'] = {
            'type': 'fibonacci',
            'chart_count': 1,
            'fibonacci_part': 1,
            'scores': [],
            'chart_data': None,
            'coin': None,
            'timeframe': None,
            'interval': None,         # Add missing keys
            'current_section': 0,     # Add missing keys
            'question_index': 0       # Add missing keys
        }

    exam_data = session['exam_data']

    if request.method == 'GET':
        # Only fetch new chart data if it doesn't exist or if reset was requested
        if exam_data.get('chart_data') is None or request.args.get('reset') == 'true':
            chart_data, coin, timeframe = fetch_chart_data(limit=100)  # Ensure enough candles
            if not chart_data:
                return render_template(
                    'charting_exams/fibonacci_retracement.html',  # FIXED PATH
                    chart_data=[],
                    progress={'chart_count': exam_data['chart_count'], 'fibonacci_part': exam_data['fibonacci_part']},
                    symbol="ERROR",
                    timeframe=timeframe,
                    error="Failed to fetch chart data."
                )
            
            exam_data['chart_data'] = chart_data
            exam_data['coin'] = coin
            exam_data['timeframe'] = timeframe
            session['exam_data'] = exam_data
        else:
            # Use existing data from session
            chart_data = exam_data['chart_data']
            coin = exam_data['coin']
            timeframe = exam_data['timeframe']

        logging.debug(f"Fibonacci Retracement - Stored Chart Data Length: {len(chart_data)}")

        return render_template(
            'charting_exams/fibonacci_retracement.html',  # FIXED PATH
            chart_data=chart_data,
            progress={'chart_count': exam_data['chart_count'], 'fibonacci_part': exam_data['fibonacci_part']},
            symbol=coin.upper(),
            timeframe=timeframe
        )
    return jsonify({'message': 'Fibonacci Retracement POST received'})

@app.route('/charting_exam/fair_value_gaps', methods=['GET', 'POST'])
def fair_value_gaps():
    """
    Specialized route for fair value gaps exam.
    """
    if 'exam_data' not in session:
        session['exam_data'] = {
            'chart_count': 1,
            'fvg_part': 1,
            'scores': [],
            'chart_data': None,
            'coin': None,
            'timeframe': None
        }

    exam_data = session['exam_data']

    if request.method == 'GET':
        chart_data, coin, timeframe = fetch_chart_data()
        
        # Validate the chart data
        is_valid, message = validate_chart_data(chart_data, coin, timeframe)
        
        # If data is invalid, try to get a different chart
        if not is_valid:
            logging.warning(f"Invalid chart data: {message}")
            chart_data, coin, timeframe = refresh_problem_chart()
        
        if not chart_data:
            return render_template(
                'fair_value_gaps.html',
                chart_data=[],
                progress={'chart_count': exam_data['chart_count'], 'fvg_part': exam_data['fvg_part']},
                symbol="ERROR",
                timeframe=timeframe,
                error="Failed to fetch chart data."
            )
        
        exam_data['chart_data'] = chart_data
        exam_data['coin'] = coin
        exam_data['timeframe'] = timeframe
        exam_data['fvg_part'] = 1
        session['exam_data'] = exam_data

        logging.debug(f"Fair Value Gaps - Stored Chart Data Length: {len(chart_data)}")
        logging.debug(f"Fair Value Gaps - Coin: {coin}, Timeframe: {timeframe}")

        return render_template(
            'fair_value_gaps.html',
            chart_data=chart_data,
            progress={'chart_count': exam_data['chart_count'], 'fvg_part': exam_data['fvg_part']},
            symbol=coin.upper(),
            timeframe=timeframe
        )
    return jsonify({'message': 'Fair Value Gaps POST received'})

@app.route('/charting_exam/orderblocks', methods=['GET', 'POST'])
def orderblocks():
    """
    Specialized route for order blocks exam.
    """
    if 'exam_data' not in session:
        session['exam_data'] = {
            'chart_count': 1,
            'scores': [],
            'chart_data': None,
            'coin': None,
            'timeframe': None
        }

    exam_data = session['exam_data']

    if request.method == 'GET':
        chart_data, coin, timeframe = fetch_chart_data()
        
        # Validate the chart data
        is_valid, message = validate_chart_data(chart_data, coin, timeframe)
        
        # If data is invalid, try to get a different chart
        if not is_valid:
            logging.warning(f"Invalid chart data in orderblocks: {message}")
            chart_data, coin, timeframe = refresh_problem_chart()
            
        if not chart_data:
            return render_template(
                'orderblocks.html',
                chart_data=[],
                progress={'chart_count': exam_data['chart_count']},
                symbol="ERROR",
                timeframe=timeframe,
                error="Failed to fetch chart data."
            )
        
        exam_data['chart_data'] = chart_data
        exam_data['coin'] = coin
        exam_data['timeframe'] = timeframe
        session['exam_data'] = exam_data

        return render_template(
            'orderblocks.html',
            chart_data=chart_data,
            progress={'chart_count': exam_data['chart_count']},
            symbol=coin.upper(),
            timeframe=timeframe
        )
    return jsonify({'message': 'Orderblocks POST received'})

@app.route('/fetch_new_chart', methods=['GET'])
def fetch_new_chart():
    """
    Enhanced route to fetch a new chart for the charting exam.
    """
    exam_data = session.get('exam_data', {
        'chart_count': 1, 
        'fibonacci_part': 1, 
        'fvg_part': 1
    })
    
    current_chart_count = exam_data.get('chart_count', 1)
    
    # Get the next chart - ensure enough candles for visual analysis
    chart_data, coin, timeframe = fetch_chart_data(limit=100)
    
    # Validate the chart data
    is_valid, message = validate_chart_data(chart_data, coin, timeframe)
    
    # If data is invalid, try to get a different chart
    if not is_valid:
        logging.warning(f"Invalid chart data in fetch_new_chart: {message}")
        chart_data, coin, timeframe = refresh_problem_chart()
    
    if not chart_data:
        return jsonify({
            'chart_data': [],
            'chart_count': current_chart_count,
            'fibonacci_part': exam_data.get('fibonacci_part', 1),
            'fvg_part': exam_data.get('fvg_part', 1),
            'symbol': "ERROR",
            'timeframe': timeframe,
            'error': "Failed to fetch chart data."
        })

    # Reset exam part to 1 for multi-part exams
    if 'fibonacci_part' in exam_data:
        exam_data['fibonacci_part'] = 1
    if 'fvg_part' in exam_data:
        exam_data['fvg_part'] = 1
        
    # Update exam data with new chart
    exam_data['chart_data'] = chart_data
    exam_data['coin'] = coin
    exam_data['timeframe'] = timeframe
    session['exam_data'] = exam_data

    logging.debug(f"Fetch New Chart - Stored Chart Data Length: {len(chart_data)}")
    logging.debug(f"Fetch New Chart - Current chart_count: {exam_data['chart_count']}")

    return jsonify({
        'chart_data': chart_data,
        'chart_count': exam_data['chart_count'],
        'fibonacci_part': exam_data.get('fibonacci_part', 1),
        'fvg_part': exam_data.get('fvg_part', 1),
        'symbol': coin.upper(),
        'timeframe': timeframe
    })

@app.route('/charting_exam/validate', methods=['POST'])
def validate_drawing():
    """
    Enhanced unified validation route for all drawing types.
    """
    data = request.get_json()
    exam_type = data.get('examType')
    drawings = data.get('drawings', [])
    chart_count = data.get('chartCount')

    exam_data = session.get('exam_data', {})
    chart_data = exam_data.get('chart_data', [])
    interval = exam_data.get('timeframe', '4h')
    
    # Route to the appropriate validation function based on exam type
    if exam_type == 'fibonacci_retracement' or exam_type == 'fibonacci':
        fibonacci_part = exam_data.get('fibonacci_part', 1)
        chart_count = exam_data.get('chart_count', 1)
        validation_result = validate_fibonacci_retracement(drawings, chart_data, interval, fibonacci_part)
        
        if fibonacci_part == 1:
            # Save first part score and move to second part
            if 'scores' not in exam_data:
                exam_data['scores'] = []
            
            # Make sure we have enough elements in the scores array
            while len(exam_data['scores']) < chart_count:
                exam_data['scores'].append({})
                
            exam_data['scores'][chart_count - 1]['uptrend'] = validation_result['score']
            exam_data['fibonacci_part'] = 2
            session['exam_data'] = exam_data
            validation_result['next_part'] = 2
        else:
            # Save second part score and calculate average
            exam_data['scores'][chart_count - 1]['downtrend'] = validation_result['score']
            avg_score = (exam_data['scores'][chart_count - 1]['uptrend'] + validation_result['score']) / 2
            exam_data['scores'][chart_count - 1]['average'] = avg_score
            
            # Move to next chart if appropriate
            current_chart_count = exam_data.get('chart_count', 1)
            if current_chart_count < 5:
                exam_data['chart_count'] = current_chart_count + 1
            exam_data['fibonacci_part'] = 1
            
            session['exam_data'] = exam_data
            validation_result['next_part'] = None
            chart_count = exam_data['chart_count']
    
    elif exam_type == 'swing_analysis':
        validation_result = validate_swing_points(drawings, chart_data, interval)
        
        # Store the score in session
        if 'scores' not in exam_data:
            exam_data['scores'] = []
        
        # Append the score for this chart attempt
        exam_data['scores'].append(validation_result['score'])
        
        # Get the current chart count
        current_chart_count = exam_data.get('chart_count', 1)
        
        # Increment chart count if not at max
        if current_chart_count < 5:
            exam_data['chart_count'] = current_chart_count + 1
        
        # Update session
        session['exam_data'] = exam_data
        
        # Return the updated chart count to the client
        chart_count = exam_data['chart_count']
        
    elif exam_type == 'gap_analysis' or exam_type == 'fair_value_gaps':
        fvg_part = exam_data.get('fvg_part', 1)
        chart_count = exam_data.get('chart_count', 1)
        validation_result = validate_fair_value_gaps(drawings, chart_data, interval, fvg_part)
        
        if fvg_part == 1:
            # Save first part (bullish FVGs) score and move to second part
            if 'scores' not in exam_data:
                exam_data['scores'] = []
                
            # Make sure we have enough elements in the scores array
            while len(exam_data['scores']) < chart_count:
                exam_data['scores'].append({})
                
            exam_data['scores'][chart_count - 1]['bullish'] = validation_result['score']
            exam_data['fvg_part'] = 2
            session['exam_data'] = exam_data
            validation_result['next_part'] = 2
        else:
            # Save second part (bearish FVGs) score and calculate average
            exam_data['scores'][chart_count - 1]['bearish'] = validation_result['score']
            avg_score = (exam_data['scores'][chart_count - 1]['bullish'] + validation_result['score']) / 2
            exam_data['scores'][chart_count - 1]['average'] = avg_score
            
            # Move to next chart if appropriate
            current_chart_count = exam_data.get('chart_count', 1)
            if current_chart_count < 5:
                exam_data['chart_count'] = current_chart_count + 1
            exam_data['fvg_part'] = 1
            
            session['exam_data'] = exam_data
            validation_result['next_part'] = None
            chart_count = exam_data['chart_count']
    elif exam_type == 'order_blocks':
        validation_result = validate_order_blocks(drawings)
        
        # Add basic score tracking
        if 'scores' not in exam_data:
            exam_data['scores'] = []
        exam_data['scores'].append(1 if validation_result['success'] else 0)
        
        # Increment chart count if not at max
        current_chart_count = exam_data.get('chart_count', 1)
        if current_chart_count < 5:
            exam_data['chart_count'] = current_chart_count + 1
        
        # Update session
        session['exam_data'] = exam_data
        chart_count = exam_data['chart_count']
    else:
        return jsonify({'success': False, 'message': 'Exam type not implemented yet'})

    response = {
        'success': validation_result['success'],
        'message': validation_result['message'],
        'chart_count': chart_count,
        'feedback': validation_result['feedback'],
        'score': validation_result['score'],
        'totalExpectedPoints': validation_result['totalExpectedPoints'],
        'expected': validation_result.get('expected', {})
    }
    
    # Add specific fields for different exam types
    if exam_type == 'fibonacci_retracement' or exam_type == 'fibonacci':
        response['fibonacci_part'] = exam_data.get('fibonacci_part', 1)
        response['next_part'] = validation_result.get('next_part')
    elif exam_type == 'gap_analysis' or exam_type == 'fair_value_gaps':
        response['fvg_part'] = exam_data.get('fvg_part', 1)
        response['next_part'] = validation_result.get('next_part')
        
    response['symbol'] = exam_data.get('coin', 'Unknown').upper()
    
    return jsonify(response)

@app.route('/charting_exam/<exam_type>/practice', methods=['GET', 'POST'])
def charting_exam_practice(exam_type):
    print(f"Session before processing: {session.get('exam_data', 'No exam data')}")
    print(f"URL parameters: {request.args}")
    
    if exam_type not in charting_exam_descriptions:
        return redirect(url_for('charting_exams'))
    
    # Check if reset is explicitly requested via query parameter
    reset_requested = request.args.get('reset') == 'true'
    if reset_requested:
        print("Reset explicitly requested, clearing exam data")
        if 'exam_data' in session:
            session.pop('exam_data')
    
    # Define default exam data structure
    default_exam_data = {
        'type': exam_type,
        'current_section': 0,
        'question_index': 0,
        'score': 0,
        'drawings': [],
        'validations': [],
        'chart_data': None,
        'chart_count': 1,
        'interval': None,
        'fibonacci_part': 1,
        'fvg_part': 1,
        'coin': None,
        'timeframe': None
    }
    
    # Check if we need to initialize new data or use existing
    if 'exam_data' not in session:
        print("No exam_data in session, creating new")
        session['exam_data'] = default_exam_data.copy()
    elif session['exam_data'].get('type') != exam_type:
        print(f"Exam type mismatch: session has {session['exam_data'].get('type')} but URL has {exam_type}")
        session['exam_data'] = default_exam_data.copy()
    else:
        print("Using existing exam_data from session")
        # Ensure all required keys exist
        for key, value in default_exam_data.items():
            if key not in session['exam_data']:
                print(f"Adding missing key to exam_data: {key}")
                session['exam_data'][key] = value
    
    # Get section from URL if present
    requested_section = request.args.get('section')
    if requested_section:
        print(f"Section requested in URL: {requested_section}")
        if requested_section == 'swing_points':
            session['exam_data']['current_section'] = 0
        elif requested_section == 'equal_levels':
            session['exam_data']['current_section'] = 1
        else:
            session['exam_data']['current_section'] = 2
    
    # Now access the exam_data from session
    exam_data = session['exam_data']
    
    # Determine template path - ALWAYS include the subfolder
    if exam_type == 'fibonacci':
        template = 'charting_exams/fibonacci_retracement.html'
        section = 'fib_retracement'
        instruction = "Draw Fibonacci retracements for both uptrend (low to high) and downtrend (high to low) scenarios."
    elif exam_type == 'gap_analysis':
        template = 'charting_exams/fvg_practice.html'
        section = 'fvg'
        instruction = "Identify Fair Value Gaps in the chart. Draw bullish FVGs (when price jumps up with a gap) and bearish FVGs (when price gaps down)."
    else:
        section = requested_section or ('swing_points' if exam_data['current_section'] == 0 else 
                                       ('equal_levels' if exam_data['current_section'] == 1 else 'fib_retracement'))
        questions = swing_analysis_data.get(section, swing_analysis_data['swing_points'])['questions']
        instruction = questions[exam_data['question_index']]['instruction']
        template = 'charting_exams/practice.html'
        if section == 'equal_levels':
            template = 'charting_exams/equal_levels_practice.html'
        elif section == 'fib_retracement':
            template = 'charting_exams/fibonacci_retracement.html'
    
    # Check if we need to fetch new chart data
    fetch_new_data = reset_requested or exam_data.get('chart_data') is None
    print(f"Fetch new data? {fetch_new_data}")
    
    if fetch_new_data:
        print("Fetching new chart data")
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LTCUSDT", "LINKUSDT"]
        intervals = ["5m", "4h", "1d", "1w"]
        selected_interval = random.choice(intervals)
        
        selected_symbol = random.choice(symbols)
        coingecko_symbol = symbol_map.get(selected_symbol, "bitcoin")
        
        chart_data, coin, selected_interval = fetch_chart_data(coin=coingecko_symbol, timeframe=selected_interval, limit=100)
        
        exam_data['chart_data'] = chart_data
        exam_data['coin'] = coin
        exam_data['interval'] = selected_interval
        # Explicitly update the session
        session['exam_data'] = exam_data
        session.modified = True
    else:
        print("Using existing chart data from session")
        chart_data = exam_data.get('chart_data', [])
        coin = exam_data.get('coin', 'bitcoin')
        
        # Ensure interval exists
        if 'interval' not in exam_data or exam_data['interval'] is None:
            intervals = ["5m", "4h", "1d", "1w"]
            selected_interval = random.choice(intervals)
            exam_data['interval'] = selected_interval
            session['exam_data'] = exam_data
            session.modified = True
        else:
            selected_interval = exam_data['interval']
    
    # Default questions array for certain exam types
    if exam_type == 'fibonacci' or exam_type == 'gap_analysis':
        questions = [{'instruction': instruction}]
    
    # Force session save
    session.modified = True
    print(f"Final session exam_data: {session.get('exam_data', 'No exam data')}")
    
    return render_template(
        template,
        exam_type=exam_type,
        exam_info=charting_exam_descriptions[exam_type],
        tools=charting_exam_descriptions[exam_type]['tools_required'],
        chart_data=chart_data,
        instructions=instruction,
        current_section=section,
        progress={
            'section': exam_data.get('current_section', 0) + 1,
            'total_sections': len(swing_analysis_data.keys()) - 1 if exam_type == 'swing_analysis' else 1,
            'question': exam_data.get('question_index', 0) + 1,
            'total_questions': len(questions) if exam_type != 'fibonacci' and exam_type != 'gap_analysis' else 1,
            'chart_count': exam_data.get('chart_count', 1),
            'fibonacci_part': exam_data.get('fibonacci_part', 1),
            'fvg_part': exam_data.get('fvg_part', 1)
        },
        symbol=coin.upper(),
        interval=selected_interval,
        timeframe=selected_interval, 
        section=section
    )


@app.route('/charting_exams')
def charting_exams():
    session.pop('exam_data', None)
    return render_template(
        'charting_exams/index.html',
        exam_descriptions=charting_exam_descriptions
    )


@app.route('/charting_exam/<exam_type>')
def charting_exam_intro(exam_type):
    if exam_type not in charting_exam_descriptions:
        return redirect(url_for('charting_exams'))
    return render_template(
        'charting_exams/intro.html',
        exam_type=exam_type,
        exam_info=charting_exam_descriptions[exam_type]
    )

def track_server_event(event_name, category=None, label=None, value=None):
    """Track server-side events using Google Analytics Measurement Protocol."""
    # For production use, you would implement the actual Measurement Protocol
    # This is a placeholder for logging the events
    app.logger.info(f"ANALYTICS EVENT: {event_name}, Category: {category}, Label: {label}, Value: {value}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)