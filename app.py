from flask import Flask, render_template, request, redirect, url_for, make_response, session
import os
import random
from quiz_data import quiz_topics

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session tracking

# Original topic descriptions
topic_descriptions = {
    "Swing Point Basics": "Learn to identify key swing highs and lows in price action",
    "Liquidity Concepts": "Understand how liquidity pools form and their significance",
    "Range Trading": "Master the art of trading within defined ranges",
    "Risk Management": "Learn proper risk:reward ratios and position sizing",
    "Stop/Target Orders": "Understand proper order placement and management"
}

# Daily Bias Prediction Test Setup
daily_candle_data = [
    {"image": "images/1.png", "correct": "Bullish"},
    {"image": "images/2.png", "correct": "Bearish"},
    {"image": "images/3.png", "correct": "Bullish"},
    {"image": "images/4.png", "correct": "Bearish"},
    {"image": "images/5.png", "correct": "Bullish"},
    {"image": "images/6.png", "correct": "Bearish"},
    {"image": "images/7.png", "correct": "Bullish"},
    {"image": "images/8.png", "correct": "Bearish"},
    {"image": "images/9.png", "correct": "Bullish"},
    {"image": "images/10.png", "correct": "Bearish"},
    {"image": "images/11.png", "correct": "Bullish"},
    {"image": "images/12.png", "correct": "Bearish"},
    {"image": "images/13.png", "correct": "Bullish"},
    {"image": "images/14.png", "correct": "Bearish"},
    {"image": "images/15.png", "correct": "Bullish"},
    {"image": "images/16.png", "correct": "Bearish"},
    {"image": "images/17.png", "correct": "Bullish"},
    {"image": "images/18.png", "correct": "Bearish"},
    {"image": "images/19.png", "correct": "Bullish"},
    {"image": "images/20.png", "correct": "Bearish"},
    {"image": "images/21.png", "correct": "Bullish"},
    {"image": "images/22.png", "correct": "Bearish"},
    {"image": "images/23.png", "correct": "Bullish"},
    {"image": "images/24.png", "correct": "Bearish"},
]


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
        
        if user_answer == question_data['correct_option']:
            score += 1
            
        response = redirect(url_for('quiz', topic=topic, question_id=question_id + 1))
        response.set_cookie(f'score_{topic}', str(score))
        return response

    # Handle both single image and multiple images
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
        images_list=images_list,  # Pass the list of images if available
        question_id=question_id,
        total_questions=len(quiz_topics[topic])
    )

@app.route('/results/<topic>')
def results(topic):
    score = int(request.cookies.get(f'score_{topic}', 0))
    total = len(quiz_topics[topic])
    
    response = render_template('results.html', 
                             topic=topic,
                             score=score,
                             total=total)
                             
    # Clear the score cookie
    response = make_response(response)
    response.delete_cookie(f'score_{topic}')
    return response

# New route for Daily Bias Prediction Test
@app.route('/daily_bias', methods=['GET', 'POST'])
def daily_bias():
    if request.method == 'POST':
        user_prediction = request.form.get('prediction', None)
        correct_prediction = session.get('correct_prediction', None)
        
        # Update scores in session
        if user_prediction == correct_prediction:
            session['score'] = session.get('score', 0) + 1
        
        session['attempts'] = session.get('attempts', 0) + 1

        return redirect(url_for('daily_bias_feedback'))
    
    # Randomize candle for the prediction test
    selected_candle = random.choice(daily_candle_data)
    session['correct_prediction'] = selected_candle['correct']

    return render_template(
        'daily_bias.html',
        candle_image=url_for('static', filename=selected_candle['image'])
    )

@app.route('/daily_bias_feedback')
def daily_bias_feedback():
    correct_prediction = session.get('correct_prediction', None)
    score = session.get('score', 0)
    attempts = session.get('attempts', 0)

    return render_template(
        'daily_bias_feedback.html',
        correct_prediction=correct_prediction,
        score=score,
        attempts=attempts
    )

if __name__ == "__main__":
    app.run(debug=True)
