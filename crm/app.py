from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import json
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
BEARER_TOKEN = os.getenv('CRM_BEARER_TOKEN', 'your-static-bearer-token')

# In-memory storage for demo (use database in production)
notifications = []
facilitators = {
    1: {
        'id': 1,
        'name': 'Dr. Sarah Johnson',
        'email': 'sarah@example.com',
        'bookings': []
    },
    2: {
        'id': 2,
        'name': 'Michael Chen',
        'email': 'michael@example.com',
        'bookings': []
    },
    3: {
        'id': 3,
        'name': 'Emma Rodriguez',
        'email': 'emma@example.com',
        'bookings': []
    }
}

def require_bearer_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header missing'}), 401
        
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({'error': 'Invalid token type'}), 401
            
            if token != BEARER_TOKEN:
                return jsonify({'error': 'Invalid bearer token'}), 401
                
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/api/notify', methods=['POST'])
@require_bearer_token
def receive_booking_notification():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['booking_id', 'user', 'event', 'facilitator_id']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # Validate user object
        user = data.get('user', {})
        if not all(field in user for field in ['id', 'name', 'email']):
            return jsonify({
                'error': 'Invalid user object',
                'required_user_fields': ['id', 'name', 'email']
            }), 400
        
        # Validate event object
        event = data.get('event', {})
        if not all(field in event for field in ['id', 'title', 'date', 'type']):
            return jsonify({
                'error': 'Invalid event object',
                'required_event_fields': ['id', 'title', 'date', 'type']
            }), 400
        
        facilitator_id = data['facilitator_id']
        
        # Create notification record
        notification = {
            'id': len(notifications) + 1,
            'booking_id': data['booking_id'],
            'user': user,
            'event': event,
            'facilitator_id': facilitator_id,
            'received_at': datetime.utcnow().isoformat(),
            'status': 'received'
        }
        
        notifications.append(notification)
        
        # Add to facilitator's bookings
        if facilitator_id in facilitators:
            facilitators[facilitator_id]['bookings'].append({
                'booking_id': data['booking_id'],
                'user_name': user['name'],
                'user_email': user['email'],
                'event_title': event['title'],
                'event_date': event['date'],
                'event_type': event['type'],
                'received_at': notification['received_at']
            })
        
        # Log the notification
        print(f"[CRM] New booking notification received:")
        print(f"  Booking ID: {data['booking_id']}")
        print(f"  User: {user['name']} ({user['email']})")
        print(f"  Event: {event['title']}")
        print(f"  Facilitator ID: {facilitator_id}")
        print(f"  Received at: {notification['received_at']}")
        
        return jsonify({
            'message': 'Booking notification received successfully',
            'notification_id': notification['id'],
            'status': 'success'
        }), 200
        
    except Exception as e:
        print(f"[CRM] Error processing notification: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/notifications', methods=['GET'])
@require_bearer_token
def get_notifications():
    try:
        limit = request.args.get('limit', type=int, default=50)
        facilitator_id = request.args.get('facilitator_id', type=int)
        
        filtered_notifications = notifications
        
        if facilitator_id:
            filtered_notifications = [
                n for n in notifications 
                if n['facilitator_id'] == facilitator_id
            ]
        
        # Sort by received_at descending and apply limit
        sorted_notifications = sorted(
            filtered_notifications,
            key=lambda x: x['received_at'],
            reverse=True
        )[:limit]
        
        return jsonify({
            'notifications': sorted_notifications,
            'total': len(filtered_notifications)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch notifications',
            'message': str(e)
        }), 500

@app.route('/api/facilitators/<int:facilitator_id>/bookings', methods=['GET'])
@require_bearer_token
def get_facilitator_bookings(facilitator_id):
    try:
        if facilitator_id not in facilitators:
            return jsonify({'error': 'Facilitator not found'}), 404
        
        facilitator = facilitators[facilitator_id]
        
        return jsonify({
            'facilitator': {
                'id': facilitator['id'],
                'name': facilitator['name'],
                'email': facilitator['email']
            },
            'bookings': facilitator['bookings'],
            'total_bookings': len(facilitator['bookings'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch facilitator bookings',
            'message': str(e)
        }), 500

@app.route('/api/facilitators', methods=['GET'])
@require_bearer_token
def get_facilitators():
    try:
        facilitators_list = []
        for fid, facilitator in facilitators.items():
            facilitators_list.append({
                'id': facilitator['id'],
                'name': facilitator['name'],
                'email': facilitator['email'],
                'total_bookings': len(facilitator['bookings'])
            })
        
        return jsonify({
            'facilitators': facilitators_list,
            'total': len(facilitators_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch facilitators',
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'CRM Notification Service',
        'timestamp': datetime.utcnow().isoformat(),
        'total_notifications': len(notifications)
    }), 200

@app.route('/api/stats', methods=['GET'])
@require_bearer_token
def get_stats():
    try:
        total_notifications = len(notifications)
        facilitator_stats = {}
        
        for fid, facilitator in facilitators.items():
            facilitator_stats[fid] = {
                'name': facilitator['name'],
                'total_bookings': len(facilitator['bookings'])
            }
        
        recent_notifications = sorted(
            notifications,
            key=lambda x: x['received_at'],
            reverse=True
        )[:10]
        
        return jsonify({
            'total_notifications': total_notifications,
            'facilitator_stats': facilitator_stats,
            'recent_notifications': recent_notifications
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch stats',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print(f"[CRM] Starting CRM Notification Service...")
    print(f"[CRM] Bearer Token: {BEARER_TOKEN}")
    print(f"[CRM] Service will be available at http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
