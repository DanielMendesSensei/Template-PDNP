"""
URL configuration for django_clamav REST API.

Include in your project's urlpatterns::

    urlpatterns = [
        ...
        path('api/clamav/', include('django_clamav.urls')),
    ]
"""

from django.urls import path

app_name = "django_clamav"

urlpatterns = []

try:
    from django_clamav.views import HealthCheckView, InfoView, ScanFileView

    urlpatterns = [
        path("scan/", ScanFileView.as_view(), name="scan"),
        path("health/", HealthCheckView.as_view(), name="health"),
        path("info/", InfoView.as_view(), name="info"),
    ]
except ImportError:
    # DRF not installed; no API routes available
    pass
