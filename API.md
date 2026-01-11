# Twistt API Documentation

Twistt exposes an HTTP/WebSocket API for external control (StreamDeck, automation, etc.).

Default port: `7777` (configurable via `TWISTT_SERVER_PORT` or `--server-port`)

## HTTP Endpoints

### GET /api/status

Returns the current state.

**Response:**
```json
{
  "state": "idle" | "recording" | "processing",
  "pipeline": "pipeline-name" | null
}
```

### GET /api/pipelines

Lists available pipelines.

**Response:**
```json
["brainstorm", "translate"]
```

### POST /api/start

Starts recording.

**Request body (optional):**
```json
{
  "pipeline": "pipeline-name"
}
```

**Responses:**
- `200 OK`: Recording started
  ```json
  {"status": "recording", "pipeline": "pipeline-name" | null}
  ```
- `404 Not Found`: Pipeline doesn't exist
  ```json
  {"error": "Pipeline 'unknown' not found"}
  ```
- `409 Conflict`: Already recording
  ```json
  {"error": "Already recording"}
  ```

### POST /api/stop

Stops recording.

**Responses:**
- `200 OK`: Recording stopped
  ```json
  {"status": "stopped"}
  ```
- `409 Conflict`: Not recording
  ```json
  {"error": "Not recording"}
  ```

## WebSocket

### Endpoint

`ws://localhost:7777/api/ws`

### Protocol

1. On connect, server sends current status:
   ```json
   {"state": "idle", "pipeline": null}
   ```

2. Server sends status updates whenever state changes:
   ```json
   {"state": "recording", "pipeline": "brainstorm"}
   ```
   ```json
   {"state": "processing", "pipeline": "brainstorm"}
   ```
   ```json
   {"state": "idle", "pipeline": null}
   ```

### States

| State | Description |
|-------|-------------|
| `idle` | Ready, not recording |
| `recording` | Recording audio |
| `processing` | Transcription or post-treatment in progress |

## Pipelines

Pipelines are `.env` files in the pipeline directory (default: `~/.config/twistt/pipelines/`).

Configure with `TWISTT_PIPELINE_DIR` or `--pipeline-dir`.

### Example pipeline file

`pipelines/brainstorm.env`:
```env
TWISTT_POST_TREATMENT_PROMPT=Reformulate these messy thoughts into clear, structured text.
```

### Overridable parameters

- `TWISTT_POST_TREATMENT_PROMPT` - Post-treatment prompt
- `TWISTT_POST_MODEL` / `TWISTT_POST_TREATMENT_MODEL` - Post-treatment model
- `TWISTT_POST_PROVIDER` / `TWISTT_POST_TREATMENT_PROVIDER` - Post-treatment provider

## Example: StreamDeck integration

```python
import httpx

# Start recording with brainstorm pipeline
httpx.post("http://localhost:7777/api/start", json={"pipeline": "brainstorm"})

# Stop recording
httpx.post("http://localhost:7777/api/stop")
```

## Example: WebSocket client

```python
import asyncio
import websockets

async def monitor():
    async with websockets.connect("ws://localhost:7777/api/ws") as ws:
        async for message in ws:
            print(message)

asyncio.run(monitor())
```
