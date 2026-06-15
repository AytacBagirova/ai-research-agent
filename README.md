# Cute Researcher — AI Research Agent

Cute Researcher is a full-stack AI-powered research agent that autonomously searches the web, reads sources, and produces structured reports. Given a topic, the agent plans its research, uses multiple tools to gather information, critiques its own output, and delivers a comprehensive markdown report — all in real time.

---

## What It Does

The agent follows a structured research loop:

1. Searches the web using Tavily Search API
2. Reads web pages, Wikipedia articles, arXiv papers, and PDFs
3. Embeds each source into a vector database (Qdrant) for semantic retrieval
4. Critiques and improves its own report before finalizing
5. Streams every step to the UI in real time via Server-Sent Events

Supports three research depths (Basic, Medium, Deep) and three output languages (English, Azerbaijani, Russian).

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, TanStack Router, Tailwind CSS |
| AI Agent | Claude Haiku (Anthropic) with tool-use loop |
| Search | Tavily Search API |
| Embeddings | OpenAI text-embedding-3-small (1536 dimensions) |
| Vector Database | Qdrant |
| Relational Database | PostgreSQL 16 with pgvector extension |
| ORM | SQLAlchemy (async) |
| API Framework | FastAPI |
| Streaming | Server-Sent Events (SSE) |
| PDF Reading | Google Gemini Flash |
| Token Counting | tiktoken (cl100k_base) |
| Logging | JSONL (per-session log files) |
| Infrastructure | Docker |

---

## Project Structure

```
ResearchAgent/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agent/
│   │   ├── agent_loop.py       # Core agent loop
│   │   ├── prompts.py          # System and user prompts
│   │   ├── critique.py         # Self-critique logic
│   │   ├── embeddings.py       # OpenAI + Qdrant integration
│   │   ├── logger.py           # Terminal + JSONL logger
│   │   └── token_counter.py    # tiktoken-based token counting
│   ├── tools/
│   │   ├── search_web.py
│   │   ├── read_url.py
│   │   ├── read_arxiv.py
│   │   ├── read_wikipedia.py
│   │   ├── read_pdf.py
│   │   └── compare_sources.py
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   └── db/
│       ├── models.py
│       ├── crud.py
│       └── database.py
├── frontend/
├── logs/
├── .env
└── requirements.txt
```

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- API keys: Anthropic, OpenAI, Tavily, Gemini

### 1. Start Docker Services

```bash
# PostgreSQL with pgvector
docker run -d --name research_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=research_agent \
  -p 5433:5432 pgvector/pgvector:pg16

# Qdrant vector database
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# pgAdmin (optional, for inspecting the database)
docker run -d --name pgadmin \
  -e PGADMIN_DEFAULT_EMAIL=admin@admin.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 5050:80 dpage/pgadmin4
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
TAVILY_API_KEY=tvly-...
GEMINI_API_KEY=AIza...

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/research_agent
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=research_sources
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Backend

```bash
uvicorn backend.main:app --reload
```

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:8080`.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research` | Start a new research session |
| GET | `/api/research/{id}/stream` | Stream agent steps via SSE |
| GET | `/api/research/{id}/report` | Retrieve the final report |
| GET | `/api/sessions` | List all sessions |
| DELETE | `/api/research/{id}` | Delete a session |

---

## How Sources Are Stored

Every source the agent reads is saved to PostgreSQL with its URL, snippet, type, and credibility score, then embedded via OpenAI and stored in Qdrant. On subsequent sessions covering similar topics, the agent retrieves previously found sources as context before starting new searches — reducing redundant API calls and token usage.

---

## Logging

Each session generates a JSONL log file at `logs/session_{id}.jsonl` containing every thought, tool call, tool result, token count, and final report.