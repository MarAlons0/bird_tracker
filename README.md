# Bird Tracker Application

A Flask-based web application that helps users track and discover bird sightings in their area using eBird data and AI-powered analysis. The application provides real-time bird observation data, interactive mapping, and intelligent analysis powered by Claude AI.

**Live Demo**: [https://bird-tracker.onrender.com](https://bird-tracker.onrender.com)

## Features

### Core Functionality
- **Interactive Home Page**: Combined map and sightings table on a single page for seamless bird tracking
- **Real-time Bird Data**: Live bird sightings from eBird API within your selected radius
- **AI-Powered Analysis**: Get insights about bird populations and trends using Claude AI
- **Intelligent Chat Interface**: Ask questions about local bird activity and get AI-powered responses
- **Location Management**: Set and update your preferred location and search radius
- **User Authentication**: Secure login system with password management

### Bird Classification System
Birds are automatically categorized into four main groups:
- **Raptors**: Eagles, hawks, owls, falcons, vultures
- **Waterfowl**: Ducks, geese, swans, herons, egrets
- **Shorebirds**: Sandpipers, plovers, gulls, terns
- **Songbirds**: Cardinals, finches, sparrows, warblers, and other small birds

### Admin Panel
- **User Management**: View, activate/deactivate, and delete user accounts
- **Allowed Emails Management**: Database-driven whitelist of authorized email addresses
- **Dashboard**: Overview of system statistics and user activity
- **Password Management**: Reset user passwords to default values
- **Registration Requests**: Review and approve/reject new user registration requests

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Alembic
- **Frontend**: Bootstrap 5, JavaScript, Leaflet Maps
- **Database**: SQLite (development) / PostgreSQL (production)
- **External APIs**: eBird API, Google Places API
- **AI**: Claude AI (Anthropic) for analysis and chat
- **Authentication**: Flask-Login with CSRF protection

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/MarAlons0/bird_tracker.git
cd bird_tracker
```

2. **Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
Create a `.env` file in the root directory with the following variables:
```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/bird_tracker.db
EBIRD_API_KEY=your-ebird-api-key
GOOGLE_PLACES_API_KEY=your-google-places-api-key
ANTHROPIC_API_KEY=your-claude-api-key
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-admin-password
```

5. **Initialize the database:**
```bash
flask db upgrade
```

6. **Run the development server:**
```bash
python app.py
```

The application will be available at `http://localhost:5001`

### Creating an Admin User

The application automatically creates an admin user on startup if `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables are set. This admin user will be created with full admin rights.

**Note:**
After being granted admin rights, you must log out and log back in for the admin panel to appear.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_APP` | Application entry point | Yes |
| `FLASK_ENV` | Development/Production environment | Yes |
| `SECRET_KEY` | Flask secret key for session management | Yes |
| `DATABASE_URL` | Database connection URL (SQLite for local, PostgreSQL for production) | Yes |
| `EBIRD_API_KEY` | eBird API key for bird sighting data | Yes |
| `GOOGLE_PLACES_API_KEY` | Google Places API key for location search | Yes |
| `ANTHROPIC_API_KEY` | Claude AI API key for analysis and chat | Yes |
| `ADMIN_EMAIL` | Email for the auto-created admin user | Yes |
| `ADMIN_PASSWORD` | Password for the auto-created admin user | Yes |
| `DEFAULT_USER_PASSWORD` | Default password for new users created via registration | No |

## Project Structure

```
bird_tracker/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
│   │       └── Banner.jpeg
│   ├── templates/
│   │   ├── admin/
│   │   │   ├── dashboard.html
│   │   │   ├── users.html
│   │   │   └── allowed_emails.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── change_password.html
│   │   │   └── request_registration.html
│   │   ├── base.html
│   │   ├── home.html
│   │   └── analysis.html
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── bird_service.py
│   │   └── map_service.py
│   ├── models.py
│   └── forms.py
├── routes/
│   ├── admin.py
│   ├── auth.py
│   └── main.py
├── config/
│   └── extensions.py
├── instance/
├── app.py
├── requirements.txt
├── render.yaml
├── .env
└── README.md
```

## Key Features Explained

### Home Page Integration
The main page combines the interactive map and sightings table, eliminating the need for separate navigation. Users can:
- View bird sightings on an interactive Leaflet map
- See a detailed table of recent observations
- Filter and search through bird data
- Update their location preferences

### AI Analysis
The analysis page provides:
- Real-time chat with Claude AI about local bird activity
- Intelligent responses based on current eBird data
- Contextual information about bird species and behaviors
- Personalized insights based on user location

### Bird Classification
The application automatically categorizes birds using a comprehensive classification system:
- **Color-coded markers** on the map for easy identification
- **Background-colored cells** in the sightings table
- **Legend** showing all four categories with their respective colors

### Admin Panel
Administrators can:
- View system statistics and user counts
- Manage user accounts (activate/deactivate/delete)
- Manage allowed emails (add/remove email addresses that can register)
- Review and process registration requests
- Reset user passwords

## API Endpoints

### Public Endpoints
- `GET /` - Home page (requires authentication)
- `GET /login` - Login page
- `POST /login` - User authentication

### Protected Endpoints
- `GET /profile` - User profile page
- `GET /analysis` - AI analysis and chat page
- `GET /change-password` - Password change form
- `POST /change-password` - Update user password

### API Endpoints
- `GET /api/sightings` - Get bird sightings for location
- `POST /api/analyze` - AI analysis of bird data
- `POST /api/chat` - Chat with Claude AI
- `POST /api/update-location` - Update user location preferences
- `GET /api/user-preferences` - Get user preferences

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management page
- `POST /admin/users` - User management actions
- `GET /admin/allowed-emails` - Allowed emails management
- `POST /admin/allowed-emails` - Add/remove allowed emails
- `GET /admin/registration-requests` - Registration requests list
- `POST /admin/registration-request/<id>/<action>` - Approve/reject requests

## Database Models

### Core Models
- **User**: User accounts with authentication
- **Location**: User-defined locations for bird tracking
- **UserPreferences**: User settings and preferences
- **AllowedEmail**: Whitelist of email addresses permitted to register
- **Image**: User-uploaded bird images

## Deployment

### Render (Recommended)

The application is configured for deployment on Render with PostgreSQL. A `render.yaml` blueprint is included for easy deployment.

1. Push your code to GitHub
2. Connect your GitHub repository to Render
3. Create a new PostgreSQL database on Render
4. Add environment variables in Render dashboard
5. Deploy the web service

The application automatically creates database tables and an admin user on startup.

### Local Development

For local development, use SQLite:
```bash
DATABASE_URL=sqlite:///instance/bird_tracker.db
```

## Troubleshooting

### Admin Panel Not Visible
- Ensure you have logged out and logged back in after being granted admin rights
- Verify the `ADMIN_EMAIL` matches your login email

### Database Issues
- For local development, ensure the `instance/` directory exists
- For Render, verify `DATABASE_URL` is correctly set from the PostgreSQL database

### API Key Restrictions
- Google Maps API: Add your deployment URL and localhost to allowed referrers in Google Cloud Console
- eBird API: No referrer restrictions needed 