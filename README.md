# Bird Tracker Application

A Flask-based web application that helps users track and discover bird sightings in their area using eBird data and AI-powered analysis. The application provides real-time bird observation data, interactive mapping, and intelligent analysis powered by Claude AI.

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
- **Dashboard**: Overview of system statistics and user activity
- **Password Management**: Reset user passwords to default values

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
EBIRD_API_KEY=your-ebird-api-key
GOOGLE_PLACES_API_KEY=your-google-places-api-key
ANTHROPIC_API_KEY=your-claude-api-key
DEFAULT_USER_PASSWORD=admin123
ALLOWED_EMAILS=user@example.com,admin@example.com
```

5. **Initialize the database:**
```bash
flask db upgrade
```

6. **Run the development server:**
```bash
flask run --port 8000
```

The application will be available at `http://localhost:8000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_APP` | Application entry point | Yes |
| `FLASK_ENV` | Development/Production environment | Yes |
| `SECRET_KEY` | Flask secret key for session management | Yes |
| `EBIRD_API_KEY` | eBird API key for bird sighting data | Yes |
| `GOOGLE_PLACES_API_KEY` | Google Places API key for location search | Yes |
| `ANTHROPIC_API_KEY` | Claude AI API key for analysis and chat | Yes |
| `DEFAULT_USER_PASSWORD` | Default password for new users | Yes |
| `ALLOWED_EMAILS` | Comma-separated list of allowed email addresses | Yes |

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
│   │   │   ├── base.html
│   │   │   ├── dashboard.html
│   │   │   └── users.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── change_password.html
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── analysis.html
│   │   └── profile.html
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   └── main.py
│   ├── models.py
│   ├── forms.py
│   ├── extensions.py
│   └── bird_tracker.py
├── migrations/
├── instance/
├── requirements.txt
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
- Reset user passwords
- Monitor application activity

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

## Database Models

### Core Models
- **User**: User accounts with authentication
- **Location**: User-defined locations for bird tracking
- **UserPreferences**: User settings and preferences
- **BirdSightingCache**: Cached eBird observations

## Development

### Running Tests
```bash
python -m pytest
```

### Database Migrations
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Code Style
The project follows PEP 8 guidelines. Use a linter like `flake8` to check code style.

## Deployment

### Local Development
```bash
flask run --port 8000
```

### Production Deployment
1. Set `FLASK_ENV=production`
2. Configure production database (PostgreSQL recommended)
3. Set up proper environment variables
4. Use a production WSGI server like Gunicorn

## Troubleshooting

### Common Issues
1. **CSRF Token Errors**: Ensure all forms include `{{ csrf_token() }}`
2. **API Key Issues**: Verify all required API keys are set in `.env`
3. **Database Errors**: Run `flask db upgrade` to ensure migrations are applied
4. **Map Not Loading**: Check Google Places API key and referrer settings

### Logs
Application logs are available in the console output. Check for:
- Authentication issues
- API request failures
- Database connection problems

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or support:
- Open an issue in the GitHub repository
- Check the troubleshooting section above
- Review the application logs for error details

## Changelog

### Recent Updates
- Removed carousel and newsletter features for simplified interface
- Consolidated map functionality into home page
- Implemented new bird classification system with color coding
- Updated admin panel with streamlined user management
- Fixed CSRF token issues and authentication flows
- Improved error handling and user experience 