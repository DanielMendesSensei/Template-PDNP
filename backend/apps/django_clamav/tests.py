"""
Comprehensive tests for django_clamav.

Run with: python -m pytest django_clamav/tests.py -v
Or with Django: python manage.py test django_clamav
"""

import io
from unittest import TestCase
from unittest.mock import MagicMock, patch

from django_clamav.clamd import (
    BufferTooLongError,
    ClamdError,
    ClamdNetworkSocket,
    ClamdUnixSocket,
    CommunicationError,
    ResponseError,
)
from django_clamav.scanner import (
    ClamdScanner,
    ClamdScannerConfig,
    ClamscanScanner,
    ClamscanScannerConfig,
    ScannerInfo,
    ScanResult,
    get_scanner,
)


class TestExceptions(TestCase):
    """Test exception hierarchy."""

    def test_clamd_error_is_exception(self):
        assert issubclass(ClamdError, Exception)

    def test_response_error_is_clamd_error(self):
        assert issubclass(ResponseError, ClamdError)

    def test_buffer_too_long_is_response_error(self):
        assert issubclass(BufferTooLongError, ResponseError)

    def test_communication_error_is_clamd_error(self):
        assert issubclass(CommunicationError, ClamdError)


class TestClamdNetworkSocket(TestCase):
    """Test ClamdNetworkSocket initialization."""

    def test_default_init(self):
        client = ClamdNetworkSocket()
        assert client.host == "127.0.0.1"
        assert client.port == 3310
        assert client.timeout is None

    def test_custom_init(self):
        client = ClamdNetworkSocket(host="clamav", port=3311, timeout=30.0)
        assert client.host == "clamav"
        assert client.port == 3311
        assert client.timeout == 30.0

    def test_error_message_single_arg(self):
        client = ClamdNetworkSocket()
        err = OSError("Connection refused")
        msg = client._error_message(err)
        assert "127.0.0.1:3310" in msg
        assert "Connection refused" in msg

    def test_error_message_two_args(self):
        client = ClamdNetworkSocket()
        err = OSError(111, "Connection refused")
        msg = client._error_message(err)
        assert "111" in msg


class TestClamdUnixSocket(TestCase):
    """Test ClamdUnixSocket initialization."""

    def test_default_init(self):
        client = ClamdUnixSocket()
        assert client.unix_socket == "/var/run/clamav/clamd.ctl"

    def test_strip_unix_scheme(self):
        client = ClamdUnixSocket(path="unix:///var/run/clamav/clamd.ctl")
        assert client.unix_socket == "/var/run/clamav/clamd.ctl"

    def test_plain_path(self):
        client = ClamdUnixSocket(path="/tmp/clamd.sock")
        assert client.unix_socket == "/tmp/clamd.sock"


class TestScanResult(TestCase):
    """Test ScanResult dataclass."""

    def test_passed_ok(self):
        result = ScanResult(filename="test.pdf", state="OK", details=None, err=None)
        assert result.passed is True

    def test_passed_found(self):
        result = ScanResult(filename="test.pdf", state="FOUND", details="Eicar", err=None)
        assert result.passed is False

    def test_passed_error(self):
        result = ScanResult(filename="test.pdf", state="ERROR", details="err", err=None)
        assert result.passed is False

    def test_passed_communication_error(self):
        result = ScanResult(
            filename="test.pdf", state=None, details=None,
            err=CommunicationError("timeout")
        )
        assert result.passed is None

    def test_passed_buffer_too_long(self):
        result = ScanResult(
            filename="test.pdf", state=None, details=None,
            err=BufferTooLongError("too big")
        )
        assert result.passed is None

    def test_update(self):
        result = ScanResult(filename="test.pdf", state=None, details=None, err=None)
        result.update("OK", None)
        assert result.state == "OK"
        assert result.details is None

    def test_equality(self):
        r1 = ScanResult(filename="f.pdf", state="OK", details=None, err=None)
        r2 = ScanResult(filename="f.pdf", state="OK", details=None, err=None)
        assert r1 == r2

    def test_inequality(self):
        r1 = ScanResult(filename="f.pdf", state="OK", details=None, err=None)
        r2 = ScanResult(filename="f.pdf", state="FOUND", details="Eicar", err=None)
        assert r1 != r2


