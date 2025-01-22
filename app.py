# app.py
from flask import Flask, render_template, request, redirect, url_for, make_response
import os
from quiz_data import quiz_topics

app = Flask(__name__)

topic_descriptions = {
    "Swing Point Basics": "Learn to identify key swing highs and lows in price action",
    "Liquidity Concepts": "Understand how liquidity pools form and their significance",
    "Range Trading": "Master the art of trading within defined ranges",
    "Risk Management": "Learn proper risk:reward ratios and position sizing",
    "Stop/Target Orders": "Understand proper order placement and management"
}

@app.route('/')
def index():
    return render_template('index.html', 
                         topics=list(quiz_topics.keys()),
                         topic_descriptions=topic_descriptions)

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

if __name__ == "__main__":
    app.run(debug=True)