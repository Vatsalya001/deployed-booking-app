# Booking System for Sessions & Retreats

A comprehensive booking system built with React (Vite) frontend, Flask backend, and a separate CRM notification service. The system allows users to browse events, make bookings, and notifies facilitators through a secure CRM integration.

## Features

### User Features
- **Authentication**: JWT-based authentication with secure login/register
- **Event Browsing**: View available sessions and retreats with detailed information
- **Booking Management**: Book events, view booking history, cancel bookings
- **Dashboard**: Personal dashboard with booking statistics and recent activity
- **Responsive Design**: Mobile-friendly interface built with Tailwind CSS

### System Features
- **Secure API**: RESTful API with JWT authentication
- **CRM Integration**: Separate Flask service for facilitator notifications
- **Real-time Updates**: Automatic participant count updates
- **Data Validation**: Comprehensive input validation and error handling
- **Dockerized**: Complete containerization for easy deployment

## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API communication
- **React Hot Toast** for notifications
- **Lucide React** for icons

### Backend
- **Flask** with Python 3.11
- **SQLAlchemy** for database ORM
- **Flask-JWT-Extended** for authentication
- **Flask-CORS** for cross-origin requests
- **SQLite** for development (PostgreSQL ready)

### CRM Service
- **Flask** microservice
- **Bearer token authentication**
- **In-memory storage** (database ready)
- **RESTful API** for notifications

## Project Structure

