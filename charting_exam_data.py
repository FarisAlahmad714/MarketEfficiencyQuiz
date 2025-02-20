# Create a new file: charting_exam_data.py

swing_analysis_data = {
    "swing_points": {
        "questions": [
            {
                "id": "sp1",
                "chart_image": "images/SwingPoints.png",
                "title": "Identify Swing Points",
                "instruction": "Mark all significant swing highs and lows on this chart",
                "correct_points": {
                    "swing_highs": [
                        {"x": 150, "y": 200, "description": "Major swing high"},
                        {"x": 300, "y": 180, "description": "Secondary swing high"}
                    ],
                    "swing_lows": [
                        {"x": 220, "y": 120, "description": "Major swing low"},
                        {"x": 400, "y": 140, "description": "Secondary swing low"}
                    ],
                    "tolerance": 15  # Pixel tolerance for validation
                }
            },
            {
                "id": "sp2",
                "chart_image": "images/SwingHigh.png",
                "title": "Higher Highs Pattern",
                "instruction": "Identify the series of higher highs in this uptrend",
                "correct_points": {
                    "swing_highs": [
                        {"x": 100, "y": 160, "description": "First high"},
                        {"x": 200, "y": 180, "description": "Second high"},
                        {"x": 300, "y": 220, "description": "Third high"}
                    ],
                    "tolerance": 15
                }
            }
        ]
    },
    "equal_levels": {
        "questions": [
            {
                "id": "el1",
                "chart_image": "images/EqualH&L.png",
                "title": "Equal Highs and Lows",
                "instruction": "Draw horizontal lines connecting the equal highs and equal lows",
                "correct_levels": {
                    "equal_highs": [
                        {
                            "y": 200,
                            "points": [
                                {"x1": 100, "x2": 300},
                                {"x1": 400, "x2": 500}
                            ],
                            "description": "Major equal high level"
                        }
                    ],
                    "equal_lows": [
                        {
                            "y": 120,
                            "points": [
                                {"x1": 150, "x2": 350},
                                {"x1": 450, "x2": 550}
                            ],
                            "description": "Major equal low level"
                        }
                    ],
                    "tolerance": {
                        "y": 10,  # Vertical pixel tolerance
                        "x": 20   # Horizontal pixel tolerance
                    }
                }
            },
            {
                "id": "el2",
                "chart_image": "images/OldH&L.png",
                "title": "Old Highs and Lows",
                "instruction": "Identify the old highs that are being retested",
                "correct_levels": {
                    "old_highs": [
                        {
                            "y": 180,
                            "points": [
                                {"x1": 200, "x2": 400}
                            ],
                            "description": "Previous resistance level"
                        }
                    ],
                    "tolerance": {
                        "y": 10,
                        "x": 20
                    }
                }
            }
        ]
    },
    "validation_rules": {
        "swing_points": {
            "min_points": 2,  # Minimum number of points required
            "max_points": 6,  # Maximum number of points allowed
            "required_types": ["high", "low"],  # Must identify both highs and lows
            "scoring": {
                "correct_point": 10,    # Points for each correctly identified swing
                "wrong_point": -5,      # Points deducted for incorrect placements
                "missing_point": -3     # Points deducted for missing key swings
            }
        },
        "equal_levels": {
            "min_lines": 1,
            "max_lines": 4,
            "required_types": ["horizontal"],
            "scoring": {
                "correct_line": 15,
                "wrong_angle": -5,
                "wrong_level": -5
            }
        }
    }
}