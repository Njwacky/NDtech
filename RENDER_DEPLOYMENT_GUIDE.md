# Render.com Deployment Guide for futurePOS

This guide will help you deploy your Django application to Render.com and fix the database connection issues.

## Prerequisites

1. A Render.com account
2. Your code pushed to a GitHub repository
3. All the configuration files are already set up in this project

## Step-by-Step Deployment

### 1. Push Your Code to GitHub

Make sure your latest changes are pushed to GitHub:

```bash
git add .
git commit -m "Add Render.com deployment configuration"
git push origin main
```

### 2. Create a New Web Service on Render

1. Go to [Render.com](https://render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- Name: `futurepos-django` (or your preferred name)
- Region: Choose the nearest region
- Branch: `main`

**Build Settings:**
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn confige.wsgi:application --bind 0.0.0.0:$PORT`

**Environment Variables:**
- `DJANGO_SETTINGS_MODULE`: `confige.settings`
- `DJANGO_DEBUG`: `False`
- `DJANGO_SECRET_KEY`: (Generate a new one or use existing)
- `ALLOWED_HOSTS`: `.onrender.com,localhost,127.0.0.1`

### 3. Create a PostgreSQL Database

1. Click "New +" and select "PostgreSQL"
2. Name: `futurepos-db`
3. Plan: Free (to start)
4. Region: Same as your web service

### 4. Connect Database to Web Service

1. Go to your web service settings
2. Scroll down to "Environment Variables"
3. Add a new environment variable:
   - Key: `DATABASE_URL`
   - Value: Click "Connect to Database" and select your PostgreSQL database

### 5. Run Database Migrations

After deployment, you'll need to run migrations. You can do this by:

1. Going to your web service on Render
2. Click on "Shell" tab
3. Run these commands:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: Create admin user
python manage.py collectstatic --noinput
```

### 6. Update CSRF Settings (Already Done)

The CSRF configuration has been updated to handle Render.com URLs. However, you'll need to:

1. After deployment, get your Render.com URL (e.g., `https://your-app-name.onrender.com`)
2. Add this URL to your `CSRF_TRUSTED_ORIGINS` in production

You can do this by adding an environment variable:
- `RENDER_URL`: `https://your-app-name.onrender.com`

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. **Check DATABASE_URL**: Make sure the DATABASE_URL environment variable is correctly set
2. **Verify Database Status**: Ensure your PostgreSQL database is running
3. **Check Network**: Make sure both services are in the same region

### CSRF Issues

If you still get CSRF errors:

1. **Add Your URL**: Make sure your actual Render.com URL is added to CSRF_TRUSTED_ORIGINS
2. **Check HTTPS**: Ensure you're accessing via HTTPS (Render provides this automatically)
3. **Clear Browser Cache**: Sometimes old CSRF tokens can cause issues

### Static Files Issues

If static files aren't loading:

1. **Run collectstatic**: Make sure `python manage.py collectstatic --noinput` was run
2. **Check STATIC_URL**: Verify it's set to `/static/`
3. **Verify STATIC_ROOT**: Ensure it points to the correct directory

## Environment Variables Summary

Here are all the environment variables you need:

```bash
# Core Django Settings
DJANGO_SETTINGS_MODULE=confige.settings
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1

# Database
DATABASE_URL=your-render-database-url

# Optional: CSRF Trusted Origins
RENDER_URL=https://your-app-name.onrender.com

# Optional: API Keys (if using FCM or Brevo)
FCM_API_KEY=your-fcm-api-key
FCM_SENDER_ID=your-sender-id
FCM_PROJECT_ID=your-project-id
BREVO_API_KEY=your-brevo-api-key
BREVO_SENDER_EMAIL=your-email@example.com
BREVO_SENDER_NAME=your-app-name
```

## Post-Deployment Checklist

- [ ] Application loads without errors
- [ ] Database tables are created
- [ ] Static files are loading correctly
- [ ] Login/Registration forms work
- [ ] CSRF protection is working
- [ ] All pages are accessible via HTTPS

## Monitoring

- Check the Render dashboard for logs
- Monitor resource usage
- Set up alerts for downtime

## Support

If you encounter issues:

1. Check Render's [documentation](https://render.com/docs)
2. Review the deployment logs
3. Check the environment variables
4. Verify your database connection

The configuration files (render.yaml, settings.py) are already optimized for Render.com deployment, so most issues should be resolved by following this guide.
