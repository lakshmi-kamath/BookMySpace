import { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar navbar-expand-lg animate-fade-in">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">Event Booking</Link>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            {user ? (
              <>
                <li className="nav-item"><Link className="nav-link" to="/profile">Profile</Link></li>
                <li className="nav-item"><Link className="nav-link" to="/bookings">Bookings</Link></li>
                {user.role === 'admin' && (
                  <>
                    <li className="nav-item"><Link className="nav-link" to="/admin/venues">Venues</Link></li>
                    <li className="nav-item"><Link className="nav-link" to="/admin/users">Users</Link></li>
                    <li className="nav-item"><Link className="nav-link" to="/admin/bookings">Bookings Overview</Link></li>
                    <li className="nav-item"><Link className="nav-link" to="/admin/statistics">Statistics</Link></li>
                  </>
                )}
              </>
            ) : (
              <>
                <li className="nav-item"><Link className="nav-link" to="/login">Login</Link></li>
                <li className="nav-item"><Link className="nav-link" to="/signup">Signup</Link></li>
              </>
            )}
          </ul>
          {user && <button className="btn btn-outline-danger" onClick={handleLogout}>Logout</button>}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;