# Hyper-Personalized Health & Fitness Coach

A full-stack, user-specific AI chatbot: **React + Tailwind CSS** frontend, **FastAPI + Pydantic** backend,
**MongoDB** for users / conversations / messages and **Qdrant** for RAG over a fitness & nutrition knowledge base.
The coach persona, safety rules, RAG rules and response structure come straight from the project brief (`app/prompts.py`).

---

## 1. Features (per the brief)

- Register (name, email, password, confirm) / login / logout, bcrypt hashing, HttpOnly-cookie session
- Multiple independent chats, persistent history (survives refresh, logout, re-login)
- Sidebar grouped by **Today / Yesterday / Previous 7 Days / Older** (derived from `last_message_at`)
- Rename + delete (with confirmation), automatic titles from the first message
- RAG: query embedding -> Qdrant semantic search -> context passed to the LLM; honest fallback when nothing relevant is found
- Loading states, retry on failure (user message is never lost), responsive layout with mobile drawer
- Ownership checks on every conversation/message operation, Pydantic validation everywhere
- Tests for auth, conversation ownership, and chat persistence (+ RAG wiring)

## 2. Architecture

```
Browser (React, Tailwind)
   |  fetch /api/*  (HttpOnly cookie)         Vite dev proxy -> :8000
   v
FastAPI  ── routers (auth, conversations, chat) ── services ──┬── MongoDB  (users, conversations, messages, revoked_tokens)
                                                              ├── Qdrant   (knowledge-base vectors only)
                                                              └── LLM + Embeddings (OpenAI-compatible API, keys stay on the server)
```

**One chat turn** (`POST /api/conversations/{id}/messages`):
1. Verify the conversation belongs to the current user (404 otherwise).
2. Save the **user message** in MongoDB (first message -> auto title).
3. Embed the question, search Qdrant (`access_scope = public`, top-k, score threshold).
4. Call the LLM with the system prompt + retrieved context + last N messages.
5. Save the **assistant message** (with retrieval metadata) and bump `last_message_at`.
If step 3/4 fails, the user message stays saved, **no fake assistant answer is stored**, and the API returns an error containing the saved `user_message` so the UI can show **Retry** (`retry_message_id`).

### Folder structure
```
health-coach/
├── docker-compose.yml            # MongoDB + Qdrant for local development
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py               # app factory, CORS, Origin check, lifespan (indexes + Qdrant collection)
│   │   ├── deps.py               # get_current_user (cookie -> JWT -> revocation check -> user)
│   │   ├── prompts.py            # system prompt (from the brief) + RAG context formatting
│   │   ├── core/                 # config.py, security.py, errors.py, timeutil.py
│   │   ├── db/                   # mongo.py (client + indexes), qdrant.py (client + collection setup)
│   │   ├── schemas/              # Pydantic request/response models (auth.py, conversation.py)
│   │   ├── services/             # auth, conversation, embedding, llm, retrieval, chat, kb_ingest
│   │   └── routers/              # auth.py, conversations.py, chat.py
│   ├── data/knowledge_base/      # sample knowledge base (11 markdown docs)
│   ├── scripts/ingest_kb.py      # indexes the knowledge base into Qdrant
│   ├── tests/                    # pytest suite (mongomock + in-memory Qdrant + fakes)
│   ├── requirements.txt / requirements-dev.txt / pytest.ini / .env.example
└── frontend/
    ├── index.html, vite.config.js, package.json, .env.example
    └── src/
        ├── api/client.js         # fetch wrapper + ApiError
        ├── context/AuthContext.jsx
        ├── hooks/                # useConversations, useChatSession, useNow
        ├── utils/                # dateGroups.js, validation.js
        ├── pages/                # LoginPage, RegisterPage, ChatPage
        └── components/           # auth/, sidebar/, chat/, ui/
```

## 3. Setup

**Prerequisites:** Python 3.11+, Node 18+, Docker (for MongoDB + Qdrant), an OpenAI-compatible API key.

### 3.1 Start MongoDB and Qdrant
```bash
docker compose up -d
```
(Or use your own: MongoDB Atlas + Qdrant Cloud — set `MONGODB_URI`, `QDRANT_URL`, `QDRANT_API_KEY`.)

