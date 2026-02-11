"""
Django form mixins for ClamAV file scanning.

Provides a ``ClamAVFormMixin`` that can be added to any Django ModelForm
to automatically scan uploaded files for viruses.

Usage::

    from django import forms
    from django_clamav.forms import ClamAVFormMixin

    class DocumentUploadForm(ClamAVFormMixin, forms.ModelForm):
        # The mixin will automatically scan file fields during clean()
        clamav_file_fields = ['file', 'attachment']  # Optional: specify which fields

        class Meta:
            model = Document
            fields = ['file', 'title']
"""

import logging
from typing import Optional

from django_clamav.clamd import CommunicationError
from django_clamav.conf import clamav_settings
from django_clamav.scanner import ClamdScanner, get_scanner

logger = logging.getLogger("django_clamav.forms")


class ClamAVFormMixin:
    """
    Form mixin that scans uploaded files with ClamAV during validation.

    Add this mixin to any Django Form or ModelForm to enable automatic
    virus scanning of uploaded files.

    Attributes:
        clamav_file_fields (list[str] | None):
            List of field names to scan. If None, all FileField instances
            will be scanned automatically.
        clamav_skip_on_error (bool):
            Whether to allow the upload if ClamAV is unreachable.
            Defaults to the DJANGO_CLAMAV_SKIP_ON_CONNECTION_ERROR setting.
    """

    clamav_file_fields: Optional[list] = None
    clamav_skip_on_error: Optional[bool] = None

    def _get_clamav_scanner(self):
        """Create and return a ClamAV scanner instance."""
        config = clamav_settings.get_scanner_config()
        logger.debug(f"ClamAVFormMixin: scanner config={config}")
        return get_scanner(config)

    def _get_clamav_client(self):
        """Get the clamd client for stream scanning."""
        scanner = self._get_clamav_scanner()
        if isinstance(scanner, ClamdScanner):
            return scanner.get_client()
        return None

    def _get_file_fields(self):
        """Get the list of file field names to scan."""
        if self.clamav_file_fields is not None:
            return self.clamav_file_fields

        # Auto-detect file fields
        from django import forms
        file_fields = []
        for name, field in self.fields.items():
            if isinstance(field, (forms.FileField, forms.ImageField)):
                file_fields.append(name)
        return file_fields

    def _scan_file(self, file) -> tuple:
        """
        Scan a single file with ClamAV.

        Returns:
            (is_clean, reason) where:
            - is_clean is True (clean), False (virus found), or None (error/unavailable)
            - reason is the virus name or error message
        """
        client = self._get_clamav_client()
        if client is None:
            logger.debug("ClamAVFormMixin: no clamd client available, skipping scan.")
            return None, None

        try:
            # Reset file position
            if hasattr(file, "seek"):
                file.seek(0)

            result = client.instream(file)

            # Reset file position for Django to continue processing
            if hasattr(file, "seek"):
                file.seek(0)

            logger.debug(f"ClamAVFormMixin: scan result={result}")
            stream_result = result.get("stream")
            if stream_result is None:
                return None, None

            status, details = stream_result
            is_clean = status.upper() == "OK"
            return is_clean, details

        except CommunicationError as e:
            logger.error(f"ClamAVFormMixin: communication error: {e}")
            return None, str(e)
        except Exception as e:
            logger.error(f"ClamAVFormMixin: scan error: {e}")
            return None, str(e)

    def clean(self):
        """Override clean to add ClamAV scanning."""
        cleaned_data = super().clean()

        if not clamav_settings.ENABLED:
            return cleaned_data

        skip_on_error = (
            self.clamav_skip_on_error
            if self.clamav_skip_on_error is not None
            else clamav_settings.SKIP_ON_CONNECTION_ERROR
        )

        for field_name in self._get_file_fields():
            file = cleaned_data.get(field_name)
            if file is None:
                continue

            # Get the underlying file object
            file_obj = getattr(file, "file", file)
            is_clean, reason = self._scan_file(file_obj)

            if is_clean is False:
                from django.utils.translation import gettext as _
                self.add_error(
                    field_name,
                    _("Virus found in submitted file [%(file)s]: %(reason)s")
                    % {"file": file.name if hasattr(file, "name") else field_name, "reason": reason}
                )
            elif is_clean is None and not skip_on_error:
                from django.utils.translation import gettext as _
                self.add_error(
                    field_name,
                    _("Unable to scan file for viruses. Please try again later.")
                )

        return cleaned_data
