import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';

function Bookings() {
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const res = await axios.get('http://localhost:5001/api/bookings', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setBookings(res.data.bookings);
      } catch (err) {
        toast.error(err.response?.data?.error || 'Failed to load bookings');
      }
    };
    fetchBookings();
  }, []);

  const handleCancel = async (id) => {
    if (window.confirm('Delete this booking?')) {
      try {
        await axios.delete(`http://localhost:5001/api/bookings/${id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setBookings(bookings.filter((b) => b.id !== id));
        toast.success('Booking deleted');
      } catch (err) {
        toast.error(err.response?.data?.error || 'Failed to delete booking');
      }
    }
  };

  return (
    <div className="card animate-fade-in">
      <h2>My Bookings</h2>
      <Link to="/bookings/create" className="btn btn-success mb-3">Create New Booking</Link>
      {bookings.length === 0 ? (
        <p>No bookings found.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Venue</th>
              <th>Date</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>Time Slot</th>
              <th>Status</th>
              <th>Payment Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((booking) => (
              <tr key={booking.id} className="hover:scale-105 transition-transform duration-200">
                <td>{booking.id}</td>
                <td>{booking.venue_name}</td>
                <td>{booking.booking_date}</td>
                <td>{booking.start_time}</td>
                <td>{booking.end_time}</td>
                <td>{booking.time_slot}</td>
                <td>{booking.status}</td>
                <td>{booking.payment_status}</td>
                <td>
                  {booking.status !== 'cancelled' && (
                    <button className="btn btn-danger" onClick={() => handleCancel(booking.id)}>Delete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Bookings;