### 3.2 Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env
```
Edit `.env`: set `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`) and `OPENAI_API_KEY`.

Index the sample knowledge base into Qdrant (creates the collection `health_fitness_kb`, cosine, 1536 dims):
```bash
python -m scripts.ingest_kb
```
Run the API:
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive API docs (development only): http://localhost:8000/docs

### 3.3 Frontend
```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173  (proxies /api -> http://localhost:8000)
```
Production build: `npm run build` (output in `frontend/dist`).

### 3.4 Run the tests
```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```
Tests need no running services: MongoDB is mocked (`mongomock-motor`), Qdrant runs in-memory, and the LLM/embeddings are deterministic fakes.

## 4. Environment variables (`backend/.env`)

| Variable | Purpose | Default |
| --- | --- | --- |
| `ENVIRONMENT` | `development` or `production` (production: Secure cookie, docs disabled) | `development` |
| `SECRET_KEY` | JWT signing key, **min 32 chars** | *(required)* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session lifetime | `720` |
| `COOKIE_NAME` / `COOKIE_SAMESITE` / `COOKIE_SECURE` | Cookie flags (`COOKIE_SECURE` empty = auto) | `access_token` / `lax` / auto |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |
| `MONGODB_URI`, `MONGODB_DB_NAME` | MongoDB | `mongodb://localhost:27017`, `health_coach` |
| `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` | Qdrant | `http://localhost:6333`, empty, `health_fitness_kb` |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL` | LLM + embeddings provider (any OpenAI-compatible API) | *(key required)* |
| `LLM_MODEL` | Chat model | `gpt-4o-mini` |
| `EMBEDDING_MODEL`, `EMBEDDING_DIM` | Embedding model and its vector size (**must match**) | `text-embedding-3-small`, `1536` |
| `RAG_TOP_K`, `RAG_SCORE_THRESHOLD` | Retrieval size and minimum cosine similarity | `4`, `0.30` |
| `MAX_MESSAGE_LENGTH`, `HISTORY_CONTEXT_MESSAGES` | Message size limit; how many past messages go to the LLM | `4000`, `12` |

Frontend (`frontend/.env`, optional): `VITE_API_BASE_URL` (empty in dev), `VITE_PROXY_TARGET`.

> Changing `EMBEDDING_MODEL`/`EMBEDDING_DIM` after indexing? Re-index with `python -m scripts.ingest_kb --recreate`. The app refuses to start if the collection dimension and `EMBEDDING_DIM` disagree.

## 5. API contract

All routes except register/login require the session cookie. Errors look like `{"detail": "...", "code": "...", "errors": [{"field","message"}]}`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create account (validates fields, rejects duplicate email with 409) and sign in |
| POST | `/api/auth/login` | Verify credentials, set HttpOnly session cookie |
| POST | `/api/auth/logout` | Revoke the token server-side and clear the cookie |
| GET | `/api/auth/me` | Safe profile of the authenticated user |
| POST | `/api/conversations` | Create a conversation (optional `title`) |
| GET | `/api/conversations?limit=50&skip=0` | Current user's conversations, newest activity first (`limit` ≤ 100) |
| GET | `/api/conversations/{id}?limit=100&before={message_id}` | Conversation + bounded message history (`limit` ≤ 200, `has_more`) |
| PATCH | `/api/conversations/{id}` | Rename (`{"title": "..."}`) |
| DELETE | `/api/conversations/{id}` | Delete conversation + its messages (204) |
| POST | `/api/conversations/{id}/messages` | `{"content": "...", "retry_message_id"?: "..."}` -> saves user msg, retrieves, generates, saves reply |

Status codes: `401` unauthenticated, `404` not found **or not yours** (never reveals other users' data), `409` duplicate email / already-answered retry, `422` validation, `502/503` LLM / embedding / Qdrant / DB outage.

## 6. Data model

**MongoDB** (`MONGODB_DB_NAME`)
- `users`: `_id, name, email (normalized, unique), password_hash, created_at, updated_at`
- `conversations`: `_id, user_id, title, title_locked, created_at, updated_at, last_message_at, metadata`
- `messages`: `_id, conversation_id, user_id, role (user|assistant|system), content, created_at, metadata` (assistant `metadata.retrieval` = used flag + sources with `document_id, chunk_id, source, score`)
- `revoked_tokens`: `_id (jti), expires_at` (TTL index, auto-cleaned)

**Indexes** (created automatically on startup): unique `users.email`; `conversations (user_id, last_message_at desc)`; `messages (conversation_id, created_at)`; TTL on `revoked_tokens.expires_at`.

**Qdrant collection** `health_fitness_kb`: cosine distance, `EMBEDDING_DIM` dimensions. Payload: `document_id, chunk_id, source, text, access_scope`. IDs are deterministic (`uuid5(chunk_id)`), so re-running ingestion never duplicates. Qdrant is *not* the source of truth for users or chat history — MongoDB is.

To add your own knowledge: drop `.md` files (`# Title` + `## Section` blocks) into `backend/data/knowledge_base/` and run `python -m scripts.ingest_kb`.

## 7. Design decisions (security, reliability, behaviour)

- **Auth:** bcrypt password hashes (never logged/returned); JWT in an **HttpOnly, SameSite=Lax** cookie (`Secure` in production) so JavaScript can never read it. Lifetime = `ACCESS_TOKEN_EXPIRE_MINUTES` (12 h default). Logout stores the token id in `revoked_tokens`, so a copied token stops working immediately. Login runs a dummy hash for unknown emails (no timing/enumeration leak).
- **CSRF:** SameSite cookie + an `Origin` check on every state-changing request (must be listed in `CORS_ORIGINS`).
- **Ownership:** every query includes `user_id`; IDs are validated (24-hex ObjectId) before touching MongoDB; foreign/invalid IDs both return 404.
- **Errors:** custom handlers return clean JSON — no stack traces, and validation errors never echo submitted passwords. Chat text is not logged.
- **Partial failure:** user message is saved first. If retrieval/LLM fails -> HTTP 502/503 with the saved message; UI shows **Retry**; a fake assistant answer is never stored.
- **Timezone assumption:** date clusters use the **browser's timezone** (`Intl`), recalculated from `last_message_at` every minute, so a chat moves to Today/Yesterday automatically. Timestamps are stored/returned in UTC.
- **Titles:** the first user message becomes the title (markdown stripped, truncated to 50 chars at a word boundary). Renaming locks the title.
- **RAG honesty:** if no chunk passes `RAG_SCORE_THRESHOLD`, the prompt tells the model no context was found; factual questions then get the fallback sentence from the brief (*"Mujhe iska support ya data nahi mila ..."* or its English equivalent). Greetings and plan-building from the user's own inputs still work.
- **Production:** serve the frontend and API under the same domain behind HTTPS (reverse proxy `/api` -> FastAPI) and set `ENVIRONMENT=production`, a real `SECRET_KEY`, and `CORS_ORIGINS` to your site origin. For a cross-site frontend use `COOKIE_SAMESITE=none` (forces `Secure`) and set `VITE_API_BASE_URL`.

## 8. Demo walkthrough (for screenshots / screen recording)

1. Open http://localhost:5173 -> **Register** (try mismatched passwords to see validation) -> auto sign-in.
2. Click **New Chat**, ask *"How much protein do I need per day to build muscle?"* (RAG answer from the knowledge base).
3. Ask *"Mujhe ghar par 3-day beginner workout plan chahiye"* (structured plan + follow-up question).
4. Create a second chat — history is grouped under **Today**; open the first chat again to see its messages restored.
5. **Rename** (pencil icon) and **Delete** (trash icon -> confirmation dialog).
6. Refresh the page, then **Log out** and log back in — everything is still there.
7. Stop the LLM provider (wrong key) and send a message to see the error + **Retry** state.

## 9. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ValidationError ... secret_key` on startup | Set `SECRET_KEY` (≥ 32 chars) in `backend/.env` |
| Server won't start: MongoDB timeout | Run `docker compose up -d` / check `MONGODB_URI` |
| `Qdrant collection ... has dimension X but EMBEDDING_DIM=Y` | Fix `EMBEDDING_DIM` or run ingest with `--recreate` |
| Chat returns 503 "knowledge base unavailable" | Start Qdrant and run `python -m scripts.ingest_kb` |
| Chat returns 502 "couldn't respond" | Check `OPENAI_API_KEY`, `LLM_MODEL`, `OPENAI_BASE_URL` |
| Answers always say "no data found" | Run the ingest script; lower `RAG_SCORE_THRESHOLD` (e.g. 0.2) if your embedding model scores lower |
| Login works but you're logged out on refresh (cross-origin deploy) | Use same-site hosting or `COOKIE_SAMESITE=none` + HTTPS |
