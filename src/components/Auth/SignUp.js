import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';

function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [adminToken, setAdminToken] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const headers = role === 'admin' ? { Authorization: `Bearer ${adminToken}` } : {};
      await axios.post('http://localhost:5001/api/signup', { name, email, password, role }, { headers });
      toast.success('Signup successful. Please login.');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Signup failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-purple-400 to-pink-500 animate-fade-in">
      <div className="card max-w-md w-full mx-4 transform hover:scale-105 transition-transform duration-300">
        <h2 className="text-center text-2xl font-bold text-gray-800 mb-6">Signup</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="form-label text-gray-700">Name</label>
            <input
              type="text"
              className="form-control"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Enter your name"
            />
          </div>
          <div className="mb-4">
            <label className="form-label text-gray-700">Email</label>
            <input
              type="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          <div className="mb-4">
            <label className="form-label text-gray-700">Password</label>
            <input
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          <div className="mb-4">
            <label className="form-label text-gray-700">Role</label>
            <select className="form-control" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {role === 'admin' && (
            <div className="mb-4">
              <label className="form-label text-gray-700">Admin Token</label>
              <input
                type="text"
                className="form-control"
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value)}
                required
                placeholder="Enter admin token"
              />
            </div>
          )}
          <button type="submit" className="btn btn-primary w-full hover:bg-gradient-to-r hover:from-blue-600 hover:to-purple-600 transition-colors duration-300">
            Signup
          </button>
        </form>
        <p className="text-center mt-4 text-gray-600">
          Already have an account? <a href="/login" className="text-blue-600 hover:underline">Log In</a>
        </p>
      </div>
    </div>
  );
}

export default Signup;