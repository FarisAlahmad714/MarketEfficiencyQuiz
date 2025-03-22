from flask import Flask, jsonify, render_template, request, redirect, url_for, make_response, session, flash
import os
import random
import time
import requests
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
from datetime import datetime

validator = CandleAnalyzer('static')
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Create necessary directories
os.makedirs("static/crypto", exist_ok=True)
os.makedirs("static/equities", exist_ok=True)
os.makedirs("cache", exist_ok=True)

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
        "description": "Complete order block analysis including liquidity, BOS, and reaction",
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

# Lazy loading function
def load_asset_data(asset_code):
    """Load data for an asset only when needed"""
    if asset_code in BIAS_TEST_DATA and BIAS_TEST_DATA[asset_code]:
        return BIAS_TEST_DATA[asset_code]
    
    try:
        if asset_code == 'random':
            # Generate random dataset
            if not BIAS_TEST_DATA.get('random'):
                BIAS_TEST_DATA['random'] = []
                # Only use assets we've already loaded to avoid cascade
                for code in list(BIAS_TEST_DATA.keys()):
                    if code != 'random' and BIAS_TEST_DATA[code]:
                        test = random.choice(BIAS_TEST_DATA[code])
                        test['asset_code'] = code
                        test['asset_info'] = get_asset_info(code)
                        BIAS_TEST_DATA['random'].append(test)
                random.shuffle(BIAS_TEST_DATA['random'])
            return BIAS_TEST_DATA['random']
        
        # For a specific asset
        asset_type = "crypto" if asset_code in CRYPTO_ASSETS else "equities"
        BIAS_TEST_DATA[asset_code] = prepare_bias_test(asset_code, asset_type, 5)
        return BIAS_TEST_DATA[asset_code]
    except Exception as e:
        print(f"Error loading data for {asset_code}: {str(e)}")
        BIAS_TEST_DATA[asset_code] = []
        return []

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

@app.route('/charting_exams')
def charting_exams():
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

def fetch_coingecko_data(symbol="bitcoin", interval="1d", limit=50):
    # Map intervals to valid CoinGecko 'days' parameters
    if interval == '5m':
        days = 1
    elif interval == '4h':
        days = 7
    elif interval == '1d':
        days = 30
    elif interval == '1w':
        days = 365
    else:
        days = 30  # Fallback

    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/ohlc?vs_currency=usd&days={days}"
    headers = {"x-cg-demo-api-key": "CG-X9rKSiVeFyMS6FPbUCaFw4Lc"}  # Replace with your actual API key
    print(f"Fetching CoinGecko data for {symbol} ({interval}, {limit} candles, {days} days)")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"CoinGecko API response status: {response.status_code}")
        if response.status_code != 200:
            print(f"CoinGecko API error: {response.status_code} - {response.text}")
            return []
        data = response.json()
        print(f"Received {len(data)} candles from CoinGecko")
        candles_to_take = min(limit, len(data))
        candles = [
            {
                'time': int(candle[0]) // 1000,
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'symbol': symbol.upper() + 'USD'
            }
            for candle in data[-candles_to_take:]
        ]
        print(f"Fetched {len(candles)} candles for {symbol} ({interval})")
        return candles
    except requests.exceptions.RequestException as e:
        print(f"CoinGecko request failed: {str(e)}")
        return []

