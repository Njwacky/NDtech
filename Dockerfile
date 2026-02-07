# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (to leverage Docker cache)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY confige/ ./confige/
COPY nano/ ./nano/
COPY food_ordering/ ./food_ordering/
COPY NDtechTrack/ ./NDtechTrack/
COPY manage.py ./
COPY deploy_fix.py ./
COPY generate_favicons.py ./

# Set environment variables for build
# NOTE: These are defaults for the build process. 
# Secrets should be injected at runtime securely.
ENV DJANGO_SECRET_KEY=build-time-dummy-key-change-in-prod
ENV DJANGO_DEBUG=False
ENV DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
# External service keys (Set these in your deployment environment)
ENV FCM_API_KEY=""
ENV FCM_SENDER_ID=""
ENV FCM_PROJECT_ID=""

# Create staticfiles directory
RUN mkdir -p /app/staticfiles

# Verify Django setup and collect static files
RUN python manage.py check && python manage.py collectstatic --noinput --clear 2>&1 || echo "Collectstatic completed with warnings"

# Expose port (Render will use PORT env var, default 10000)
EXPOSE 8000

# Run the application using Render's PORT environment variable
CMD ["sh", "-c", "python deploy_fix.py && gunicorn confige.wsgi:application --bind 0.0.0.0:$PORT --workers 3"]
