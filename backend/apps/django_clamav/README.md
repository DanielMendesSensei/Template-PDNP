# django-clamav

A reusable ClamAV integration for **Django** and **Python** projects. Can be used as:

1. **Django reusable app** -- Form mixins, validators, middleware, REST API
2. **Python library** -- Pure Python clamd client + scanner (no Django required)
3. **Microservice** -- FastAPI REST API with Docker support

## Features

- ClamAV daemon client supporting **TCP** and **Unix socket** connections
- **clamd** (daemon) and **clamscan** (binary) scanner backends
- Django **form mixin** for automatic file scanning during validation
- Django **file validator** for model fields and form fields
- Django **middleware** for scanning all uploads automatically
- Optional **REST API** endpoints (requires Django REST Framework)
- **FastAPI microservice** for language-agnostic integration
- Self-contained settings with `DJANGO_CLAMAV_` prefix
- Backwards compatible with legacy `CLAMD_*` / `USE_CLAMAV` settings
- Zero required dependencies (pure Python core)
- Docker-ready with compose configuration

## Quick Start

### Installation

```bash
# Copy the django_clamav directory to your project
cp -r django_clamav /path/to/your/project/

# Or install as a package (from source)
pip install -e ./django_clamav

# With Django support
pip install -e "./django_clamav[django]"

# With REST API support
pip install -e "./django_clamav[drf]"

# With microservice support
pip install -e "./django_clamav[microservice]"
```

### As a Python Library (No Django)

```python
from django_clamav.scanner import get_scanner

# Using clamd daemon (TCP)
scanner = get_scanner({
    "backend": "clamd",
    "address": "http://localhost:3310",
    "timeout": 60.0,
    "stream": True,
})

# Using clamscan binary
scanner = get_scanner({"backend": "clamscan"})

# Scan a file
result = scanner.scan("/path/to/file.pdf")
print(result.passed)    # True (clean), False (virus), None (error)
print(result.state)     # "OK", "FOUND", "ERROR"
print(result.details)   # Virus name or error message

# Stream scanning with clamd
client = scanner.get_client()
result = client.instream(open("/path/to/file.pdf", "rb"))
# {'stream': ('OK', None)}

# Health check
print(client.ping())     # "PONG"
print(client.version())  # "ClamAV 1.4.3/27816/..."
```

### As a Django App

#### 1. Settings

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_clamav',
]

# Enable ClamAV scanning
DJANGO_CLAMAV_ENABLED = True

# Connection mode: 'host' (TCP) or 'socket' (Unix socket)
DJANGO_CLAMAV_CONNECTION_MODE = 'host'

# TCP connection (when mode is 'host')
DJANGO_CLAMAV_URL = 'http://clamav:3310'

# Unix socket (when mode is 'socket')
# DJANGO_CLAMAV_SOCKET_PATH = 'unix:///var/run/clamav/clamd.ctl'

# Timeout in seconds
DJANGO_CLAMAV_TIMEOUT = 60.0

# Allow uploads when ClamAV is unreachable
DJANGO_CLAMAV_SKIP_ON_CONNECTION_ERROR = True
```

Or use environment variables:

```bash
DJANGO_CLAMAV_ENABLED=true
DJANGO_CLAMAV_CONNECTION_MODE=host
DJANGO_CLAMAV_URL=http://clamav:3310
DJANGO_CLAMAV_TIMEOUT=60
```

**Legacy settings are also supported** (`USE_CLAMAV`, `CLAMD_URL`, `CLAMD_SOCKET_PATH`, etc.).

#### 2. Form Mixin (Recommended)

```python
from django import forms
from django_clamav.forms import ClamAVFormMixin

class DocumentUploadForm(ClamAVFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'title']

    # Optional: specify which fields to scan (auto-detects FileField by default)
    clamav_file_fields = ['file']
```

The mixin automatically scans all `FileField`/`ImageField` fields during `clean()`.

#### 3. File Validator

```python
from django.db import models
from django_clamav.validators import clamav_file_validator

class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        validators=[clamav_file_validator],
    )
```

Or in a form:

```python
from django import forms
from django_clamav.validators import clamav_file_validator

class UploadForm(forms.Form):
    file = forms.FileField(validators=[clamav_file_validator])
```

#### 4. Middleware (Scan All Uploads)

```python
# settings.py
MIDDLEWARE = [
    ...
    'django_clamav.middleware.ClamAVUploadMiddleware',
    ...
]

DJANGO_CLAMAV_ENABLED = True
DJANGO_CLAMAV_SCAN_ON_UPLOAD = True  # Required for middleware
```

The middleware scans all files on POST/PUT/PATCH requests. Returns HTTP 403 if a virus is detected.

#### 5. REST API (Requires DRF)

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path('api/clamav/', include('django_clamav.urls')),
]
```

