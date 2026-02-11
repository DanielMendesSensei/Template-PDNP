# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-02-11

### Added
- **ClamAV Integration**: Full virus scanning and file validation via `django-clamav` reusable app
  - REST API endpoints for file scanning (`/api/clamav/scan/`), health check (`/api/clamav/health/`), and daemon info (`/api/clamav/info/`)
  - Django form mixin (`AntivirusFormMixin`) for automatic file validation
  - Django model field validator (`validate_file`) for file uploads
  - Direct Python scanner API for programmatic virus scanning
  - Optional middleware for scanning all uploaded files automatically
  - Support for TCP (host) and Unix socket connection modes
  - Self-contained with zero additional dependencies
- ClamAV Docker service (`clamav/clamav:latest`) with persistent virus definitions volume
- ClamAV environment variables in `.env.example`
- ClamAV section in README with usage examples and configuration guide

### Changed
- Backend service now depends on ClamAV health check before starting
- Updated `docker-compose.yml` with ClamAV service and `clamav_data` volume

---

## [2.0.0] - 2025-12-09

### Added
- Python 3.13 support
- Django 5.1.4 (latest stable release)
- Full security audit and vulnerability patching
- Improved Docker multi-stage builds

### Changed

#### Backend
- **Python**: Upgraded from 3.11 to **3.13**
- **Django**: Upgraded from 4.2.17 to **5.1.4**
- **django-celery-beat**: Upgraded from 2.7.0 to **2.8.1**
- **djangorestframework-simplejwt**: Upgraded from 5.3.1 to **5.5.1**
- **django-stubs**: Upgraded from 5.1.1 to **5.2.8**

#### Frontend
- **Next.js**: Upgraded from 14.1.0 to **15.5.7**
- **React**: Upgraded from 18.x to **19.0.1**
- **React DOM**: Upgraded from 18.x to **19.0.1**
- **TypeScript**: Upgraded to **5.7.2**

### Security
- **CVE-2024-34351**: Fixed SSRF vulnerability in Next.js Server Actions (Next.js < 14.1.1)
- **CVE-2024-51479**: Fixed authorization bypass in Next.js (Next.js < 14.2.15)
- **CVE-2025-66478**: Fixed React2Shell RCE vulnerability (CVSS 10.0) affecting React < 19.0.1
- **CVE-2024-42005**: Fixed Django SQL injection in QuerySet.values() and values_list()
- **CVE-2024-53908**: Fixed Django SQL injection in HasKey lookup on Oracle
- **glob vulnerability**: Fixed with npm override to ^11.0.0

### Removed
- Legacy Python 3.11 support (minimum is now 3.13)
- Deprecated Django 4.x configurations

---

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Django 4.2 backend with Django REST Framework
- Next.js 14 frontend with App Router
- PostgreSQL database integration
- Redis caching and Celery async tasks
- JWT authentication with Simple JWT
- Docker Compose setup for development and production
- Nginx reverse proxy configuration
- Flower for Celery monitoring
- API documentation with Swagger/ReDoc
- Code quality tools (Black, Flake8, isort, ESLint, Prettier)
- Testing setup with pytest and Jest
- Makefile with common commands
- Environment-based configuration

---

[2.1.0]: https://github.com/DanielMendesSensei/Template-PDNP/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/DanielMendesSensei/Template-PDNP/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/DanielMendesSensei/Template-PDNP/releases/tag/v1.0.0