\`\`\`
booking-system/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── contexts/        # React contexts (Auth)
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   └── main.tsx        # Application entry point
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── backend/                 # Flask backend API
│   ├── app.py              # Main application file
│   ├── requirements.txt
│   └── Dockerfile
├── crm/                    # CRM notification service
│   ├── app.py              # CRM service application
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml      # Docker orchestration
├── .env.example           # Environment variables template
└── README.md
\`\`\`

## Database Schema

### Users Table
- id (Primary Key)
- name
- email (Unique)
- password_hash
- created_at

### Facilitators Table
- id (Primary Key)
- name
- email (Unique)
- specialization
- bio
- created_at

### Events Table
- id (Primary Key)
- title
- description
- date
- duration (minutes)
- location
- price
- max_participants
- current_participants
- facilitator_id (Foreign Key)
- type (session/retreat)
- status
- created_at

### Bookings Table
- id (Primary Key)
- user_id (Foreign Key)
- event_id (Foreign Key)
- booking_date
- status
- Unique constraint on (user_id, event_id)

## API Documentation

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
\`\`\`json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
\`\`\`

**Response:**
\`\`\`json
{
  "token": "jwt_token_here",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
\`\`\`

#### POST /api/auth/login
Authenticate user and get access token.

**Request Body:**
\`\`\`json
{
  "email": "john@example.com",
  "password": "securepassword"
}
\`\`\`

#### GET /api/auth/me
Get current user information (requires authentication).

### Event Endpoints

#### GET /api/events
Get all available events (requires authentication).

**Response:**
\`\`\`json
{
  "events": [
    {
      "id": 1,
      "title": "Morning Meditation Session",
      "description": "Start your day with peaceful meditation...",
      "date": "2024-01-15T09:00:00",
      "duration": 60,
      "location": "Zen Studio, Downtown",
      "price": 25.00,
      "max_participants": 15,
      "current_participants": 5,
      "facilitator_name": "Dr. Sarah Johnson",
      "facilitator_id": 1,
      "type": "session"
    }
  ]
}
\`\`\`

### Booking Endpoints

#### POST /api/bookings
Create a new booking (requires authentication).

**Request Body:**
\`\`\`json
{
  "event_id": 1
}
\`\`\`

#### GET /api/bookings
Get user's bookings (requires authentication).

#### DELETE /api/bookings/{booking_id}
Cancel a booking (requires authentication).

### Dashboard Endpoints

#### GET /api/dashboard/stats
Get user dashboard statistics (requires authentication).

### CRM Service Endpoints

#### POST /api/notify
Receive booking notifications (requires Bearer token).

**Headers:**
\`\`\`
Authorization: Bearer your-static-bearer-token
\`\`\`

**Request Body:**
\`\`\`json
{
  "booking_id": 1,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "event": {
    "id": 1,
    "title": "Morning Meditation Session",
    "date": "2024-01-15T09:00:00",
    "type": "session"
  },
  "facilitator_id": 1
}
\`\`\`

#### GET /api/notifications
Get all notifications (requires Bearer token).

#### GET /api/facilitators/{facilitator_id}/bookings
Get bookings for a specific facilitator (requires Bearer token).

## Local Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose (optional)

### Method 1: Manual Setup

#### 1. Clone the Repository
\`\`\`bash
git clone <repository-url>
cd booking-system
\`\`\`

#### 2. Setup Backend
\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
\`\`\`

The backend will start on http://localhost:5000

#### 3. Setup CRM Service
\`\`\`bash
cd crm
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
\`\`\`

The CRM service will start on http://localhost:5001

#### 4. Setup Frontend
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

The frontend will start on http://localhost:3000

### Method 2: Docker Setup

#### 1. Clone and Start Services
\`\`\`bash
git clone <repository-url>
cd booking-system
cp .env.example .env
docker-compose up --build
\`\`\`

This will start all services:
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- CRM: http://localhost:5001

## Production Deployment

### Environment Variables
Create a \`.env\` file with the following variables:

\`\`\`env
# Backend Configuration
DATABASE_URL=postgresql://user:password@localhost/booking_db
JWT_SECRET_KEY=your-super-secret-jwt-key

# CRM Configuration
CRM_BASE_URL=https://your-crm-domain.com
CRM_BEARER_TOKEN=your-secure-bearer-token

# Frontend Configuration
VITE_API_URL=https://your-api-domain.com
\`\`\`

### Database Migration
For production, replace SQLite with PostgreSQL:

1. Update \`DATABASE_URL\` in environment variables
2. Install \`psycopg2-binary\` (already in requirements.txt)
3. Run the application to auto-create tables

### Docker Production Deployment

#### 1. Build Production Images
\`\`\`bash
# Build backend
docker build -t booking-backend ./backend

# Build frontend
docker build -t booking-frontend ./frontend

# Build CRM
docker build -t booking-crm ./crm
\`\`\`

#### 2. Deploy with Docker Compose
\`\`\`bash
docker-compose -f docker-compose.prod.yml up -d
\`\`\`

### Cloud Deployment Options

#### Vercel (Frontend)
\`\`\`bash
cd frontend
npm install -g vercel
vercel --prod
\`\`\`

#### Railway/Heroku (Backend & CRM)
1. Create separate apps for backend and CRM
2. Set environment variables
3. Deploy using Git or Docker

#### AWS/GCP/Azure
Use container services like:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances

## Security Features

### Authentication
- JWT tokens with configurable expiration
- Password hashing using Werkzeug
- Protected routes with middleware

### API Security
- CORS configuration
- Input validation and sanitization
- Bearer token authentication for CRM
- SQL injection prevention with SQLAlchemy ORM

### Data Protection
- Sensitive data encryption
- Environment variable configuration
- Secure session management

## Testing

### Backend Testing
\`\`\`bash
cd backend
python -m pytest tests/
\`\`\`

### Frontend Testing
\`\`\`bash
cd frontend
npm run test
\`\`\`

### API Testing
Use the provided Postman collection or test with curl:

\`\`\`bash
# Register user
curl -X POST http://localhost:5000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@example.com","password":"password123"}'

# Get events (replace TOKEN with actual JWT)
curl -X GET http://localhost:5000/api/events \\
  -H "Authorization: Bearer TOKEN"
\`\`\`

## Troubleshooting

### Common Issues

#### Port Already in Use
\`\`\`bash
# Kill processes on specific ports
lsof -ti:3000 | xargs kill -9
lsof -ti:5000 | xargs kill -9
lsof -ti:5001 | xargs kill -9
\`\`\`

#### Database Issues
\`\`\`bash
# Reset database
rm backend/booking.db
python backend/app.py  # Will recreate with sample data
\`\`\`

#### CORS Issues
Ensure the backend CORS configuration includes your frontend URL.

#### JWT Token Issues
Check token expiration and ensure proper header format: \`Bearer <token>\`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Create an issue in the repository
4. Contact the development team

---

**Happy Booking! 🎉**
\`\`\`

This completes the comprehensive booking system with all the requested features including authentication, event management, booking functionality, CRM integration, and deployment instructions.
