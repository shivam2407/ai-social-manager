# AI Social Manager

A full-stack AI-powered social media content platform that uses a **multi-agent pipeline** to generate platform-native posts that match your brand voice. Built with **LangGraph**, **FastAPI**, and **React**.

> The only AI social media manager that sounds like YOU, not like AI.

---

## What It Does

Users create brand profiles with their voice, tone, and example posts. When they request content, a 4-agent LangGraph pipeline kicks in:

1. **Trend Researcher** — Searches the web for trending topics and competitor insights relevant to the brand's niche
2. **Strategist** — Designs platform-specific content angles, hooks, and content types based on research
3. **Writer** — Generates platform-native drafts (Twitter/X, LinkedIn, Instagram) with proper formatting, character limits, hashtags, and CTAs
4. **Critic** — Scores each draft on brand voice, engagement potential, platform fit, and clarity. Posts scoring below 7/10 are sent back for revision (up to 3 cycles)

The result: polished, on-brand content tailored to each platform — not generic copy-paste across channels.

---

## Tech Stack

### Backend
- **Python 3.11** / **FastAPI** — Async REST API with Pydantic validation
- **LangGraph** — Multi-agent orchestration with conditional edges and revision loops
- **LangChain** — LLM abstractions across 5 providers
- **SQLAlchemy 2.0 (async)** — ORM with PostgreSQL (prod) and SQLite (dev)
- **JWT + bcrypt + Fernet** — Auth, password hashing, and encrypted API key storage

### Frontend
- **React 18** / **Vite** — SPA with hot module replacement
- **Tailwind CSS 4** — Utility-first styling
- **React Router 7** — Client-side routing
- **Google & GitHub OAuth** — Social login integration

### LLM Providers (user-configurable)
| Provider | Models |
|----------|--------|
| Groq | Llama 3.3 70B, Mixtral 8x7B |
| Anthropic | Claude 3.5 Sonnet, Claude 3 Opus |
| OpenAI | GPT-4o, GPT-4 Turbo |
| Google | Gemini 2.0 Flash, Gemini Pro |
| xAI | Grok-2, Grok-2 Vision |

### Infrastructure
- **Docker** — Multi-stage build (Node 20 + Python 3.11)
- **Render** — Deployment config included
- **PostgreSQL** (Neon/Render) in production, **SQLite** for local dev

---

## Architecture

```
┌──────────────────────────────────────────────┐
│           React Frontend (Vite)              │
│  Dashboard · Generate · History · Settings   │
└─────────────────┬────────────────────────────┘
                  │ REST / SSE
                  ▼
┌──────────────────────────────────────────────┐
│           FastAPI Backend (:8000)             │
│                                              │
│  Auth (JWT + OAuth) ─── Brand CRUD           │
│  API Key Management ─── Generation History   │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │     LangGraph 4-Agent Pipeline        │  │
│  │                                        │  │
│  │  Trend Researcher → Strategist         │  │
│  │       → Writer ⇄ Critic (loop)        │  │
│  │             → Final Posts              │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  LLM Factory (Groq / Claude / GPT / Gemini) │
└─────────────────┬────────────────────────────┘
                  │ Async SQL
                  ▼
┌──────────────────────────────────────────────┐
│     PostgreSQL / SQLite                      │
│  users · brand_profiles · generations        │
│  posts · user_api_keys                       │
└──────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- At least one LLM API key (Groq is free and the default)

### 1. Clone and set up the backend

```bash
cd langgraph-api
cp .env.example .env
# Edit .env with your ENCRYPTION_KEY and JWT_SECRET_KEY

python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Generate an encryption key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

uvicorn app.main:app --reload --port 8000
```

### 2. Set up the frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` with the API at `http://localhost:8000`.

### 3. Configure an LLM provider

