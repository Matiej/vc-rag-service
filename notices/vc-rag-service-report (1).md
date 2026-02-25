# VC-RAG-SERVICE — Raport Planowania Projektu

**Data:** 2026-02-23  
**Autor:** Claude + Developer  
**Status:** Faza planowania / architektura  
**Wersja:** 2.0 (zaktualizowany po sesji Q&A)

---

## 1. Cel Projektu

Stworzenie mikroserwisu w Pythonie (FastAPI), który będzie odpowiedzialny za tworzenie embeddingów ze zdjęć pojazdów (samochodów i motocykli) oraz przechowywanie ich w wektorowej bazie danych. Serwis będzie współpracował z istniejącą aplikacją Kotlin/Spring Boot (vehicle-collector — VC) i umożliwi w przyszłości wyszukiwanie podobnych pojazdów na podstawie obrazów.

---

## 2. Kontekst Developera

- Java/Kotlin developer z doświadczeniem komercyjnym (7 lat nauki, ~7 lat pracy)
- Doświadczenie z: Spring Boot, MongoDB, PostgreSQL + pgvector (z pracy)
- Znikome doświadczenie z FastAPI (kontakt w pracy)
- Python — nauka od zera, ale z solidnymi fundamentami programistycznymi
- Środowisko: VSCode + Claude (konsola WSL2), IntelliJ, PyCharm Community
- Cel dodatkowy: nauka Pythona przez praktyczny projekt, z analogiami do Java/Kotlin

---

## 3. Architektura Systemu

### 3.1 Komponenty

| Komponent | Technologia | Rola |
|-----------|-------------|------|
| **vehicle-collector (VC)** | Kotlin + Spring Boot | Główna aplikacja — zbieranie zdjęć, miniaturki, zarządzanie |
| **vc-rag-service** | Python + FastAPI | Mikroserwis embeddingowy — vectorizacja zdjęć, storage, search |
| **Baza wektorowa** | PostgreSQL + pgvector | Przechowywanie embeddingów i metadanych |
| **Model embeddingowy** | HuggingFace Transformers — CLIP base (512 dim) | Lokalne modele do tworzenia embeddingów |
| **PWA** | Frontend mobilny | Wysyłanie zdjęć (do 20 na raz, max 20MB/plik, iPhone 16) |

### 3.2 Diagram Flow (aktualny — bez walidacji LLM)

