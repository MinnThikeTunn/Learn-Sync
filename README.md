# LearnSync AI 🎓⚡

> **The Context-Aware Adaptive Learning, Virtual Folder Resource Manager & Workload Co-Pilot**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.0+-black.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E.svg?style=flat&logo=supabase&logoColor=white)](https://supabase.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

---

## 📖 Overview

**LearnSync AI** is an intelligent academic co-pilot designed to bridge the gap between heavy university workloads and consistent, deep learning. 

Traditional learning platforms ignore real-time deadlines and cognitive fatigue, while standard productivity tools require tedious manual upkeep and offer zero adaptive pedagogical support. LearnSync AI continuously computes a **rolling Workload Score $W(t)$**, automatically scaling study materials between **Free Mode** (deep interactive sandboxes, podcasts, and diagrams) and **Busy Mode** (90-second micro-tasks, cheat-sheets, and rapid recaps) with zero ongoing maintenance.

---

## ✨ Core Features & Capabilities

### 1. 🗂️ Virtual Folder Resource Manager & Scoped RAG
- **Hierarchical Course Organization:** Nested virtual folders (e.g., `/CS101/Week_03_Recursion/`) linked directly to course modules and syllabus schedules.
- **Strictly Scoped Retrieval:** Vector queries and hybrid search are partitioned by course and folder path to prevent cross-contamination and minimize latency.
- **Reciprocal Rank Fusion (RRF):** Combines dense vector embeddings with sparse BM25 keyword matching ($k=60$) for hyper-accurate context retrieval.

### 2. ⚡ Workload Co-Pilot & Adaptive Mode Engine
- **Rolling Workload Score $W(t)$:** Computes an exponential decay lookahead over a 3-day window based on upcoming exam/assignment weights and proximity.
- **Schmitt Trigger Hysteresis:**
  - **Free Mode ($W(t) \le 0.55$):** Deep comprehension through multi-modal formats (diagrams, sandboxes, long-form guides).
  - **Busy Mode ($W(t) > 0.70$):** High-yield, low-friction micro-learning (cheat-sheets, 30s recaps, 90s bug-fixes).
  - **Dead-Band ($0.55 < W(t) \le 0.70$):** Retains active state to eliminate rapid mode flapping.

### 3. 🧠 Multi-Modal Adaptive Learning (VARK Framework)
Adapts educational artifacts to the student's primary learning style:
- **Visual:** Interactive Mermaid.js diagrams, concept maps, and high-contrast cheat-sheets.
- **Auditory:** Socratic dialogue scripts, long-form podcast explainers, and 30-second audio recaps.
- **Read/Write:** Structured study guides, comprehensive technical notes, and bullet summaries.
- **Kinesthetic:** Hands-on code sandboxes, interactive challenges, and syntax bug-fix micro-tasks.

### 4. 🔁 FSRS Spaced Repetition & Leech Quarantine
- **Free Spaced Repetition Scheduler (FSRS v4):** Modern memory modeling (Stability, Retrievability, Difficulty).
- **Dynamic Retention Scaling:** Dynamically modulates target retention based on workload score.
- **Leech Quarantine:** Automatically detects cards failed 4+ times, pauses them from the review queue, and schedules LLM-driven simplification.

### 5. 🎯 Feynman Active Recall & Gap Analysis
- Prompts students to explain complex concepts in plain language.
- LLM precision-gap evaluation detects missing prerequisites, circular reasoning, and misconceptions, auto-generating targeted remedial flashcards.

### 6. 📊 Bayesian Knowledge Tracing (BKT) & Burnout Guard
- **BKT Mastery Tracking:** Tracks latent knowledge component (KC) mastery $P(L_t)$ updated in real-time.
- **Burnout Guard:** Monitors acute 48-hour deadline clusters and automatically swaps daunting study blocks with low-barrier B=MAP micro-tasks.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    subgraph Client["Frontend (Next.js 15 + Tailwind)"]
        UI[Dashboard / Study Hub / Review / Folders]
        State[Mode & Workload Visualizer]
    end

    subgraph Backend["FastAPI Compute Engine"]
        API[API Router /api/v1]
        Parser[Syllabus Parser & Ingestion]
        Workload[Workload & Hysteresis Engine]
        RAG[Adaptive RAG & RRF Hybrid Search]
        FSRS[FSRS Spaced Repetition]
        Feynman[Feynman Active Recall & Gap Analysis]
        BKT[Bayesian Knowledge Tracing]
        Burnout[Burnout Guard Service]
    end

    subgraph Storage["Data & Event Layer"]
        DB[(Supabase PostgreSQL + pgvector)]
        Redis[(Redis Cache / Locks / Limits / Streams)]
        MQ[[RabbitMQ + Celery Queue]]
    end

    UI <-->|REST / JSON| API
    API --> Parser
    API --> Workload
    API --> RAG
    API --> FSRS
    API --> Feynman
    API --> BKT
    API --> Burnout
    Workload -->|Spike Events| MQ
    API -->|Cache / Lock / Rate Limit| Redis
    API -->|Document Jobs| MQ
    MQ --> Worker[Celery Document Worker]
    Worker --> DB
    API -->|Learning Events| Redis
    RAG <-->|Hybrid Vector + BM25| DB
    FSRS <-->|Cards & Logs| DB
    BKT <-->|KC State| DB
```

---

## 📂 Project Structure

```text
learnSync/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/          # API endpoint routes (syllabus, workload, artifacts, fsrs, feynman, etc.)
│   │   ├── core/            # Config, Redis adapters, queues, and event publishers
│   │   ├── schemas/         # Pydantic data contracts and validation models
│   │   ├── services/        # Core business & algorithmic logic (Workload, RAG, FSRS, BKT, Feynman, Burnout)
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Pytest comprehensive test suite
│   └── requirements.txt     # Backend Python dependencies
├── frontend/                 # Next.js 15 TypeScript frontend
│   ├── app/                 # Next.js App Router (dashboard, study, review, folders)
│   ├── components/          # Reusable UI components & layouts
│   ├── package.json         # Node.js dependencies and scripts
│   └── tailwind.config.ts   # Tailwind CSS design system configuration
├── supabase/                 # Supabase PostgreSQL schema and migration scripts
│   └── schema.sql           # Database schema, pgvector configuration, and RRF RPC functions
├── Project/                  # Project specifications, SRS, proposals, and design documents
├── CONTEXT.md                # Domain terminology and system vocabulary
└── README.md                 # Project documentation
```

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [Pydantic v2](https://docs.pydantic.dev/), [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs), [NumPy](https://numpy.org/), [Pika](https://pika.readthedocs.io/)
- **Frontend:** [Next.js 15](https://nextjs.org/), [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Tailwind CSS](https://tailwindcss.com/), [Lucide Icons](https://lucide.dev/)
- **Database & Storage:** [Supabase](https://supabase.com/) (PostgreSQL, `pgvector`, Row-Level Security)
- **Distributed Infrastructure:** [Redis](https://redis.io/) for caching, locks, rate limiting, and Streams; [RabbitMQ](https://www.rabbitmq.com/) + [Celery](https://docs.celeryq.dev/) for document-processing jobs and event delivery
- **AI / LLMs:** Google Gemini API (Embeddings & Generative Artifact Synthesis)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm** / **pnpm**
- **Supabase** project (or local Supabase instance)
- **RabbitMQ** instance (optional for local standalone test runs)
- **Redis 7+** (optional for local fallback mode; required for shared cache, locks, limits, and Streams)

---

### Backend Setup

1. **Navigate to the backend directory and create a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables (`.env` in the root or `backend/`):**
   ```env
   PROJECT_NAME="LearnSync AI"
   VERSION="0.1.0"
   SUPABASE_URL="https://your-project.supabase.co"
   SUPABASE_KEY="your-anon-or-service-role-key"
   RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
   REDIS_URL="redis://localhost:6379/0"
   ASYNC_DOCUMENT_PROCESSING="false"
   ARTIFACT_CACHE_TTL_SECONDS="3600"
   FEYNMAN_RPM_LIMIT="10"
   GEMINI_API_KEY="your-gemini-api-key"
   ```

4. **Run the FastAPI development server:**
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
   Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure frontend environment (`frontend/.env.local`):**
   ```env
   NEXT_PUBLIC_API_URL="http://localhost:8000/api/v1"
   NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
   NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"
   ```

4. **Start the Next.js development server:**
   ```bash
   npm run dev
   ```
   Access the web interface at [http://localhost:3000](http://localhost:3000).

---

### Database Setup

1. Open your **Supabase Dashboard** (or run `supabase db push` with the Supabase CLI).
2. Execute the contents of [`supabase/schema.sql`](file:///D:/learnSync/supabase/schema.sql) in the SQL Editor.
3. This creates all necessary tables (`users`, `courses`, `virtual_folders`, `documents`, `document_chunks`, `flashcards`, `knowledge_components`, `events`), enables `pgvector`, configures RRF search functions, and sets up RLS policies.

---

## Distributed Infrastructure

**Implementation status: complete for the intended distributed-project scope.** LearnSync includes asynchronous document processing, Redis caching, distributed locking, event delivery, distributed rate limiting, BKT persistence, and demonstration tests. See [`docs/distributed_concepts.md`](docs/distributed_concepts.md) for the detailed implementation report.

LearnSync adds five infrastructure concepts without changing the core learning workflow:

| Concept | Implementation | Applied to |
|---|---|---|
| Async message queue | Celery + RabbitMQ | Document upload processing |
| Distributed cache | Redis with TTL | Study artifact generation |
| Distributed locking | Redis ownership locks | BKT and flashcard updates |
| Event streaming | RabbitMQ and Redis Streams | Learning, workload, and burnout events |
| Distributed rate limiting | Shared Redis fixed-window limiter | Feynman and artifact endpoints |

### Start Redis and RabbitMQ

From the project root:

```bash
docker compose -f docker-compose.distributed.yml up -d
```

RabbitMQ management is available at [http://localhost:15672](http://localhost:15672) using `guest` / `guest`.

Set these values in `backend/.env`:

```env
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
ASYNC_DOCUMENT_PROCESSING=true
```

### Run the Celery worker

From the project root, with the backend virtual environment active:

```bash
celery -A backend.app.core.task_queue:celery_app worker --loglevel=INFO
```

When asynchronous processing is enabled, document uploads return a pending document and a job identifier. Check processing state with:

```text
GET /api/v1/documents/{document_id}/status
```

If Redis or RabbitMQ is unavailable, the application falls back to local cache/lock behavior and synchronous document processing for development.

### Distributed demonstration tests

```bash
python -m pytest backend/tests/test_distributed_infrastructure.py -q
```

The tests demonstrate TTL expiry, concurrent lock serialization, shared-limit behavior, replayable event metadata, and safe queue fallback.

The syllabus preview endpoint remains synchronous because it must return staged folders and events in the same request. Converting it to a queued workflow would require a frontend polling flow.

### Final implementation checklist

- Redis and RabbitMQ services run through [`docker-compose.distributed.yml`](docker-compose.distributed.yml).
- Celery document worker is available through `backend/app/core/task_queue.py`.
- Redis cache, locks, rate limiting, and Streams are implemented in `backend/app/core/distributed.py`.
- Learning events are published through `backend/app/core/events.py`.
- BKT mastery state is persisted through Supabase upsert.
- Distributed demonstration tests pass in `backend/tests/test_distributed_infrastructure.py`.

---

## 🧪 Running Tests

The test suite covers API endpoints, syllabus parsing, workload scoring, FSRS scheduling, RAG hybrid retrieval, Feynman evaluation, and BKT mastery state updates:

```bash
# From the project root:
pytest backend/tests -v
```

---

## 📚 Domain Terminology

To maintain domain consistency, LearnSync adheres to specific terminology (defined in [`CONTEXT.md`](file:///D:/learnSync/CONTEXT.md)):

| Canonical Term | Definition | Avoid Using |
|---|---|---|
| **Workload Score $W(t)$** | Continuous 3-day lookahead score in $[0.0, 1.0]$ computed from deadline density and event weights. | *Stress score, busy level, pressure index* |
| **Free Mode** | Learning state when $W(t) \le 0.55$, delivering deep interactive walkthroughs and sandboxes. | *Normal mode, relaxed mode, standard mode* |
| **Busy Mode** | Low-cognitive-load state when $W(t) > 0.70$, delivering cheat-sheets, 30s recaps, and micro-tasks. | *Exam mode, crunch mode, stress mode* |
| **Hysteresis Dead-Band** | The $0.55\text{--}0.70$ $W(t)$ interval where active mode is retained to avoid rapid state oscillation. | *Buffer zone, transition zone, neutral state* |
| **Virtual Folder** | Logical organizational node bound to a course module that scopes document retrieval. | *Category, directory, tag group* |
| **Knowledge Component (KC)** | Atomic curriculum unit tracked via Bayesian Knowledge Tracing. | *Skill, topic item, concept tag* |
| **Leech** | A flashcard failed 4+ times, automatically quarantined for AI simplification. | *Hard card, failure card* |
| **Burnout Guard** | Monitoring layer that replaces standard sessions with low-barrier B=MAP micro-tasks during deadline clusters. | *Stress blocker, anti-burnout filter* |
| **Reciprocal Rank Fusion (RRF)** | Hybrid ranking combining dense vector embeddings and sparse BM25 keyword matching. | *Hybrid search, blended search* |

---

## 📄 License

This project is licensed under the MIT License.
