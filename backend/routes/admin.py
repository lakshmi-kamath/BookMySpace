from flask import Blueprint, request, jsonify
from database import get_db_connection
from functools import wraps
import jwt
import os
from dotenv import load_dotenv
from .middleware import admin_required

load_dotenv()

admin_bp = Blueprint('admin', __name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')


# Create a new venue
@admin_bp.route('/venues', methods=['POST'])
@admin_required
def create_venue(user_id):  # Add user_id parameter
    try:
        data = request.get_json()
        name = data.get('name')
        location = data.get('location')
        capacity = data.get('capacity')
        price = data.get('price')
        
        if not all([name, location, capacity, price]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO venues (name, location, capacity, price) VALUES (%s, %s, %s, %s)',
            (name, location, capacity, price)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({'message': 'Venue created successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get all venues
@admin_bp.route('/venues', methods=['GET'])
@admin_required
def get_venues(user_id):  # Add user_id parameter
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM venues')
        venues = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify({'venues': venues}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get single venue
@admin_bp.route('/venues/<int:id>', methods=['GET'])
@admin_required
def get_venue(user_id, id):  # Add user_id parameter, keep id
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM venues WHERE id = %s', (id,))
        venue = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not venue:
            return jsonify({'error': 'Venue not found'}), 404
        return jsonify({'venue': venue}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update venue
@admin_bp.route('/venues/<int:id>', methods=['PUT'])
@admin_required
def update_venue(user_id, id):  # Add user_id parameter, keep id
    try:
        data = request.get_json()
        name = data.get('name')
        location = data.get('location')
        capacity = data.get('capacity')
        price = data.get('price')
        
        if not any([name, location, capacity, price]):
            return jsonify({'error': 'At least one field must be provided'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        if name:
            update_fields.append('name = %s')
            values.append(name)
        if location:
            update_fields.append('location = %s')
            values.append(location)
        if capacity:
            update_fields.append('capacity = %s')
            values.append(capacity)
        if price:
            update_fields.append('price = %s')
            values.append(price)
            
        if update_fields:
            values.append(id)
            query = f'UPDATE venues SET {", ".join(update_fields)} WHERE id = %s'
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Venue not found'}), 404
                
        cursor.close()
        conn.close()
        return jsonify({'message': 'Venue updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Delete venue
@admin_bp.route('/venues/<int:id>', methods=['DELETE'])
@admin_required
def delete_venue(user_id, id):  # Add user_id parameter, keep id
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM venues WHERE id = %s', (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Venue not found'}), 404
            
        cursor.close()
        conn.close()
        return jsonify({'message': 'Venue deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Delete user
@admin_bp.route('/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(user_id, id):  # user_id is from decorator, id is from URL
    try:
        if user_id == id:
            return jsonify({'error': 'Cannot delete your own account'}), 403

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT role FROM users WHERE id = %s', (id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
            
        if user['role'] == 'admin':
            cursor.execute('SELECT COUNT(*) as admin_count FROM users WHERE role = "admin"')
            admin_count = cursor.fetchone()['admin_count']
            if admin_count <= 1:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Cannot delete the last admin'}), 403
            
        cursor.execute('DELETE FROM users WHERE id = %s', (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Failed to delete user'}), 500
            
        cursor.close()
        conn.close()
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@admin_bp.route('/users/<int:id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id, id):  # user_id is from decorator, id is from URL
    try:
        if user_id == id:
            return jsonify({'error': 'Cannot change your own role'}), 403

        data = request.get_json()
        new_role = data.get('role')

        if not new_role or new_role not in ['user', 'admin']:
            return jsonify({'error': 'Invalid or missing role'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute('SELECT role FROM users WHERE id = %s', (id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # Prevent demoting the last admin
        if user['role'] == 'admin' and new_role == 'user':
            cursor.execute('SELECT COUNT(*) as admin_count FROM users WHERE role = "admin"')
            admin_count = cursor.fetchone()['admin_count']
            if admin_count <= 1:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Cannot demote the last admin'}), 403

        # Update user role
        cursor.execute('UPDATE users SET role = %s WHERE id = %s', (new_role, id))
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Failed to update user role'}), 500

        cursor.close()
        conn.close()
        return jsonify({'message': f'User role updated to {new_role}'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500