```
┌─────────────────────────────────────────────────────────────┐
│  PWA (telefon)                                              │
│  Wysyła do 20 zdjęć na raz (iPhone 16, 5-10MB/szt)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  KOTLIN (vehicle-collector - VC)                            │
│                                                             │
│  1. Zdjęcie przychodzi → response 200 natychmiast           │
│  2. Zapis oryginału + MongoDB (status: RAW)                 │
│  3. Fire & forget: generowanie miniaturek (320px + 640px)   │
│  4. Po wygenerowaniu miniaturek:                            │
│     - thumbnail320, thumbnail640 ścieżki w MongoDB          │
│     - vectorized: false                                     │
│                                                             │
│  5. CRON job (np. co noc):                                  │
│     Query: vectorized == false AND thumbnail640 != null      │
│     → batch request do vc-rag-service                       │
│     Wysyła: path do 640px, photoId, externalId, metadata    │
│                                                             │
│  UWAGA: Walidacja LLM (treści) — ODROCZONA na przyszłość.  │
│  Zostanie dodana gdy aplikacja będzie udostępniana innym     │
│  użytkownikom (+ Terms of Service z odpowiedzialnością      │
│  za treść). Walidacja jako dodatkowy async job wstrzyknięty  │
│  między punkt 2 a 3.                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    POST /api/v1/photos/batch
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PYTHON (vc-rag-service)                                    │
│                                                             │
│  1. Przyjęcie batcha → zapis do tabeli photos               │
│     (external_id, path do 640px, metadata, status: QUEUED)  │
│                                                             │
│  2. Background Job (APScheduler / cron):                    │
│     Dla każdego rekordu ze statusem QUEUED:                 │
│     a) Wczytaj miniaturkę 640px z podanej ścieżki          │
│     b) CLIP base → embedding vector (512 dim)               │
│     c) Zapisz vector do pgvector                            │
│     d) Ustaw status: VECTORIZED + timestamp                 │
│                                                             │
│  3. Endpointy query (dla VC):                               │
│     - Similarity search                                     │
│     - Status check                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Kluczowe Decyzje Technologiczne

### 4.1 Transformers (nie Ollama)

| Kryterium | Ollama | Transformers (HuggingFace) |
|-----------|--------|---------------------------|
| Kontrola nad modelem | Średnia (wrapper) | Pełna |
| Overhead | HTTP API nawet lokalnie | Brak — model w pamięci procesu |
| Embedding pipeline | Wymaga pośrednictwa | Natywne w Pythonie |
| Wielomodalność (obraz+tekst) | Ograniczona | Pełna (CLIP, SigLIP) |

**Decyzja:** Transformers — model ładowany raz przy starcie aplikacji, trzymany w pamięci, bez narzutu sieciowego.

### 4.2 Model embeddingowy — CLIP base (na start)

**Wybrany model:** `openai/clip-vit-base-patch32` — wymiar 512, ~600MB RAM

Uzasadnienie:
- Najlepiej udokumentowany, ogromna społeczność
- 512 dim wystarczy do rozróżniania pojazdów
- Działa komfortowo na CPU (batch nocny)
- Podmiana modelu w przyszłości to zmiana jednej linii kodu

Kandydaci na przyszłość (po testach):
- `google/siglip-base-patch16-224` (768 dim) — nowszy, lepsza jakość
- `openai/clip-vit-large-patch14` (768 dim) — lepsze detale

### 4.3 Embedding z miniaturki 640px (nie z oryginału)

**Kluczowa decyzja:** CLIP wewnętrznie resizuje każdy obraz do 224×224 px. Niezależnie czy podamy oryginał 4000×3000 (10MB) czy miniaturkę 640px (~100KB), wynikowy embedding jest identyczny.

| Źródło | Rozmiar pliku | Czas wczytania (PIL) | Embedding |
|--------|--------------|---------------------|-----------|
| Oryginał 4000×3000 | 5-10 MB | ~200-500ms | identyczny |
| Miniatura 640px | ~50-150 KB | ~5-15ms | identyczny |

**Decyzja:** Embedujemy z 640px. Szybsze I/O, mniej RAM, ten sam wynik. Oryginał zostaje na dysku do wyświetlania.

**Naturalny "ready gate" w VC:** Cron wysyła do vectorizacji tylko zdjęcia gdzie `vectorized == false AND thumbnail640 != null`. Jeśli miniaturka jeszcze się nie wygenerowała (fire & forget jeszcze pracuje), cron pomija i łapie w następnym cyklu.

### 4.4 Wydajność embeddingu (CLIP base, CPU)

| Operacja | Czas (CPU) | Czas (GPU) |
|----------|-----------|-----------|
| 1 zdjęcie (640px) | ~0.3-0.5s | ~0.02s |
| Batch 20 zdjęć | ~6-10s | ~0.3s |
| Batch 100 zdjęć | ~30-50s | ~1s |

Nocny batch na CPU jest w zupełności wystarczający. GPU nie jest wymagane.

### 4.5 Baza danych — PostgreSQL + pgvector

- Developer zna pgvector z pracy
- Jedna tabela na dane + vectory (prostsze)
- Wystarczy dla tysięcy/dziesiątek tysięcy zdjęć
- Milvus rozważyć przy milionach rekordów

### 4.6 Background Jobs — APScheduler

- Prosty, analogiczny do `@Scheduled` w Springu
- Celery (wymaga Redis/RabbitMQ) to overkill na tym etapie
- Migracja do Celery możliwa później

### 4.7 Walidacja LLM — odroczona

Obecnie aplikacja jest prywatna (tylko developer). Walidacja treści zdjęć zostanie dodana gdy:
- Aplikacja będzie udostępniana innym użytkownikom
- Użytkownik będzie musiał zaakceptować ToS z odpowiedzialnością za treść
- Walidacja LLM jako dodatkowy safety net (na miniaturce 640px — taniej, szybciej)

Architektura jest przygotowana — walidacja to dodatkowy async job w pipeline VC.

---

## 5. Stack Technologiczny

| Warstwa | Narzędzie | Analogia w Java/Spring |
|---------|-----------|----------------------|
| Framework webowy | FastAPI | Spring Web / @RestController |
| Walidacja requestów | Pydantic | Bean Validation / @Valid |
| Dependency Injection | FastAPI Depends() | @Autowired / @Bean |
| ORM / Baza danych | SQLAlchemy + asyncpg | JPA / Hibernate |
| Vector DB | pgvector (extension do PostgreSQL) | pgvector (to samo) |
| Embedding model | transformers — CLIP base (512 dim) | — |
| Background jobs | APScheduler | @Scheduled / Quartz |
| Konfiguracja | pydantic-settings | application.yml |
| Migracje DB | Alembic | Flyway / Liquibase |
| Testy | pytest | JUnit |

---

## 6. Struktura Projektu

```
vc-rag-service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # ≈ @SpringBootApplication
│   │
│   ├── api/                       # ≈ warstwa @RestController
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── photo_routes.py    # endpointy batch, status, search
│   │       └── health_routes.py   # healthcheck
│   │
│   ├── core/                      # ≈ konfiguracja + infra
│   │   ├── __init__.py
│   │   ├── config.py              # ≈ application.yml (pydantic-settings)
│   │   ├── database.py            # ≈ DataSource config
│   │   └── dependencies.py        # ≈ @Configuration / @Bean
│   │
│   ├── service/                   # ≈ warstwa @Service
│   │   ├── __init__.py
│   │   ├── embedding_service.py   # logika embeddingu (CLIP)
│   │   └── photo_service.py       # orchestracja (batch, vectorize)
│   │
│   ├── repository/                # ≈ warstwa @Repository / DAO
│   │   ├── __init__.py
│   │   └── photo_repository.py    # CRUD + vector ops na pgvector
│   │
│   ├── model/                     # ≈ DTO + Entity
│   │   ├── __init__.py
│   │   ├── schemas.py             # ≈ request/response DTOs (Pydantic)
│   │   └── entities.py            # ≈ @Entity (SQLAlchemy models)
│   │
│   └── jobs/                      # ≈ @Scheduled
│       ├── __init__.py
│       └── vectorize_job.py       # cron job do vectorizacji QUEUED
│
├── alembic/                       # ≈ Flyway migrations
│   └── versions/
├── alembic.ini
├── pyproject.toml                 # ≈ pom.xml / build.gradle
├── Dockerfile
├── docker-compose.yml             # PostgreSQL + pgvector + app
├── .env                           # ≈ application-local.yml
└── tests/
    ├── __init__.py
    ├── test_photo_routes.py
    ├── test_embedding_service.py
    └── test_photo_repository.py
