from flask import Blueprint, request, jsonify
from database import get_db_connection
from functools import wraps
import jwt
import os
from dotenv import load_dotenv
from .middleware import admin_required
import pymysql
import datetime
import logging

load_dotenv()

admin_bp = Blueprint('admin', __name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def timedelta_to_str(td):
    """Convert timedelta to HH:MM string."""
    if td is None:
        return None
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

# Create a new venue
@admin_bp.route('/venues', methods=['POST'])
@admin_required
def create_venue(user_id):
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
def get_venues(user_id):
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
def get_venue(user_id, id):
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
def update_venue(user_id, id):
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
def delete_venue(user_id, id):
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
def delete_user(user_id, id):
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
def update_user_role(user_id, id):
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

def validate_venue_id(venue_id, cursor):
    """Validate if venue_id exists in the venues table."""
    cursor.execute('SELECT id FROM venues WHERE id = %s', (venue_id,))
    return cursor.fetchone() is not None

def validate_date(date_str):
    """Validate date string format (YYYY-MM-DD)."""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@admin_bp.route('/revenue', methods=['GET'])
@admin_required
def get_revenue_report(user_id):
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        venue_id = request.args.get('venue_id')

        # Validate inputs
        if start_date and not validate_date(start_date):
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        if end_date and not validate_date(end_date):
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        if venue_id and not venue_id.isdigit():
            return jsonify({'error': 'Invalid venue_id. Must be an integer'}), 400

        params = []
        query = '''
                SELECT 
                    COALESCE(SUM(p.amount), 0) as total_revenue, 
                    COUNT(p.id) as total_successful_payments
                FROM payments p
                JOIN bookings b ON p.booking_id = b.id
                WHERE p.status = 'success' AND b.status = 'confirmed'
            '''
        if start_date:
            query += ' AND b.booking_date >= %s'
            params.append(start_date)
        if end_date:
            query += ' AND b.booking_date <= %s'
            params.append(end_date)
        if venue_id:
            query += ' AND b.venue_id = %s'
            params.append(venue_id)

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if venue_id:
                    if not validate_venue_id(venue_id, cursor):
                        return jsonify({'error': 'Venue not found'}), 404
                cursor.execute(query, params)
                report = cursor.fetchone()

        return jsonify({
                'total_revenue': float(report['total_revenue']) if report['total_revenue'] else 0.0,
                'total_successful_payments': report['total_successful_payments'] or 0
            }), 200

    except pymysql.MySQLError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@admin_bp.route('/bookings/all', methods=['GET'])
@admin_required
def get_all_bookings(user_id):
    """
    Admin endpoint to view all bookings with optional filters.
    Supports filtering by status, payment_status, venue_id, user_id, date range.
    """
    try:
        # Get query parameters for filtering
        status_filter = request.args.get('status')
        payment_status_filter = request.args.get('payment_status')
        venue_id_filter = request.args.get('venue_id')
        user_id_filter = request.args.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Validate inputs
        if start_date and not validate_date(start_date):
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        if end_date and not validate_date(end_date):
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        if venue_id_filter and not venue_id_filter.isdigit():
            return jsonify({'error': 'Invalid venue_id. Must be an integer'}), 400
        if user_id_filter and not user_id_filter.isdigit():
            return jsonify({'error': 'Invalid user_id. Must be an integer'}), 400
        if status_filter and status_filter not in ['confirmed', 'cancelled', 'pending']:
            return jsonify({'error': 'Invalid status. Must be confirmed, cancelled, or pending'}), 400
        if payment_status_filter and payment_status_filter not in ['success', 'failed', 'refunded', 'pending']:
            return jsonify({'error': 'Invalid payment_status. Must be success, failed, refunded, or pending'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build the query with joins to get comprehensive booking information
        query = '''
            SELECT 
                b.id,
                b.user_id,
                b.venue_id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                b.created_at,
                u.name as user_name,
                u.email as user_email,
                v.name as venue_name,
                v.location,
                v.price,
                p.status as payment_status,
                p.amount as payment_amount,
                p.created_at as payment_created_at
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.id
            LEFT JOIN venues v ON b.venue_id = v.id
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE 1=1
        '''
        
        params = []
        
        # Add filters to the query
        if status_filter:
            query += ' AND b.status = %s'
            params.append(status_filter)
        
        if payment_status_filter:
            query += ' AND p.status = %s'
            params.append(payment_status_filter)
        
        if venue_id_filter:
            query += ' AND b.venue_id = %s'
            params.append(venue_id_filter)
        
        if user_id_filter:
            query += ' AND b.user_id = %s'
            params.append(user_id_filter)
        
        if start_date:
            query += ' AND b.booking_date >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND b.booking_date <= %s'
            params.append(end_date)
        
        # Order by most recent bookings first
        query += ' ORDER BY b.created_at DESC'
        
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        
        # Enhance response with additional computed fields
        enhanced_bookings = []
        for booking in bookings:
            enhanced_booking = dict(booking)
            enhanced_booking['is_cancelled'] = booking['status'] == 'cancelled'
            enhanced_booking['is_refunded'] = booking['payment_status'] == 'refunded' if booking['payment_status'] else False
            enhanced_booking['start_time'] = timedelta_to_str(booking['start_time'])
            enhanced_booking['end_time'] = timedelta_to_str(booking['end_time'])
            enhanced_booking['time_slot'] = f"{timedelta_to_str(booking['start_time'])}-{timedelta_to_str(booking['end_time'])}" if booking['start_time'] and booking['end_time'] else None
            
            # Format dates for better readability
            if booking['created_at']:
                enhanced_booking['created_at'] = booking['created_at'].isoformat()
            if booking['payment_created_at']:
                enhanced_booking['payment_created_at'] = booking['payment_created_at'].isoformat()
            
            enhanced_bookings.append(enhanced_booking)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'bookings': enhanced_bookings,
            'total_bookings': len(enhanced_bookings),
            'filters_applied': {
                'status': status_filter,
                'payment_status': payment_status_filter,
                'venue_id': venue_id_filter,
                'user_id': user_id_filter,
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except pymysql.MySQLError as e:
        logger.error(f"Database error in get_all_bookings: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_all_bookings: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@admin_bp.route('/bookings/statistics', methods=['GET'])
@admin_required  
def get_booking_statistics(user_id):
    """
    Admin endpoint to get booking statistics summary.
    Returns counts for different booking statuses, payment statuses, etc.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get booking status counts
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count
            FROM bookings 
            GROUP BY status
        ''')
        booking_status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Get payment status counts
        cursor.execute('''
            SELECT 
                p.status,
                COUNT(*) as count
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            GROUP BY p.status
        ''')
        payment_status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Get total revenue by status
        cursor.execute('''
            SELECT 
                p.status,
                COALESCE(SUM(p.amount), 0) as total_amount
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            GROUP BY p.status
        ''')
        revenue_by_payment_status = {
            row['status']: float(row['total_amount']) 
            for row in cursor.fetchall()
        }
        
        # Get bookings by venue
        cursor.execute('''
            SELECT 
                v.name as venue_name,
                COUNT(b.id) as booking_count,
                COALESCE(SUM(CASE WHEN p.status = 'success' THEN p.amount END), 0) as revenue
            FROM venues v
            LEFT JOIN bookings b ON v.id = b.venue_id
            LEFT JOIN payments p ON b.id = p.booking_id
            GROUP BY v.id, v.name
            ORDER BY booking_count DESC
        ''')
        venue_statistics = [
            {
                'venue_name': row['venue_name'],
                'booking_count': row['booking_count'],
                'revenue': float(row['revenue'])
            }
            for row in cursor.fetchall()
        ]
        
        # Get recent booking trends (last 30 days by day)
        cursor.execute('''
            SELECT 
                DATE(b.created_at) as booking_date,
                COUNT(*) as bookings_count,
                COALESCE(SUM(CASE WHEN p.status = 'success' THEN p.amount END), 0) as daily_revenue
            FROM bookings b
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE b.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(b.created_at)
            ORDER BY booking_date DESC
            LIMIT 30
        ''')
        recent_trends = [
            {
                'date': row['booking_date'].isoformat() if row['booking_date'] else None,
                'bookings_count': row['bookings_count'],
                'daily_revenue': float(row['daily_revenue'])
            }
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'booking_status_counts': booking_status_counts,
            'payment_status_counts': payment_status_counts,
            'revenue_by_payment_status': revenue_by_payment_status,
            'venue_statistics': venue_statistics,
            'recent_trends_30_days': recent_trends,
            'summary': {
                'total_bookings': sum(booking_status_counts.values()),
                'total_revenue': revenue_by_payment_status.get('success', 0),
                'successful_bookings': booking_status_counts.get('confirmed', 0),
                'cancelled_bookings': booking_status_counts.get('cancelled', 0),
                'pending_bookings': booking_status_counts.get('pending', 0)
            }
        }), 200
        
    except pymysql.MySQLError as e:
        logger.error(f"Database error in get_booking_statistics: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_booking_statistics: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
@admin_bp.route('/admin/bookings/<int:id>', methods=['DELETE'])
@admin_required
def cancel_booking(user_id, id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Start transaction
            conn.begin()

            # Verify booking exists
            cursor.execute('SELECT status FROM bookings WHERE id = %s', (id,))
            booking = cursor.fetchone()

            if not booking:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Booking not found'}), 404

            if booking['status'] == 'cancelled':
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Booking is already cancelled'}), 400

            # Update booking status
            cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('cancelled', id))

            # Update payment status to refunded if applicable
            cursor.execute('UPDATE payments SET status = %s WHERE booking_id = %s', ('refunded', id))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({
                'message': 'Booking cancelled successfully',
                'is_cancelled': True,
                'is_refunded': True
            }), 200

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, role, created_at FROM users')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'users': [
            {
                **user,
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            } for user in users
        ]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500