Endpoints:
- `POST /api/clamav/scan/` -- Scan an uploaded file
- `GET /api/clamav/health/` -- Check ClamAV daemon status
- `GET /api/clamav/info/` -- Get ClamAV version info

### As a Microservice

See [microservice/README.md](microservice/README.md) for the FastAPI microservice setup.

Quick start:

```bash
cd django_clamav/microservice
docker compose up -d
```

Then scan files via HTTP:

```bash
curl -X POST http://localhost:8000/scan \
  -F "file=@document.pdf"
```

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `DJANGO_CLAMAV_ENABLED` | `False` | Enable/disable ClamAV scanning |
| `DJANGO_CLAMAV_CONNECTION_MODE` | `host` | `'host'` (TCP) or `'socket'` (Unix) |
| `DJANGO_CLAMAV_URL` | `http://127.0.0.1:3310` | ClamAV daemon TCP address |
| `DJANGO_CLAMAV_SOCKET_PATH` | `unix:///var/run/clamav/clamd.ctl` | ClamAV Unix socket path |
| `DJANGO_CLAMAV_TIMEOUT` | `60.0` | Connection timeout (seconds) |
| `DJANGO_CLAMAV_STREAM` | `True` | Use stream scanning (INSTREAM) |
| `DJANGO_CLAMAV_BACKEND` | `clamd` | `'clamd'` (daemon) or `'clamscan'` (binary) |
| `DJANGO_CLAMAV_SCAN_ON_UPLOAD` | `False` | Enable middleware auto-scanning |
| `DJANGO_CLAMAV_RAISE_ON_VIRUS` | `True` | Raise ValidationError on virus |
| `DJANGO_CLAMAV_SKIP_ON_CONNECTION_ERROR` | `True` | Allow upload when ClamAV unavailable |
| `DJANGO_CLAMAV_MAX_FILE_SIZE` | `2000` | Max file size in MB (clamscan) |
| `DJANGO_CLAMAV_MAX_SCAN_SIZE` | `2000` | Max scan size in MB (clamscan) |

## ClamAV Setup

### Docker (Recommended)

```yaml
# docker-compose.yml
services:
  clamav:
    image: clamav/clamav:1.4.3_base
    platform: linux/amd64
    ports:
      - "127.0.0.1:3310:3310"
    volumes:
      - clamav-data:/var/lib/clamav
    environment:
      CLAMAV_NO_FRESHCLAMD: "false"

volumes:
  clamav-data:
```

```bash
docker compose up -d clamav
```

### Local Installation

```bash
# Ubuntu/Debian
sudo apt install clamav clamav-daemon clamav-freshclam
sudo freshclam  # Update virus definitions

# macOS
brew install clamav

# Update definitions
sudo freshclam
```

## File Structure

```
django_clamav/
|-- __init__.py          # Package init, version, public API
|-- apps.py              # Django AppConfig
|-- conf.py              # Settings handling with DJANGO_CLAMAV_ prefix
|-- clamd.py             # ClamAV daemon client (TCP + Unix socket) [no Django deps]
|-- scanner.py           # Scanner abstraction (clamd + clamscan) [no Django deps]
|-- forms.py             # ClamAVFormMixin for Django forms
|-- validators.py        # Django file validators
|-- middleware.py         # Upload scanning middleware
|-- views.py             # DRF API views (optional)
|-- urls.py              # API URL routes (optional)
|-- tests.py             # Comprehensive test suite
|-- pyproject.toml       # Package configuration
|-- README.md            # This file
|-- bin/
|   `-- get_docker_host.sh  # Docker helper script
`-- microservice/
    |-- app.py           # FastAPI microservice
    |-- Dockerfile       # Container image
    |-- docker-compose.yml
    |-- requirements.txt
    `-- README.md
```

## Migration from Legacy `clamav` App

If migrating from the original `clamav` app in Kapybar:

1. Replace `'clamav'` with `'django_clamav'` in `INSTALLED_APPS`
2. Update imports:
   - `import clamav.scanner as clamd` -> `import django_clamav.scanner as clamd`
   - `from clamav import get_scanner` -> `from django_clamav import get_scanner`
3. (Optional) Rename settings from `CLAMD_*` to `DJANGO_CLAMAV_*` (legacy names still work)
4. (Optional) Replace manual scanning logic in forms with `ClamAVFormMixin`

## Testing

```bash
# Unit tests
python -m pytest django_clamav/tests.py -v

# With Django
python manage.py test django_clamav

# With coverage
coverage run -m pytest django_clamav/tests.py
coverage report
```

## License

MIT License
