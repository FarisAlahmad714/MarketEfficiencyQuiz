from flask import Flask, jsonify, render_template, request, redirect, url_for, make_response, session, flash
import os
import random
import requests
from quiz_data import quiz_topics
from btc_data import btc_candle_data
from daily_candle_data import daily_candle_data
from prediction_validator import CandleAnalyzer
from charting_exam_data import swing_analysis_data
from study_content import study_content

validator = CandleAnalyzer('static')
app = Flask(__name__)
app.secret_key = "your_secret_key"

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

@app.route('/')
def index():
    return render_template(
        'index.html',
        topics=list(quiz_topics.keys()),
        topic_descriptions=topic_descriptions,
        charting_exam_descriptions=charting_exam_descriptions
    )
# Add these routes to your Flask application

@app.route('/study')
def study_selection():
    """
    Render the study selection page, showing all available study topics
    """
    return render_template('study_selection.html', study_content=study_content)

@app.route('/study/<topic>')
def study_topic(topic):
    """
    Render a specific study topic page with all lessons
    """
    if topic in study_content:
        lessons = study_content[topic]
        return render_template('study_topic.html', topic=topic, lessons=lessons)
    else:
        # If topic doesn't exist, redirect back to selection page
        return redirect(url_for('study_selection'))
    
@app.route('/quiz_selection')
def quiz_selection():
    # Get all topics and their descriptions
    return render_template('quiz_selection.html', quiz_topics=quiz_topics)

    
    # Create a dictionary to store descriptions for each topic
    topic_descriptions = {
        "Swing Point Basics": "Learn to identify significant reversal points in price action for better entries and exits.",
        "Market Structure": "Understand how markets organize through trends, patterns and key structural components.",
        "Liquidity Concepts": "Discover how institutions use liquidity zones for major price movements.",
        "Risk Management": "Master position sizing, risk:reward ratios, and capital preservation techniques.",
        "Optimal Trade Entry (Fibonacci Levels)": "Use Fibonacci retracements to identify high-probability entry zones.",
        "Fair Value Gaps": "Learn to spot imbalances and inefficiencies that lead to price rebalancing.",
        "Order_Block_Analysis": "Identify institutional positioning before significant market moves."
    }
    
    return render_template('quiz_selection.html', topics=topics, topic_descriptions=topic_descriptions)

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

    if 'image' in question_data:
        image_url = url_for('static', filename=question_data['image'])
        images_list = None
    elif 'images' in question_data:
        image_url = None
        images_list = [url_for('static', filename=img) for img in question_data['images']]
    else:
        image_url = None
        images_list = None

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
    session.clear()
    return render_template('bias_test_selection.html')