@app.route('/charting_exam/<exam_type>/practice', methods=['GET', 'POST'])
def charting_exam_practice(exam_type):
    if exam_type not in charting_exam_descriptions:
        return redirect(url_for('charting_exams'))
        
    requested_section = request.args.get('section')
    session['exam_data'] = {
        'type': exam_type,
        'current_section': 0 if not requested_section or requested_section == 'swing_points' else (1 if requested_section == 'equal_levels' else 2),
        'question_index': 0,
        'score': 0,
        'drawings': [],
        'validations': [],
        'chart_data': None,
        'chart_count': 1,
        'interval': None,
        'fibonacci_part': 1
    }
    
    exam_data = session['exam_data']
    
    if exam_type == 'fibonacci':
        template = 'charting_exams/fibonacci_practice.html'
        section = 'fib_retracement'
        instruction = "Draw Fibonacci retracements for both uptrend (low to high) and downtrend (high to low) scenarios."
    else:
        section = requested_section or ('swing_points' if exam_data['current_section'] == 0 else ('equal_levels' if exam_data['current_section'] == 1 else 'fib_retracement'))
        questions = swing_analysis_data.get(section, swing_analysis_data['swing_points'])['questions']
        instruction = questions[exam_data['question_index']]['instruction']
        template = 'charting_exams/practice.html'
        if section == 'equal_levels':
            template = 'charting_exams/equal_levels_practice.html'
        elif section == 'fib_retracement':
            template = 'charting_exams/fibonacci_practice.html'
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LTCUSDT", "LINKUSDT"]
    intervals = ["5m", "4h", "1d", "1w"]
    selected_interval = random.choice(intervals)
    candle_limits = {'5m': 200, '4h': 100, '1d': 75, '1w': 50}
    limit = candle_limits[selected_interval]
    
    selected_symbol = random.choice(symbols)
    coingecko_symbol = symbol_map.get(selected_symbol, "bitcoin")
    
    chart_data = fetch_coingecko_data(
        symbol=coingecko_symbol,
        interval=selected_interval,
        limit=limit
    )
    
    # Define realistic base prices for synthetic data
    base_prices = {
        "BTCUSDT": 40000, "ETHUSDT": 3000, "BNBUSDT": 400, "SOLUSDT": 100,
        "XRPUSDT": 0.5, "LTCUSDT": 70, "LINKUSDT": 20
    }
    if not chart_data or len(chart_data) < 10:
        time_increment = {'5m': 300, '4h': 14400, '1d': 86400, '1w': 604800}[selected_interval]
        start_time = 1743350400  # March 1, 2025, for future-looking data
        base_price = base_prices.get(selected_symbol, 40000)
        chart_data = [
            {
                'time': start_time + i * time_increment,
                'open': base_price + i * 0.1,
                'high': base_price + 0.2 + i * 0.1,
                'low': base_price - 0.1 + i * 0.1,
                'close': base_price + 0.15 + i * 0.1,
                'symbol': selected_symbol
            }
            for i in range(limit)
        ]
        print(f"Using synthetic data for {selected_symbol} ({selected_interval}): {len(chart_data)} candles")
    
    chart_data_for_frontend = [
        {k: v for k, v in candle.items() if k != 'symbol'}
        for candle in chart_data
    ]
    print(f"Passing {len(chart_data_for_frontend)} candles to frontend")
    session['exam_data']['chart_data'] = chart_data_for_frontend
    session['exam_data']['interval'] = selected_interval

    return render_template(
        template,
        exam_type=exam_type,
        exam_info=charting_exam_descriptions[exam_type],
        tools=charting_exam_descriptions[exam_type]['tools_required'],
        chart_data=chart_data_for_frontend,
        instructions=instruction,
        current_section=section,
        progress={
            'section': exam_data['current_section'] + 1,
            'total_sections': len(swing_analysis_data.keys()) - 1 if exam_type == 'swing_analysis' else 1,
            'question': exam_data['question_index'] + 1,
            'total_questions': len(questions) if exam_type != 'fibonacci' else 1,
            'chart_count': exam_data['chart_count']
        },
        symbol=selected_symbol,
        interval=selected_interval,
        section=section
    )

@app.route('/fetch_new_chart', methods=['GET'])
def fetch_new_chart():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LTCUSDT", "LINKUSDT"]
    intervals = ["5m", "4h", "1d", "1w"]
    selected_interval = random.choice(intervals)
    candle_limits = {'5m': 200, '4h': 100, '1d': 75, '1w': 50}
    limit = candle_limits[selected_interval]
    
    selected_symbol = random.choice(symbols)
    coingecko_symbol = symbol_map.get(selected_symbol, "bitcoin")
    
    chart_data = fetch_coingecko_data(
        symbol=coingecko_symbol,
        interval=selected_interval,
        limit=limit
    )
    
    base_prices = {
        "BTCUSDT": 40000, "ETHUSDT": 3000, "BNBUSDT": 400, "SOLUSDT": 100,
        "XRPUSDT": 0.5, "LTCUSDT": 70, "LINKUSDT": 20
    }
    if not chart_data or len(chart_data) < 10:
        time_increment = {'5m': 300, '4h': 14400, '1d': 86400, '1w': 604800}[selected_interval]
        start_time = 1743350400  # March 1, 2025
        base_price = base_prices.get(selected_symbol, 40000)
        chart_data = [
            {
                'time': start_time + i * time_increment,
                'open': base_price + i * 0.1,
                'high': base_price + 0.2 + i * 0.1,
                'low': base_price - 0.1 + i * 0.1,
                'close': base_price + 0.15 + i * 0.1,
                'symbol': selected_symbol
            }
            for i in range(limit)
        ]
        print(f"Using synthetic data for {selected_symbol} ({selected_interval}): {len(chart_data)} candles")
    
    chart_data_for_frontend = [
        {k: v for k, v in candle.items() if k != 'symbol'}
        for candle in chart_data
    ]
    print(f"Returning {len(chart_data_for_frontend)} candles to frontend")
    
    exam_data = session.get('exam_data', {'chart_count': 1})
    current_count = exam_data.get('chart_count', 1)
    exam_data['chart_count'] = current_count + 1
    if exam_data['chart_count'] > 5:
        exam_data['chart_count'] = 1
    exam_data['chart_data'] = chart_data_for_frontend
    exam_data['interval'] = selected_interval
    session['exam_data'] = exam_data
    
    return jsonify({
        'chart_data': chart_data_for_frontend,
        'chart_count': exam_data['chart_count'],
        'symbol': selected_symbol,
        'interval': selected_interval
    })