```

---

## 7. Schemat Bazy Danych

### Tabela: photos (PostgreSQL + pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE photos (
    id              SERIAL PRIMARY KEY,
    external_id     VARCHAR(255) UNIQUE NOT NULL,  -- ID z MongoDB (vehicle-collector)
    photo_id        VARCHAR(255),                  -- business ID zdjęcia
    file_path       VARCHAR(1024) NOT NULL,        -- ścieżka do miniaturki 640px
    sha256          VARCHAR(64),                   -- hash zdjęcia
    metadata        JSONB DEFAULT '{}',            -- marka, model, rok, kolor, itp.
    embedding       vector(512),                   -- CLIP base output (512-dim)
    status          VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
                    -- QUEUED → PROCESSING → VECTORIZED / ERROR
    error_message   TEXT,                          -- szczegóły błędu (jeśli ERROR)
    created_at      TIMESTAMP DEFAULT NOW(),
    vectorized_at   TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Indeksy
CREATE INDEX idx_photos_external_id ON photos(external_id);
CREATE INDEX idx_photos_status ON photos(status);

-- Indeks wektorowy (IVFFlat — dobry do < 1M rekordów)
CREATE INDEX idx_photos_embedding ON photos
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

---

## 8. API Endpoints

| Metoda | Endpoint | Opis |
|--------|----------|------|
| POST | `/api/v1/photos/batch` | Przyjmij batch zdjęć do vectorizacji |
| GET | `/api/v1/photos/{externalId}` | Status i metadane zdjęcia |
| POST | `/api/v1/photos/search` | Similarity search |
| GET | `/api/v1/health` | Healthcheck (+ status modelu) |

### Przykłady requestów

**POST /api/v1/photos/batch** (wysyłany przez VC cron job):
```json
{
  "photos": [
    {
      "external_id": "mongo-id-abc123",
      "photo_id": "VH-2024-001-front",
      "file_path": "/mnt/photos/thumbnails/640/2024/01/img_001.jpg",
      "sha256": "a1b2c3d4...",
      "metadata": {
        "brand": "Toyota",
        "model": "Corolla",
        "year": 2020,
        "color": "silver",
        "angle": "front"
      }
    }
  ]
}
```

**Response:**
```json
{
  "accepted": 15,
  "duplicates_skipped": 2,
  "status": "QUEUED"
}
```

---

## 9. Embedding — jak to działa (referencyjna implementacja)

```python
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

