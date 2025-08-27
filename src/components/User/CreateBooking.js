import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';

function CreateBooking() {
  const { user } = useContext(AuthContext);
  const [venues, setVenues] = useState([]);
  const [venueId, setVenueId] = useState('');
  const [bookingDate, setBookingDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchVenues = async () => {
      try {
        const res = await axios.get('http://localhost:5001/api/venues', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setVenues(res.data.venues);
      } catch (err) {
        toast.error(err.response?.data?.error || 'Failed to load venues');
      }
    };
    fetchVenues();
  }, []);

  const validateTimeFormat = (time) => {
    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
    return timeRegex.test(time);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateTimeFormat(startTime) || !validateTimeFormat(endTime)) {
      toast.error('Invalid time format. Use HH:MM (e.g., 14:00)');
      return;
    }

    const start = new Date(`1970-01-01T${startTime}:00`);
    const end = new Date(`1970-01-01T${endTime}:00`);
    if (start >= end) {
      toast.error('Start time must be before end time');
      return;
    }

    const payload = {
      user_id: user?.user_id,
      venue_id: venueId,
      booking_date: bookingDate,
      start_time: startTime,
      end_time: endTime,
    };
    try {
      await axios.post('http://localhost:5001/api/bookings', payload, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      toast.success('Booking created');
      navigate('/bookings');
    } catch (err) {
      if (err.response?.data?.error === 'Payment failed, booking deleted. Please try again.') {
        toast.error('Payment failed. Please try booking again.');
      } else {
        toast.error(err.response?.data?.error || 'Booking failed');
      }
    }
  };

  return (
    <div className="card max-w-md mx-auto animate-fade-in">
      <h2 className="text-center">Create Booking</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label">Venue</label>
          <select className="form-control" value={venueId} onChange={(e) => setVenueId(e.target.value)} required>
            <option value="">Select Venue</option>
            {venues.map((venue) => (
              <option key={venue.id} value={venue.id}>{venue.name} - {venue.location}</option>
            ))}
          </select>
        </div>
        <div className="mb-3">
          <label className="form-label">Date</label>
          <input
            type="date"
            className="form-control"
            value={bookingDate}
            onChange={(e) => setBookingDate(e.target.value)}
            min={new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
            required
          />
        </div>
        <div className="mb-3">
          <label className="form-label">Start Time (e.g., 14:00)</label>
          <input
            type="text"
            className="form-control"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            placeholder="HH:MM"
            required
          />
        </div>
        <div className="mb-3">
          <label className="form-label">End Time (e.g., 16:00)</label>
          <input
            type="text"
            className="form-control"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            placeholder="HH:MM"
            required
          />
        </div>
        <button type="submit" className="btn btn-primary w-full">Book</button>
      </form>
    </div>
  );
}

export default CreateBooking;