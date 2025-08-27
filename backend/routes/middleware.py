# middleware.py
from flask import request, jsonify
from functools import wraps
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1] if token.startswith("Bearer ") else token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return f(user_id=data['user_id'], *args, **kwargs)  # Pass user_id to route
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1] if token.startswith("Bearer ") else token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            if data['role'] != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            return f(user_id=data['user_id'], *args, **kwargs)  # Pass user_id to route
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated