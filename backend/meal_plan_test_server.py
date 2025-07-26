from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8081"}})

@app.route('/api/test/meal_plan', methods=['GET', 'OPTIONS'])
def test_meal_plan():
    """Test endpoint that returns a sample meal plan"""
    try:
        # Generate dates for the next 7 days
        today = datetime.utcnow().date()
        days = [today + timedelta(days=i) for i in range(7)]
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # Sample meal plan data
        meal_plan = {
            'days': [],
            'shopping_list': {
                'ingredients': [
                    {'name': 'chicken breast', 'total_amount': '1.5 kg', 'estimated_cost': 12.99},
                    {'name': 'brown rice', 'total_amount': '1 kg', 'estimated_cost': 3.49},
                ],
                'total_estimated_cost': {'amount': 45.99, 'currency': 'USD'}
            },
            'nutrition_summary': {
                'weekly_average_daily': {
                    'calories': 2100,
                    'protein_g': 150,
                    'carbs_g': 200,
                    'fat_g': 70,
                    'fiber_g': 35
                },
                'weekly_totals': {
                    'calories': 14700,
                    'protein_g': 1050,
                    'carbs_g': 1400,
                    'fat_g': 490,
                    'fiber_g': 245
                }
            },
            'preparation_tips': [
                "Meal prep on Sunday for the week's breakfasts and lunches.",
                "Use leftovers from dinner for next day's lunch.",
                "Chop vegetables in advance to save time during weekdays."
            ],
            'notes': 'This is a sample meal plan.'
        }
        
        # Sample meal template
        sample_meal = {
            'breakfast': {
                'name': 'Greek Yogurt with Berries',
                'description': 'Creamy Greek yogurt with mixed berries and honey',
                'cuisine': 'Mediterranean',
                'cook_time': '0 mins',
                'prep_time': '5 mins',
                'total_time': '5 mins',
                'difficulty': 'easy',
                'ingredients': [
                    {'name': 'Greek yogurt', 'amount': '1 cup', 'notes': 'plain, non-fat'},
                    {'name': 'mixed berries', 'amount': '1/2 cup', 'notes': 'fresh or frozen'},
                    {'name': 'honey', 'amount': '1 tsp', 'notes': 'optional'}
                ],
                'nutrition': {
                    'calories': 250,
                    'protein_g': 20,
                    'carbs_g': 30,
                    'fat_g': 6,
                    'fiber_g': 5,
                    'sugar_g': 18,
                    'sodium_mg': 80
                },
                'instructions': [
                    'Scoop yogurt into a bowl.',
                    'Top with berries and drizzle with honey.'
                ],
                'estimated_cost': {'amount': 2.50, 'currency': 'USD'}
            }
        }
        
        # Generate meals for each day of the week
        for i, day in enumerate(days):
            day_meals = {
                'day': day_names[day.weekday()],
                'date': day.isoformat(),
                'meals': {
                    'breakfast': sample_meal['breakfast'].copy(),
                    'lunch': sample_meal['breakfast'].copy(),  # Just for testing
                    'dinner': sample_meal['breakfast'].copy()  # Just for testing
                },
                'nutrition_totals': {
                    'calories': 2100,
                    'protein_g': 150,
                    'carbs_g': 200,
                    'fat_g': 70,
                    'fiber_g': 35
                }
            }
            meal_plan['days'].append(day_meals)
        
        return jsonify({
            'success': True,
            'data': meal_plan,
            'message': 'Sample meal plan generated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=True)
