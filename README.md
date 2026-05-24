# vc-rag-service

Microservice for vehicle image embedding and similarity search, built with Python and FastAPI.

Part of the **vehicle-collector** ecosystem. Receives vehicle photos from the Kotlin backend, generates vector embeddings using a local CLIP model, stores them in PostgreSQL with pgvector, and provides similarity search capabilities for vehicle recognition.

---

## What it does

- Accepts batches of vehicle photo references (640px thumbnails) from the Kotlin vehicle-collector service
- Generates 512-dimensional embeddings locally using the CLIP model (HuggingFace Transformers) — no external API calls
- Stores embeddings and metadata in PostgreSQL + pgvector
- Runs a background job (APScheduler) to process queued images asynchronously
- Performs cosine similarity search to find visually similar vehicles
- Manages recognition candidates and their verification status

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Server | Uvicorn |
| ORM | SQLAlchemy (sync) |
| Database | PostgreSQL + pgvector |
| Embedding model | HuggingFace Transformers — CLIP (`openai/clip-vit-base-patch32`, 512 dim) |
| Image loading | Pillow |
| Background jobs | APScheduler |
| Config | pydantic-settings |

---

## Requirements

- **Python** 3.12 or higher
- **PostgreSQL** 14+ with [pgvector extension](https://github.com/pgvector/pgvector)

---

## Local setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd vc-rag-service
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
```

> **Note:** `torch` is included as a dependency (~2GB). First install may take a few minutes.

For development tools (pytest, httpx):

```bash
pip install -e ".[dev]"
```

### 4. Configure environment

Copy the example env file and fill in your local values:

```bash
cp .env.example .env.local
```

`.env.local` contents:

```env
APP_ENV=local
DATABASE_URL=postgresql+psycopg://vc:change-me@localhost:5433/vc_rag
POOL_SIZE=10

# Optional — override the default embedding model (see app/core/config.py for available options)
# EMBEDDING_MODEL=openai/clip-vit-base-patch32
```

### 5. Start PostgreSQL

Make sure PostgreSQL is running with the credentials matching your `.env.local`.
The pgvector extension is created automatically on first startup — no manual setup needed.

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

Application starts at: `http://127.0.0.1:8000`

---

## API documentation

Swagger UI is available at:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

---

## Available endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/health/info` | Application info |
| POST | `/api/v1/ingest/images` | Ingest batch of images from Kotlin VC |

---

## Project structure

```
vc-rag-service/
├── app/
│   ├── main.py                          # FastAPI app, startup, exception handlers
│   ├── core/
│   │   ├── config.py                    # Settings (pydantic-settings, .env.local)
│   │   └── database.py                  # SQLAlchemy engine, session factory
│   ├── api/
│   │   └── routes/
│   │       ├── health/                  # GET /health, GET /health/info
│   │       └── ingestimage/             # POST /ingest/images
│   ├── service/
│   │   └── image_ingest_service.py      # Ingest orchestration
│   ├── repository/
│   │   ├── entities.py                  # SQLAlchemy models (ImageIndex, RecognitionState, ...)
│   │   ├── image_index_repository.py
│   │   └── recognition_state_repository.py
│   ├── model/
│   │   └── app_info.py
│   ├── jobs/                            # APScheduler background jobs (coming soon)
│   └── exceptions.py
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Embedding model

The default model is `openai/clip-vit-base-patch32` (512 dimensions, ~600MB RAM).
It is downloaded automatically from HuggingFace on first use and cached locally.

The model is loaded **once at application startup** and kept in memory for the lifetime of the process.

> **Important:** Changing the embedding model requires re-vectorizing all existing records in the database.

Available alternatives (configured via `EMBEDDING_MODEL` env variable):

| Model | Dimensions | RAM | Notes |
|-------|-----------|-----|-------|
| `openai/clip-vit-base-patch32` | 512 | ~600MB | Default — fast on CPU, good baseline |
| `openai/clip-vit-large-patch14` | 768 | ~1.7GB | Better detail recognition |
| `google/siglip-base-patch16-224` | 768 | ~600MB | Newer architecture, stronger semantic quality |