@app.route('/charting_exam/validate', methods=['POST'])
def validate_drawing():
    data = request.get_json()
    exam_type = data.get('examType')
    section = data.get('section', 'swing_points')
    drawings = data.get('drawings', [])
    chart_count = data.get('chartCount')
    chart_data = data.get('chartData')
    
    exam_data = session.get('exam_data', {'chart_count': 1, 'score': 0})
    chart_data = exam_data.get('chart_data', [{}])
    interval = exam_data.get('interval', '4h')
    
    if exam_type == 'swing_analysis':
        validation_result = validate_swing_points(drawings, section)
    elif exam_type == 'fibonacci' and section == 'fib_retracement':
        validation_result = validate_fibonacci(drawings, chart_data)
    else:
        return jsonify({'success': False, 'message': 'Exam type or section not implemented yet'})
    
    current_count = exam_data.get('chart_count', 1)
    symbol = chart_data[0].get('symbol', 'Unknown') if chart_data else 'Unknown'

    if 'expected' not in validation_result:
        validation_result['expected'] = {'start': {'price': 0, 'time': 0}, 'end': {'price': 0, 'time': 0}}
    if 'score' not in validation_result:
        validation_result['score'] = 0
    if 'feedback' not in validation_result:
        validation_result['feedback'] = {'correct': [], 'incorrect': []}
    if 'totalExpectedPoints' not in validation_result:
        validation_result['totalExpectedPoints'] = 1
    
    if 'score' not in exam_data:
        exam_data['score'] = 0
    exam_data['score'] += validation_result['score']
    exam_data['chart_count'] = current_count
    session['exam_data'] = exam_data
    
    return jsonify({
        'success': validation_result['success'],
        'message': validation_result['message'],
        'chart_count': current_count,
        'symbol': symbol,
        'feedback': validation_result['feedback'],
        'score': validation_result['score'],
        'totalExpectedPoints': validation_result['totalExpectedPoints'],
        'expected': validation_result['expected']
    })

