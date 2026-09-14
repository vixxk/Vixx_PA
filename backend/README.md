# Vixx PA — Backend

FastAPI backend powering Vixx PA. Provides a REST API for project management, payments, reminders, and reports, backed by PostgreSQL and an AI orchestrator built with LangGraph agents running on Groq (`llama-3.3-70b-versatile`).

---

## Tech Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy 2.0** (async) with **asyncpg** — PostgreSQL ORM
- **LangGraph** — agentic AI workflow orchestration
- **Groq API** — LLM inference (`llama-3.3-70b-versatile`)
- **Uvicorn** — ASGI server
- **ReportLab** — PDF generation
- **Twilio** — SMS notifications

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI entry point — app init, CORS, routers, startup events
│   ├── config.py               # Pydantic Settings (reads from .env)
│   ├── database.py             # Async SQLAlchemy engine, session factory, get_db dependency
│   ├── models/                 # SQLAlchemy ORM models (13 tables)
│   │   ├── user.py                 # User accounts
│   │   ├── project.py              # Projects with status, priority, budget, risks, notepad
│   │   ├── milestone.py            # Project milestones
│   │   ├── todo.py                 # Tasks with priority, status, hours tracking
│   │   ├── timeline_event.py       # Timeline events (milestones, payments, meetings)
│   │   ├── payment.py              # Payment records (INR)
│   │   ├── contract.py             # Contract files and metadata
│   │   ├── pending_thing.py        # Pending items / file attachments
│   │   ├── reminder.py             # Scheduled reminders (SMS/email)
│   │   ├── conversation_log.py     # Chat message history
│   │   ├── entity_memory.py        # Long-term entity facts
│   │   ├── session_summary.py      # Compressed session summaries
│   │   └── session_state.py        # Serialized workflow state
│   ├── schemas/                # Pydantic request/response models
│   ├── routers/                # API route handlers (10 routers)
│   │   ├── auth.py                 # Registration, login, JWT, Google OAuth
│   │   ├── project.py              # Project CRUD
│   │   ├── todo.py                 # Todo CRUD
│   │   ├── timeline.py             # Timeline event CRUD
│   │   ├── payment.py              # Payment CRUD
│   │   ├── contract.py             # Contract CRUD with file upload
│   │   ├── pending_thing.py        # Pending thing CRUD with file upload
│   │   ├── reminder.py             # Reminder CRUD + test SMS
│   │   ├── ai.py                   # AI command processor, transcription, sessions
│   │   ├── sync.py                 # Google Calendar, GitHub sync
│   │   └── reminder.py             # Reminder management
│   ├── agents/                 # LangGraph agent nodes
│   │   ├── router_agent.py         # Intent classification
│   │   ├── requirement_agent.py    # Natural language field extraction
│   │   ├── clarification_agent.py  # Validation and clarification
│   │   ├── timeline_agent.py       # Milestone/timeline generation
│   │   ├── todo_agent.py           # Task generation
│   │   ├── sprint_agent.py         # Sprint assignment
│   │   ├── risk_agent.py           # Risk identification
│   │   └── summary_agent.py        # Kickoff summary generation
│   ├── graphs/                 # LangGraph workflow definition
│   │   ├── state.py                # WorkflowState TypedDict
│   │   └── workflow.py             # StateGraph: router -> extractor -> clarifier -> pipeline
│   ├── services/               # Business logic layer
│   │   ├── memory_service.py       # 3-tier memory (session, entity, long-term)
│   │   ├── entity_resolver.py      # Fuzzy entity matching
│   │   ├── project_service.py      # Project CRUD + LLM formatting
│   │   ├── task_service.py         # Todo CRUD + PDF generation
│   │   ├── payment_service.py      # Payment CRUD + PDF generation
│   │   ├── timeline_service.py     # Timeline CRUD
│   │   ├── reminder_service.py     # Reminder CRUD
│   │   ├── pending_service.py      # Pending thing CRUD
│   │   ├── report_service.py       # PDF report generation with themes
│   │   └── analytics_service.py    # Analytics cache (stub)
│   ├── tools/                  # External integration tools
│   │   ├── calendar_tool.py        # Google Calendar event creation
│   │   └── github_tool.py          # GitHub issue creation
│   └── utils/                  # Utility modules
│       ├── llm.py                  # ChatGroq LLM factory
│       ├── auth_helper.py          # JWT creation/verification, password hashing
│       ├── pdf_generator.py        # Core ReportLab PDF generation
│       ├── pdf_generator_templates.py  # Report templates (notepad, todo, payments)
│       ├── reminder_daemon.py      # Background reminder scheduler
│       ├── notification_helper.py  # Twilio SMS helper
│       ├── sync_helper.py          # Google Sheets helpers (disabled)
│       ├── timezone_helper.py      # Local-to-UTC conversion
│       ├── validators.py           # Input validation
│       └── clear_db.py             # Database reset utility
├── seed_db.py                  # Database seeder (4 projects, tasks, payments, etc.)
├── requirements.txt            # Python dependencies
├── google_sheets_config.json   # Google Sheet IDs (legacy)
├── notification_logs/          # Reminder daemon log output
├── uploads/                    # Generated PDFs, contract files
├── .env.example                # Environment variable template
└── .gitignore
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **PostgreSQL** running locally or remotely

