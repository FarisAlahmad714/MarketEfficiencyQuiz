from flask import Flask, render_template, request, redirect, url_for, make_response, session
import os
import random
from quiz_data import quiz_topics
from btc_data import btc_candle_data
from daily_candle_data import daily_candle_data
from prediction_validator import CandleAnalyzer

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

@app.route('/')
def index():
    return render_template(
        'index.html',
        topics=list(quiz_topics.keys()),
        topic_descriptions=topic_descriptions
    )

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
    # Clear any existing session data when returning to test selection
    session.clear()
    return render_template('bias_test_selection.html')

@app.route('/daily_bias/<test_type>', methods=['GET', 'POST'])
def daily_bias(test_type):
    # Select data based on test type
    data = btc_candle_data if test_type == 'btc' else daily_candle_data

    if request.method == 'POST':
        user_prediction = request.form.get('prediction')
        current_index = session.get('current_index', 0)

        # Validate the user's prediction
        actual_outcome = validator.validate_sequence(
            session['data'][current_index]['setup'],
            session['data'][current_index]['outcome']
        )

        # Update score if the prediction is correct
        if 'score' not in session:
            session['score'] = 0
        if user_prediction == actual_outcome:
            session['score'] += 1

        # Store the user's answer
        if 'user_answers' not in session:
            session['user_answers'] = []
        session['user_answers'].append(user_prediction)

        # Move to the next question
        session['current_index'] = current_index + 1

        # Redirect to feedback page
        return redirect(url_for('daily_bias_feedback', test_type=test_type))

    # Only initialize if there's no existing session data
    if 'data' not in session:
        random.shuffle(data)
        session['data'] = data[:5]
        session['current_index'] = 0
        session['score'] = 0
        session['user_answers'] = []
        session['start_new'] = False

    # Calculate progress
    current_index = session.get('current_index', 0)
    total_questions = len(session['data'])
    progress = f"{current_index + 1}/{total_questions}"

    return render_template(
        'daily_bias.html',
        candle_image=url_for('static', filename=session['data'][current_index]['setup']),
        progress=progress,
        score=session.get('score', 0),
        total=len(session.get('user_answers', [])),
        test_type=test_type
    )

@app.route('/daily_bias_feedback/<test_type>')
def daily_bias_feedback(test_type):
    current_index = session.get('current_index', 0)
    data = session.get('data', [])

    # If we've answered all questions, go to results
    if current_index >= len(data):
        return redirect(url_for('daily_bias_results', test_type=test_type))

    # Get the correct prediction from the validator
    correct_prediction = validator.validate_sequence(
        data[current_index - 1]['setup'],
        data[current_index - 1]['outcome']
    )

    # Progress shows the next question we're going to
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
        progress=progress
    )

@app.route('/daily_bias_results/<test_type>')
def daily_bias_results(test_type):
    score = session.get('score', 0)
    data = session.get('data', [])
    user_answers = session.get('user_answers', [])

    # Handle case where no questions exist
    if len(data) == 0:
        return render_template(
            'daily_bias_results.html',
            score=score,
            total=0,
            accuracy="N/A",
            results=[],
            test_type=test_type
        )

    # Create results array with all needed data for each question
    results = []
    for i, question in enumerate(data):
        correct_prediction = validator.validate_sequence(
            question['setup'],
            question['outcome']
        )
        results.append({
            'setup_image': question['setup'],
            'outcome_image': question['outcome'],
            'user_prediction': user_answers[i] if i < len(user_answers) else None,
            'correct_prediction': correct_prediction,
            'question_number': i + 1
        })

    # Clear session data after processing
    session.clear()

    return render_template(
        'daily_bias_results.html',
        score=score,
        total=len(data),
        accuracy=f"{(score / len(data)) * 100:.1f}%",
        results=results,
        test_type=test_type
    )

if __name__ == "__main__":
    app.run(debug=True)




