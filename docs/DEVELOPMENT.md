# Bird Tracker Development Guide

## Site Architecture

### Development Environment (`bird-tracker-dev`)
- URL: https://bird-tracker-dev-a7bb94e09a81.herokuapp.com
- Purpose: Testing new features and changes before deploying to production
- Database: Separate PostgreSQL database for development
- Environment Variables: Development-specific configuration

### Production Environment (`bird-tracker-app`)
- URL: https://bird-tracker-app-9af5a4fb26d3.herokuapp.com
- Purpose: Live site serving real users
- Database: Production PostgreSQL database
- Environment Variables: Production-specific configuration

## Development Workflow

### Local Development
```bash
# Start local development server
flask run
```
- Runs on http://127.0.0.1:5000
- Uses local SQLite database
- Loads configuration from `config.py`

### Testing in Development Environment
```bash
# Push changes to development
git push heroku-dev main
```
- Changes are deployed to `bird-tracker-dev`
- Test new features and bug fixes
- Verify database migrations
- Check environment variables

### Deploying to Production
```bash
# Push changes to production
git push heroku main
```
- Changes are deployed to `bird-tracker-app`
- Production database is updated
- Environment variables are applied

## Database Management

### Development Database
- Initialized with test data
- Can be reset without affecting production
- Used for testing migrations and data changes

### Production Database
- Contains real user data
- Requires careful migration management
- Backed up regularly

## Environment Variables

Both environments have their own set of environment variables:
- `FLASK_SECRET_KEY`: For session management
- `DATABASE_URL`: Database connection string
- `ALLOWED_EMAILS`: List of authorized users
- Other API keys and configurations

## Testing Process

### Local Testing
1. Make code changes locally
2. Run tests
3. Test with local database

### Development Environment Testing
1. Deploy to `bird-tracker-dev`
2. Test with development database
3. Verify all features work
4. Check for any issues

### Production Deployment
1. After successful testing in development
2. Deploy to `bird-tracker-app`
3. Monitor for any issues
4. Roll back if necessary

## Best Practices

### Code Changes
- Always test locally first
- Deploy to development for thorough testing
- Only deploy to production when confident

### Database Changes
- Use migrations for schema changes
- Test migrations in development first
- Back up production database before migrations

### Environment Variables
- Keep development and production variables separate
- Never commit sensitive data
- Use different API keys for each environment

### Version Control
- Use meaningful commit messages
- Create feature branches for major changes
- Review changes before deploying to production

## Common Tasks

### Initializing Development Environment
```bash
# Clone repository
git clone <repository-url>
cd bird_tracker

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db upgrade
python init_db.py
```

### Adding New Features
1. Create a new branch
   ```bash
   git checkout -b feature/new-feature
   ```
2. Make changes and test locally
3. Deploy to development environment
4. Test thoroughly
5. Merge to main branch
6. Deploy to production

### Database Migrations
1. Create migration
   ```bash
   flask db migrate -m "Description of changes"
   ```
2. Review migration file
3. Apply migration in development
   ```bash
   flask db upgrade
   ```
4. Test changes
5. Apply to production when ready

### Environment Setup
1. Development environment variables
   ```bash
   heroku config:set --app bird-tracker-dev KEY=value
   ```
2. Production environment variables
   ```bash
   heroku config:set --app bird-tracker-app KEY=value
   ```

## Troubleshooting

### Common Issues
1. Database connection errors
   - Check DATABASE_URL environment variable
   - Verify database is running
   - Check network connectivity

2. Authentication issues
   - Verify FLASK_SECRET_KEY is set
   - Check ALLOWED_EMAILS configuration
   - Clear browser cookies if needed

3. Deployment failures
   - Check Heroku logs
   - Verify all dependencies are in requirements.txt
   - Ensure environment variables are set

### Logging
- Development logs: `heroku logs --tail --app bird-tracker-dev`
- Production logs: `heroku logs --tail --app bird-tracker-app`
- Local logs: Check terminal output when running `flask run`

## API Credentials Management

### Google Maps API
- Production URL: https://bird-tracker-app-9af5a4fb26d3.herokuapp.com/*
- Development URL: https://bird-tracker-dev-a7bb94e09a81.herokuapp.com/*
- Both URLs must be authorized in Google Cloud Console
- API key restrictions should include both domains
- Separate API keys can be used for development and production

### Other API Credentials
- Keep development and production API keys separate
- Document all required API keys in environment variables
- Never commit API keys to version control
- Use different API keys for each environment

## Reverting Development Changes

If you need to revert changes tested in the development environment and return to the production state, you have two main options:

### Option 1: Reset the Development Database

To reset the development database to match the production state:

```bash
# Reset the development database
heroku run python init_db.py --app bird-tracker-dev
```

This will:
- Drop all existing tables
- Recreate the database schema
- Add initial data (users, locations, etc.)
- Reset any test data

### Option 2: Revert Git Changes

If you made code changes that you want to undo:

```bash
# View recent changes
git log

# Revert to a specific commit
git revert <commit-hash>

# Or reset to the last production state
git reset --hard origin/main
```

After reverting changes:
1. Push the changes to the development environment:
   ```bash
   git push heroku-dev main
   ```
2. Reset the database if needed:
   ```bash
   heroku run python init_db.py --app bird-tracker-dev
   ```

### Best Practices

1. Always commit your changes before testing in development
2. Use feature branches for significant changes
3. Keep a backup of important data before resetting
4. Document any environment-specific configurations
5. Test the reversion process in development before applying to production 