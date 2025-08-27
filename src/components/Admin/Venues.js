import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

function Venues() {
  const [venues, setVenues] = useState([]);
  const [formData, setFormData] = useState({ name: '', location: '', capacity: '', price: '' });
  const [editId, setEditId] = useState(null);

  useEffect(() => {
    fetchVenues();
  }, []);

  const fetchVenues = async () => {
    try {
      const res = await axios.get('http://localhost:5001/api/venues', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      setVenues(res.data.venues);
    } catch (err) {
      toast.error('Failed to load venues');
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`http://localhost:5001/api/venues/${editId}`, formData, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        toast.success('Venue updated');
      } else {
        await axios.post('http://localhost:5001/api/venues', formData, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        toast.success('Venue created');
      }
      setFormData({ name: '', location: '', capacity: '', price: '' });
      setEditId(null);
      fetchVenues();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Operation failed');
    }
  };

  const handleEdit = (venue) => {
    setFormData(venue);
    setEditId(venue.id);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete venue?')) {
      try {
        await axios.delete(`http://localhost:5001/api/venues/${id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        toast.success('Venue deleted');
        fetchVenues();
      } catch (err) {
        toast.error(err.response?.data?.error || 'Delete failed');
      }
    }
  };

  return (
    <div className="card animate-fade-in">
      <h2>Manage Venues</h2>
      <form onSubmit={handleSubmit}>
        <div className="row">
          <div className="col-md-3 mb-3">
            <input name="name" placeholder="Name" className="form-control" value={formData.name} onChange={handleChange} required />
          </div>
          <div className="col-md-3 mb-3">
            <input name="location" placeholder="Location" className="form-control" value={formData.location} onChange={handleChange} required />
          </div>
          <div className="col-md-2 mb-3">
            <input name="capacity" placeholder="Capacity" type="number" className="form-control" value={formData.capacity} onChange={handleChange} required />
          </div>
          <div className="col-md-2 mb-3">
            <input name="price" placeholder="Price" type="number" className="form-control" value={formData.price} onChange={handleChange} required />
          </div>
          <div className="col-md-2 mb-3">
            <button type="submit" className="btn btn-primary">{editId ? 'Update' : 'Create'}</button>
          </div>
        </div>
      </form>
      <table className="table mt-4">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Location</th>
            <th>Capacity</th>
            <th>Price</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {venues.map((venue) => (
            <tr key={venue.id} className="hover:scale-105 transition-transform duration-200">
              <td>{venue.id}</td>
              <td>{venue.name}</td>
              <td>{venue.location}</td>
              <td>{venue.capacity}</td>
              <td>{venue.price}</td>
              <td>
                <button className="btn btn-warning me-2" onClick={() => handleEdit(venue)}>Edit</button>
                <button className="btn btn-danger" onClick={() => handleDelete(venue.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Venues;