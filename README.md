# PDNP - Fullstack Template v2.0

> **P**ython | **D**jango | **N**ext.js | **P**ostgreSQL

A modern, secure, and production-ready fullstack application template with Django REST Framework backend and Next.js frontend, fully containerized with Docker.

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1.4-green?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5.7-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.0.1-blue?logo=react&logoColor=white)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Features

### Backend (Django)
- **Python 3.13** with **Django 5.1.4** and Django REST Framework
- **PostgreSQL 15** database
- **Redis 7** for caching and Celery broker
- **Celery 5.4** for async tasks and scheduled jobs
- **JWT Authentication** with Simple JWT 5.5.1
- **ClamAV Integration** for file scanning and virus detection
- **CORS** configured for frontend integration
- **API Documentation** with Swagger/ReDoc (drf-spectacular)
- **Code Quality** tools (Black, Flake8, isort, mypy)
- **Testing** with pytest and coverage

### Frontend (Next.js)
- **Next.js 15.5.7** with App Router
- **React 19.0.1** with latest features
- **TypeScript 5.7** for type safety
- **Tailwind CSS 3.4** for styling
- **Shadcn/ui** components
- **API Integration** configured
- **Authentication** flow with JWT
- **ESLint** and **Prettier** configured

### DevOps
- **Docker** and **Docker Compose** for containerization
- **Multi-stage builds** for optimized images
- **Nginx** as reverse proxy
- **Flower** for Celery monitoring
- **PgAdmin** for database management (dev)
- **Hot reload** in development
- **Production-ready** configurations

## 📋 Requirements

- Docker 24+ and Docker Compose v2
- Make (optional, for using Makefile commands)
- Git

## 🛠️ Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <project-directory>
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the setup**
   ```bash
   make install
   # or without make:
   docker-compose up -d
   ```

4. **Access the services**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin
   - API Documentation: http://localhost:8000/api/docs
   - ClamAV API: http://localhost:8000/api/clamav/
   - Flower (Celery): http://localhost:5555
   - PgAdmin: http://localhost:5050

## 📁 Project Structure

```
.
├── backend/                # Django backend
│   ├── apps/              # Django apps
│   ├── config/            # Django settings
│   ├── requirements/      # Python dependencies
│   ├── static/            # Static files
│   ├── media/             # User uploads
│   └── tests/             # Tests
├── frontend/              # Next.js frontend
│   ├── app/              # App router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and API
│   ├── public/           # Static assets
│   └── styles/           # CSS files
├── docker/               # Docker configurations
│   ├── nginx/           # Nginx configs
│   ├── postgres/        # PostgreSQL init scripts
│   └── redis/           # Redis configs
├── docker-compose.yml    # Main compose file
├── docker-compose.override.yml  # Dev overrides
├── docker-compose.prod.yml      # Prod overrides
├── Makefile             # Make commands
├── CHANGELOG.md         # Version history
└── .env.example         # Environment template
```

## 🔧 Common Commands

### Development

```bash
# Start development environment
make dev

# View logs
make logs

# Access backend shell
make shell

# Access database
make shell-db

# Run migrations
make migrate

# Create superuser
make create-superuser

# Run tests
make test

# Format code
make format
```

### Production

```bash
# Start production environment
make prod

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-prod
```

### Database

```bash
# Create migrations
make makemigrations

# Apply migrations
make migrate

# Backup database
make backup-db

# Restore database
make restore-db

# Reset database (CAUTION!)
make reset-db
```

### Monitoring

```bash
# Check service status
make status

# Health check
make health

# View system stats
make stats

# Monitor services
make monitor
```

## 🔐 Environment Variables

Key environment variables (see `.env.example` for full list):

- `PROJECT_NAME`: Your project name
- `PROJECT_PREFIX`: Short prefix for container names
- `DJANGO_ENVIRONMENT`: development/production
- `DEBUG`: Django debug mode
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_HOSTS`: Django allowed hosts
- `CORS_ALLOWED_ORIGINS`: CORS origins

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
docker-compose exec backend pytest path/to/test.py
```

### Frontend Tests
```bash
# Run frontend tests
docker-compose exec frontend npm test

# Run in watch mode
docker-compose exec frontend npm test -- --watch
```

## 📦 Adding Dependencies

### Backend (Python)
```bash
# Add to requirements file
echo "package-name==1.0.0" >> backend/requirements/base.txt

# Install in container
make install-requirements
```

