import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

function Statistics() {
  const [stats, setStats] = useState({});

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('http://localhost:5001/api/bookings/statistics', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setStats(res.data);
      } catch (err) {
        toast.error('Failed to load statistics');
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="card animate-fade-in">
      <h2>Booking Statistics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(stats).map(([key, value]) => (
          <div key={key} className="p-4 bg-gray-50 rounded-lg hover:shadow-md transition-shadow duration-200">
            <h3 className="text-lg font-semibold capitalize">{key.replace('_', ' ')}</h3>
            <p className="text-2xl font-bold text-blue-600">{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Statistics;