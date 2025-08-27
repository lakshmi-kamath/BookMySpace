from flask import Blueprint, request, jsonify
from database import get_db_connection
import pymysql
from datetime import datetime
import random  # For simulating payment success/failure
from .middleware import admin_required

user_bp = Blueprint('user', __name__)

# Simulate payment processing
def simulate_payment(amount):
    success = random.random() < 0.7  # 70% chance of success
    status = 'success' if success else 'failed'
    return success, status

# Create a new booking with transaction, payment simulation, and rollback
@user_bp.route('/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        venue_id = data.get('venue_id')
        booking_date = data.get('booking_date')
        time_slot = data.get('time_slot')

        if not all([user_id, venue_id, booking_date, time_slot]):
            return jsonify({'error': 'Missing required fields: user_id, venue_id, booking_date, and time_slot are required'}), 400

        # Validate date format
        try:
            datetime.strptime(booking_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Validate time slot format (e.g., "14:00-16:00")
        if not isinstance(time_slot, str) or '-' not in time_slot:
            return jsonify({'error': 'Invalid time_slot format. Use HH:MM-HH:MM'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Start transaction
            conn.begin()

            # Lock the bookings table for this venue, date, and time slot
            cursor.execute(
                'SELECT * FROM bookings WHERE venue_id = %s AND booking_date = %s AND time_slot = %s FOR UPDATE',
                (venue_id, booking_date, time_slot)
            )
            
            # Check if slot is already booked
            existing_booking = cursor.fetchone()
            if existing_booking:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'This time slot is already booked'}), 409

            # Verify venue exists
            cursor.execute('SELECT id, price FROM venues WHERE id = %s', (venue_id,))
            venue = cursor.fetchone()
            if not venue:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Venue not found'}), 404

            # Verify user exists
            cursor.execute('SELECT id FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            if not user:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'User not found'}), 404

            # Create booking
            cursor.execute(
                'INSERT INTO bookings (user_id, venue_id, booking_date, time_slot, status) VALUES (%s, %s, %s, %s, %s)',
                (user_id, venue_id, booking_date, time_slot, 'pending')
            )

            # Get the booking ID
            booking_id = cursor.lastrowid

            # Create payment record
            cursor.execute(
                'INSERT INTO payments (booking_id, amount, status) VALUES (%s, %s, %s)',
                (booking_id, venue['price'], 'pending')
            )

            # Simulate payment processing
            payment_success, payment_status = simulate_payment(venue['price'])

            # Update payment status
            cursor.execute(
                'UPDATE payments SET status = %s WHERE booking_id = %s',
                (payment_status, booking_id)
            )

            if not payment_success:
                # Rollback booking if payment fails
                cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('cancelled', booking_id))
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({
                    'error': 'Payment failed, booking cancelled',
                    'booking': {
                        'id': booking_id,
                        'user_id': user_id,
                        'venue_id': venue_id,
                        'booking_date': booking_date,
                        'time_slot': time_slot,
                        'status': 'cancelled'
                    }
                }), 400

            # Update booking status to confirmed if payment succeeds
            cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('confirmed', booking_id))

            # Commit transaction
            conn.commit()

            cursor.close()
            conn.close()
            return jsonify({
                'message': 'Booking and payment processed successfully',
                'booking': {
                    'id': booking_id,
                    'user_id': user_id,
                    'venue_id': venue_id,
                    'booking_date': booking_date,
                    'time_slot': time_slot,
                    'status': 'confirmed'
                }
            }), 201

        except pymysql.IntegrityError as e:
            conn.rollback()
            cursor.close()
            conn.close()
            if "Duplicate entry" in str(e):
                return jsonify({'error': 'This time slot is already booked'}), 409
            return jsonify({'error': 'Database error occurred'}), 500

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update payment status (for testing or external payment gateway integration)
@user_bp.route('/payments/<int:booking_id>/status', methods=['PUT'])
def update_payment_status(booking_id):
    try:
        data = request.get_json()
        new_status = data.get('status')

        if not new_status or new_status not in ['success', 'failed', 'refunded', 'pending']:
            return jsonify({'error': 'Invalid or missing status'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Start transaction
            conn.begin()

            # Verify booking exists
            cursor.execute('SELECT id, status FROM bookings WHERE id = %s', (booking_id,))
            booking = cursor.fetchone()
            if not booking:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Booking not found'}), 404

            # Verify payment exists
            cursor.execute('SELECT id, status FROM payments WHERE booking_id = %s', (booking_id,))
            payment = cursor.fetchone()
            if not payment:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Payment not found'}), 404

            # Update payment status
            cursor.execute('UPDATE payments SET status = %s WHERE booking_id = %s', (new_status, booking_id))

            # If payment failed, cancel the booking
            if new_status == 'failed' and booking['status'] != 'cancelled':
                cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('cancelled', booking_id))
            # If payment succeeded, confirm the booking (if not already confirmed)
            elif new_status == 'success' and booking['status'] == 'pending':
                cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('confirmed', booking_id))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': f'Payment status updated to {new_status}'}), 200

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user's bookings (unchanged)
@user_bp.route('/bookings', methods=['GET'])
def get_user_bookings():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT b.*, v.name as venue_name, v.location, v.price, p.status as payment_status
            FROM bookings b
            JOIN venues v ON b.venue_id = v.id
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE b.user_id = %s
            ''',
            (user_id,)
        )
        bookings = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({'bookings': bookings}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Cancel booking (unchanged, but included for completeness)
@user_bp.route('/bookings/<int:id>', methods=['DELETE'])
def cancel_booking(id):
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Start transaction
            conn.begin()

            # Verify booking exists and belongs to user
            cursor.execute('SELECT user_id, status FROM bookings WHERE id = %s', (id,))
            booking = cursor.fetchone()

            if not booking:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Booking not found'}), 404

            if booking['user_id'] != int(user_id):
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Unauthorized: Cannot cancel another user\'s booking'}), 403

            if booking['status'] == 'cancelled':
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({'error': 'Booking is already cancelled'}), 400

            # Update booking status
            cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', ('cancelled', id))

            # Update payment status if exists
            cursor.execute('UPDATE payments SET status = %s WHERE booking_id = %s', ('cancelled', id))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Booking cancelled successfully'}), 200

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500