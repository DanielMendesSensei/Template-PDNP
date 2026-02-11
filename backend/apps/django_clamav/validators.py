"""
Django form validators for ClamAV file scanning.

These validators can be used with any Django form field or model field
that handles file uploads.

Usage::

    from django_clamav.validators import clamav_file_validator

    class MyModel(models.Model):
        document = models.FileField(validators=[clamav_file_validator])

    # Or in a form
    class MyForm(forms.Form):
        file = forms.FileField(validators=[clamav_file_validator])
"""

import logging

from django_clamav.clamd import CommunicationError
from django_clamav.conf import clamav_settings
from django_clamav.scanner import get_scanner

logger = logging.getLogger("django_clamav.validators")


class ClamAVValidationError(Exception):
    """Raised when a file fails ClamAV scanning."""

    def __init__(self, message, virus_name=None):
        super().__init__(message)
        self.virus_name = virus_name


def validate_file_clamav(file):
    """
    Django validator that scans an uploaded file with ClamAV.

    This validator uses the settings from ``django_clamav.conf`` to connect
    to the ClamAV daemon and scan the file stream.

    Raises:
        django.core.exceptions.ValidationError: If a virus is detected.

    Note:
        If ClamAV is disabled or unreachable (and SKIP_ON_CONNECTION_ERROR is True),
        the file passes validation.
    """
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext as _

    if not clamav_settings.ENABLED:
        return

    config = clamav_settings.get_scanner_config()
    scanner = get_scanner(config)

    # Only clamd-based scanners support stream scanning
    if hasattr(scanner, "get_client"):
        client = scanner.get_client()
        try:
            # Reset file position before scanning
            if hasattr(file, "seek"):
                file.seek(0)

            result = client.instream(file)

            # Reset file position after scanning
            if hasattr(file, "seek"):
                file.seek(0)

            stream_result = result.get("stream")
            if stream_result is None:
                logger.warning("ClamAV returned no result for stream scan.")
                return

            status, virus_name = stream_result
            if status.upper() != "OK":
                raise ValidationError(
                    _("Virus detected in uploaded file: %(virus)s"),
                    code="virus_found",
                    params={"virus": virus_name or "unknown"},
                )
        except CommunicationError as e:
            logger.error(f"ClamAV communication error: {e}")
            if not clamav_settings.SKIP_ON_CONNECTION_ERROR:
                raise ValidationError(
                    _("Unable to scan file for viruses. Please try again later."),
                    code="scan_unavailable",
                )
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            if not clamav_settings.SKIP_ON_CONNECTION_ERROR:
                raise ValidationError(
                    _("Error during virus scanning. Please try again later."),
                    code="scan_error",
                )
    else:
        logger.debug("Scanner does not support stream scanning; skipping validation.")


# Shorthand alias for the validator
clamav_file_validator = validate_file_clamav
