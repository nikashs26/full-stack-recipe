from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "http://localhost:8081",
        "supports_credentials": True
    }
})

@app.route('/api/test/meal_plan', methods=['POST'])
def test_meal_plan():
    return jsonify({
        'success': True,
        'days': [{
            'day': 'Monday',
            'date': '2023-07-25',
            'meals': {
                'breakfast': {
                    'name': 'Protein Oatmeal',
                    'description': 'Oatmeal with protein powder and berries',
                    'cuisine': 'American',
                    'cook_time': '10 mins',
                    'prep_time': '5 mins',
                    'difficulty': 'easy',
                    'ingredients': ['oats', 'protein powder', 'berries', 'milk'],
                    'nutrition': {
                        'calories': 350,
                        'protein': 25,
                        'carbs': 45,
                        'fat': 8,
                        'fiber': 7
                    }
                },
                'lunch': {
                    'name': 'Grilled Chicken Salad',
                    'description': 'Mixed greens with grilled chicken and vinaigrette',
                    'cuisine': 'American',
                    'cook_time': '15 mins',
                    'prep_time': '10 mins',
                    'difficulty': 'easy',
                    'ingredients': ['chicken breast', 'mixed greens', 'olive oil', 'lemon', 'vegetables'],
                    'nutrition': {
                        'calories': 450,
                        'protein': 35,
                        'carbs': 20,
                        'fat': 15,
                        'fiber': 8
                    }
                },
                'dinner': {
                    'name': 'Salmon with Quinoa',
                    'description': 'Baked salmon with quinoa and steamed vegetables',
                    'cuisine': 'International',
                    'cook_time': '20 mins',
                    'prep_time': '10 mins',
                    'difficulty': 'medium',
                    'ingredients': ['salmon fillet', 'quinoa', 'broccoli', 'carrots', 'olive oil'],
                    'nutrition': {
                        'calories': 500,
                        'protein': 40,
                        'carbs': 35,
                        'fat': 20,
                        'fiber': 10
                    }
                }
            },
            'nutrition': {
                'calories': 1300,
                'protein': 100,
                'carbs': 100,
                'fat': 43,
                'fiber': 25
            }
        }],
        'plan_type': 'test',
        'currency': 'USD',
        'budget': 50.00,
        'totalCost': 45.00,
        'generated_at': '2023-07-25T18:30:00Z'
    })

if __name__ == '__main__':
    print("Starting test server on port 5004...")
    app.run(port=5004, debug=True)