### Frontend (Node.js)
```bash
# Install package
docker-compose exec frontend npm install package-name

# Install dev dependency
docker-compose exec frontend npm install -D package-name
```

## �️ ClamAV Integration

This template includes **django-clamav**, a comprehensive ClamAV integration for file scanning and virus detection.

### Features

- Automatic file scanning for uploaded files
- REST API endpoints for manual scanning
- Django form validators and mixins
- Support for TCP and Unix socket connections
- Self-contained with zero required dependencies

### API Endpoints

```bash
# Health check
GET http://localhost:8000/api/clamav/health/

# ClamAV info (version, signatures)
GET http://localhost:8000/api/clamav/info/

# Scan file
POST http://localhost:8000/api/clamav/scan/
Content-Type: multipart/form-data
file: [your-file]
```

### Usage in Django

#### Form Validation
```python
from apps.django_clamav.forms import AntivirusFormMixin

class MyUploadForm(AntivirusFormMixin, forms.Form):
    file = forms.FileField()
```

#### Model Field Validation
```python
from apps.django_clamav.validators import validate_file

class MyModel(models.Model):
    file = models.FileField(validators=[validate_file])
```

#### Direct Scanning
```python
from apps.django_clamav.scanner import get_scanner

scanner = get_scanner()
result = scanner.scan("/path/to/file.pdf")

if result.passed:
    print("File is clean")
elif result.passed is False:
    print(f"Virus found: {result.details}")
else:
    print(f"Scanning error: {result.details}")
```

### Configuration

ClamAV settings in `.env`:

- `DJANGO_CLAMAV_ENABLED`: Enable/disable scanning (default: True)
- `DJANGO_CLAMAV_CONNECTION_MODE`: 'host' for TCP or 'socket' for Unix socket
- `DJANGO_CLAMAV_URL`: ClamAV daemon URL (default: http://clamav:3310)
- `DJANGO_CLAMAV_TIMEOUT`: Connection timeout in seconds (default: 60.0)
- `DJANGO_CLAMAV_FAIL_LOUDLY`: Raise errors on scan failure (default: False)

### Docker Service

The ClamAV service:
- Downloads virus definitions on first start (~300MB)
- Takes 1-2 minutes to initialize
- Updates definitions automatically via freshclam
- Uses persistent volume for virus database

### Middleware (Optional)

To scan all uploaded files automatically, add to `MIDDLEWARE` in settings:

```python
MIDDLEWARE = [
    ...
    'apps.django_clamav.middleware.AntivirusMiddleware',
]
```

**Note:** ClamAV initialization takes a few minutes on first run. The backend will wait for ClamAV to be healthy before starting.

## �🚀 Deployment

### Production Checklist

1. **Environment Variables**
   - Set `DEBUG=False`
   - Generate strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`
   - Set production database credentials

2. **Security**
   - Enable HTTPS in Nginx
   - Configure CSRF settings
   - Set secure headers
   - Review CORS settings

3. **Performance**
   - Enable caching
   - Configure Gunicorn workers
   - Set up CDN for static files
   - Optimize database queries

4. **Monitoring**
   - Set up error tracking (e.g., Sentry)
   - Configure logging
   - Set up metrics collection
   - Configure health checks

## 🤝 Contributing
By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
Why MIT License?
We chose the MIT License because:

🚀 Maximum flexibility for users and contributors
💼 Business-friendly - can be used in commercial projects
🔧 Simple and permissive - easy to understand and comply
🌍 Wide compatibility - works well with other open source licenses
📚 Well-known - developers are familiar with its terms

What this means for you:

✅ You can use this template for personal or commercial projects
✅ You can modify and distribute as you wish
✅ You can incorporate it into proprietary software
You just need to include the original copyright notice

## ⚙️ Tech Stack

| Layer | Technology | Version |
|-------|------------|--------|
| Backend Runtime | Python | 3.13 |
| Backend Framework | Django | 5.1.4 |
| API Framework | Django REST Framework | 3.15.2 |
| Frontend Runtime | Node.js | 18 LTS |
| Frontend Framework | Next.js | 15.5.7 |
| UI Library | React | 19.0.1 |
| Database | PostgreSQL | 15 |
| Cache/Broker | Redis | 7 |
| Task Queue | Celery | 5.4.0 |
| Reverse Proxy | Nginx | Latest |

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework for perfectionists with deadlines
- [Next.js](https://nextjs.org/) - The React framework for production
- [Docker](https://www.docker.com/) - Containerization platform
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components