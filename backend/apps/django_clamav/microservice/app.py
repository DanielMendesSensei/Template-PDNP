"""
ClamAV Scanning Microservice - FastAPI

A standalone HTTP service for virus scanning. Can be used by any application
regardless of language or framework.

Endpoints:
    POST /scan       -- Scan an uploaded file
    GET  /health     -- Check ClamAV daemon health
    GET  /info       -- Get ClamAV version information
    GET  /           -- Service info

Run:
    uvicorn app:app --host 0.0.0.0 --port 8000

Environment Variables:
    CLAMAV_ADDRESS    -- ClamAV daemon address (default: http://clamav:3310)
    CLAMAV_TIMEOUT    -- Connection timeout in seconds (default: 60)
    CLAMAV_BACKEND    -- Backend: 'clamd' or 'clamscan' (default: clamd)
"""

import logging
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import django_clamav
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",".."))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from django_clamav.clamd import CommunicationError
from django_clamav.scanner import ClamdScanner, ClamdScannerConfig, get_scanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clamav-microservice")

# Configuration from environment
CLAMAV_ADDRESS = os.getenv("CLAMAV_ADDRESS", "http://clamav:3310")
CLAMAV_TIMEOUT = float(os.getenv("CLAMAV_TIMEOUT", "60"))
CLAMAV_BACKEND = os.getenv("CLAMAV_BACKEND", "clamd")

app = FastAPI(
    title="ClamAV Scanning Microservice",
    description="A standalone microservice for virus scanning using ClamAV.",
    version="1.0.0",
)


# Response models
class ScanResponse(BaseModel):
    filename: str
    status: str
    details: str | None = None
    is_clean: bool | None = None
    scanned_at: str


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str


class InfoResponse(BaseModel):
    name: str
    version: str
    virus_definitions: str | None = None
    service_version: str = "1.0.0"


class ServiceInfo(BaseModel):
    name: str = "ClamAV Scanning Microservice"
    version: str = "1.0.0"
    status: str = "running"
    endpoints: list[str]


def _get_scanner():
    """Create a scanner from environment configuration."""
    if CLAMAV_BACKEND == "clamd":
        config = ClamdScannerConfig(
            backend="clamd",
            address=CLAMAV_ADDRESS,
            timeout=CLAMAV_TIMEOUT,
            stream=True,
        )
    else:
        config = {"backend": "clamscan"}
    return get_scanner(config)


@app.get("/", response_model=ServiceInfo)
async def root():
    """Service information."""
    return ServiceInfo(
        endpoints=["/scan", "/health", "/info"],
    )


@app.post("/scan", response_model=ScanResponse)
async def scan_file(file: UploadFile = File(...)):
    """
    Scan an uploaded file for viruses.

    Returns the scan result including whether the file is clean.
    """
    scanner = _get_scanner()

    if not isinstance(scanner, ClamdScanner):
        raise HTTPException(
            status_code=501,
            detail="Stream scanning not supported with current backend.",
        )

    client = scanner.get_client()

    try:
        result = client.instream(file.file)
        stream_result = result.get("stream")

        if stream_result is None:
            return ScanResponse(
                filename=file.filename or "unknown",
                status="UNKNOWN",
                details=None,
                is_clean=None,
                scanned_at=datetime.utcnow().isoformat(),
            )

        scan_status, details = stream_result
        return ScanResponse(
            filename=file.filename or "unknown",
            status=scan_status,
            details=details,
            is_clean=scan_status.upper() == "OK",
            scanned_at=datetime.utcnow().isoformat(),
        )

    except CommunicationError as e:
        logger.error(f"ClamAV communication error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"ClamAV service unavailable: {e}",
        )
    except Exception as e:
        logger.error(f"Scan error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scanning error: {e}",
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check ClamAV daemon availability."""
    scanner = _get_scanner()

    if not isinstance(scanner, ClamdScanner):
        return HealthResponse(
            status="ok",
            message="Using clamscan binary backend.",
            timestamp=datetime.utcnow().isoformat(),
        )

    client = scanner.get_client()
    try:
        pong = client.ping()
        return HealthResponse(
            status="ok",
            message=pong.strip(),
            timestamp=datetime.utcnow().isoformat(),
        )
    except CommunicationError as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/info", response_model=InfoResponse)
async def clamav_info():
    """Get ClamAV version and virus definition information."""
    scanner = _get_scanner()

    try:
        info = scanner.info()
        return InfoResponse(
            name=info.name,
            version=info.version,
            virus_definitions=info.virus_definitions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot get ClamAV info: {e}",
        )
