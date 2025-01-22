# quiz_data.py

quiz_topics = {
    "Swing Point Basics": [
        {
            "question": "What does this chart indicate about Old High and Old Low levels?",
            "image": "images/OldH&L.png",  # Image 2
            "options": [
                "They are simple support and resistance levels",
                "They represent trend reversal points",
                "They are liquidity pools for institutional orders",
                "They are just previous price levels"
            ],
            "correct_option": 3,
            "explanation": "Old Highs and Old Lows represent significant liquidity pools where institutional orders gather, making them important targets for price movement."
        },
        {
            "question": "What trading concept is illustrated in this range diagram?",
            "image": "images/Range.png",  # Image 1
            "options": [
                "Trend following",
                "Range boundaries",
                "Breakout patterns",
                "Support and resistance"
            ],
            "correct_option": 2,
            "explanation": "The diagram shows how range boundaries are formed by swing highs and swing lows, creating tradeable areas in the market."
        },
        {
            "question": "In this chart, what do the labeled 'Swing High' and 'Swing Low' points represent?",
            "image": "images/SwingPoints.png",  # Image 5
            "options": [
                "Points where price action reversed",
                "Points where volume was highest",
                "Points where liquidity was removed",
                "Points where market orders were executed"
            ],
            "correct_option": 1,
            "explanation": "Swing Highs and Swing Lows in this chart are points where the price action reversed, indicating potential areas for future support or resistance."
        }
    ],
    "Market Structure": [
        {
            "question": "What do equal lows indicate in this chart pattern?",
            "image": "images/EqualH&L.png",  # Image 3
            "options": [
                "Trend reversal",
                "Continuation pattern",
                "Liquidity pool",
                "Random price action"
            ],
            "correct_option": 3,
            "explanation": "Equal lows indicate a liquidity pool where stop orders accumulate, making it a target for larger players."
        },
        {
            "question": "How are swing points validated in this chart example?",
            "image": "images/SwingPoints.png",  # Image 5
            "options": [
                "By time duration",
                "By price level only",
                "By surrounding price action",
                "By volume"
            ],
            "correct_option": 3,
            "explanation": "Swing points are validated by the surrounding price action creating higher highs/lows or lower highs/lows."
        }
    ],
    "Liquidity Concepts": [
        {
            "question": "What type of orders create sellside liquidity as shown?",
            "image": "images/SwingLow.png",  # Image 6
            "options": [
                "Stop losses from long trades",
                "Take profit from shorts",
                "Market buy orders",
                "Limit sell orders"
            ],
            "correct_option": 1,
            "explanation": "Sellside liquidity is created primarily by stop losses from long trades being clustered at certain levels, leading to sell orders when those levels are hit."
        },
        {
            "question": "In the buyside liquidity diagram, what does the green box represent?",
            "image": "images/SwingHigh.png",  # Image 7
            "options": [
                "Take profit area",
                "Entry zone",
                "Stop loss cluster",
                "Accumulation area"
            ],
            "correct_option": 4,
            "explanation": "The green box represents an accumulation area where buyside liquidity pools form from clustered buy orders, indicating a zone where traders are looking to enter long positions."
        }
    ]
}