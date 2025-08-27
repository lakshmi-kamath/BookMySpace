import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

function BookingsOverview() {
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const res = await axios.get('http://localhost:5001/api/bookings/all', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setBookings(res.data.bookings);
      } catch (err) {
        toast.error('Failed to load bookings');
      }
    };
    fetchBookings();
  }, []);

  const handleCancel = async (id) => {
    if (window.confirm('Cancel this booking?')) {
      try {
        await axios.delete(`http://localhost:5001/api/admin/bookings/${id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setBookings(bookings.filter((b) => b.id !== id));
        toast.success('Booking cancelled');
      } catch (err) {
        toast.error(err.response?.data?.error || 'Cancel failed');
      }
    }
  };

  return (
    <div className="card animate-fade-in">
      <h2>Bookings Overview</h2>
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>User ID</th>
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
              <td>{booking.user_id}</td>
              <td>{booking.venue_name}</td>
              <td>{booking.booking_date}</td>
              <td>{booking.start_time}</td>
              <td>{booking.end_time}</td>
              <td>{booking.time_slot}</td>
              <td>{booking.status}</td>
              <td>{booking.payment_status}</td>
              <td>
                {!booking.is_cancelled && (
                  <button className="btn btn-danger" onClick={() => handleCancel(booking.id)}>Cancel</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default BookingsOverview;