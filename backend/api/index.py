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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///booking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 7)))

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'message': 'Authorization token is required'}), 401

# CORS Configuration - Fixed trailing slashes and added more permissive settings
CORS(app, 
     origins=[
         "https://booking-app-frontend-aws8.onrender.com",
         "https://deployed-booking-app-new-backend.onrender.com",
         "http://localhost:3000",
         "http://localhost:3001",
         "*"  # Allow all origins for debugging
     ],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type", "Authorization"]
)

# CRM Configuration
CRM_BASE_URL = os.getenv('CRM_BASE_URL', 'http://localhost:5001')
CRM_BEARER_TOKEN = os.getenv('CRM_BEARER_TOKEN', 'your-static-bearer-token')

# Models (same as before)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Facilitator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialization = db.Column(db.String(200))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    events = db.relationship('Event', backref='facilitator', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    current_participants = db.Column(db.Integer, default=0)
    facilitator_id = db.Column(db.Integer, db.ForeignKey('facilitator.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='event', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='confirmed')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='unique_user_event'),)

# Helper Functions
def notify_crm(booking_data):
    """Send booking notification to CRM system"""
    try:
        headers = {
            'Authorization': f'Bearer {CRM_BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'{CRM_BASE_URL}/api/notify',
            json=booking_data,
            headers=headers,
            timeout=10
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"CRM notification failed: {str(e)}")
        return False

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already registered'}), 400
        
        user = User(
            name=data['name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to get user info', 'error': str(e)}), 500

# Event Routes
@app.route('/api/events', methods=['GET'])
@jwt_required()
def get_events():
    try:
        print(f"Events endpoint called by user: {get_jwt_identity()}")
        
        # Check if database is accessible
        try:
            events = Event.query.filter(
                Event.status == 'active',
                Event.date > datetime.utcnow()
            ).order_by(Event.date).all()
        except Exception as db_error:
            print(f"Database query failed: {str(db_error)}")
            return jsonify({'message': 'Database connection failed', 'error': str(db_error)}), 422

        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.date.isoformat(),
                'duration': event.duration,
                'location': event.location,
                'price': event.price,
                'max_participants': event.max_participants,
                'current_participants': event.current_participants,
                'facilitator_name': event.facilitator.name,
                'facilitator_id': event.facilitator_id,
                'type': event.type
            })
        
        return jsonify({'events': events_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch events', 'error': str(e)}), 500

# Booking Routes
@app.route('/api/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('event_id'):
            return jsonify({'message': 'Event ID is required'}), 400
        
        event = Event.query.get(data['event_id'])
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        if event.current_participants >= event.max_participants:
            return jsonify({'message': 'Event is fully booked'}), 400
        
        if event.date <= datetime.utcnow():
            return jsonify({'message': 'Cannot book past events'}), 400
        
        existing_booking = Booking.query.filter_by(
            user_id=user_id,
            event_id=event.id
        ).first()
        
        if existing_booking:
            return jsonify({'message': 'You have already booked this event'}), 400
        
        booking = Booking(
            user_id=user_id,
            event_id=event.id
        )
        
        event.current_participants += 1
        
        db.session.add(booking)
        db.session.commit()
        
        user = User.query.get(user_id)
        crm_data = {
            'booking_id': booking.id,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            },
            'event': {
                'id': event.id,
                'title': event.title,
                'date': event.date.isoformat(),
                'type': event.type
            },
            'facilitator_id': event.facilitator_id
        }
        
        notify_crm(crm_data)
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking_id': booking.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Booking failed', 'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
@jwt_required()
def get_user_bookings():
    try:
        user_id = get_jwt_identity()
        print(f"Bookings endpoint called by user: {user_id}")
        limit = request.args.get('limit', type=int)
        
        query = db.session.query(Booking, Event, Facilitator).join(
            Event, Booking.event_id == Event.id
        ).join(
            Facilitator, Event.facilitator_id == Facilitator.id
        ).filter(
            Booking.user_id == user_id
        ).order_by(Event.date.desc())
        
        if limit:
            query = query.limit(limit)
        
        results = query.all()
        
        bookings_data = []
        for booking, event, facilitator in results:
            bookings_data.append({
                'id': booking.id,
                'event_id': event.id,
                'event_title': event.title,
                'event_description': event.description,
                'event_date': event.date.isoformat(),
                'event_duration': event.duration,
                'event_location': event.location,
                'event_price': event.price,
                'event_type': event.type,
                'facilitator_name': facilitator.name,
                'status': booking.status,
                'booking_date': booking.booking_date.isoformat()
            })
        
        return jsonify({'bookings': bookings_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@jwt_required()
def cancel_booking():
    try:
        user_id = get_jwt_identity()
        booking_id = request.view_args['booking_id']
        
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
        
        booking.status = 'cancelled'
        event.current_participants -= 1
        
        db.session.commit()
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to cancel booking', 'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    try:
        user_id = get_jwt_identity()
        print(f"Dashboard stats endpoint called by user: {user_id}")
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

# Initialize database and sample data
# Initialize database and sample data
def init_db():
    try:
        with app.app_context():
            print("Initializing database...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Check if data already exists
            if not Facilitator.query.first():
                print("Creating sample data...")
                facilitators = [
                    Facilitator(
                        name="Dr. Sarah Johnson",
                        email="sarah@example.com",
                        specialization="Mindfulness & Meditation",
                        bio="Expert in mindfulness practices with 15+ years experience"
                    ),
                    Facilitator(
                        name="Michael Chen",
                        email="michael@example.com",
                        specialization="Yoga & Wellness",
                        bio="Certified yoga instructor and wellness coach"
                    ),
                    Facilitator(
                        name="Emma Rodriguez",
                        email="emma@example.com",
                        specialization="Life Coaching",
                        bio="Professional life coach specializing in personal development"
                    )
                ]
                
                for facilitator in facilitators:
                    db.session.add(facilitator)
                
                db.session.commit()
                
                sample_events = [
                    Event(
                        title="Morning Meditation Session",
                        description="Start your day with a peaceful meditation session focusing on breath awareness and mindfulness techniques.",
                        date=datetime.utcnow() + timedelta(days=3),
                        duration=60,
                        location="Zen Studio, Downtown",
                        price=25.00,
                        max_participants=15,
                        facilitator_id=1,
                        type="session"
                    ),
                    Event(
                        title="Weekend Yoga Retreat",
                        description="A rejuvenating weekend retreat combining yoga, meditation, and nature walks in a serene mountain setting.",
                        date=datetime.utcnow() + timedelta(days=10),
                        duration=2880,
                        location="Mountain View Retreat Center",
                        price=299.00,
                        max_participants=20,
                        facilitator_id=2,
                        type="retreat"
                    ),
                    Event(
                        title="Life Coaching Workshop",
                        description="Interactive workshop on goal setting, overcoming obstacles, and creating positive life changes.",
                        date=datetime.utcnow() + timedelta(days=7),
                        duration=180,
                        location="Community Center, Room 201",
                        price=75.00,
                        max_participants=12,
                        facilitator_id=3,
                        type="session"
                    )
                ]
                
                for event in sample_events:
                    db.session.add(event)
                
                db.session.commit()
                print("Database initialized with sample data!")
            else:
                print("Sample data already exists, skipping creation.")
     
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        # Don't raise the exception to prevent deployment failure
        # The database might already exist or have permissions issues

# Add a health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500


# Initialize database
init_db()

# This is the main entry point for Vercel
def handler(event, context):
    return app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
