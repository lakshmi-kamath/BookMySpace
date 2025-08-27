# main.py
from flask import Flask
from flask_cors import CORS
from database import get_db_connection
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Register blueprints for routes
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')

# Test database connection
@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {'status': 'Database connection successful', 'result': result}
    except Exception as e:
        return {'status': 'Database connection failed', 'error': str(e)}
    
   
@app.route('/')
def home():
    return {'message': 'Welcome to the Event Booking API'}

if __name__ == '__main__':
    app.run(debug=True, port=5001)

