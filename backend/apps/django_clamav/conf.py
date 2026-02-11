"""
Configuration handling for django_clamav.

All settings use the ``DJANGO_CLAMAV_`` prefix. Backwards compatibility with
legacy settings (``USE_CLAMAV``, ``CLAMD_*``) is provided for easy migration.

Settings:
    DJANGO_CLAMAV_ENABLED (bool):
        Enable or disable ClamAV scanning. Default: False.

    DJANGO_CLAMAV_CONNECTION_MODE (str):
        Connection mode: 'socket' or 'host'. Default: 'host'.

    DJANGO_CLAMAV_SOCKET_PATH (str):
        Unix socket path for clamd. Default: 'unix:///var/run/clamav/clamd.ctl'.

    DJANGO_CLAMAV_URL (str):
        TCP URL for clamd daemon. Default: 'http://127.0.0.1:3310'.

    DJANGO_CLAMAV_TIMEOUT (float):
        Timeout for clamd connections in seconds. Default: 60.0.

    DJANGO_CLAMAV_STREAM (bool):
        Whether to use stream scanning (INSTREAM) or file reference. Default: True.

    DJANGO_CLAMAV_BACKEND (str):
        Scanner backend: 'clamd' or 'clamscan'. Default: 'clamd'.

    DJANGO_CLAMAV_SCAN_ON_UPLOAD (bool):
        Enable middleware-based automatic scanning of uploads. Default: False.

    DJANGO_CLAMAV_RAISE_ON_VIRUS (bool):
        Raise ValidationError when a virus is found in forms. Default: True.

    DJANGO_CLAMAV_SKIP_ON_CONNECTION_ERROR (bool):
        If True, allow file upload when ClamAV is unreachable. Default: True.

    DJANGO_CLAMAV_MAX_FILE_SIZE (float):
        Max file size in MB for clamscan backend. Default: 2000.

    DJANGO_CLAMAV_MAX_SCAN_SIZE (float):
        Max scan size in MB for clamscan backend. Default: 2000.
"""

import logging
import os

logger = logging.getLogger("django_clamav.conf")

# Sentinel for "not set"
_UNSET = object()


def _get_django_setting(name, default=_UNSET):
    """Get a setting from Django settings if available, otherwise return default."""
    try:
        from django.conf import settings
        return getattr(settings, name, default)
    except Exception:
        return default


def _get_env(name, default=None):
    """Get an environment variable value."""
    return os.getenv(name, default)


def _to_bool(value):
    """Convert a string value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "t", "y", "yes")
    return bool(value)


def _to_float(value, default, name="setting"):
    """Safely convert a value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"{name} must be a float. Defaulting to {default}.")
        return default


def get_setting(name, default=_UNSET):
    """
    Resolve a django_clamav setting value.

    Priority order:
    1. Django setting with DJANGO_CLAMAV_ prefix (e.g., DJANGO_CLAMAV_ENABLED)
    2. Environment variable with DJANGO_CLAMAV_ prefix
    3. Legacy Django setting (e.g., USE_CLAMAV, CLAMD_URL)
    4. Legacy environment variable
    5. Default value
    """
    prefixed = f"DJANGO_CLAMAV_{name}"

    # 1. Django setting (prefixed)
    value = _get_django_setting(prefixed)
    if value is not _UNSET:
        return value

    # 2. Environment variable (prefixed)
    env_val = _get_env(prefixed)
    if env_val is not None:
        return env_val

    # 3. Legacy mappings
    legacy_map = {
        "ENABLED": ("USE_CLAMAV",),
        "CONNECTION_MODE": ("CLAMD_CONNECTION_MODE",),
        "SOCKET_PATH": ("CLAMD_SOCKET_PATH",),
        "URL": ("CLAMD_URL",),
        "TIMEOUT": ("CLAMD_TIMEOUT",),
    }

    if name in legacy_map:
        for legacy_name in legacy_map[name]:
            # Try Django setting
            val = _get_django_setting(legacy_name)
            if val is not _UNSET:
                return val
            # Try environment variable
            env_val = _get_env(legacy_name)
            if env_val is not None:
                return env_val

    # 4. Default
    if default is not _UNSET:
        return default

    return None


