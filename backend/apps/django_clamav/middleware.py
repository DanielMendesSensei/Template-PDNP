"""
Django middleware for automatic ClamAV scanning of all file uploads.

When enabled, this middleware intercepts every request with uploaded files
and scans them using ClamAV before they reach the view layer.

Add to Django settings::

    MIDDLEWARE = [
        ...
        'django_clamav.middleware.ClamAVUploadMiddleware',
        ...
    ]

    DJANGO_CLAMAV_ENABLED = True
    DJANGO_CLAMAV_SCAN_ON_UPLOAD = True
"""

import json
import logging

from django.http import HttpResponseForbidden

from django_clamav.clamd import CommunicationError
from django_clamav.conf import clamav_settings
from django_clamav.scanner import ClamdScanner, get_scanner

logger = logging.getLogger("django_clamav.middleware")


class ClamAVUploadMiddleware:
    """
    Middleware that scans all uploaded files with ClamAV.

    This middleware only activates when:
    - DJANGO_CLAMAV_ENABLED is True
    - DJANGO_CLAMAV_SCAN_ON_UPLOAD is True
    - The request contains uploaded files

    On virus detection, returns HTTP 403 with details.
    On ClamAV connection errors, behavior depends on SKIP_ON_CONNECTION_ERROR.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not clamav_settings.ENABLED or not clamav_settings.SCAN_ON_UPLOAD:
            return self.get_response(request)

        if request.method in ("POST", "PUT", "PATCH") and request.FILES:
            blocked = self._scan_uploaded_files(request)
            if blocked:
                return blocked

        return self.get_response(request)

    def _scan_uploaded_files(self, request):
        """Scan all uploaded files. Returns HttpResponseForbidden if infected."""
        config = clamav_settings.get_scanner_config()
        scanner = get_scanner(config)

        if not isinstance(scanner, ClamdScanner):
            logger.debug("ClamAVUploadMiddleware: scanner does not support stream; skipping.")
            return None

        client = scanner.get_client()

        for field_name, uploaded_file in request.FILES.items():
            try:
                # Reset file position
                uploaded_file.seek(0)

                result = client.instream(uploaded_file)

                # Reset file position for downstream processing
                uploaded_file.seek(0)

                stream_result = result.get("stream")
                if stream_result is None:
                    continue

                status, virus_name = stream_result
                if status.upper() != "OK":
                    logger.warning(
                        f"ClamAVUploadMiddleware: virus detected in "
                        f"'{field_name}' ({uploaded_file.name}): {virus_name}"
                    )
                    return HttpResponseForbidden(
                        json.dumps({
                            "error": "virus_detected",
                            "field": field_name,
                            "filename": uploaded_file.name,
                            "virus": virus_name,
                        }),
                        content_type="application/json",
                    )

            except CommunicationError as e:
                logger.error(f"ClamAVUploadMiddleware: communication error: {e}")
                if not clamav_settings.SKIP_ON_CONNECTION_ERROR:
                    return HttpResponseForbidden(
                        json.dumps({
                            "error": "scan_unavailable",
                            "message": "Unable to scan uploaded files.",
                        }),
                        content_type="application/json",
                    )
            except Exception as e:
                logger.error(f"ClamAVUploadMiddleware: unexpected error: {e}")
                if not clamav_settings.SKIP_ON_CONNECTION_ERROR:
                    return HttpResponseForbidden(
                        json.dumps({
                            "error": "scan_error",
                            "message": "Error scanning uploaded files.",
                        }),
                        content_type="application/json",
                    )

        return None
