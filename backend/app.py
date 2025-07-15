from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import requests
import os
from functools import wraps

app = Flask(__name__)

# Configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///booking.db')
print(f"Using database: {database_url[:20]}...")  # Print first 20 chars for debugging

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 7)))
app.config['JWT_TOKEN_LOCATION'] = ['headers']  # ✅ FIXED JWT CONFIG
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Change debug mode based on environment ✅
app.config['DEBUG'] = os.getenv('FLASK_DEBUG') == 'True'

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# CORS Configuration ✅ removed wildcard '*'
CORS(app, 
     origins=[
         "https://booking-app-frontend-aws8.onrender.com",
         "https://deployed-booking-app-new-backend.onrender.com",
         "http://localhost:3000",
         "http://localhost:3001"
     ],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type", "Authorization"]
)

...

# Booking Routes
@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])  # ✅ FIXED PARAM
@jwt_required()
def cancel_booking(booking_id):  # ✅ FIXED PARAM
    try:
        user_id = get_jwt_identity()
        
        booking = Booking.query.filter_by(
            id=booking_id,
            user_id=user_id
        ).first()
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        if booking.status == 'cancelled':
            return jsonify({'message': 'Booking already cancelled'}), 400
        
        event = Event.query.get(booking.event_id)
        if event.date <= datetime.utcnow():
            return jsonify({'message': 'Cannot cancel past events'}), 400
        
        # Update booking status and event participant count
        booking.status = 'cancelled'
        event.current_participants -= 1
        
        db.session.commit()
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to cancel booking', 'error': str(e)}), 500

...

# Dashboard Routes
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    try:
        user_id = get_jwt_identity()
        print("JWT Identity:", user_id)  # ✅ TOKEN DEBUGGING

        total_bookings = Booking.query.filter_by(user_id=user_id).count()
        
        upcoming_bookings = db.session.query(Booking).join(Event).filter(
            Booking.user_id == user_id,
            Event.date > datetime.utcnow(),
            Booking.status != 'cancelled'
        ).count()
        
        past_bookings = db.session.query(Booking).join(Event).filter(
            Booking.user_id == user_id,
            Event.date <= datetime.utcnow()
        ).count()
        
        total_events = Event.query.filter(
            Event.status == 'active',
            Event.date > datetime.utcnow()
        ).count()
        
        return jsonify({
            'total_bookings': total_bookings,
            'upcoming_bookings': upcoming_bookings,
            'past_bookings': past_bookings,
            'total_events': total_events
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch stats', 'error': str(e)}), 500
if __name__ == '__main__':
    print("Starting application initialization...")
    init_db()
    print("Application initialization completed!")
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
