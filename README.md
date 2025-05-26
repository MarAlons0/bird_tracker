# Bird Tracker Application

A Flask-based web application that helps users track and discover bird sightings in their area using eBird data and AI-powered analysis.

## Features

- **Interactive Map**: View bird sightings on an interactive map centered on your selected location
- **AI Analysis**: Get insights about bird populations and trends in your area using Claude AI
- **Newsletter**: Receive email updates about new bird sightings in your area
- **Location Management**: Easily set and update your preferred location and search radius
- **Bird Categories**: View birds categorized as Raptors, Waterfowl, Shorebirds, and Songbirds
- **Image Carousel**: Browse through beautiful bird images on the home page

## Tech Stack

- **Backend**: Flask, SQLAlchemy, APScheduler
- **Frontend**: Bootstrap 5, JavaScript, Google Maps API
- **Database**: PostgreSQL
- **External APIs**: eBird API, Google Places API
- **AI**: Claude AI for analysis
- **Image Storage**: Cloudinary

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/MarAlons0/bird_tracker.git
cd bird_tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
python init_db.py
```

6. Run the development server:
```bash
flask run
```

## Environment Variables

Required environment variables:
- `FLASK_APP`: Application entry point
- `FLASK_ENV`: Development/Production environment
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: PostgreSQL database URL
- `EBIRD_API_KEY`: eBird API key
- `GOOGLE_PLACES_API_KEY`: Google Places API key
- `CLOUDINARY_URL`: Cloudinary configuration URL
- `ANTHROPIC_API_KEY`: Claude AI API key

## Project Structure

```
bird_tracker/
├── app/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   ├── models.py
│   ├── routes.py
│   └── extensions.py
├── migrations/
├── config/
├── requirements.txt
├── Procfile
└── wsgi.py
```

## Deployment

The application is configured for deployment on Heroku. The `Procfile` includes:
- Web process: `gunicorn "app:create_app()"`
- Scheduler process: `python scheduler.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please open an issue in the GitHub repository. 