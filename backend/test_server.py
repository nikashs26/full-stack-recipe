from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "http://localhost:8081",
        "supports_credentials": True
    }
})

def get_nutritional_info(meal_name):
    """Helper function to generate nutritional info based on meal"""
    nutrition_db = {
        'breakfast': {
            'calories': 450,
            'protein': 25,
            'carbs': 40,
            'fat': 18,
            'fiber': 8
        },
        'lunch': {
            'calories': 600,
            'protein': 30,
            'carbs': 80,
            'fat': 15,
            'fiber': 12
        },
        'dinner': {
            'calories': 550,
            'protein': 35,
            'carbs': 50,
            'fat': 20,
            'fiber': 10
        },
        'snack': {
            'calories': 200,
            'protein': 10,
            'carbs': 25,
            'fat': 8,
            'fiber': 4
        }
    }
    return nutrition_db.get(meal_name, nutrition_db['lunch'])

def generate_weekly_plan():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_plan = []
    
    for day in days:
        meals = {
            'breakfast': {
                'name': 'Protein Oatmeal with Berries',
                'description': 'Steel-cut oats with whey protein, mixed berries, and chia seeds',
                'cuisine': 'International',
                'cook_time': '10 mins',
                'prep_time': '5 mins',
                'difficulty': 'easy',
                'ingredients': ['oats', 'whey protein', 'mixed berries', 'chia seeds', 'almond milk', 'honey'],
                'nutrition': get_nutritional_info('breakfast')
            },
            'morning_snack': {
                'name': 'Greek Yogurt with Nuts',
                'description': 'Greek yogurt with mixed nuts and a drizzle of honey',
                'cuisine': 'International',
                'prep_time': '2 mins',
                'difficulty': 'easy',
                'ingredients': ['greek yogurt', 'mixed nuts', 'honey'],
                'nutrition': get_nutritional_info('snack')
            },
            'lunch': {
                'name': 'Grilled Chicken Quinoa Bowl',
                'description': 'Grilled chicken with quinoa, roasted vegetables, and tahini dressing',
                'cuisine': 'Mediterranean',
                'cook_time': '25 mins',
                'prep_time': '15 mins',
                'difficulty': 'medium',
                'ingredients': ['chicken breast', 'quinoa', 'bell peppers', 'zucchini', 'tahini', 'lemon'],
                'nutrition': get_nutritional_info('lunch')
            },
            'afternoon_snack': {
                'name': 'Protein Shake with Banana',
                'description': 'Whey protein shake with banana and peanut butter',
                'cuisine': 'International',
                'prep_time': '5 mins',
                'difficulty': 'easy',
                'ingredients': ['whey protein', 'banana', 'peanut butter', 'almond milk'],
                'nutrition': get_nutritional_info('snack')
            },
            'dinner': {
                'name': 'Baked Salmon with Sweet Potato',
                'description': 'Oven-baked salmon with roasted sweet potatoes and steamed broccoli',
                'cuisine': 'International',
                'cook_time': '30 mins',
                'prep_time': '10 mins',
                'difficulty': 'medium',
                'ingredients': ['salmon fillet', 'sweet potato', 'broccoli', 'olive oil', 'lemon', 'herbs'],
                'nutrition': get_nutritional_info('dinner')
            },
            'evening_snack': {
                'name': 'Cottage Cheese with Berries',
                'description': 'Low-fat cottage cheese with mixed berries and cinnamon',
                'cuisine': 'International',
                'prep_time': '2 mins',
                'difficulty': 'easy',
                'ingredients': ['cottage cheese', 'mixed berries', 'cinnamon'],
                'nutrition': get_nutritional_info('snack')
            }
        }
        
        # Calculate daily totals
        daily_totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for meal in meals.values():
            for key in daily_totals.keys():
                daily_totals[key] += meal['nutrition'].get(key, 0)
        
        weekly_plan.append({
            'day': day,
            'date': (datetime.now() + timedelta(days=days.index(day))).strftime('%Y-%m-%d'),
            'meals': meals,
            'nutrition': daily_totals
        })
    
    return weekly_plan

@app.route('/api/test/meal_plan', methods=['POST'])
def test_meal_plan():
    weekly_plan = generate_weekly_plan()
    
    # Calculate weekly totals
    weekly_totals = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0,
        'fiber': 0
    }
    
    for day in weekly_plan:
        for key in weekly_totals.keys():
            weekly_totals[key] += day['nutrition'].get(key, 0)
    
    return jsonify({
        'success': True,
        'days': weekly_plan,
        'plan_type': 'detailed',
        'nutrition': weekly_totals,
        'currency': 'USD',
        'budget': 150.00,
        'totalCost': 135.75,
        'generated_at': datetime.now().isoformat(),
        'timeframe': 'week',
        'dietary_restrictions': [],
        'preferences': ['high_protein', 'balanced_meals']
    })

if __name__ == '__main__':
    print("Starting test server on port 5002...")
    app.run(port=5002, debug=False)