def validate_swing_points(drawings, section):
    exam_data = session.get('exam_data', {})
    chart_data = exam_data.get('chart_data', [])
    interval = exam_data.get('interval', '4h')
    if not chart_data or len(chart_data) < 10:
        return {
            'success': False,
            'message': 'Insufficient chart data for validation.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'No chart data available.'}]},
            'expected': {'start': {'price': 0, 'time': 0}, 'end': {'price': 0, 'time': 0}},
            'totalExpectedPoints': 4
        }
    
    def pixel_to_price_time(x, y, chart_width=800, chart_height=600):
        times = [c['time'] for c in chart_data]
        prices = [c['high'] for c in chart_data] + [c['low'] for c in chart_data]
        if not times or not prices:
            return 0, 0
        time_range = times[-1] - times[0]
        price_range = max(prices) - min(prices)
        time = times[0] + (x / chart_width) * time_range
        price = min(prices) + (1 - y / chart_height) * price_range
        return time, price

    price_range = max(c['high'] for c in chart_data) - min(c['low'] for c in chart_data) if chart_data else 1
    tolerance_map = {'5m': 0.005, '4h': 0.015, '1d': 0.025, '1w': 0.035}
    price_tolerance = price_range * tolerance_map.get(interval, 0.02)
    time_increment = {'5m': 300, '4h': 14400, '1d': 86400, '1w': 604800}.get(interval, 14400)
    time_tolerance = time_increment * 3

    if section == 'swing_points':
        swing_points = detect_swing_points(chart_data, lookback=5)
        highs = sorted(swing_points['highs'], key=lambda x: x['price'], reverse=True)[:2]
        lows = sorted(swing_points['lows'], key=lambda x: x['price'])[:2]
        required_points = [(p['time'], p['price']) for p in highs] + [(p['time'], p['price']) for p in lows]
        
        if len(required_points) < 4:
            return {
                'success': False,
                'message': 'Not enough significant swing points detected.',
                'score': 0,
                'feedback': {'correct': [], 'incorrect': [{'advice': f"Detected only {len(highs)} highs and {len(lows)} lows—need 2 of each."}]},
                'expected': {
                    'start': {'price': lows[0]['price'] if lows else 0, 'time': lows[0]['time'] if lows else 0},
                    'end': {'price': highs[0]['price'] if highs else 0, 'time': highs[0]['time'] if highs else 0}
                },
                'totalExpectedPoints': 4
            }
        
        matched = 0
        feedback = {'correct': [], 'incorrect': []}
        used_points = set()
        
        for d in drawings:
            if d['type'] == 'line':
                start_t, start_p = pixel_to_price_time(d['start']['x'], d['start']['y'])
                end_t, end_p = pixel_to_price_time(d['end']['x'], d['end']['y'])
                point_matched = False
                
                for i, (rt, rp) in enumerate(required_points):
                    if i in used_points:
                        continue
                    if (abs(start_t - rt) < time_tolerance and abs(start_p - rp) < price_tolerance) or \
                       (abs(end_t - rt) < time_tolerance and abs(end_p - rp) < price_tolerance):
                        matched += 1
                        point_matched = True
                        used_points.add(i)
                        point_type = 'high' if rp in [h['price'] for h in highs] else 'low'
                        feedback['correct'].append({
                            'type': 'swing_point',
                            'time': rt,
                            'price': rp,
                            'advice': f"Good job! You identified a swing {point_type} at price {rp:.2f}."
                        })
                        break
                
                if not point_matched:
                    feedback['incorrect'].append({
                        'type': 'swing_point',
                        'start_time': start_t,
                        'start_price': start_p,
                        'end_time': end_t,
                        'end_price': end_p,
                        'advice': f"This line (start: {start_p:.2f}, end: {end_p:.2f}) doesn't match a significant swing point."
                    })
        
        for i, (rt, rp) in enumerate(required_points):
            if i not in used_points:
                point_type = 'high' if rp in [h['price'] for h in highs] else 'low'
                feedback['incorrect'].append({
                    'type': 'missed_point',
                    'time': rt,
                    'price': rp,
                    'advice': f"You missed a swing {point_type} at price {rp:.2f}."
                })
        
        total_expected = 4
        success = matched >= total_expected
        score = min(matched / total_expected, 1.0)
        expected = {
            'start': {'price': lows[0]['price'] if lows else 0, 'time': lows[0]['time'] if lows else 0},
            'end': {'price': highs[0]['price'] if highs else 0, 'time': highs[0]['time'] if highs else 0}
        }
        
        return {
            'success': success,
            'message': 'Swing points identified correctly!' if success else 'Some swing points were missed or incorrect.',
            'score': score,
            'feedback': feedback,
            'totalExpectedPoints': total_expected,
            'expected': expected
        }
    else:
        return {
            'success': False,
            'message': f'Validation for section "{section}" not implemented.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'Section not supported yet.'}]},
            'expected': {'start': {'price': 0, 'time': 0}, 'end': {'price': 0, 'time': 0}},
            'totalExpectedPoints': 4
        }

