"""A general-purpose scanner compatible with both ``clamd`` and ``clamscan``.

This module has NO Django dependencies and can be used standalone in any Python project.

Usage::

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
    print(result.passed)    # True/False/None
    print(result.state)     # "OK", "FOUND", "ERROR"
    print(result.details)   # Virus name or error message
"""

import abc
import logging
import re
from dataclasses import dataclass
from errno import EPIPE
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Any, Literal, Optional, TypedDict, Union, cast
from urllib.parse import urlparse

from django_clamav.clamd import (
    BufferTooLongError, ClamdNetworkSocket, ClamdUnixSocket, CommunicationError, ScanResults
)

logger = logging.getLogger("django_clamav.scanner")

ProgramName = Literal[
    "ClamAV (clamd)",
    "ClamAV (clamscan)",
]


@dataclass
class ScannerInfo:
    """
    Provides information of the ClamAV backend.

    Attributes:
        name: The program name identifier.
        version: The ClamAV version string.
        virus_definitions: The virus definitions version or None.
    """

    name: ProgramName
    version: str
    virus_definitions: Optional[str]


ScanResultState = Optional[Literal["ERROR", "OK", "FOUND"]]
ScanResultDetails = Optional[str]


@dataclass
class ScanResult:
    """
    Represents the result of a file scan operation.

    Attributes:
        filename: The name of the file scanned.
        state: The scan result state: "ERROR", "OK", "FOUND", or None.
        details: Error messages, detected threats, or additional information.
        err: The exception object if an error occurred.
    """

    filename: str
    state: ScanResultState
    details: ScanResultDetails
    err: Optional[Exception]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ScanResult):
            return NotImplemented
        return (
            self.filename == other.filename
            and self.state == other.state
            and self.details == other.details
            and str(self.err) == str(other.err)
        )

    def update(
        self,
        state: ScanResultState,
        details: ScanResultDetails,
        err: Optional[Exception] = None,
    ) -> "ScanResult":
        self.state = state
        self.details = details
        self.err = err
        return self

    @property
    def passed(self) -> Optional[bool]:
        """Indicates whether the file passed the virus scan.

        Returns:
            True if clean, False if infected/error, None if inconclusive
            (e.g., connection issues, buffer too long).
        """
        if self.err is None:
            return self.state == "OK"
        elif isinstance(self.err, (BufferTooLongError, CommunicationError)):
            return None
        elif isinstance(self.err, OSError) and self.err.errno == EPIPE:
            return None
        else:
            return False


class Scanner(abc.ABC):
    """Abstract base class for ClamAV scanners."""

    _info: dict[ProgramName, ScannerInfo]
    _program: ProgramName

    @abc.abstractmethod
    def scan(self, filename: str) -> ScanResult:
        """Scan a file and return the result."""

    def info(self) -> ScannerInfo:
        """Fetch information of the current backend."""
        if not hasattr(self, "_info"):
            self._info = {}
        try:
            return self._info[self._program]
        except KeyError:
            self._info[self._program] = self._parse_version(self._get_version())
            return self._info[self._program]

    @abc.abstractmethod
    def _get_version(self) -> str:
        """Return the program version details."""

    def _parse_version(self, version: str) -> ScannerInfo:
        parts = version.strip().split("/")
        n = len(parts)
        if n == 1:
            version = parts[0]
            if re.match("^ClamAV", version):
                return ScannerInfo(self._program, version, None)
        elif n == 3:
            version, defs, date = parts
            return ScannerInfo(self._program, version, f"{defs}/{date}")
        raise ValueError("Cannot extract scanner information.")


class ClamdScannerConfig(TypedDict, total=False):
    """Configuration for the clamd scanner backend."""
    backend: Literal["clamd"]
    address: str
    timeout: float
    stream: bool
    host: str
    port: int


