# AirGap

AirGap — meeting intelligence service: upload a meeting, transcribe it, generate a structured protocol with a local LLM, and export the result.

## Quick start

```bash
cp .env.example .env
./run_airgap.sh
```

The script uses Python 3.11 and installs both the core and STT dependencies into `stt-venv`.

Open `http://127.0.0.1:8000/` and create an account. The protected workspace is available at `/dashboard` and the API documentation at `/docs`.

## Local AI services

Start Ollama and install the lightweight model:

```bash
ollama serve
ollama pull qwen2.5:0.5b
```

Speech-to-text can also be installed manually:

```bash
python -m pip install -r requirements-stt.txt
```

The recommended STT environment is Python 3.11 on Intel macOS. Check the current runtime with `GET /health/models`.

## Speaker diarization (optional)

Diarization uses `pyannote.audio` and is disabled by default because it requires more memory. On Python 3.11, install it with:

```bash
python -m pip install -r requirements-ml.txt
```

Create a Hugging Face read token, accept the conditions for `pyannote/speaker-diarization-3.1` and its dependent models, then add this to `.env`:

```env
DIARIZATION_ENABLED=true
HUGGINGFACE_TOKEN=hf_your_read_token
```

Newly processed meetings will receive labels such as `SPEAKER_00` and `SPEAKER_01`. With `DIARIZATION_ENABLED=false`, the service remains fully usable and labels segments as `UNKNOWN`.

## Processing flow

1. Register or log in.
2. Upload MP3, WAV, M4A, MP4, or WebM from the dashboard.
3. The service starts transcription and stores the transcript in SQLite.
4. Ollama generates summary, decisions, topics, open questions, action items, and risks.
5. Download JSON, CSV, or PDF from the meeting result.

For downstream demos without STT, an authenticated user can provide a prepared transcript:

```http
POST /api/meetings/{id}/transcript
Content-Type: application/json

{"text":"Команда согласовала запуск проекта в понедельник.","language":"ru"}
```

Then call `POST /api/meetings/{id}/analyze`.

## Important endpoints

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
POST /api/meetings
GET  /api/meetings
POST /api/meetings/{id}/process
GET  /api/meetings/{id}
POST /api/meetings/{id}/analyze
GET  /api/meetings/{id}/export/json
GET  /api/meetings/{id}/export/csv
GET  /api/meetings/{id}/export/pdf
POST /api/meetings/{id}/chat
GET  /health/models
```

All meeting endpoints are scoped to the authenticated user.