### 1. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://user:pass@host:5432/dbname`) |
| `GROQ_API_KEY` | Groq Cloud API key for LLM inference |
| `JWT_SECRET_KEY` | Secret key for JWT token signing |
| `TWILIO_ACCOUNT_SID` | Twilio account SID (for SMS reminders) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `GITHUB_ACCESS_TOKEN` | GitHub personal access token |

### 4. Seed the Database (Optional)

```bash
python seed_db.py
```

Creates a default user, 4 projects, 10 tasks, 8 payments, 2 contracts, 3 reminders, and sample AI conversation logs.

### 5. Run the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or from the project root: `./run.sh`

- **API Base**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## API Endpoints

All routes are prefixed with `/api/v1`.

### Authentication (`/auth`)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login (OAuth2 form), returns JWT |
| GET | `/auth/me` | Get current user profile |
| GET | `/auth/google/callback` | Google OAuth callback |

### Projects (`/projects`)

| Method | Path | Description |
|---|---|---|
| GET | `/projects/` | List all projects |
| POST | `/projects/` | Create a project |
| GET | `/projects/{id}` | Get project by ID |
| PUT | `/projects/{id}` | Update a project |
| DELETE | `/projects/{id}` | Delete a project |

### Todos (`/todos`)

| Method | Path | Description |
|---|---|---|
| GET | `/todos/` | List todos (optional `?project_id=`) |
| POST | `/todos/` | Create a todo |
| PUT | `/todos/{id}` | Update a todo |
| DELETE | `/todos/{id}` | Delete a todo |

### Timeline (`/timeline`)

| Method | Path | Description |
|---|---|---|
| GET | `/timeline/` | List events (optional `?project_id=`) |
| POST | `/timeline/` | Create a timeline event |
| PUT | `/timeline/{id}` | Update a timeline event |

### Payments (`/payments`)

| Method | Path | Description |
|---|---|---|
| GET | `/payments/` | List all payments |
| POST | `/payments/` | Create a payment |
| PUT | `/payments/{id}` | Update a payment |
| DELETE | `/payments/{id}` | Delete a payment |

### Contracts (`/contracts`)

| Method | Path | Description |
|---|---|---|
| GET | `/contracts/` | List all contracts |
| POST | `/contracts/` | Create contract (multipart file upload) |
| PUT | `/contracts/{id}` | Update a contract |
| DELETE | `/contracts/{id}` | Delete a contract |

### Pending Things (`/pending-things`)

| Method | Path | Description |
|---|---|---|
| GET | `/pending-things/` | List all pending things |
| POST | `/pending-things/` | Create pending thing (multipart file upload) |
| PUT | `/pending-things/{id}` | Update a pending thing |
| DELETE | `/pending-things/{id}` | Delete a pending thing |

### Reminders (`/reminders`)

| Method | Path | Description |
|---|---|---|
| GET | `/reminders/` | List all reminders |
| POST | `/reminders/` | Create a reminder |
| PUT | `/reminders/{id}` | Update a reminder |
| DELETE | `/reminders/{id}` | Delete a reminder |
| DELETE | `/reminders/` | Clear all reminders |
| POST | `/reminders/test-sms` | Send diagnostic test SMS |

