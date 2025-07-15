from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import requests
import os
from functools import wraps
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError # Import these

app = Flask(__name__)

# Configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///booking.db')
print(f"Using database: {database_url[:20]}...")  # Print first 20 chars for debugging

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 7)))

# Update JWT configuration
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Change debug mode based on environment
app.config['DEBUG'] = os.getenv('FLASK_DEBUG') == 'True'


# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# JWT Error Handlers
# Add more specific logging for token issues
@jwt.unauthorized_loader
def unauthorized_response(callback):
    print(f"UNAUTHORIZED: {callback}")
    return jsonify({"message": "Request does not contain an access token or token is invalid."}), 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    print(f"INVALID TOKEN: {callback}")
    return jsonify({"message": "Signature verification failed or token is malformed."}), 401

@jwt.expired_token_loader
def expired_token_callback(callback):
    print(f"EXPIRED TOKEN: {callback}")
    return jsonify({"message": "The token has expired."}), 401

@jwt.missing_token_loader
def missing_token_callback(callback):
    print(f"MISSING TOKEN: {callback}")
    return jsonify({"message": "Missing JWT in Authorization header."}), 401

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return False  # For now, no tokens are revoked

# Request logging for debugging
@app.before_request
def log_request_info():
    if request.path.startswith('/api/'):
        auth_header = request.headers.get('Authorization', 'No Auth Header')
        content_type = request.headers.get('Content-Type', 'No Content-Type')
        origin = request.headers.get('Origin', 'No Origin')
        
        print(f"==== REQUEST DEBUG ====")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
        print(f"Origin: {origin}")
        print(f"Content-Type: {content_type}")
        print(f"Auth Header: {auth_header[:50]}..." if len(auth_header) > 50 else f"Auth Header: {auth_header}")
        
        # Check if it's a protected endpoint
        protected_endpoints = ['/api/auth/me', '/api/events', '/api/bookings', '/api/dashboard/stats', '/api/jwt-test']
        if any(request.path.startswith(endpoint) for endpoint in protected_endpoints):
            print(f"Protected endpoint accessed: {request.path}")
            if not auth_header or auth_header == 'No Auth Header':
                print("WARNING: No authorization header for protected endpoint!")
            elif not auth_header.startswith('Bearer '):
                print("WARNING: Authorization header doesn't start with 'Bearer '!")
        print(f"======================")

# Add JWT debug helper function
def debug_jwt_token():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            print(f"JWT Debug - Token decoded successfully: {decoded}")
            return True
        except Exception as e:
            print(f"JWT Debug - Token decode failed: {str(e)}")
            return False
    else:
        print(f"JWT Debug - Invalid auth header format: {auth_header}")
        return False

# Combined and corrected CORS Configuration
CORS(app, resources={r"/api/*": {
    "origins": [
        "https://booking-app-frontend-aws8.onrender.com",
        "https://deployed-booking-app-new-backend.onrender.com",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    "supports_credentials": True,
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}})

# CRM Configuration
CRM_BASE_URL = os.getenv('CRM_BASE_URL', 'http://localhost:5001')
CRM_BEARER_TOKEN = os.getenv('CRM_BEARER_TOKEN', 'your-static-bearer-token')

# Models
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
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    current_participants = db.Column(db.Integer, default=0)
    facilitator_id = db.Column(db.Integer, db.ForeignKey('facilitator.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'session' or 'retreat'
    status = db.Column(db.String(50), default='active')  # 'active', 'cancelled', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='event', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='confirmed')  # 'confirmed', 'cancelled', 'pending'
    
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='unique_user_event'),)

    # Add a to_dict method for easy JSON serialization
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'booking_date': self.booking_date.isoformat(),
            'status': self.status
            # You might want to include event details here as well,
            # but for now, just the booking itself.
        }

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For demo purposes, we'll skip admin check
        # In production, implement proper admin role checking
        return f(*args, **kwargs)
    return decorated_function

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
        print(f"Auth/me endpoint called, user_id: {user_id}")
        
        if not user_id:
            print("No user_id found in JWT token")
            return jsonify({'message': 'Invalid token payload'}), 422

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
        user_id = get_jwt_identity()
        print(f"Events endpoint called by user: {user_id}")
        
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
        
        # Check if user already booked this event
        existing_booking = Booking.query.filter_by(
            user_id=user_id,
            event_id=event.id
        ).first()
        
        if existing_booking:
            return jsonify({'message': 'You have already booked this event'}), 400
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            event_id=event.id
        )
        
        # Update event participant count
        event.current_participants += 1
        
        db.session.add(booking)
        db.session.commit()
        
        # Notify CRM
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
        
    except (ExpiredSignatureError, InvalidTokenError, DecodeError) as e:
        print(f"JWT processing error in get_user_bookings: {e}")
        return jsonify({"message": f"Authentication failed: {str(e)}"}), 401
    except Exception as e:
        print(f"Unexpected error in get_user_bookings: {e}")
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500