def validate_fibonacci(drawings, chart_data):
    if not chart_data or len(chart_data) < 10:
        return {
            'success': False,
            'message': 'Insufficient chart data for validation.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'No chart data available.'}]},
            'expected': {'start': {'price': 0, 'time': 0}, 'end': {'price': 0, 'time': 0}},
            'totalExpectedPoints': 1
        }
    
    exam_data = session.get('exam_data', {})
    interval = exam_data.get('interval', '4h')
    swing_points = detect_swing_points(chart_data)
    
    if not swing_points['lows'] or not swing_points['highs']:
        return {
            'success': False,
            'message': 'No valid swing points detected.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'No swing points found.'}]},
            'expected': {'start': {'price': 0, 'time': 0}, 'end': {'price': 0, 'time': 0}},
            'totalExpectedPoints': 1
        }
    
    lowest_low = min(swing_points['lows'], key=lambda x: x['price'])
    highest_high = max(swing_points['highs'], key=lambda x: x['price'])
    expected = {'start': lowest_low, 'end': highest_high}
    
    tolerance = get_dynamic_tolerance(interval, chart_data)
    score = 0
    feedback = {'correct': [], 'incorrect': []}
    
    if drawings and len(drawings) > 0:
        user_fib = drawings[0]
        start_diff = abs(user_fib['start']['price'] - expected['start']['price'])
        end_diff = abs(user_fib['end']['price'] - expected['end']['price'])
        if start_diff <= tolerance and end_diff <= tolerance:
            score = 1
            feedback['correct'].append({
                'type': 'fib',
                'start': user_fib['start']['price'],
                'end': user_fib['end']['price'],
                'startTime': user_fib['start']['time'],
                'endTime': user_fib['end']['time'],
                'advice': f"Correct! Fibonacci from {user_fib['start']['price']:.2f} to {user_fib['end']['price']:.2f}."
            })
        else:
            feedback['incorrect'].append({
                'type': 'fib',
                'start': user_fib['start']['price'],
                'end': user_fib['end']['price'],
                'startTime': user_fib['start']['time'],
                'endTime': user_fib['end']['time'],
                'advice': f"Off target - expected start: {expected['start']['price']:.2f}, end: {expected['end']['price']:.2f}."
            })
    else:
        feedback['incorrect'].append({
            'type': 'fib',
            'advice': 'No Fibonacci drawn—draw from swing low to high.'
        })

    success = score > 0
    message = 'Fibonacci retracement correct!' if success else 'Fibonacci placement incorrect.'
    return {
        'success': success,
        'message': message,
        'score': score,
        'feedback': feedback,
        'expected': expected,
        'totalExpectedPoints': 1
    }

def get_dynamic_tolerance(interval, chart_data):
    if not chart_data:
        return 0.02
    price_range = max(c['high'] for c in chart_data) - min(c['low'] for c in chart_data)
    tolerance_map = {'5m': 0.005, '4h': 0.015, '1d': 0.025, '1w': 0.035}
    return price_range * tolerance_map.get(interval, 0.02)

def detect_swing_points(data, lookback=5):
    swing_points = {'highs': [], 'lows': []}
    for i in range(lookback, len(data) - lookback):
        current = data[i]
        before = [c['high'] for c in data[i - lookback:i]]
        after = [c['high'] for c in data[i + 1:i + 1 + lookback]]
        if current['high'] > max(before) and current['high'] > max(after):
            swing_points['highs'].append({'time': current['time'], 'price': current['high']})
        before_lows = [c['low'] for c in data[i - lookback:i]]
        after_lows = [c['low'] for c in data[i + 1:i + 1 + lookback]]
        if current['low'] < min(before_lows) and current['low'] < min(after_lows):
            swing_points['lows'].append({'time': current['time'], 'price': current['low']})
    return swing_points

def validate_gaps(drawings):
    correct_gaps = {
        'fvg': [(100, 150, 200, 180)],
        'tolerance': 15
    }
    for drawing in drawings:
        if drawing['type'] == 'box':
            return {
                'success': True,
                'message': 'Gap analysis completed correctly!'
            }
    return {
        'success': False,
        'message': 'Gap analysis not correctly identified. Try again!'
    }

def validate_order_blocks(drawings):
    correct_blocks = {
        'blocks': [(100, 150, 200, 180)],
        'tolerance': 15
    }
    for drawing in drawings:
        if drawing['type'] == 'box':
            return {
                'success': True,
                'message': 'Order blocks identified correctly!'
            }
    return {
        'success': False,
        'message': 'Order blocks not correctly identified. Try again!'
    }

# Flask CLI commands for cache management
@app.cli.command("list-cache")
def list_cache():
    """List all cached data files with their age."""
    files = glob.glob("cache/*.pkl")
    if not files:
        click.echo("No cached files found.")
        return
    
    click.echo(f"Found {len(files)} cached files:")
    for file in sorted(files):
        file_time = datetime.fromtimestamp(os.path.getmtime(file))
        file_age = datetime.now() - file_time
        file_size = os.path.getsize(file) / 1024  # Size in KB
        
        click.echo(f"  {os.path.basename(file):<30} | {file_age.days} days, {file_age.seconds//3600} hours old | {file_size:.1f} KB")