# Resolved settings (computed at import time for Django apps, or on first access)
class ClamAVSettings:
    """Lazy settings object that resolves values on first access."""

    _cache = {}

    @classmethod
    def _reset(cls):
        """Reset cached settings (useful for testing)."""
        cls._cache.clear()

    @property
    def ENABLED(self):
        if "ENABLED" not in self._cache:
            self._cache["ENABLED"] = _to_bool(get_setting("ENABLED", False))
        return self._cache["ENABLED"]

    @property
    def CONNECTION_MODE(self):
        if "CONNECTION_MODE" not in self._cache:
            mode = str(get_setting("CONNECTION_MODE", "host")).strip().lower()
            if mode not in ("socket", "host"):
                logger.warning(
                    "DJANGO_CLAMAV_CONNECTION_MODE must be 'socket' or 'host'. "
                    "Defaulting to 'host'."
                )
                mode = "host"
            self._cache["CONNECTION_MODE"] = mode
        return self._cache["CONNECTION_MODE"]

    @property
    def SOCKET_PATH(self):
        if "SOCKET_PATH" not in self._cache:
            self._cache["SOCKET_PATH"] = str(
                get_setting("SOCKET_PATH", "unix:///var/run/clamav/clamd.ctl")
            )
        return self._cache["SOCKET_PATH"]

    @property
    def URL(self):
        if "URL" not in self._cache:
            self._cache["URL"] = str(
                get_setting("URL", "http://127.0.0.1:3310")
            )
        return self._cache["URL"]

    @property
    def TIMEOUT(self):
        if "TIMEOUT" not in self._cache:
            raw = get_setting("TIMEOUT", 60.0)
            self._cache["TIMEOUT"] = _to_float(raw, 60.0, "DJANGO_CLAMAV_TIMEOUT")
        return self._cache["TIMEOUT"]

    @property
    def STREAM(self):
        if "STREAM" not in self._cache:
            self._cache["STREAM"] = _to_bool(get_setting("STREAM", True))
        return self._cache["STREAM"]

    @property
    def BACKEND(self):
        if "BACKEND" not in self._cache:
            self._cache["BACKEND"] = str(get_setting("BACKEND", "clamd")).strip().lower()
        return self._cache["BACKEND"]

    @property
    def SCAN_ON_UPLOAD(self):
        if "SCAN_ON_UPLOAD" not in self._cache:
            self._cache["SCAN_ON_UPLOAD"] = _to_bool(
                get_setting("SCAN_ON_UPLOAD", False)
            )
        return self._cache["SCAN_ON_UPLOAD"]

    @property
    def RAISE_ON_VIRUS(self):
        if "RAISE_ON_VIRUS" not in self._cache:
            self._cache["RAISE_ON_VIRUS"] = _to_bool(
                get_setting("RAISE_ON_VIRUS", True)
            )
        return self._cache["RAISE_ON_VIRUS"]

    @property
    def SKIP_ON_CONNECTION_ERROR(self):
        if "SKIP_ON_CONNECTION_ERROR" not in self._cache:
            self._cache["SKIP_ON_CONNECTION_ERROR"] = _to_bool(
                get_setting("SKIP_ON_CONNECTION_ERROR", True)
            )
        return self._cache["SKIP_ON_CONNECTION_ERROR"]

    @property
    def MAX_FILE_SIZE(self):
        if "MAX_FILE_SIZE" not in self._cache:
            self._cache["MAX_FILE_SIZE"] = _to_float(
                get_setting("MAX_FILE_SIZE", 2000.0), 2000.0, "DJANGO_CLAMAV_MAX_FILE_SIZE"
            )
        return self._cache["MAX_FILE_SIZE"]

    @property
    def MAX_SCAN_SIZE(self):
        if "MAX_SCAN_SIZE" not in self._cache:
            self._cache["MAX_SCAN_SIZE"] = _to_float(
                get_setting("MAX_SCAN_SIZE", 2000.0), 2000.0, "DJANGO_CLAMAV_MAX_SCAN_SIZE"
            )
        return self._cache["MAX_SCAN_SIZE"]

    def get_scanner_config(self):
        """Build a scanner config dict from the current settings."""
        if self.BACKEND == "clamscan":
            return {
                "backend": "clamscan",
                "max_file_size": self.MAX_FILE_SIZE,
                "max_scan_size": self.MAX_SCAN_SIZE,
            }
        else:
            address = (
                self.SOCKET_PATH
                if self.CONNECTION_MODE == "socket"
                else self.URL
            )
            return {
                "backend": "clamd",
                "address": address,
                "timeout": self.TIMEOUT,
                "stream": self.STREAM,
            }


clamav_settings = ClamAVSettings()