class ClamdScanner(Scanner):
    """Scanner that communicates with the ClamAV daemon (clamd)."""

    _program = "ClamAV (clamd)"

    def __init__(self, config: ClamdScannerConfig):
        self.address = config.get("address", "unix:///var/run/clamav/clamd.ctl")
        logger.debug(f"ClamdScanner.__init__: address={self.address}")
        self.timeout = config.get("timeout", float(86400))
        self.stream = config.get("stream", True)
        self.client = self.get_client()

    def get_client(self) -> Union["ClamdNetworkSocket", "ClamdUnixSocket"]:
        """Create the appropriate clamd client based on the configured address."""
        logger.debug(f"ClamdScanner.get_client: address={self.address}")
        parsed = urlparse(self.address, scheme="dummy")
        if parsed.scheme == "unix" or not parsed.hostname:
            return ClamdUnixSocket(path=self.address, timeout=int(self.timeout))
        elif parsed.hostname and parsed.port:
            return ClamdNetworkSocket(
                host=parsed.hostname, port=parsed.port, timeout=self.timeout
            )
        else:
            raise ValueError(f"Invalid address format: {self.address}")

    def scan(self, filename: str) -> ScanResult:
        result = ScanResult(filename=filename, state=None, details=None, err=None)
        method_name = "_pass_by_stream" if self.stream else "_pass_by_reference"
        report_key = "stream" if self.stream else filename
        try:
            method = getattr(self, method_name)
            report = method(filename)
        except Exception as err:
            return result.update(state="ERROR", details=str(err), err=err)
        file_report = report.get(report_key)
        if file_report is None:
            return result
        state, details = file_report
        return result.update(state, details)

    def _get_version(self) -> str:
        return self.client.version()

    def _pass_by_reference(self, filename: str) -> ScanResults:
        return self.client.scan(filename)

    def _pass_by_stream(self, filename: str) -> ScanResults:
        return self.client.instream(open(filename, "rb"))


class ClamscanScannerConfig(TypedDict, total=False):
    """Configuration for the clamscan binary scanner backend."""
    backend: Literal["clamscan"]
    max_file_size: float
    max_scan_size: float


class ClamscanScanner(Scanner):
    """Scanner that uses the clamscan command-line binary."""

    _program = "ClamAV (clamscan)"
    _command = "clamscan"

    found_pattern = re.compile(r":\s([A-Za-z0-9._-]+)\sFOUND")

    def __init__(self, config: ClamscanScannerConfig) -> None:
        self.max_file_size = config.get("max_file_size", float(2000))
        self.max_scan_size = config.get("max_scan_size", float(2000))

    def _call(self, *args: str) -> bytes:
        return check_output((self._command,) + args, stderr=STDOUT)

    def scan(self, filename: str) -> ScanResult:
        result = ScanResult(filename=filename, state=None, details=None, err=None)
        max_file_size = f"--max-filesize={int(self.max_file_size)}M"
        max_scan_size = f"--max-scansize={int(self.max_scan_size)}M"
        try:
            self._call(max_file_size, max_scan_size, "--no-summary", filename)
        except CalledProcessError as err:
            if err.returncode == 1:
                result.update("FOUND", self._parse_found(err.output))
            else:
                result.update("ERROR", self._parse_error(err.output))
        else:
            result.update("OK", None)
        return result

    def _get_version(self) -> str:
        return self._call("-V").decode("utf-8")

    def _parse_error(self, output: Any) -> Optional[str]:
        if output is None or not isinstance(output, bytes):
            return None
        try:
            decoded: str = output.decode("utf-8")
            return decoded.split("\n")[0]
        except Exception:
            return None

    def _parse_found(self, output: Any) -> Optional[str]:
        if output is None or not isinstance(output, bytes):
            return None
        try:
            stdout = output.decode("utf-8")
            match = self.found_pattern.search(stdout)
            return match.group(1) if match else None
        except Exception:
            return None


ScannerConfig = Union[ClamdScannerConfig, ClamscanScannerConfig]


def get_scanner(config: Optional[ScannerConfig] = None) -> Scanner:
    """
    Factory function to create the appropriate scanner.

    Args:
        config: Scanner configuration dict. If None, defaults to clamscan backend.

    Returns:
        A Scanner instance (ClamdScanner or ClamscanScanner).

    Raises:
        ValueError: If the backend type is not supported.

    Example::

        scanner = get_scanner({"backend": "clamd", "address": "http://localhost:3310"})
        result = scanner.scan("/path/to/file")
    """
    if config is None:
        config = {"backend": "clamscan"}
    logger.debug(f"get_scanner: config={config}")
    backend = config.get("backend")
    if backend == "clamscan":
        return ClamscanScanner(cast(ClamscanScannerConfig, config))
    elif backend == "clamd":
        return ClamdScanner(cast(ClamdScannerConfig, config))
    raise ValueError(f"Unsupported backend type: {backend}")