Sign up, create an account, and add your API key in **Settings** within the app. Groq offers a free tier and is the default provider.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ENCRYPTION_KEY` | Yes | Fernet key for encrypting stored API keys |
| `JWT_SECRET_KEY` | Yes | Secret for signing JWT tokens |
| `DATABASE_URL` | No | PostgreSQL connection string (defaults to SQLite) |
| `CORS_ORIGINS` | No | Allowed origins (defaults to `localhost:5173`) |
| `GOOGLE_CLIENT_ID` | No | Enables Google OAuth login |
| `GITHUB_CLIENT_ID` | No | Enables GitHub OAuth login |
| `GITHUB_CLIENT_SECRET` | No | GitHub OAuth secret |

---

## Project Structure

```
ai-social-manager/
├── frontend/
│   └── src/
│       ├── pages/          # Dashboard, Generate, History, BrandSettings, Settings
│       ├── components/     # UI components, agent visualizations, onboarding
│       ├── context/        # AuthContext
│       └── api.js          # API client
│
├── langgraph-api/
│   └── app/
│       ├── agents/         # trend_researcher, strategist, writer, critic
│       ├── graph/          # LangGraph state definition and builder
│       ├── routers/        # FastAPI route handlers (auth, brands, history, settings)
│       ├── models.py       # SQLAlchemy ORM models
│       ├── llm_factory.py  # Multi-provider LLM factory
│       ├── prompts.py      # System prompts for all 4 agents
│       ├── tools.py        # Web search, character count, platform best practices
│       ├── auth.py         # JWT, OAuth, password hashing
│       └── encryption.py   # Fernet encryption for API keys
│
├── docs/                   # Competitive analysis, development roadmap
├── Dockerfile              # Multi-stage production build
├── render.yaml             # Render deployment config
└── build.sh                # Build script
```

---

## Key Design Decisions

- **Multi-agent over single-prompt**: Splitting generation into research, strategy, writing, and review produces significantly better output than a single LLM call. The critic loop catches low-quality drafts before they reach the user.
- **LLM Factory pattern**: Users bring their own API keys and choose their preferred provider. The factory abstracts provider differences behind a unified LangChain interface.
- **Async everywhere**: FastAPI + SQLAlchemy async sessions + async LLM calls keep the server responsive during long-running generation pipelines.
- **Encrypted key storage**: User API keys are encrypted at rest with Fernet symmetric encryption, never stored in plaintext.
- **Platform-native content**: Each platform gets its own draft with appropriate formatting, length, and style — not the same post copy-pasted three times.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Email/password login |
| POST | `/api/auth/google` | Google OAuth |
| POST | `/api/auth/github` | GitHub OAuth |
| GET | `/api/brands/` | List brand profiles |
| POST | `/api/brands/` | Create brand profile |
| POST | `/api/generate` | Run the 4-agent pipeline |
| GET | `/api/generate/{id}/stream` | SSE stream of agent progress |
| GET | `/api/history/` | List past generations |
| GET | `/api/history/stats` | Generation statistics |
| POST | `/api/settings/api-keys` | Store an LLM API key |
| POST | `/api/settings/api-keys/test` | Validate a key works |

---

## Running Tests

```bash
cd langgraph-api
pytest
```

---

## Deployment

### Docker

```bash
docker build -t ai-social-manager .
docker run -p 8000:8000 \
  -e ENCRYPTION_KEY=your-key \
  -e JWT_SECRET_KEY=your-secret \
  -e DATABASE_URL=postgresql+asyncpg://... \
  ai-social-manager
```

### Render

Push to GitHub and connect the repo on Render. The included `render.yaml` handles the build and start commands. Set environment variables in the Render dashboard.

---

## Roadmap

- [ ] Real-time SSE streaming for agent progress on the frontend
- [ ] Premium trend research (SerpAPI / Tavily integration)
- [ ] Direct publishing to Twitter/X, LinkedIn, and Instagram via platform APIs
- [ ] AI image generation for posts (DALL-E / Stable Diffusion)
- [ ] Analytics dashboard with engagement tracking
- [ ] Stripe billing with usage-based tiers
