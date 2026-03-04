# AccompanAIment API Documentation

This document describes the REST API and WebSocket endpoints for the
AccompanAIment backend service.

## Base URL

```
http://localhost:8000
```

In production, replace with your deployed hostname and ensure HTTPS is used.

## Authentication

All endpoints (except `/health` and `/metrics`) require a valid JWT bearer
token in the `Authorization` header.

### Obtaining a Token

Tokens are issued during user registration or login. The token is a signed
JWT containing the user ID as the `sub` claim.

### Using the Token

Include the token in every request:

```
Authorization: Bearer <your-jwt-token>
```

If the token is missing, expired, or invalid, the API returns a
`401 Unauthorized` response:

```json
{
  "detail": "Not authenticated"
}
```

or:

```json
{
  "detail": "Invalid or expired token"
}
```

### Token Configuration

| Parameter            | Default  | Description                        |
|----------------------|----------|------------------------------------|
| JWT_ALGORITHM        | HS256    | Signing algorithm                  |
| JWT_EXPIRATION_MINUTES | 1440  | Token lifetime in minutes (24h)    |
| JWT_SECRET           | (none)   | Secret key (must be set in .env)   |

---

## Endpoints

### Upload a Song

Upload an audio file for processing. The file is accepted asynchronously
and processing begins via Celery workers.

**Request:**

```
POST /songs/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Parameters:**

| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| file  | file   | yes      | Audio file (MP3, WAV, M4A, or FLAC)  |

**Constraints:**

- Maximum file size: 100 MB
- Maximum audio duration: 600 seconds (10 minutes)
- Accepted MIME types: audio/mpeg, audio/wav, audio/x-m4a, audio/flac

**curl Example:**

```bash
curl -X POST http://localhost:8000/songs/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@my_song.mp3"
```

**Response (202 Accepted):**

```json
{
  "song_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "message": "Upload accepted. Processing will begin shortly."
}
```

**Error Responses:**

| Code | Condition                              |
|------|----------------------------------------|
| 401  | Missing or invalid authentication      |
| 413  | File exceeds 100 MB limit              |
| 422  | Unsupported file format                |

---

### Get Extracted Melody

Retrieve the pitch contour and timing data extracted from a previously
uploaded song by the CREPE melody extraction pipeline.

**Request:**

```
GET /songs/{song_id}/melody
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type   | Description              |
|-----------|--------|--------------------------|
| song_id   | string | UUID of the uploaded song |

**curl Example:**

```bash
curl -X GET http://localhost:8000/songs/a1b2c3d4-e5f6-7890-abcd-ef1234567890/melody \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "song_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "melody": {
    "pitches": [440.0, 493.88, 523.25, 440.0],
    "confidences": [0.95, 0.87, 0.92, 0.89],
    "timestamps": [0.0, 0.5, 1.0, 1.5],
    "sample_rate": 22050,
    "model_capacity": "full"
  }
}
```

**Error Responses:**

| Code | Condition                                         |
|------|---------------------------------------------------|
| 401  | Missing or invalid authentication                 |
| 404  | Song not found or not owned by the current user   |

---

### Generate Piano Accompaniment

Trigger piano accompaniment generation for a song. The generation runs
asynchronously via Celery workers. Connect to the WebSocket endpoint
for real-time progress updates.

**Request:**

```
POST /songs/{song_id}/generate-piano
Content-Type: application/json
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type   | Description              |
|-----------|--------|--------------------------|
| song_id   | string | UUID of the uploaded song |

**Request Body:**

| Field          | Type   | Required | Description                                     |
|----------------|--------|----------|-------------------------------------------------|
| chords         | string | yes      | Chord progression (e.g., "C \| F \| G \| C")   |
| style          | string | yes      | One of: jazz, soulful, rnb, pop, classical      |
| tempo          | int    | no       | BPM (40-300). Auto-detected if omitted.         |
| time_signature | string | no       | e.g., "4/4", "3/4". Defaults to "4/4".          |

**curl Example:**

```bash
curl -X POST http://localhost:8000/songs/a1b2c3d4-e5f6-7890-abcd-ef1234567890/generate-piano \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "chords": "Dm7 | G7 | Cmaj7 | Cmaj7",
    "style": "jazz",
    "tempo": 120,
    "time_signature": "4/4"
  }'
