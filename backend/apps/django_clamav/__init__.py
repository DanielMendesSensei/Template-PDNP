"""
django_clamav - A reusable ClamAV integration for Django and Python projects.

This package provides:
- A low-level ClamAV daemon client (TCP and Unix socket)
- A high-level scanner abstraction (clamd and clamscan backends)
- Django form mixins and validators for automatic file scanning
- Optional middleware for scanning all uploaded files
- Optional REST API endpoints for file scanning
- Microservice-ready architecture

Usage as Python library (no Django required):
    from django_clamav.scanner import get_scanner
    scanner = get_scanner({"backend": "clamd", "address": "tcp://localhost:3310"})
    result = scanner.scan("/path/to/file")

Usage as Django app:
    # settings.py
    INSTALLED_APPS = [..., 'django_clamav']
    DJANGO_CLAMAV_ENABLED = True
    DJANGO_CLAMAV_CONNECTION_MODE = 'host'
    DJANGO_CLAMAV_URL = 'http://clamav:3310'

    # forms.py
    from django_clamav.forms import ClamAVFormMixin
    class MyUploadForm(ClamAVFormMixin, forms.ModelForm):
        ...
"""

from django_clamav.scanner import get_scanner

__version__ = "1.0.0"
__author__ = "Kapybar Team"

__all__ = [
    "get_scanner",
    "__version__",
]
