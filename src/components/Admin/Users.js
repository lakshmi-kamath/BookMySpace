import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

function Users() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await axios.get('http://localhost:5001/api/users', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setUsers(res.data.users);
      } catch (err) {
        toast.error('Failed to load users');
      }
    };
    fetchUsers();
  }, []);

  const handleDelete = async (id) => {
    if (window.confirm('Delete user?')) {
      try {
        await axios.delete(`http://localhost:5001/api/users/${id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setUsers(users.filter((u) => u.id !== id));
        toast.success('User deleted');
      } catch (err) {
        toast.error(err.response?.data?.error || 'Delete failed');
      }
    }
  };

  const handleRoleUpdate = async (id, newRole) => {
    try {
      await axios.put(`http://localhost:5001/api/users/${id}/role`, { role: newRole }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      setUsers(users.map((u) => u.id === id ? { ...u, role: newRole } : u));
      toast.success('Role updated');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Update failed');
    }
  };

  return (
    <div className="card animate-fade-in">
      <h2>Manage Users</h2>
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id} className="hover:scale-105 transition-transform duration-200">
              <td>{user.id}</td>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <select value={user.role} onChange={(e) => handleRoleUpdate(user.id, e.target.value)} className="form-control w-auto d-inline-block me-2">
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
                <button className="btn btn-danger" onClick={() => handleDelete(user.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Users;