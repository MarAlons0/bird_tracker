# Render Migration Setup Guide

## Environment Variables Needed

Based on your app configuration, you'll need these environment variables on Render:

### Required Variables:
- `SECRET_KEY` - Flask secret key (generate a new one)
- `DATABASE_URL` - Will be provided by Render PostgreSQL
- `FLASK_ENV` - Set to `production`

### Email Configuration:
- `SMTP_SERVER` - Your email server (e.g., smtp.gmail.com)
- `SMTP_PORT` - Email port (usually 587)
- `SMTP_USER` - Your email username
- `SMTP_PASSWORD` - Your email password/app password

### API Keys:
- `EBIRD_API_KEY` - Your eBird API key
- `ANTHROPIC_API_KEY` - Your Anthropic/Claude API key
- `GOOGLE_PLACES_API_KEY` - Your Google Places API key

### Cloudinary (Image Storage):
- `CLOUDINARY_CLOUD_NAME` - Your Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Your Cloudinary API key
- `CLOUDINARY_API_SECRET` - Your Cloudinary API secret

### Admin Configuration:
- `ADMIN_EMAIL` - Admin user email
- `ADMIN_PASSWORD` - Admin user password
- `DEFAULT_USER_PASSWORD` - Default password for new users
- `ALLOWED_EMAILS` - Comma-separated list of allowed email domains

## Migration Steps:

1. **Export Heroku Data**: Export your PostgreSQL data from Heroku
2. **Create Render Account**: Sign up at render.com
3. **Create PostgreSQL Database**: Set up a free PostgreSQL database on Render
4. **Deploy Web Service**: Connect your GitHub repo and deploy
5. **Import Data**: Import your data to the new database
6. **Test**: Verify everything works correctly

## Notes:
- Render free tier apps sleep after 15 minutes of inactivity
- Cold start takes about 30 seconds
- Free PostgreSQL database has 1GB storage limit
- Perfect for personal projects like yours!

