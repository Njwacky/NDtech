# Docker Setup Guide for FuturePOS

This guide provides comprehensive instructions for setting up and running the FuturePOS application using Docker containers.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed
- At least 4GB of RAM available
- Git for cloning the repository

## Quick Start (Development)

### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd futurePOS
```

### 2. Build and Run
```bash
docker-compose up --build
```

The application will be available at:
- Main app: http://localhost:8000
- Nginx proxy: http://localhost:80
- Database: localhost:5432

### 3. Initialize Database
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Production Setup

### 1. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your production settings
```

### 2. SSL Certificates
Create an `ssl` directory and add your SSL certificates:
```bash
mkdir ssl
# Place cert.pem and key.pem in the ssl directory
```

### 3. Build and Run Production
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

### 4. Production Database Setup
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Docker Files Overview

### Core Files
- **`Dockerfile`** - Development container with Django dev server
- **`Dockerfile.prod`** - Production container with Gunicorn WSGI server
- **`docker-compose.yml`** - Development orchestration with PostgreSQL and Nginx
- **`docker-compose.prod.yml`** - Production orchestration with Redis, Celery, and SSL

### Configuration Files
- **`nginx.conf`** - Development Nginx configuration
- **`nginx.prod.conf`** - Production Nginx with SSL and security headers
- **`.dockerignore`** - Files excluded from Docker build context
- **`.env.example`** - Environment variables template

## Services

### Development Services
- **web**: Django application with development server
- **db**: PostgreSQL database
- **nginx**: Reverse proxy for static files and load balancing

### Production Services
- **web**: Django application with Gunicorn
- **db**: PostgreSQL database with persistent storage
- **redis**: Redis for caching and Celery broker
- **nginx**: SSL-enabled reverse proxy with security headers
- **celery**: Asynchronous task worker
- **celery-beat**: Scheduled task manager

## Common Commands

### Development
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose up --build web

# Access Django shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Production
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale web service
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres futurepos_db > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres futurepos_db < backup.sql
```

## Volume Management

### Development Volumes
- `postgres_data`: PostgreSQL data persistence
- `static_volume`: Collected static files

### Production Volumes
- `postgres_data`: PostgreSQL data persistence
- `static_volume`: Collected static files
- `media_volume`: User uploaded media files

## Health Checks

All services include health checks:
- **Database**: PostgreSQL connection check
- **Redis**: Redis ping check
- **Web**: HTTP health endpoint check
- **Nginx**: Service availability check

Monitor health status:
```bash
docker-compose ps
```

## Security Features

### Production Security
- SSL/TLS encryption with HTTP to HTTPS redirect
- Security headers (HSTS, XSS protection, Content Security Policy)
- Rate limiting for API and login endpoints
- Non-root user for application container
- Hidden file and backup file access restrictions

### PWA Optimizations
- Service worker caching headers
- Manifest.json optimization
- Offline page support
- Static file long-term caching

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using ports
   netstat -tulpn | grep :80
   netstat -tulpn | grep :5432
   ```

2. **Database Connection Issues**
   ```bash
   # Check database health
   docker-compose exec db pg_isready -U postgres
   ```

3. **Static Files Not Loading**
   ```bash
   # Recollect static files
   docker-compose exec web python manage.py collectstatic --noinput --clear
   ```

4. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Logs and Debugging
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# Real-time logs
docker-compose logs -f web

# Access container shell
docker-compose exec web bash
```

## Performance Optimization

### Production Tuning
- Gunicorn workers configured for optimal performance
- Nginx gzip compression enabled
- Static file caching optimized
- Database connection pooling
- Redis caching layer

### Monitoring
Monitor resource usage:
```bash
# Container resource usage
docker stats

# Disk usage
docker system df

# Clean up unused images
docker system prune -a
```

## Backup and Recovery

### Database Backup
```bash
# Create backup
docker-compose exec db pg_dump -U postgres futurepos_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec db pg_dump -U postgres futurepos_db > backups/backup_$DATE.sql
```

### Media Backup
```bash
# Backup media files
docker run --rm -v futurepos_media_volume:/data -v $(pwd)/backups:/backup alpine tar czf /backup/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

## Scaling

### Horizontal Scaling
```bash
# Scale web service
docker-compose -f docker-compose.prod.yml up -d --scale web=3
```

### Vertical Scaling
Adjust resource limits in `docker-compose.prod.yml`:
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Environment Variables

### Required Variables
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `ALLOWED_HOSTS`: Comma-separated hostnames

### Optional Variables
- `REDIS_URL`: Redis connection string
- `EMAIL_*`: Email configuration
- `LOG_LEVEL`: Logging verbosity

## Maintenance

### Regular Tasks
1. Update Docker images regularly
2. Monitor disk space usage
3. Review and rotate logs
4. Update dependencies
5. Security audit

### Updates
```bash
# Pull latest images
docker-compose pull

# Rebuild with latest changes
docker-compose up --build

# Clean up old images
docker image prune -f
```

## Support

For issues related to:
- Docker setup: Check this guide and Docker documentation
- Application functionality: Check application logs and Django documentation
- Performance: Monitor resource usage and consider scaling options

Remember to never commit sensitive information like `.env` files or SSL certificates to version control.
