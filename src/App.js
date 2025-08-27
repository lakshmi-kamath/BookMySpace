import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import Navbar from './components/Navbar';
import Login from './components/Auth/Login';
import Signup from './components/Auth/SignUp';
import Profile from './components/User/Profile';
import Bookings from './components/User/Bookings';
import CreateBooking from './components/User/CreateBooking';
import Venues from './components/Admin/Venues';
import Users from './components/Admin/Users';
import BookingsOverview from './components/Admin/BookingsOverview';
import Statistics from './components/Admin/Statistics';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Navbar />
        <div className="container mt-4">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/profile" element={<ProtectedRoute component={Profile} />} />
            <Route path="/bookings" element={<ProtectedRoute component={Bookings} />} />
            <Route path="/bookings/create" element={<ProtectedRoute component={CreateBooking} />} />
            <Route path="/admin/venues" element={<ProtectedRoute component={Venues} requiredRole="admin" />} />
            <Route path="/admin/users" element={<ProtectedRoute component={Users} requiredRole="admin" />} />
            <Route path="/admin/bookings" element={<ProtectedRoute component={BookingsOverview} requiredRole="admin" />} />
            <Route path="/admin/statistics" element={<ProtectedRoute component={Statistics} requiredRole="admin" />} />
            <Route
              path="/"
              element={
                <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-purple-400 to-pink-500 animate-fade-in">
                  <div className="card max-w-2xl w-full mx-4 transform hover:scale-105 transition-transform duration-300">
                    <h2 className="text-center text-3xl font-bold text-gray-800 mb-6">About Book My Space</h2>
                    <p className="text-gray-600 text-lg leading-relaxed mb-6">
                      Book My Space is designed to streamline venue booking at PES University and other premium locations. Whether you're organizing academic events, cultural programs, workshops, or personal celebrations, our platform provides a seamless experience to discover, compare, and book the ideal space for your needs.
                      <br /><br />
                      With real-time availability, secure booking processes, and comprehensive venue details, we make it easy to turn your event vision into reality. Join our community and experience hassle-free venue booking today.
                    </p>
                    <div className="text-center">
                      <a href="/signup" className="btn btn-primary animate-pulse">Get Started</a>
                    </div>
                  </div>
                </div>
              }
            />
          </Routes>
        </div>
        <ToastContainer />
      </Router>
    </AuthProvider>
  );
}

export default App;