# Book My Space

Book My Space is a full-stack web application designed to streamline venue booking at PES University and other premium locations. It allows users to discover, compare, and book venues for academic events, cultural programs, workshops, or personal celebrations. The platform features real-time availability, secure booking processes, and admin tools for managing users, venues, bookings, and statistics.

## Features

### User Features
- User registration and login (with role-based access: user or admin).
- Profile management (update name and password).
- Browse and book venues with date and time slot selection.
- View and cancel personal bookings.
- Payment simulation (70% success rate for demo purposes).

### Admin Features
- Manage venues (create, update, delete).
- Manage users (view, update roles, delete).
- View all bookings and cancel them (with refund simulation).
- View booking statistics (total bookings, revenue, status breakdowns).

### General Features
- Role-based protected routes.
- Real-time notifications using Toastify.
- Overlap prevention for booking time slots.
- JWT authentication for secure API access.
- Responsive UI with animations and gradients.

## Technologies Used

### Frontend
- React.js (with Hooks and Context API for state management).
- React Router for routing.
- Axios for API requests.
- React Toastify for notifications.
- Tailwind CSS/Bootstrap for styling (inferred from class names like `btn btn-primary`, `card`, etc.).
- Deployed on port 3000 (default Create React App).

### Backend
- Flask (Python web framework).
- MySQL database (via PyMySQL).
- JWT for authentication (using PyJWT).
- Bcrypt for password hashing.
- CORS for cross-origin requests.
- Environment variables via `.env` (using python-dotenv).
- Deployed on port 5001.

### Database
- MySQL with tables: `users`, `venues`, `bookings`, `payments`.
- Schema provided in `bms.sql`.

## Prerequisites
- Node.js (v14+) and npm for frontend.
- Python 3.8+ and pip for backend.
- MySQL server.
- `.env` file for backend with keys: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `SECRET_KEY`.

## Installation

### Backend Setup
1. Clone the repository:
   ```
   git clone <repo-url>
   cd backend
   ```
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install flask flask-cors pymysql bcrypt pyjwt python-dotenv
   ```
4. Set up the database:
   - Create a MySQL database named `event_booking`.
   - Run the schema from `bms.sql`:
     ```
     mysql -u <user> -p event_booking < bms.sql
     ```
5. Create `.env` file in the backend root:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=yourpassword
   MYSQL_DB=event_booking
   SECRET_KEY=your-secret-key  # Generate a strong key
   ```
6. Run the backend:
   ```
   python main.py
   ```
   The API will be available at `http://localhost:5001`.

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```
2. Install dependencies:
   ```
   npm install
   ```
   (This includes `react-router-dom`, `react-toastify`, `axios`, etc.)
3. Run the frontend:
   ```
   npm start
   ```
   The app will be available at `http://localhost:3000`.

## Usage

1. Open the app in your browser: `http://localhost:3000`.
2. Sign up as a user or admin (admin signup requires a valid admin JWT token from an existing admin).
3. Log in to access protected routes.
4. Users can book venues via `/bookings/create` and view bookings at `/bookings`.
5. Admins can access management tools at `/admin/*` (e.g., `/admin/venues`, `/admin/users`).

### API Endpoints (Key Examples)
- **Auth**:
  - POST `/api/signup`: Create user (body: {name, email, password, role}).
  - POST `/api/login`: Login (body: {email, password}).
- **User**:
  - GET `/api/venues`: List venues.
  - POST `/api/bookings`: Create booking (requires token).
  - GET `/api/bookings`: List user bookings.
  - DELETE `/api/bookings/<id>`: Cancel booking.
  - GET/POST `/api/profile`: View/update profile.
- **Admin**:
  - POST/GET/PUT/DELETE `/api/venues`: Manage venues.
  - GET `/api/users`: List users.
  - PUT `/api/users/<id>/role`: Update user role.
  - DELETE `/api/users/<id>`: Delete user.
  - GET `/api/bookings/all`: List all bookings.
  - DELETE `/api/admin/bookings/<id>`: Cancel booking (admin).
  - GET `/api/bookings/statistics`: Booking stats.

All protected endpoints require `Authorization: Bearer <token>` header.

### Testing
- Test DB connection: `http://localhost:5001/test-db`.
- Payments are simulated (70% success); failures delete the booking.
- Time slots are validated for format (HH:MM) and overlaps.

## Contributing
Contributions are welcome! Fork the repo, create a branch, and submit a PR.

## License
MIT License. See `LICENSE` file for details.

