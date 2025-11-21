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
COPY manage.py ./
COPY generate_favicons.py ./

# Set environment variables for build
ENV DJANGO_SECRET_KEY=cy3fbhBI38T_ult5rpcVi1vAqEjNZEJ-PcBmTBrwDhyVMVf2lN6ljx4h9On2MKThwxg
ENV DJANGO_DEBUG=False
ENV DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.84.134.47
ENV DATABASE_URL=postgresql://postgres:Python2001@localhost:8001/postgres
ENV FCM_API_KEY=your-fcm-api-key-here
ENV FCM_SENDER_ID=your-sender-id
ENV FCM_PROJECT_ID=your-project-id
ENV BREVO_API_KEY=your-brevo-api-key-here
ENV BREVO_SENDER_EMAIL=njwayelodlamini@gmail.com
ENV BREVO_SENDER_NAME=futurePOS

# Create staticfiles directory
RUN mkdir -p /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