# Ładowanie raz przy starcie aplikacji (≈ @Bean)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Embedding zdjęcia z miniaturki 640px
image = Image.open("/mnt/photos/thumbnails/640/img_001.jpg")
inputs = processor(images=image, return_tensors="pt")
embedding = model.get_image_features(**inputs)  # → tensor [1, 512]

# Embedding tekstu (przyszłość — ten sam model, ta sama przestrzeń!)
inputs = processor(text="silver Toyota Corolla 2020", return_tensors="pt")
text_embedding = model.get_text_features(**inputs)  # → tensor [1, 512]
```

CLIP tworzy embeddingi obrazów i tekstu w tej samej przestrzeni wektorowej. W przyszłości będzie można szukać zdjęć tekstem bez zmiany modelu ani przebudowy indeksu.

---

## 10. Plan Nauki — Roadmapa

### Faza 1: Python Basics (Tydzień 1–2)
- Składnia, typy, f-stringi, list comprehensions
- Klasy, dataclasses (≈ record w Javie)
- venv, pip, pyproject.toml (≈ Maven/Gradle)
- Async/await (≈ CompletableFuture, ale wbudowane w język)

### Faza 2: FastAPI Fundamentals (Tydzień 3)
- Routing, path/query params (≈ @PathVariable, @RequestParam)
- Pydantic models (≈ DTO + @Valid)
- Depends() (≈ @Autowired)
- Middleware, exception handling (≈ @ControllerAdvice)

### Faza 3: Baza Danych (Tydzień 4)
- SQLAlchemy async (≈ JPA/Hibernate)
- Alembic migrations (≈ Flyway)
- pgvector integracja
- Repository pattern w Pythonie

### Faza 4: Embedding Pipeline (Tydzień 5–6)
- Instalacja i konfiguracja transformers + CLIP
- Ładowanie modelu, tworzenie embeddingów z miniaturek 640px
- Zapis do pgvector

### Faza 5: Integracja (Tydzień 7+)
- Background job (APScheduler) do vectorizacji
- Batch endpoint
- Similarity search
- Docker Compose (app + PostgreSQL)

---

## 11. Otwarte Pytania / Do Ustalenia

1. Jakie dodatkowe metadane w JSONB? (marka, model, rok, kolor — co jeszcze?)
2. Retry policy: co gdy vectorizacja się nie uda? Ile prób?
3. Autentykacja: czy komunikacja VC ↔ rag-service wymaga auth?
4. Skala: ile zdjęć dziennie / tygodniowo szacunkowo?
5. Search: query by image? By metadata? Hybrid?
6. Kiedy planowany embedding tekstu?

---

## 12. Narzędzia i Środowisko

- **IDE:** PyCharm Community (Python) + IntelliJ (Kotlin) + VSCode (Claude)
- **Runtime:** Python 3.11+ (WSL2 / Linux server)
- **Claude:** Konsola WSL2, panel boczny VSCode, claude.ai — tryb "nauczyciel"
- **Konteneryzacja:** Docker + Docker Compose
- **VCS:** Git

---

*Raport v2.0 — zaktualizowany po sesji Q&A architektonicznej. Następny krok: setup PyCharm, szkielet projektu, pierwszy endpoint /health.*
