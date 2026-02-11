# ClamAV Scanning Microservice

A standalone HTTP microservice for virus scanning using ClamAV, built with FastAPI.

## Quick Start

```bash
# Start both ClamAV daemon and the scanning API
docker compose up -d

# Wait for ClamAV to initialize (virus DB download takes ~2 min on first start)
docker compose logs -f clamav
```

## API Usage

### Scan a file

```bash
curl -X POST http://localhost:8000/scan \
  -F "file=@document.pdf"
```

Response:
```json
{
  "filename": "document.pdf",
  "status": "OK",
  "details": null,
  "is_clean": true,
  "scanned_at": "2026-02-11T10:30:00.000000"
}
```

### Health check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "message": "PONG",
  "timestamp": "2026-02-11T10:30:00.000000"
}
```

### ClamAV info

```bash
curl http://localhost:8000/info
```

Response:
```json
{
  "name": "ClamAV (clamd)",
  "version": "ClamAV 1.4.3",
  "virus_definitions": "27816/2025-11-07",
  "service_version": "1.0.0"
}
```

### API docs (Swagger)

Open http://localhost:8000/docs in your browser.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAMAV_ADDRESS` | `http://clamav:3310` | ClamAV daemon address |
| `CLAMAV_TIMEOUT` | `60` | Connection timeout (seconds) |
| `CLAMAV_BACKEND` | `clamd` | Backend: `clamd` or `clamscan` |

## Integration Examples

### Python (requests)

```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/scan",
        files={"file": ("document.pdf", f)},
    )

result = response.json()
if result["is_clean"]:
    print("File is clean!")
else:
    print(f"Virus detected: {result['details']}")
```

### Node.js (fetch)

```javascript
const fs = require('fs');
const FormData = require('form-data');

const form = new FormData();
form.append('file', fs.createReadStream('document.pdf'));

const response = await fetch('http://localhost:8000/scan', {
    method: 'POST',
    body: form,
});

const result = await response.json();
console.log(result.is_clean ? 'Clean!' : `Virus: ${result.details}`);
```

### cURL (shell script)

```bash
#!/bin/bash
RESULT=$(curl -s -X POST http://localhost:8000/scan -F "file=@$1")
IS_CLEAN=$(echo "$RESULT" | jq -r '.is_clean')

if [ "$IS_CLEAN" = "true" ]; then
    echo "File is clean."
else
    echo "WARNING: Virus detected!"
    echo "$RESULT" | jq .
fi
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (needs ClamAV daemon running)
CLAMAV_ADDRESS=http://localhost:3310 uvicorn app:app --reload
```