```

**Response (202 Accepted):**

```json
{
  "generation_id": "f1e2d3c4-b5a6-7890-fedc-ba0987654321",
  "status": "processing",
  "message": "Generation started. Connect to WebSocket for progress."
}
```

**Error Responses:**

| Code | Condition                                        |
|------|--------------------------------------------------|
| 401  | Missing or invalid authentication                |
| 404  | Song not found or not owned by the current user  |
| 422  | Invalid chords, style, tempo, or time signature  |

---

### Download a Generation

Download the generated accompaniment in the specified format.

**Request:**

```
GET /songs/{song_id}/generations/{gen_id}/download?format=<format>
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type   | Description                       |
|-----------|--------|-----------------------------------|
| song_id   | string | UUID of the uploaded song         |
| gen_id    | string | UUID of the generation            |

**Query Parameters:**

| Parameter | Type   | Required | Values                           |
|-----------|--------|----------|----------------------------------|
| format    | string | yes      | midi, audio, sheet               |

**Format Details:**

| Format | Content-Type        | Description                |
|--------|---------------------|----------------------------|
| midi   | audio/midi          | MIDI file (.mid)           |
| audio  | audio/wav           | WAV audio rendered via FluidSynth |
| sheet  | application/pdf     | Sheet music PDF via Lilypond      |

**curl Examples:**

```bash
# Download MIDI
curl -X GET "http://localhost:8000/songs/{song_id}/generations/{gen_id}/download?format=midi" \
  -H "Authorization: Bearer <token>" \
  -o accompaniment.mid

# Download audio
curl -X GET "http://localhost:8000/songs/{song_id}/generations/{gen_id}/download?format=audio" \
  -H "Authorization: Bearer <token>" \
  -o accompaniment.wav

# Download sheet music
curl -X GET "http://localhost:8000/songs/{song_id}/generations/{gen_id}/download?format=sheet" \
  -H "Authorization: Bearer <token>" \
  -o accompaniment.pdf
```

**Error Responses:**

| Code | Condition                                        |
|------|--------------------------------------------------|
| 401  | Missing or invalid authentication                |
| 404  | Song or generation not found                     |
| 422  | Invalid format parameter                         |

---

### Submit Feedback

Submit a multi-dimensional rating for a generated accompaniment.

**Request:**

```
POST /generations/{gen_id}/feedback
Content-Type: application/json
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type   | Description            |
|-----------|--------|------------------------|
| gen_id    | string | UUID of the generation |

**Request Body:**

| Field               | Type   | Required | Description                     |
|---------------------|--------|----------|---------------------------------|
| rating              | int    | yes      | Overall rating (1-5)            |
| musicality_score    | int    | no       | Musicality rating (1-5)         |
| style_match_score   | int    | no       | Style accuracy rating (1-5)     |
| fit_to_melody_score | int    | no       | Melody fit rating (1-5)         |
| comment             | string | no       | Free-text comment (max 2000 chars) |

**curl Example:**

```bash
curl -X POST http://localhost:8000/generations/f1e2d3c4-b5a6-7890-fedc-ba0987654321/feedback \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "musicality_score": 5,
    "style_match_score": 4,
    "fit_to_melody_score": 3,
    "comment": "Good jazz voicings but could follow the melody contour more closely."
  }'
