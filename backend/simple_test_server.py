from flask import Flask, jsonify, request, make_response
from flask_cors import CORS, cross_origin

app = Flask(__name__)

# Configure CORS with minimal settings
cors = CORS()
cors.init_app(app, resources={
    r"/api/*": {
        "origins": "http://localhost:8081",
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
    }
})

@app.route('/api/test/meal_plan', methods=['POST', 'OPTIONS'])
def test_meal_plan():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    # Return a simple response immediately
    return jsonify({
        'success': True,
        'meal_plan': """Breakfast: Paneer Bhurji with Multigrain Toast (25g protein)
Lunch: Rajma Chawal with Yogurt (30g protein)
Dinner: Palak Tofu with Roti (28g protein)""",
        'model': 'test',
        'done_reason': 'completed',
        'cached': False
    })

if __name__ == '__main__':
    print("Starting simple test server on port 5001...")
    app.run(port=5001, debug=False)
