# AI Social Manager — Next Steps

## Current State

The MVP is functional end-to-end:
- **Backend**: 4-agent LangGraph pipeline (Trend Researcher → Strategist → Writer → Critic) with FastAPI, using Groq/Llama 3.3 70B
- **Frontend**: React + Vite dashboard with Generate, History, Brand Settings pages
- **Storage**: localStorage (frontend), in-memory MemorySaver (backend)
- **Missing**: Auth, database, social platform integrations, deployment

---

## Phase 1 — Polish & Stabilize (Week 1)

### 1.1 Wire up real SSE streaming
- Frontend currently simulates pipeline stages with timers
- Backend already has `/api/generate/{thread_id}/stream` endpoint
- Connect frontend `PipelineStatus` to real SSE events so users see actual agent progress

### 1.2 Add a README
- Setup instructions (Python 3.11+, Node 18+, Groq API key)
- How to run backend and frontend
- Environment variable reference

### 1.3 Add `node_modules/` and `frontend/dist/` to .gitignore
- Currently untracked but not ignored
- Commit `package-lock.json` for reproducible installs

### 1.4 Error & edge case handling
- Handle API timeout gracefully (generation can take 30-60s)
- Add retry logic on network failures
- Show meaningful errors when Groq API key is missing or rate-limited

### 1.5 Basic tests
- Backend: pytest for `/health`, `/api/generate` with mocked LLM responses
- Frontend: smoke tests that pages render without crashing

---

## Phase 2 — Database & Auth (Week 2)

### 2.1 Add PostgreSQL database
- Replace in-memory `run_results` dict with persistent storage
- Store generation history server-side (not just localStorage)
- Tables: `users`, `brand_profiles`, `generations`, `posts`
- Use SQLAlchemy or Tortoise ORM with Alembic migrations

### 2.2 User authentication
- JWT-based auth with `/api/auth/register` and `/api/auth/login`
- Protect `/api/generate` and `/api/status` behind auth middleware
- Frontend: login/register pages, auth context, token storage

### 2.3 Server-side brand profiles
- Move brand profiles from localStorage to database
- Sync between frontend and backend
- Each user owns their own profiles

### 2.4 Server-side history
- Generation results persisted to DB on completion
- Frontend fetches from API instead of localStorage
- Pagination for history list

---

## Phase 3 — Real-Time Data & Better Content (Week 3)

### 3.1 Real trend research
- Replace DuckDuckGo instant answer with a proper search API (SerpAPI, Tavily, or Brave Search)
- Add real-time hashtag trending data
- Cache trend results for 1 hour to reduce API calls

### 3.2 Content scheduling UI
- Add date/time picker to generated posts
- Store scheduled posts in database with status tracking
- Calendar view on dashboard showing upcoming posts

### 3.3 Content editing
- Allow users to edit generated posts before saving/scheduling
- Inline editing in PostCard component
- Re-run critic on edited content

### 3.4 Export functionality
- Copy all posts as formatted text
- Export to CSV/JSON
- Download individual posts with metadata

---

## Phase 4 — Social Platform Integrations (Week 4-5)

### 4.1 Twitter/X API integration
- OAuth 2.0 flow for user's Twitter account
- Publish single tweets and threads
- Character count validation (280 limit)

### 4.2 LinkedIn API integration
- OAuth 2.0 for LinkedIn profile/page
- Publish text posts and articles
- Support for company pages vs personal profiles

### 4.3 Instagram API integration
- Meta Graph API for Instagram Business accounts
- Image post support (requires image generation — see 4.4)
- Caption + hashtag publishing

### 4.4 AI image generation
- Use the existing `image_prompt` field in post schema
- Integrate DALL-E or Stable Diffusion API
- Generate platform-appropriate images (square for Instagram, landscape for LinkedIn)
- Image preview in PostCard

---

## Phase 5 — Analytics & Monitoring (Week 6)

### 5.1 Post performance tracking
- Fetch engagement metrics from connected social accounts
- Track likes, comments, shares, impressions per post
- Display in history and dashboard

### 5.2 Analytics dashboard
- Charts: posts per week, avg engagement, best performing platforms
- Score trends over time
- Top performing content themes

### 5.3 A/B testing
- Generate multiple variants per platform
- Track which variant performs better
- Feed results back into future generation prompts

---

## Phase 6 — Production & Deployment (Week 7)

### 6.1 Containerization
- Dockerfile for backend (Python + FastAPI)
- Dockerfile for frontend (Node build + nginx)
- docker-compose.yml for local development (backend + frontend + postgres)

### 6.2 CI/CD pipeline
- GitHub Actions: lint, test, build on PR
- Auto-deploy to staging on merge to `develop`
- Manual promote to production

### 6.3 Infrastructure
- Deploy backend to Railway / Render / AWS ECS
- Frontend to Vercel / Cloudflare Pages
- PostgreSQL on managed service (Neon, Supabase, or RDS)
- Environment variable management

### 6.4 Observability
- Sentry for error tracking
- Structured logging with correlation IDs
- API response time monitoring
- LLM cost tracking per generation

---

## Phase 7 — Monetization (Week 8+)

### 7.1 Usage tiers
- **Free**: 5 generations/month, 1 brand profile
- **Creator ($19/mo)**: 50 generations, 3 profiles, all platforms
- **Agency ($49/mo)**: Unlimited generations, unlimited profiles, team members
- **Enterprise**: Custom pricing, API access, white-label

### 7.2 Billing integration
- Stripe for payment processing
- Usage tracking and quota enforcement
- Upgrade/downgrade flow in settings

### 7.3 Rate limiting
- Per-user rate limits based on tier
- Global rate limiting on API
- Queue system for high-traffic periods

---

## Priority Order

| Priority | Task | Impact | Effort |
|----------|------|--------|--------|
| P0 | Wire up real SSE streaming | Better UX | Low |
| P0 | .gitignore + README | Developer hygiene | Low |
| P1 | PostgreSQL + auth | Required for multi-user | Medium |
| P1 | Server-side history & brands | Data persistence | Medium |
| P1 | Real trend research API | Content quality | Low |
| P2 | Content editing & export | User workflow | Medium |
| P2 | Docker + deployment | Go live | Medium |
| P2 | Basic tests | Reliability | Medium |
| P3 | Social platform APIs | Core feature | High |
| P3 | Image generation | Visual content | Medium |
| P4 | Analytics & A/B testing | Growth | High |
| P4 | Billing & tiers | Revenue | High |
