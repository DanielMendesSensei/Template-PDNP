"""A client for the ClamAV daemon (clamd), supporting both TCP and Unix socket
connections.

This module stays as close as possible to its original counterpart, the clamd
project on which this code is based, to maintain backward compatibility.

This module has NO Django dependencies and can be used standalone in any Python project.
"""

import contextlib
import logging
import re
import socket
import struct
from typing import Any, BinaryIO, Optional, Union

logger = logging.getLogger("django_clamav.clamd")

# Regular expression to parse scan results
scan_response = re.compile(
    r"^(?P<path>[^:]+): ((?P<virus>.+?) )?(?P<status>(FOUND|OK|ERROR))$"
)

# Types
ScanStatus = str
ScanResult = tuple[ScanStatus, Optional[str]]
ScanResults = dict[str, ScanResult]


class ClamdError(Exception):
    """Base exception for ClamAV daemon errors."""
    pass


class ResponseError(ClamdError):
    """Raised when the ClamAV daemon returns an unexpected response."""
    pass


class BufferTooLongError(ResponseError):
    """Raised when INSTREAM buffer length exceeds StreamMaxLength in clamd.conf."""
    pass


class CommunicationError(ClamdError):
    """Raised on communication errors with the ClamAV daemon."""
    pass


class ClamdNetworkSocket:
    """
    Client for communicating with clamd via a TCP network socket.

    Example::

        client = ClamdNetworkSocket(host="127.0.0.1", port=3310, timeout=30)
        print(client.ping())   # "PONG"
        print(client.version()) # "ClamAV 1.4.3/..."
        result = client.instream(open("somefile.pdf", "rb"))
        # {'stream': ('OK', None)}
    """

    def __init__(
        self, host: str = "127.0.0.1", port: int = 3310, timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the network socket client.

        Args:
            host: Hostname or IP address of the clamd server.
            port: TCP port of the clamd server.
            timeout: Socket timeout in seconds (None for no timeout).
        """
        self.host = host
        self.port = port
        self.timeout = timeout

    def _init_socket(self) -> None:
        """Initialize and connect the socket."""
        try:
            logger.debug(f"ClamdNetworkSocket._init_socket: connecting to {self.host}:{self.port}")
            self.clamd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clamd_socket.settimeout(self.timeout)
            self.clamd_socket.connect((self.host, self.port))
            logger.debug("ClamdNetworkSocket._init_socket: connected")
        except OSError as err:
            raise CommunicationError(self._error_message(err)) from err

    def _error_message(self, exception: BaseException) -> str:
        if len(exception.args) == 1:
            return f"Error connecting to {self.host}:{self.port}. {exception.args[0]}."
        else:
            return f"Error {exception.args[0]} connecting {self.host}:{self.port}. {exception.args[1]}."

    def ping(self) -> str:
        """Ping the clamd daemon. Returns 'PONG' if alive."""
        return self._basic_command("PING")

    def version(self) -> str:
        """Get the version string from the clamd daemon."""
        return self._basic_command("VERSION")

    def reload(self) -> str:
        """Reload the clamd virus database."""
        return self._basic_command("RELOAD")

    def shutdown(self) -> None:
        """Force clamd to shutdown and exit."""
        try:
            self._init_socket()
            self._send_command("SHUTDOWN")
        finally:
            self._close_socket()

    def scan(self, file: str) -> ScanResults:
        """Scan a file by its absolute path on the clamd host."""
        return self._file_system_scan("SCAN", file)

    def contscan(self, file: str) -> ScanResults:
        """Scan a file/directory, continue on virus found."""
        return self._file_system_scan("CONTSCAN", file)

    def multiscan(self, file: str) -> ScanResults:
        """Scan a file/directory using multiple threads."""
        return self._file_system_scan("MULTISCAN", file)

    def _basic_command(self, command: str) -> str:
        """Send a command to clamd and return the reply."""
        self._init_socket()
        try:
            logger.debug(f"ClamdNetworkSocket._basic_command: {command}")
            self._send_command(command)
            response = self._recv_response()
            logger.debug(f"ClamdNetworkSocket._basic_command response: {response}")
            if response is None:
                raise ResponseError()
            error = response.rsplit("ERROR", 1)
            if len(error) > 1:
                raise ResponseError(error[0])
            else:
                return error[0]
        finally:
            self._close_socket()

    def _file_system_scan(self, command: str, file: str) -> ScanResults:
        """Scan a file or directory on the clamd host filesystem."""
        try:
            self._init_socket()
            self._send_command(command, file)
            dr = {}
            response = self._recv_response_multiline()
            if response is None:
                raise ResponseError()
            for result in response.split("\n"):
                if result:
                    filename, reason, status = self._parse_response(result)
                    dr[filename] = (status, reason)
            return dr
        finally:
            self._close_socket()

    def instream(self, buff: BinaryIO) -> ScanResults:
        """
        Scan a file-like buffer via the INSTREAM command.

        Args:
            buff: A file-like object opened in binary mode.

        Returns:
            Dict with scan results, e.g. ``{'stream': ('OK', None)}``.

        Raises:
            BufferTooLongError: If buffer exceeds clamd limits.
            CommunicationError: On connection issues.
        """
        try:
            logger.debug("ClamdNetworkSocket.instream: scanning buffer")
            self._init_socket()
            self._send_command("INSTREAM")
            max_chunk_size = 1024  # Must be < StreamMaxLength in clamd.conf
            chunk = buff.read(max_chunk_size)
            while chunk:
                size = struct.pack(b"!L", len(chunk))
                self.clamd_socket.send(size + chunk)
                chunk = buff.read(max_chunk_size)
            self.clamd_socket.send(struct.pack(b"!L", 0))
            result = self._recv_response()
            logger.debug(f"ClamdNetworkSocket.instream response: {result}")
            if len(result) > 0:
                if result == "INSTREAM size limit exceeded. ERROR":
                    raise BufferTooLongError(result)
                filename, reason, status = self._parse_response(result)
                return {filename: (status, reason)}
            else:
                return {}
        finally:
            self._close_socket()

    def stats(self) -> str:
        """Get clamd daemon statistics."""
        self._init_socket()
        try:
            self._send_command("STATS")
            return self._recv_response_multiline()
        finally:
            self._close_socket()

    def _send_command(self, cmd: str, *args: str) -> None:
        concat_args = ""
        if args:
            concat_args = " " + " ".join(args)
        send = f"n{cmd}{concat_args}\n".encode()
        self.clamd_socket.send(send)

    def _recv_response(self) -> str:
        try:
            with contextlib.closing(self.clamd_socket.makefile("rb")) as f:
                return f.readline().decode("utf-8").strip()
        except (OSError, socket.timeout) as err:
            raise CommunicationError(
                f"Error while reading from socket: {err.args}"
            ) from err

    def _recv_response_multiline(self) -> str:
        try:
            with contextlib.closing(self.clamd_socket.makefile("rb")) as f:
                return f.read().decode("utf-8")
        except (OSError, socket.timeout) as err:
            raise CommunicationError(
                f"Error while reading from socket: {err.args}"
            ) from err

    def _close_socket(self) -> None:
        self.clamd_socket.close()

    def _parse_response(self, msg: str) -> tuple[Union[str, Any], ...]:
        if match := scan_response.match(msg):
            return match.group("path", "virus", "status")
        else:
            raise ResponseError(msg.rsplit("ERROR", 1)[0])


class ClamdUnixSocket(ClamdNetworkSocket):
    """
    Client for communicating with clamd via a Unix domain socket.

    Example::

        client = ClamdUnixSocket(path="/var/run/clamav/clamd.ctl", timeout=30)
        print(client.ping())
    """

    def __init__(
        self, path: str = "/var/run/clamav/clamd.ctl", timeout: Optional[int] = None
    ) -> None:
        """
        Initialize the Unix socket client.

        Args:
            path: Path to the clamd Unix socket file.
            timeout: Socket timeout in seconds (None for no timeout).
        """
        scheme = "unix://"
        if path.startswith(scheme):
            path = path[len(scheme):]
        self.unix_socket = path
        self.timeout = timeout

    def _init_socket(self) -> None:
        try:
            self.clamd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.clamd_socket.connect(self.unix_socket)
            self.clamd_socket.settimeout(self.timeout)
        except OSError as err:
            raise CommunicationError(self._error_message(err)) from err

    def _error_message(self, exception: BaseException) -> str:
        if len(exception.args) == 1:
            return f"Error connecting to {self.unix_socket}. {exception.args[0]}."
        else:
            return f"Error {exception.args[0]} connecting {self.unix_socket}. {exception.args[1]}."