@app.route('/daily_bias/<test_type>', methods=['GET', 'POST'])
def daily_bias(test_type):
    data = btc_candle_data if test_type == 'btc' else daily_candle_data

    if request.method == 'POST':
        user_prediction = request.form.get('prediction').lower()
        current_index = session.get('current_index', 0)

        if 'data' not in session or current_index >= len(session['data']):
            return redirect(url_for('daily_bias_results', test_type=test_type))

        actual_outcome = validator.validate_sequence(
            session['data'][current_index]['setup'],
            session['data'][current_index]['outcome']
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

    if 'data' not in session:
        random.shuffle(data)
        session['data'] = data[:5]
        session['current_index'] = 0
        session['score'] = 0
        session['user_answers'] = []
        session['start_new'] = False

    current_index = session.get('current_index', 0)
    
    if current_index >= len(session['data']):
        return redirect(url_for('daily_bias_results', test_type=test_type))

    return render_template(
        'daily_bias.html',
        candle_image=url_for('static', filename=session['data'][current_index]['setup']),
        progress=f"{current_index + 1}/{len(session['data'])}",
        score=session.get('score', 0),
        total=len(session.get('user_answers', [])),
        test_type=test_type
    )

@app.route('/daily_bias_feedback/<test_type>')
def daily_bias_feedback(test_type):
    current_index = session.get('current_index', 0)
    data = session.get('data', [])
    correct_answers = session.get('correct_answers', [])

    if current_index >= len(data):
        return redirect(url_for('daily_bias_results', test_type=test_type))

    correct_prediction = validator.validate_sequence(
        data[current_index - 1]['setup'],
        data[current_index - 1]['outcome']
    ).lower()

    was_correct = correct_answers[-1] if correct_answers else False

    progress = f"{current_index + 1}/{len(data)}"

    return render_template(
        'daily_bias_feedback.html',
        question_image=url_for('static', filename=data[current_index - 1]['setup']),
        answer_image=url_for('static', filename=data[current_index - 1]['outcome']),
        correct_prediction=correct_prediction,
        user_prediction=session['user_answers'][-1],
        score=session.get('score', 0),
        total=len(session.get('user_answers', [])),
        next_image=url_for('static', filename=data[current_index]['setup']),
        test_type=test_type,
        progress=progress,
        was_correct=was_correct
    )

@app.route('/daily_bias_results/<test_type>')
def daily_bias_results(test_type):
    score = session.get('score', 0)
    data = session.get('data', [])
    user_answers = session.get('user_answers', [])
    correct_answers = session.get('correct_answers', [])

    if len(data) == 0:
        return render_template(
            'daily_bias_results.html',
            score=score,
            total=0,
            accuracy="N/A",
            results=[],
            test_type=test_type
        )

    results = []
    for i, question in enumerate(data):
        if i < len(user_answers):
            correct_prediction = validator.validate_sequence(
                question['setup'],
                question['outcome']
            ).lower()
            
            was_correct = correct_answers[i] if i < len(correct_answers) else False
            
            results.append({
                'setup_image': question['setup'],
                'outcome_image': question['outcome'],
                'user_prediction': user_answers[i],
                'correct_prediction': correct_prediction,
                'question_number': i + 1,
                'was_correct': was_correct
            })

    session.clear()

    return render_template(
        'daily_bias_results.html',
        score=score,
        total=len(results),
        accuracy=f"{(score / len(results)) * 100:.1f}%" if results else "0%",
        results=results,
        test_type=test_type
    )

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

@app.route('/charting_exams/swing_analysis')
def swing_analysis_intro():
    return render_template(
        'charting_exams/swing_analysis_intro.html',
        exam_info=charting_exam_descriptions['swing_analysis']
    )

def fetch_binance_data(symbol="BTCUSDT", interval="1h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    print(f"Binance API response status: {response.status_code}")
    if response.status_code != 200:
        print(f"API error: {response.text}")
        return []
    data = response.json()
    print(f"Fetched data: {data[:5]}")
    return [
        {
            'time': int(candle[0]) // 1000,
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'symbol': symbol
        }
        for candle in data
    ]

@app.route('/charting_exam/<exam_type>/practice', methods=['GET', 'POST'])
def charting_exam_practice(exam_type):
    if exam_type not in charting_exam_descriptions:
        return redirect(url_for('charting_exams'))
        
    # Get section parameter if provided
    requested_section = request.args.get('section')
    
    # Reset session for a fresh start, always starting at chart_count = 1
    session['exam_data'] = {
        'type': exam_type,
        'current_section': 0 if not requested_section or requested_section == 'swing_points' else (1 if requested_section == 'equal_levels' else 2),
        'question_index': 0,
        'score': 0,
        'drawings': [],
        'validations': [],
        'chart_data': None,
        'chart_count': 1  # Force start at 1
    }
    
    exam_data = session['exam_data']
    section = requested_section or ('swing_points' if exam_data['current_section'] == 0 else ('equal_levels' if exam_data['current_section'] == 1 else 'fib_retracement'))
    questions = swing_analysis_data.get(section, swing_analysis_data['swing_points'])['questions']
    
    # Select template based on section
    template = 'charting_exams/practice.html'
    if section == 'equal_levels':
        template = 'charting_exams/equal_levels_practice.html'
    elif section == 'fib_retracement':
        template = 'charting_exams/fibonacci_practice.html'
    
    # Fetch chart data with 50-candle limit, favoring shorter TFs for Fibonacci
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LTCUSDT", "LINKUSDT"]
    intervals = ["1h", "4h"]  # Shorter TFs for Fibonacci
    chart_data = fetch_binance_data(
        symbol=random.choice(symbols),
        interval=random.choice(intervals),
        limit=50
    )
    if not chart_data or len(chart_data) < 10:
        chart_data = [
            {'time': 1677657600 + i * 3600, 'open': 50000 + i * 10, 'high': 51000 + i * 10, 'low': 49500 + i * 10, 'close': 50500 + i * 10, 'symbol': 'BTCUSDT'}
            for i in range(50)
        ]
    session['exam_data']['chart_data'] = chart_data

    return render_template(
        template,
        exam_type=exam_type,
        exam_info=charting_exam_descriptions[exam_type],
        tools=charting_exam_descriptions[exam_type]['tools_required'],
        chart_data=chart_data,
        instructions=questions[exam_data['question_index']]['instruction'],
        current_section=section,
        progress={
            'section': exam_data['current_section'] + 1,
            'total_sections': len(swing_analysis_data.keys()) - 1,
            'question': exam_data['question_index'] + 1,
            'total_questions': len(questions),
            'chart_count': exam_data['chart_count']
        },
        symbol=chart_data[0]['symbol'],
        section=section
    )

@app.route('/fetch_new_chart', methods=['GET'])
def fetch_new_chart():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LTCUSDT", "LINKUSDT"]
    intervals = ["1h", "4h"]  # Shorter TFs for Fibonacci
    chart_data = fetch_binance_data(
        symbol=random.choice(symbols),
        interval=random.choice(intervals),
        limit=50
    )
    if not chart_data or len(chart_data) < 10:
        chart_data = [
            {'time': 1677657600 + i * 3600, 'open': 50000 + i * 10, 'high': 51000 + i * 10, 'low': 49500 + i * 10, 'close': 50500 + i * 10, 'symbol': 'BTCUSDT'}
            for i in range(50)
        ]
    
    exam_data = session.get('exam_data', {'chart_count': 1})
    current_count = exam_data.get('chart_count', 1)
    exam_data['chart_count'] = current_count + 1  # Increment chart count
    if exam_data['chart_count'] > 5:  # Reset to 1 after 5 charts
        exam_data['chart_count'] = 1
    exam_data['chart_data'] = chart_data
    session['exam_data'] = exam_data
    
    return jsonify({
        'chart_data': chart_data,
        'chart_count': exam_data['chart_count'],
        'symbol': chart_data[0]['symbol']
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
    
    if exam_type == 'swing_analysis':
        validation_result = validate_swing_points(drawings, section)
    elif exam_type == 'fibonacci' and section == 'fib_retracement':
        validation_result = validate_fibonacci(drawings, chart_data)
    else:
        return jsonify({'success': False, 'message': 'Exam type or section not implemented yet'})
    
    current_count = exam_data.get('chart_count', 1)
    symbol = chart_data[0].get('symbol', 'Unknown') if chart_data else 'Unknown'

    # Ensure all required keys exist in validation_result with default values
    if 'expected' not in validation_result:
        validation_result['expected'] = {'start': {'price': 0, 'time': 0}, 'end': {'price': 0, 'time': 0}}
    
    if 'score' not in validation_result:
        validation_result['score'] = 0
        
    if 'feedback' not in validation_result:
        validation_result['feedback'] = {'correct': [], 'incorrect': []}
        
    if 'totalExpectedPoints' not in validation_result:
        validation_result['totalExpectedPoints'] = 1
    
    # Initialize score in exam_data if it doesn't exist
    if 'score' not in exam_data:
        exam_data['score'] = 0
        
    # Update exam_data with new score and ensure chart count is correct
    exam_data['score'] += validation_result['score']
    exam_data['chart_count'] = current_count  # Sync with data from fetch_new_chart
    
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
    exam_data = session['exam_data']
    chart_data = exam_data['chart_data']
    rules = swing_analysis_data['validation_rules'][section]

    def pixel_to_price_time(x, y, chart_width=800, chart_height=600):
        times = [c['time'] for c in chart_data]
        prices = [c['high'] for c in chart_data] + [c['low'] for c in chart_data]
        time = times[0] + (x / chart_width) * (times[-1] - times[0])
        price = min(prices) + (1 - y / chart_height) * (max(prices) - min(prices))
        return time, price

    if section == 'swing_points':
        highs = [(c['time'], c['high']) for i, c in enumerate(chart_data) 
                 if i > 0 and i < len(chart_data)-1 and c['high'] > chart_data[i-1]['high'] and c['high'] > chart_data[i+1]['high']]
        lows = [(c['time'], c['low']) for i, c in enumerate(chart_data) 
                if i > 0 and i < len(chart_data)-1 and c['low'] < chart_data[i-1]['low'] and c['low'] < chart_data[i+1]['low']]
        required_points = highs[:2] + lows[:2]
        
        tolerance_time = (chart_data[-1]['time'] - chart_data[0]['time']) / 50
        tolerance_price = (max(c['high'] for c in chart_data) - min(c['low'] for c in chart_data)) * 0.02
        
        matched = 0
        feedback = {'correct': [], 'incorrect': []}
        for d in drawings:
            if d['type'] == 'line':
                start_t, start_p = pixel_to_price_time(d['start']['x'], d['start']['y'])
                end_t, end_p = pixel_to_price_time(d['end']['x'], d['end']['y'])
                point_matched = False
                for rt, rp in required_points:
                    if (abs(start_t - rt) < tolerance_time and abs(start_p - rp) < tolerance_price) or \
                       (abs(end_t - rt) < tolerance_time and abs(end_p - rp) < tolerance_price):
                        matched += 1
                        point_matched = True
                        feedback['correct'].append({
                            'type': 'swing_point',
                            'time': rt,
                            'price': rp,
                            'advice': f"Good job! You correctly identified a swing point at price {rp:.2f}."
                        })
                        break
                if not point_matched:
                    feedback['incorrect'].append({
                        'type': 'swing_point',
                        'start_time': start_t,
                        'start_price': start_p,
                        'end_time': end_t,
                        'end_price': end_p,
                        'advice': "This doesn't appear to be a significant swing point."
                    })
        
        # Add feedback for missed points
        for rt, rp in required_points:
            found = False
            for item in feedback['correct']:
                if item['type'] == 'swing_point' and abs(item['time'] - rt) < tolerance_time and abs(item['price'] - rp) < tolerance_price:
                    found = True
                    break
            if not found:
                feedback['incorrect'].append({
                    'type': 'missed_point',
                    'time': rt,
                    'price': rp,
                    'advice': f"You missed a swing point at price {rp:.2f}."
                })
        
        success = matched >= len(required_points)
        score = matched / max(1, len(required_points))
        
        # Create expected object with a default structure
        expected = {
            'start': {'price': 0, 'time': 0},
            'end': {'price': 0, 'time': 0}
        }
        if highs and lows:
            expected = {
                'start': {'price': lows[0][1] if lows else 0, 'time': lows[0][0] if lows else 0},
                'end': {'price': highs[0][1] if highs else 0, 'time': highs[0][0] if highs else 0}
            }
        
        return {
            'success': success, 
            'message': 'Swing points correct!' if success else 'Missed some swing points.',
            'score': score,
            'feedback': feedback,
            'totalExpectedPoints': len(required_points),
            'expected': expected
        }

    elif section == 'equal_levels':
        highs = sorted([c['high'] for c in chart_data])
        equal_highs = [h for i, h in enumerate(highs) if i > 0 and abs(h - highs[i-1]) < max(highs) * 0.005][:2]
        required_levels = equal_highs
        
        tolerance_price = max(c['high'] for c in chart_data) * 0.01
        matched = 0
        feedback = {'correct': [], 'incorrect': []}
        
        for d in drawings:
            if d['type'] == 'line':
                _, y = pixel_to_price_time(d['start']['x'], d['start']['y'])
                level_matched = False
                for level in required_levels:
                    if abs(y - level) < tolerance_price:
                        matched += 1
                        level_matched = True
                        feedback['correct'].append({
                            'type': 'equal_level',
                            'price': level,
                            'advice': f"Good job! You correctly identified an equal level at price {level:.2f}."
                        })
                        break
                if not level_matched:
                    feedback['incorrect'].append({
                        'type': 'equal_level',
                        'price': y,
                        'advice': f"This doesn't appear to be a significant equal level. Your level: {y:.2f}"
                    })
        
        # Add feedback for missed levels
        for level in required_levels:
            found = False
            for item in feedback['correct']:
                if item['type'] == 'equal_level' and abs(item['price'] - level) < tolerance_price:
                    found = True
                    break
            if not found:
                feedback['incorrect'].append({
                    'type': 'missed_level',
                    'price': level,
                    'advice': f"You missed an equal level at price {level:.2f}."
                })
        
        success = matched >= len(required_levels)
        score = matched / max(1, len(required_levels))
        
        # Create expected object with a default structure
        expected = {
            'start': {'price': 0, 'time': 0},
            'end': {'price': 0, 'time': 0}
        }
        if required_levels:
            expected = {
                'start': {'price': required_levels[0] if required_levels else 0, 'time': 0},
                'end': {'price': required_levels[-1] if len(required_levels) > 1 else 0, 'time': 0}
            }
        
        return {
            'success': success, 
            'message': 'Equal levels correct!' if success else 'Missed some levels.',
            'score': score,
            'feedback': feedback,
            'totalExpectedPoints': len(required_levels),
            'expected': expected
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
    
    swing_points = detect_swing_points(chart_data)
    expected = {
        'start': swing_points['lows'][0] or (swing_points['lows'] and swing_points['lows'][-1]),
        'end': swing_points['highs'][0] or (swing_points['highs'] and swing_points['highs'][-1])
    }
    if not expected['start'] or not expected['end']:
        return {
            'success': False,
            'message': 'No valid swing points detected for Fibonacci validation.',
            'score': 0,
            'feedback': {'correct': [], 'incorrect': [{'advice': 'No valid swing points found.'}]},
            'expected': expected,
            'totalExpectedPoints': 1
        }
    
    tolerance = 0.02  # 2% price tolerance
    score = 0
    feedback = {'correct': [], 'incorrect': []}
    
    if drawings and len(drawings) > 0:
        user_fib = drawings[0]  # Only one Fibonacci allowed
        start_diff = abs(user_fib['start']['price'] - expected['start']['price']) / expected['start']['price']
        end_diff = abs(user_fib['end']['price'] - expected['end']['price']) / expected['end']['price']

        if start_diff <= tolerance and end_diff <= tolerance:
            score = 1
            feedback['correct'].append({
                'type': 'fib',
                'start': user_fib['start']['price'],
                'end': user_fib['end']['price'],
                'startTime': user_fib['start']['time'],
                'endTime': user_fib['end']['time'],
                'advice': f"Perfect! You nailed the Fibonacci from {user_fib['start']['price']:.4f} to {user_fib['end']['price']:.4f}!"
            })
        else:
            feedback['incorrect'].append({
                'type': 'fib',
                'start': user_fib['start']['price'],
                'end': user_fib['end']['price'],
                'startTime': user_fib['start']['time'],
                'endTime': user_fib['end']['time'],
                'advice': f"Off target - start should be near {expected['start']['price']:.4f} (yours: {user_fib['start']['price']:.4f}), end near {expected['end']['price']:.4f} (yours: {user_fib['end']['price']:.4f})."
            })
    else:
        feedback['incorrect'].append({
            'type': 'fib',
            'advice': 'No Fibonacci drawn—place it from the swing low to high!'
        })

    success = score > 0
    message = 'Fibonacci retracement drawn correctly!' if success else 'Fibonacci retracement not correctly placed. Try again from the swing low to high.'
    return {
        'success': success,
        'message': message,
        'score': score,
        'feedback': feedback,
        'expected': expected,
        'totalExpectedPoints': 1
    }

def detect_swing_points(data, lookback=3):
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

if __name__ == "__main__":
    app.run(debug=True)