# Fix Parameter Handling in cancel_booking:
@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@jwt_required()
def cancel_booking(booking_id):  # Add parameter here
    try:
        user_id = get_jwt_identity()
        # booking_id = request.view_args['booking_id'] # This line is no longer needed
        
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

# Dashboard Routes
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    print("JWT Identity:", get_jwt_identity())  # Add this line
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
        
    except (ExpiredSignatureError, InvalidTokenError, DecodeError) as e:
        print(f"JWT processing error in get_dashboard_stats: {e}")
        return jsonify({"message": f"Authentication failed: {str(e)}"}), 401
    except Exception as e:
        print(f"Unexpected error in get_dashboard_stats: {e}")
        return jsonify({'message': 'Failed to fetch stats', 'error': str(e)}), 500

# Admin Routes (for demo purposes)
@app.route('/api/admin/events', methods=['POST'])
def create_event():
    try:
        data = request.get_json()
        
        required_fields = ['title', 'description', 'date', 'duration', 'location', 'price', 'max_participants', 'facilitator_id', 'type']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
        
        event = Event(
            title=data['title'],
            description=data['description'],
            date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
            duration=data['duration'],
            location=data['location'],
            price=data['price'],
            max_participants=data['max_participants'],
            facilitator_id=data['facilitator_id'],
            type=data['type']
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'event_id': event.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create event', 'error': str(e)}), 500

# Add a health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1')) # Use db.text for literal SQL
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500

# Add a simple root route to prevent 404 errors on health checks
@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'Booking App API', 'status': 'running'}), 200

# Debug endpoint to check database contents
@app.route('/api/debug', methods=['GET'])
def debug_db():
    try:
        facilitator_count = Facilitator.query.count()
        event_count = Event.query.count()
        user_count = User.query.count()
        
        # Get sample events
        events = Event.query.limit(3).all()
        event_list = []
        for event in events:
            event_list.append({
                'id': event.id,
                'title': event.title,
                'date': event.date.isoformat(),
                'facilitator_id': event.facilitator_id
            })
        
        return jsonify({
            'database_status': 'connected',
            'facilitators': facilitator_count,
            'events': event_count,
            'users': user_count,
            'sample_events': event_list
        }), 200
    except Exception as e:
        return jsonify({
            'database_status': 'error',
            'error': str(e)
        }), 500
# JWT Test endpoint
@app.route('/api/jwt-test', methods=['POST', 'GET'])
@jwt_required()
def jwt_test():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        return jsonify({
            'message': 'JWT token is valid',
            'user_id': user_id,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            } if user else None,
            'token_valid': True
        }), 200
    except Exception as e:
        return jsonify({
            'message': 'JWT token test failed',
            'error': str(e),
            'token_valid': False
        }), 500

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

# Remove duplicate init_db() calls
if __name__ == '__main__':
    # Only run this in main execution context
    print("Starting application initialization...")
    init_db()
    print("Application initialization completed!")
    app.run(debug=os.getenv('FLASK_DEBUG') == 'True', host='0.0.0.0', port=5000)