```

**Response (201 Created):**

```json
{
  "feedback_id": "d4c3b2a1-0987-6543-2109-876543210fed",
  "status": "submitted"
}
```

**Error Responses:**

| Code | Condition                                |
|------|------------------------------------------|
| 401  | Missing or invalid authentication        |
| 422  | Invalid rating value or field format     |

---

### Get Generation History

Retrieve the current user's generation history, ordered by creation
time (newest first).

**Request:**

```
GET /generations
Authorization: Bearer <token>
```

**curl Example:**

```bash
curl -X GET http://localhost:8000/generations \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "generations": [
    {
      "generation_id": "f1e2d3c4-b5a6-7890-fedc-ba0987654321",
      "song_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "style": "jazz",
      "created_at": "2026-03-01T14:30:00Z"
    },
    {
      "generation_id": "a9b8c7d6-e5f4-3210-9876-543210abcdef",
      "song_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "style": "pop",
      "created_at": "2026-02-28T10:15:00Z"
    }
  ]
}
```

---

### Prometheus Metrics

Exposes application metrics in Prometheus format. No authentication
required.

**Request:**

```
GET /metrics
```

**curl Example:**

```bash
curl -X GET http://localhost:8000/metrics
```

**Response (200 OK):**

```
# HELP accompaniment_uploads_total Total number of song uploads
# TYPE accompaniment_uploads_total counter
accompaniment_uploads_total 42
# HELP accompaniment_generations_total Total number of generation requests
# TYPE accompaniment_generations_total counter
accompaniment_generations_total 35
...
```

---

## WebSocket Protocol

Real-time progress updates for song processing and generation are
delivered via WebSocket.

### Connecting

```
WS /songs/{song_id}/status
```

**JavaScript Example:**

```javascript
const ws = new WebSocket("ws://localhost:8000/songs/a1b2c3d4/status");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}% -- ${data.step}`);
};

ws.onclose = () => {
  console.log("Connection closed");
};
```

### Message Format

The server sends JSON messages with the following structure:

```json
{
  "song_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "progress": 45,
  "step": "melody_extraction",
  "eta_seconds": 12
}
```

**Fields:**

| Field       | Type       | Description                                     |
|-------------|------------|-------------------------------------------------|
| song_id     | string     | UUID of the song being processed                |
| progress    | int        | Completion percentage (0-100)                   |
| step        | string     | Current pipeline step name                      |
| eta_seconds | int/null   | Estimated seconds remaining (null if unknown)   |

### Pipeline Steps

Progress updates are sent at each stage of the processing pipeline:

| Step                 | Description                           | Typical Progress |
|----------------------|---------------------------------------|------------------|
| upload_processing    | Normalizing and resampling audio      | 0-10%            |
| melody_extraction    | Running CREPE pitch detection         | 10-40%           |
| chord_validation     | Validating chord progression input    | 40-45%           |
| voicing_generation   | LLM agent generating piano voicings   | 45-70%           |
| midi_generation      | Creating MIDI file from voicings      | 70-80%           |
| audio_rendering      | FluidSynth MIDI-to-WAV conversion     | 80-90%           |
| sheet_generation     | Lilypond PDF sheet music rendering    | 90-98%           |
| complete             | All outputs ready for download        | 100%             |

### Connection Behavior

- Multiple clients can connect to the same song_id simultaneously.
- The server automatically cleans up broken connections.
- After the `complete` step is sent, the server closes the connection.
- If the song_id does not exist, the connection is accepted but no
  messages are sent until processing begins.

---

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Error Codes

| Code | Meaning                | Common Causes                           |
|------|------------------------|-----------------------------------------|
| 400  | Bad Request            | Malformed request body                  |
| 401  | Unauthorized           | Missing, expired, or invalid JWT        |
| 404  | Not Found              | Resource does not exist or access denied|
| 413  | Payload Too Large      | Upload exceeds 100 MB                   |
| 422  | Unprocessable Entity   | Validation error in request data        |
| 429  | Too Many Requests      | Rate limit exceeded                     |
| 500  | Internal Server Error  | Unexpected server-side failure          |

---

## Rate Limiting

The API applies rate limits per user (identified by JWT subject):

| Endpoint          | Limit             |
|-------------------|-------------------|
| POST /songs/upload | 10 per minute    |
| POST /generate-piano | 20 per minute |
| All other endpoints | 100 per minute  |

Exceeded limits return a `429 Too Many Requests` response.
