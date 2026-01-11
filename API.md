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

### Status Endpoint

`ws://localhost:7777/api/ws`

Broadcasts status changes to all connected clients.

**Protocol:**

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

### Pipeline Transcription Endpoint

`ws://localhost:7777/api/ws/pipelines/{pipeline_name}`

Receives transcription output for a specific pipeline. Used when `OUTPUT_TARGET=websocket` is set in the pipeline.

**Protocol:**

1. On connect, server confirms the pipeline:
   ```json
   {"type": "connected", "pipeline": "commands"}
   ```

2. Server sends transcription updates:
   ```json
   {"type": "transcription", "text": "open terminal", "final": false}
   ```
   ```json
   {"type": "transcription", "text": "open a terminal please", "final": true}
   ```

3. Server sends end signal when capture session is complete:
   ```json
   {"type": "end"}
   ```

**Error:** If pipeline doesn't exist, connection is closed with code `4004`.

### States

| State | Description |
|-------|-------------|
| `idle` | Ready, not recording |
| `recording` | Recording audio |
| `processing` | Transcription or post-treatment in progress |

## Pipelines

Pipelines are `.env` files in the pipeline directory (default: `~/.config/twistt/pipelines/`).

Configure with `TWISTT_PIPELINE_DIR` or `--pipeline-dir`.

### Example pipeline files

`pipelines/brainstorm.env`:
```env
TWISTT_POST_TREATMENT_PROMPT=Reformulate these messy thoughts into clear, structured text.
```

`pipelines/commands.env` (WebSocket output):
```env
TWISTT_OUTPUT_TARGET=websocket
TWISTT_POST_TREATMENT_PROMPT=Reformulate as a single imperative command. Remove hesitations, questions, politeness. Return only the command, one sentence.
TWISTT_NO_INDICATOR=yes
```

### Overridable parameters

- `TWISTT_POST_TREATMENT_PROMPT` - Post-treatment prompt
- `TWISTT_POST_MODEL` / `TWISTT_POST_TREATMENT_MODEL` - Post-treatment model
- `TWISTT_POST_PROVIDER` / `TWISTT_POST_TREATMENT_PROVIDER` - Post-treatment provider
- `TWISTT_OUTPUT_TARGET` - Output destination: `keyboard` (default) or `websocket`
- `TWISTT_NO_INDICATOR` - Disable indicator: `yes` or `no`
- `TWISTT_PASTE_METHOD` - Paste method: `clipboard`, `primary`, `xdotool`, `ydotool`

## Example: StreamDeck integration

```python
import httpx

# Start recording with brainstorm pipeline
httpx.post("http://localhost:7777/api/start", json={"pipeline": "brainstorm"})

# Stop recording
httpx.post("http://localhost:7777/api/stop")
```

## Example: WebSocket status monitor

```python
import asyncio
import websockets

async def monitor():
    async with websockets.connect("ws://localhost:7777/api/ws") as ws:
        async for message in ws:
            print(message)

asyncio.run(monitor())
```

## Example: Command listener

A background program that listens to the "commands" pipeline and executes voice commands:

```python
import asyncio
import json
import websockets

async def command_listener():
    uri = "ws://localhost:7777/api/ws/pipelines/commands"
    async with websockets.connect(uri) as ws:
        print("Connected to commands pipeline")
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "transcription" and data["final"]:
                command = data["text"].strip().lower()
                print(f"Command: {command}")
                # Execute command...
            elif data["type"] == "end":
                print("Session ended")

asyncio.run(command_listener())
```
