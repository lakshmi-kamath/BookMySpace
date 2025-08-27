from flask import Blueprint, request, jsonify
from database import get_db_connection
import pymysql
from datetime import datetime, date, timedelta
import random
from .middleware import token_required, admin_required
import bcrypt
import logging

user_bp = Blueprint('user', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def simulate_payment(amount):
    success = random.random() < 0.7
    status = 'success' if success else 'failed'
    return success, status

def validate_time_format(time_str):
    """Validate time string format (HH:MM)."""
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def check_time_slot_overlap(cursor, venue_id, booking_date, start_time, end_time):
    """Check if the requested time slot overlaps with existing bookings."""
    try:
        cursor.execute(
            '''
            SELECT start_time, end_time FROM bookings 
            WHERE venue_id = %s AND booking_date = %s AND status != 'cancelled'
            AND (
                (%s < end_time AND %s > start_time)
            )
            ''',
            (venue_id, booking_date, start_time, end_time)
        )
        overlapping_booking = cursor.fetchone()
        if overlapping_booking:
            return False, f"Time slot {start_time}-{end_time} overlaps with existing booking {overlapping_booking['start_time']}-{overlapping_booking['end_time']}"
        return True, None
    except Exception as e:
        return False, str(e)

def timedelta_to_str(td):
    """Convert timedelta to HH:MM string."""
    if td is None:
        return None
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

@user_bp.route('/venues', methods=['GET'])
@token_required
def get_venues(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, location, capacity, price, created_at FROM venues')
        venues = cursor.fetchall()
        
        cursor.close()
        conn.close()
        logger.info("Venues fetched successfully for user_id=%s", user_id)
        return jsonify({'venues': [
            {
                **venue,
                'created_at': venue['created_at'].isoformat() if venue['created_at'] else None
            } for venue in venues
        ]}), 200
        
    except Exception as e:
        logger.error("Error fetching venues: %s", str(e))
        return jsonify({'error': str(e)}), 500

@user_bp.route('/bookings', methods=['POST'])
def create_booking():
    logger.debug("Received booking request: %s", request.get_json())
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        venue_id = data.get('venue_id')
        booking_date = data.get('booking_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        logger.debug("Parsed data: user_id=%s, venue_id=%s, booking_date=%s, start_time=%s, end_time=%s", 
                     user_id, venue_id, booking_date, start_time, end_time)

        if not all([user_id, venue_id, booking_date, start_time, end_time]):
            logger.warning("Missing required fields: user_id=%s, venue_id=%s, booking_date=%s, start_time=%s, end_time=%s", 
                          user_id, venue_id, booking_date, start_time, end_time)
            return jsonify({'error': 'Missing required fields: user_id, venue_id, booking_date, start_time, and end_time are required'}), 400

        try:
            booking_date_dt = datetime.strptime(booking_date, '%Y-%m-%d').date()
            if booking_date_dt <= date.today():
                logger.warning("Booking date must be in the future: booking_date=%s", booking_date)
                return jsonify({'error': 'Booking date must be in the future'}), 400
        except ValueError:
            logger.warning("Invalid date format: %s", booking_date)
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        if not validate_time_format(start_time) or not validate_time_format(end_time):
            logger.warning("Invalid time format: start_time=%s, end_time=%s", start_time, end_time)
            return jsonify({'error': 'Invalid time format. Use HH:MM for start_time and end_time'}), 400

        # Validate that start_time is before end_time
        start_dt = datetime.strptime(start_time, '%H:%M')
        end_dt = datetime.strptime(end_time, '%H:%M')
        if start_dt >= end_dt:
            logger.warning("Invalid time range: start_time=%s is not before end_time=%s", start_time, end_time)
            return jsonify({'error': 'start_time must be before end_time'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            conn.begin()

            # Check for time slot overlap
            is_valid, error_message = check_time_slot_overlap(cursor, venue_id, booking_date, start_time, end_time)
            if not is_valid:
                conn.rollback()
                logger.warning("Time slot overlap: venue_id=%s, booking_date=%s, start_time=%s, end_time=%s, error=%s", 
                              venue_id, booking_date, start_time, end_time, error_message)
                return jsonify({'error': error_message}), 409

            cursor.execute('SELECT id, price FROM venues WHERE id = %s', (venue_id,))
            venue = cursor.fetchone()
            if not venue:
                conn.rollback()
                logger.warning("Venue not found: venue_id=%s", venue_id)
                return jsonify({'error': 'Venue not found'}), 404

            cursor.execute('SELECT id FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            if not user:
                conn.rollback()
                logger.warning("User not found: user_id=%s", user_id)
                return jsonify({'error': 'User not found'}), 404

            cursor.execute(
                'INSERT INTO bookings (user_id, venue_id, booking_date, start_time, end_time, status) VALUES (%s, %s, %s, %s, %s, %s)',
                (user_id, venue_id, booking_date, start_time, end_time, 'pending')
            )

            booking_id = cursor.lastrowid

            cursor.execute(
                'INSERT INTO payments (booking_id, amount, status) VALUES (%s, %s, %s)',
                (booking_id, venue['price'], 'pending')
            )

            payment_success, payment_status = simulate_payment(venue['price'])
            logger.debug("Payment simulation: success=%s, status=%s", payment_success, payment_status)

            cursor.execute(
                'UPDATE payments SET status = %s WHERE booking_id = %s',
                (payment_status, booking_id)
            )

            if not payment_success:
                # Delete booking instead of marking as cancelled
                cursor.execute('DELETE FROM bookings WHERE id = %s', (booking_id,))
                conn.commit()
                logger.info("Booking deleted due to payment failure: booking_id=%s", booking_id)
                return jsonify({
                    'error': 'Payment failed, booking deleted. Please try again.',
                    'booking': {
                        'id': booking_id,
                        'user_id': user_id,
                        'venue_id': venue_id,
                        'booking_date': booking_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'status': 'deleted',
                        'is_cancelled': True,
                        'is_refunded': False
                    }
                }), 400

            cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('confirmed', booking_id))

            conn.commit()
            logger.info("Booking created successfully: booking_id=%s", booking_id)

            return jsonify({
                'message': 'Booking and payment processed successfully',
                'booking': {
                    'id': booking_id,
                    'user_id': user_id,
                    'venue_id': venue_id,
                    'booking_date': booking_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'status': 'confirmed',
                    'is_cancelled': False,
                    'is_refunded': False
                }
            }), 201

        except pymysql.IntegrityError as e:
            conn.rollback()
            logger.error("Database IntegrityError: %s", str(e))
            return jsonify({'error': 'A booking for this venue, date, and exact time slot already exists'}), 409

        except Exception as e:
            conn.rollback()
            logger.error("Database error: %s", str(e))
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error("Unexpected error in create_booking: %s", str(e))
        return jsonify({'error': str(e)}), 500

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, role, created_at FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            logger.warning("User not found: user_id=%s", user_id)
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'profile': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }
        }), 200

    except Exception as e:
        logger.error("Error fetching profile: %s", str(e))
        return jsonify({'error': str(e)}), 500

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    try:
        data = request.get_json()
        name = data.get('name')
        password = data.get('password')
        
        if not name and not password:
            logger.warning("No fields to update for user_id=%s", user_id)
            return jsonify({'error': 'At least one field (name or password) must be provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if name:
            cursor.execute('UPDATE users SET name = %s WHERE id = %s', (name, user_id))
        
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password.decode('utf-8'), user_id))

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Profile updated successfully for user_id=%s", user_id)
        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        logger.error("Error updating profile: %s", str(e))
        return jsonify({'error': str(e)}), 500

@user_bp.route('/bookings', methods=['GET'])
@token_required
def get_user_bookings(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        status_filter = request.args.get('status')
        payment_status_filter = request.args.get('payment_status')
        venue_id_filter = request.args.get('venue_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = '''
            SELECT b.*, v.name as venue_name, v.location, v.price, p.status as payment_status,
                   p.created_at as payment_created_at
            FROM bookings b
            JOIN venues v ON b.venue_id = v.id
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE b.user_id = %s
        '''
        params = [user_id]

        if status_filter:
            query += ' AND b.status = %s'
            params.append(status_filter)
        if payment_status_filter:
            query += ' AND p.status = %s'
            params.append(payment_status_filter)
        if venue_id_filter:
            query += ' AND b.venue_id = %s'
            params.append(venue_id_filter)
        if start_date:
            query += ' AND b.booking_date >= %s'
            params.append(start_date)
        if end_date:
            query += ' AND b.booking_date <= %s'
            params.append(end_date)

        query += ' ORDER BY b.created_at DESC'

        cursor.execute(query, params)
        bookings = cursor.fetchall()

        enhanced_bookings = [
            {
                **booking,
                'is_cancelled': booking['status'] == 'cancelled',
                'is_refunded': booking['payment_status'] == 'refunded' if booking['payment_status'] else False,
                'created_at': booking['created_at'].isoformat() if booking['created_at'] else None,
                'payment_created_at': booking['payment_created_at'].isoformat() if booking['payment_created_at'] else None,
                'start_time': timedelta_to_str(booking['start_time']),
                'end_time': timedelta_to_str(booking['end_time']),
                'time_slot': f"{timedelta_to_str(booking['start_time'])}-{timedelta_to_str(booking['end_time'])}" if booking['start_time'] and booking['end_time'] else None
            }
            for booking in bookings
        ]

        cursor.close()
        conn.close()
        logger.info("Bookings fetched successfully for user_id=%s", user_id)
        return jsonify({
            'bookings': enhanced_bookings,
            'total_bookings': len(enhanced_bookings)
        }), 200

    except Exception as e:
        logger.error("Error fetching bookings: %s", str(e))
        return jsonify({'error': str(e)}), 500

@user_bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
@token_required
def cancel_booking(user_id, booking_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM bookings WHERE id = %s AND user_id = %s', (booking_id, user_id))
        booking = cursor.fetchone()

        if not booking:
            cursor.close()
            conn.close()
            logger.warning("Booking not found or not owned by user: booking_id=%s, user_id=%s", booking_id, user_id)
            return jsonify({'error': 'Booking not found or you do not have permission to cancel it'}), 404

        if booking['status'] == 'cancelled':
            cursor.close()
            conn.close()
            logger.warning("Booking already cancelled: booking_id=%s", booking_id)
            return jsonify({'error': 'Booking is already cancelled'}), 400

        cursor.execute('DELETE FROM bookings WHERE id = %s', (booking_id,))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Booking deleted successfully: booking_id=%s", booking_id)
        return jsonify({'message': 'Booking deleted successfully'}), 200

    except Exception as e:
        logger.error("Error cancelling booking: %s", str(e))
        return jsonify({'error': str(e)}), 500