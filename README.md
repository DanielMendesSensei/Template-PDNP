# Fullstack Template - Django + Next.js

A modern fullstack application template with Django REST Framework backend and Next.js frontend, fully containerized with Docker.

## 🚀 Features

### Backend (Django)
- **Django 4.2+** with Django REST Framework
- **PostgreSQL** database
- **Redis** for caching and Celery broker
- **Celery** for async tasks and scheduled jobs
- **JWT Authentication** with Simple JWT
- **CORS** configured for frontend integration
- **API Documentation** with Swagger/ReDoc
- **Code Quality** tools (Black, Flake8, isort)
- **Testing** with pytest and coverage

### Frontend (Next.js)
- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **API Integration** with Axios
- **Authentication** flow with JWT
- **ESLint** and **Prettier** configured

### DevOps
- **Docker** and **Docker Compose** for containerization
- **Nginx** as reverse proxy
- **Flower** for Celery monitoring
- **PgAdmin** for database management (dev)
- **Hot reload** in development
- **Production-ready** configurations

## 📋 Requirements

- Docker and Docker Compose
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

## 🚀 Deployment

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
✅ You just need to include the original copyright notice

## 🙏 Acknowledgments

- Django documentation
- Next.js documentation
- Docker documentation
- Community contributors