@app.cli.command("clear-cache")
@click.option("--asset", help="Specific asset to clear cache for (e.g., btc, eth, nvda)")
def clear_cache(asset=None):
    """Clear cached data files."""
    if asset:
        files = glob.glob(f"cache/*{asset.lower()}*.pkl")
        if not files:
            click.echo(f"No cached files found for {asset}.")
            return
        
        for file in files:
            os.remove(file)
            click.echo(f"Deleted {os.path.basename(file)}")
        
        click.echo(f"Cleared {len(files)} cache files for {asset}.")
    else:
        files = glob.glob("cache/*.pkl")
        if not files:
            click.echo("No cached files found.")
            return
        
        for file in files:
            os.remove(file)
        
        click.echo(f"Cleared {len(files)} cache files.")

@app.cli.command("refresh-bias-data")
@click.option("--asset", help="Specific asset to refresh (e.g., btc, eth, nvda)")
def refresh_bias_data(asset=None):
    """Refresh the bias test data."""
    global BIAS_TEST_DATA
    
    if asset:
        click.echo(f"Refreshing bias test data for {asset}...")
        if asset in CRYPTO_ASSETS:
            # Clear cache for this asset
            cache_file = f"cache/crypto_{CRYPTO_ASSETS[asset]['id']}_data.pkl"
            if os.path.exists(cache_file):
                os.remove(cache_file)
                click.echo(f"Deleted {os.path.basename(cache_file)}")
            
            # Refresh data
            BIAS_TEST_DATA[asset] = prepare_bias_test(asset, "crypto", 5)
            click.echo(f"Refreshed {len(BIAS_TEST_DATA[asset])} tests for {asset}.")
        elif asset in EQUITY_ASSETS:
            # Clear cache for this asset
            cache_file = f"cache/equity_{EQUITY_ASSETS[asset]['symbol']}_data.pkl"
            if os.path.exists(cache_file):
                os.remove(cache_file)
                click.echo(f"Deleted {os.path.basename(cache_file)}")
            
            # Refresh data
            BIAS_TEST_DATA[asset] = prepare_bias_test(asset, "equities", 5)
            click.echo(f"Refreshed {len(BIAS_TEST_DATA[asset])} tests for {asset}.")
        elif asset == "random":
            click.echo("Refreshing random test set...")
            BIAS_TEST_DATA['random'] = []
            
            for asset_code in list(CRYPTO_ASSETS.keys()) + list(EQUITY_ASSETS.keys()):
                if asset_code in BIAS_TEST_DATA and BIAS_TEST_DATA[asset_code]:
                    test = random.choice(BIAS_TEST_DATA[asset_code])
                    test['asset_code'] = asset_code
                    test['asset_info'] = get_asset_info(asset_code)
                    BIAS_TEST_DATA['random'].append(test)
            
            random.shuffle(BIAS_TEST_DATA['random'])
            click.echo(f"Refreshed {len(BIAS_TEST_DATA['random'])} random tests.")
        else:
            click.echo(f"Unknown asset: {asset}")
    else:
        click.echo("Refreshing all bias test data...")
        # Clear all cache
        files = glob.glob("cache/*.pkl")
        for file in files:
            os.remove(file)
        
        # Load crypto assets
        for asset_code in CRYPTO_ASSETS:
            try:
                BIAS_TEST_DATA[asset_code] = prepare_bias_test(asset_code, "crypto", 5)
                time.sleep(1)
            except Exception as e:
                print(f"Error preparing test data for {asset_code}: {str(e)}")
                BIAS_TEST_DATA[asset_code] = []
        
        # Load equity assets
        for asset_code in EQUITY_ASSETS:
            try:
                BIAS_TEST_DATA[asset_code] = prepare_bias_test(asset_code, "equities", 5)
                time.sleep(1)
            except Exception as e:
                print(f"Error preparing test data for {asset_code}: {str(e)}")
                BIAS_TEST_DATA[asset_code] = []
        
        # Recreate the random dataset
        BIAS_TEST_DATA['random'] = []
        for asset_code in list(CRYPTO_ASSETS.keys()) + list(EQUITY_ASSETS.keys()):
            if asset_code in BIAS_TEST_DATA and BIAS_TEST_DATA[asset_code]:
                test = random.choice(BIAS_TEST_DATA[asset_code])
                test['asset_code'] = asset_code
                test['asset_info'] = get_asset_info(asset_code)
                BIAS_TEST_DATA['random'].append(test)
        
        random.shuffle(BIAS_TEST_DATA['random'])
        click.echo(f"Refreshed bias test data for {len(BIAS_TEST_DATA) - 1} assets plus random mix.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)