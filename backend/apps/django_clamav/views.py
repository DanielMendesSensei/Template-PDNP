"""
Optional REST API views for ClamAV scanning.

Requires Django REST Framework to be installed. If DRF is not available,
these views will not be usable but the rest of django_clamav will work fine.

Provides endpoints for:
- POST /scan/ - Scan an uploaded file
- GET /health/ - Check ClamAV daemon health
- GET /info/ - Get ClamAV version information
"""

import logging

logger = logging.getLogger("django_clamav.views")

try:
    from rest_framework import serializers, status
    from rest_framework.parsers import MultiPartParser
    from rest_framework.response import Response
    from rest_framework.views import APIView

    HAS_DRF = True
except ImportError:
    HAS_DRF = False
    logger.debug("Django REST Framework not installed. API views not available.")

if HAS_DRF:
    from django_clamav.clamd import CommunicationError
    from django_clamav.conf import clamav_settings
    from django_clamav.scanner import ClamdScanner, get_scanner

    class ScanResultSerializer(serializers.Serializer):
        filename = serializers.CharField()
        status = serializers.CharField()
        details = serializers.CharField(allow_null=True)
        is_clean = serializers.BooleanField(allow_null=True)

    class HealthSerializer(serializers.Serializer):
        status = serializers.CharField()
        message = serializers.CharField()

    class InfoSerializer(serializers.Serializer):
        name = serializers.CharField()
        version = serializers.CharField()
        virus_definitions = serializers.CharField(allow_null=True)

    class ScanFileView(APIView):
        """
        Scan an uploaded file for viruses.

        POST /api/clamav/scan/
        Content-Type: multipart/form-data

        Returns scan results including status and detected threats.
        """
        parser_classes = [MultiPartParser]

        def post(self, request):
            if not clamav_settings.ENABLED:
                return Response(
                    {"error": "ClamAV scanning is disabled."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                return Response(
                    {"error": "No file provided. Use 'file' field."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            config = clamav_settings.get_scanner_config()
            scanner = get_scanner(config)

            if not isinstance(scanner, ClamdScanner):
                return Response(
                    {"error": "Stream scanning not supported with current backend."},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )

            client = scanner.get_client()

            try:
                uploaded_file.seek(0)
                result = client.instream(uploaded_file)
                stream_result = result.get("stream")

                if stream_result is None:
                    data = {
                        "filename": uploaded_file.name,
                        "status": "UNKNOWN",
                        "details": None,
                        "is_clean": None,
                    }
                else:
                    scan_status, details = stream_result
                    data = {
                        "filename": uploaded_file.name,
                        "status": scan_status,
                        "details": details,
                        "is_clean": scan_status.upper() == "OK",
                    }

                serializer = ScanResultSerializer(data)
                return Response(serializer.data)

            except CommunicationError as e:
                return Response(
                    {"error": f"ClamAV communication error: {e}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except Exception as e:
                return Response(
                    {"error": f"Scan error: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

    class HealthCheckView(APIView):
        """
        Check ClamAV daemon availability.

        GET /api/clamav/health/
        """

        def get(self, request):
            if not clamav_settings.ENABLED:
                return Response(
                    {"status": "disabled", "message": "ClamAV is not enabled."},
                    status=status.HTTP_200_OK,
                )

            config = clamav_settings.get_scanner_config()
            scanner = get_scanner(config)

            if not isinstance(scanner, ClamdScanner):
                return Response(
                    {"status": "ok", "message": "Using clamscan binary backend."},
                    status=status.HTTP_200_OK,
                )

            client = scanner.get_client()
            try:
                pong = client.ping()
                return Response(
                    {"status": "ok", "message": pong.strip()},
                    status=status.HTTP_200_OK,
                )
            except CommunicationError as e:
                return Response(
                    {"status": "error", "message": str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

    class InfoView(APIView):
        """
        Get ClamAV version and virus definition information.

        GET /api/clamav/info/
        """

        def get(self, request):
            if not clamav_settings.ENABLED:
                return Response(
                    {"error": "ClamAV is not enabled."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            config = clamav_settings.get_scanner_config()
            scanner = get_scanner(config)

            try:
                info = scanner.info()
                serializer = InfoSerializer({
                    "name": info.name,
                    "version": info.version,
                    "virus_definitions": info.virus_definitions,
                })
                return Response(serializer.data)
            except Exception as e:
                return Response(
                    {"error": f"Cannot get ClamAV info: {e}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
