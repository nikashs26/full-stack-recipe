from flask import Blueprint, request, jsonify, session
from services.user_service import UserService

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400
    if user_service.register_user(email, password):
        return jsonify({'success': True, 'message': 'User registered successfully'})
    else:
        return jsonify({'success': False, 'message': 'User already exists'}), 409

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400
    if user_service.authenticate(email, password):
        session['user_email'] = email
        user = user_service.get_user(email)
        # Always return a full user object with at least email and full_name
        user_obj = {
            'email': user.get('email', ''),
            'full_name': user.get('full_name', '')
        }
        return jsonify({'success': True, 'message': 'Login successful', 'user': user_obj})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    return jsonify({'success': True, 'message': 'Logged out'})

@auth_bp.route('/me', methods=['GET'])
def me():
    email = session.get('user_email')
    if not email:
        return jsonify({'loggedIn': False}), 401
    user = user_service.get_user(email)
    if user:
        user_obj = {
            'email': user.get('email', ''),
            'full_name': user.get('full_name', '')
        }
        return jsonify({'loggedIn': True, 'user': user_obj})
    else:
        return jsonify({'loggedIn': False}), 401
