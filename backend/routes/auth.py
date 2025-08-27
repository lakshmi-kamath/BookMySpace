from flask import Blueprint, request, jsonify
from database import get_db_connection
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
from functools import wraps
import pymysql
# from middleware import admin_required

load_dotenv()

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')  # Default to 'user'

        if not all([name, email, password]):
            return jsonify({'error': 'Missing required fields: name, email, and password are required'}), 400

        if role not in ['user', 'admin']:
            return jsonify({'error': 'Invalid role specified. Must be "user" or "admin"'}), 400

        # If role is 'admin', require admin token
        if role == 'admin':
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Admin token required to create admin user'}), 401
            try:
                token = token.split(" ")[1] if token.startswith("Bearer ") else token
                jwt_data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                if jwt_data['role'] != 'admin':
                    return jsonify({'error': 'Admin access required to create admin user'}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)',
                (name, email, hashed_password.decode('utf-8'), role)
            )
            conn.commit()
            return jsonify({'message': 'User created successfully'}), 201
        except pymysql.IntegrityError as e:
            if "Duplicate entry" in str(e):
                return jsonify({'error': 'Email already exists'}), 400
            return jsonify({'error': 'Database error occurred'}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY, algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500