### AI Orchestrator (`/ai`)

| Method | Path | Description |
|---|---|---|
| POST | `/ai/process` | Main AI command processor (LangGraph workflow) |
| POST | `/ai/transcribe` | Transcribe audio via Groq Whisper |
| POST | `/ai/feedback` | Log user feedback (thumbs up/down) |
| GET | `/ai/sessions` | List all conversation sessions |
| PUT | `/ai/sessions/{id}/rename` | Rename a session |
| DELETE | `/ai/sessions/{id}` | Delete a session |

### Integrations (`/sync`)

| Method | Path | Description |
|---|---|---|
| GET | `/sync/google/auth` | Get Google OAuth URL |
| GET | `/sync/google/callback` | Google OAuth callback |
| POST | `/sync/calendar` | Sync milestones to Google Calendar |
| POST | `/sync/github` | Sync todos to GitHub issues |

---

## AI Workflow

The AI orchestrator uses a **LangGraph StateGraph** with 8 agent nodes:

```
router -> extractor -> clarifier -> [conditional]
                                        |
                                  ┌─────┴─────┐
                                  │            │
                                (end)    timeline -> todo -> sprint -> risk -> summary -> end
```

**Flow:**
1. **Router** classifies user intent (`create_project`, `create_task`, `track_payment`, `set_reminder`, etc.)
2. **Extractor** pulls structured fields from natural language using LLM
3. **Clarifier** validates fields, asks for missing info, or handles conversation
4. If intent is `create_project`, the full pipeline runs:
   - **Timeline** generates milestones and events
   - **Todo** generates actionable tasks
   - **Sprint** assigns tasks to sprint buckets
   - **Risk** identifies potential risks with mitigations
   - **Summary** builds a Markdown kickoff brief
5. The dispatcher in `ai.py` routes the final state to the appropriate service for database persistence

### Memory System

Three-tier memory in `memory_service.py`:
- **Session Memory**: Per-conversation chat history stored in `conversation_logs`
- **Entity Memory**: Cross-session facts about entities (projects, clients) in `entity_memory`
- **Long-term Memory**: Auto-generated session summaries in `session_summaries`

### Background Daemon

A `reminder_daemon` starts at server boot and continuously checks for due reminders, sending SMS notifications via Twilio.

---

## Database Schema

13 tables with the following key relationships:

```
User 1:N Project 1:N Milestone 1:N Todo
                   1:N TimelineEvent
                   1:N Payment
                   1:N Contract
                   1:N PendingThing
User 1:N Reminder
```

| Table | Purpose |
|---|---|
| `users` | User accounts with email/password |
| `projects` | Workspace projects with status, priority, budget, risks, notepad |
| `milestones` | Project milestones with start/end dates |
| `todos` | Tasks with priority, status, estimated/actual hours |
| `timeline_events` | Events (milestones, payments, deadlines, meetings) |
| `payments` | Payment records (all in INR) |
| `contracts` | Contract metadata and file references |
| `pending_things` | Pending items and file attachments |
| `reminders` | Scheduled reminders with channel (sms/email/both) |
| `conversation_logs` | AI chat message history |
| `entity_memory` | Long-term entity facts learned across sessions |
| `session_summaries` | Compressed session summaries for long-term recall |
| `session_state` | Serialized workflow state for multi-turn conversations |

---

## PDF Report Generation

Reports are generated via ReportLab with 6 built-in themes:

| Theme | Primary Color |
|---|---|
| Navy | Deep blue |
| Teal | Teal/cyan |
| Emerald | Green |
| Charcoal | Dark gray |
| Ruby | Deep red |
| Dark | Black/near-black |

Report types: **Notepad** (project notes compilation), **To-Do List** (task export), **Payments Ledger** (transaction history).

---

## Key Configuration (`config.py`)

All settings are loaded from `.env` via Pydantic Settings:

| Category | Settings |
|---|---|
| Server | `PORT`, `HOST`, `DEBUG` |
| Database | `DATABASE_URL` (auto-enforces SSL for PostgreSQL) |
| Auth | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` |
| AI | `GROQ_API_KEY`, `GROQ_MODEL` |
| Google | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` |
| GitHub | `GITHUB_ACCESS_TOKEN`, `GITHUB_CLIENT_ID` |
| Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