class TestScannerInfo(TestCase):
    """Test ScannerInfo parsing via Scanner."""

    def test_parse_version_three_parts(self):
        scanner = ClamscanScanner(ClamscanScannerConfig(backend="clamscan"))
        info = scanner._parse_version("ClamAV 1.4.3/27816/2025-11-07")
        assert info.version == "ClamAV 1.4.3"
        assert info.virus_definitions == "27816/2025-11-07"

    def test_parse_version_single_part(self):
        scanner = ClamscanScanner(ClamscanScannerConfig(backend="clamscan"))
        info = scanner._parse_version("ClamAV 1.4.3")
        assert info.version == "ClamAV 1.4.3"
        assert info.virus_definitions is None

    def test_parse_version_invalid(self):
        scanner = ClamscanScanner(ClamscanScannerConfig(backend="clamscan"))
        with self.assertRaises(ValueError):
            scanner._parse_version("invalid")


class TestGetScanner(TestCase):
    """Test the get_scanner factory function."""

    def test_default_is_clamscan(self):
        scanner = get_scanner()
        assert isinstance(scanner, ClamscanScanner)

    def test_clamscan_backend(self):
        scanner = get_scanner({"backend": "clamscan"})
        assert isinstance(scanner, ClamscanScanner)

    @patch("django_clamav.scanner.ClamdScanner.get_client")
    def test_clamd_backend(self, mock_client):
        mock_client.return_value = MagicMock()
        scanner = get_scanner({
            "backend": "clamd",
            "address": "http://localhost:3310",
        })
        assert isinstance(scanner, ClamdScanner)

    def test_invalid_backend(self):
        with self.assertRaises(ValueError):
            get_scanner({"backend": "invalid"})


class TestClamdScanner(TestCase):
    """Test ClamdScanner scan methods."""

    @patch("django_clamav.scanner.ClamdScanner.get_client")
    def test_scan_stream_ok(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.instream.return_value = {"stream": ("OK", None)}
        mock_get_client.return_value = mock_client

        scanner = ClamdScanner(ClamdScannerConfig(
            backend="clamd",
            address="http://localhost:3310",
            stream=True,
        ))
        result = scanner.scan("test.pdf")
        assert result.state == "OK"
        assert result.passed is True

    @patch("django_clamav.scanner.ClamdScanner.get_client")
    def test_scan_stream_found(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.instream.return_value = {"stream": ("FOUND", "Eicar-Test")}
        mock_get_client.return_value = mock_client

        scanner = ClamdScanner(ClamdScannerConfig(
            backend="clamd",
            address="http://localhost:3310",
            stream=True,
        ))
        result = scanner.scan("test.pdf")
        assert result.state == "FOUND"
        assert result.details == "Eicar-Test"
        assert result.passed is False

    @patch("django_clamav.scanner.ClamdScanner.get_client")
    def test_scan_connection_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.instream.side_effect = CommunicationError("timeout")
        mock_get_client.return_value = mock_client

        scanner = ClamdScanner(ClamdScannerConfig(
            backend="clamd",
            address="http://localhost:3310",
            stream=True,
        ))
        result = scanner.scan("test.pdf")
        assert result.state == "ERROR"
        assert result.err is not None


class TestClamAVSettings(TestCase):
    """Test the settings configuration module."""

    def test_settings_import(self):
        from django_clamav.conf import clamav_settings
        assert clamav_settings is not None

    def test_get_scanner_config_clamd(self):
        from django_clamav.conf import ClamAVSettings
        settings = ClamAVSettings()
        settings._cache = {
            "BACKEND": "clamd",
            "CONNECTION_MODE": "host",
            "URL": "http://localhost:3310",
            "TIMEOUT": 60.0,
            "STREAM": True,
        }
        config = settings.get_scanner_config()
        assert config["backend"] == "clamd"
        assert config["address"] == "http://localhost:3310"

    def test_get_scanner_config_clamscan(self):
        from django_clamav.conf import ClamAVSettings
        settings = ClamAVSettings()
        settings._cache = {
            "BACKEND": "clamscan",
            "MAX_FILE_SIZE": 2000.0,
            "MAX_SCAN_SIZE": 2000.0,
        }
        config = settings.get_scanner_config()
        assert config["backend"] == "clamscan"
