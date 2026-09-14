# Vixx PA — Freelancing OS & AI Personal Assistant

Vixx PA is a premium, state-of-the-art Personal Assistant and Freelancing Operating System. It is built as a complete monorepo containing a high-performance **FastAPI backend** powered by **LangGraph AI Agents** and **PostgreSQL**, alongside a modern, rich **React + Vite frontend** styled with vanilla CSS glassmorphic components.

> **Docs**: [Backend README](./backend/README.md) | [Frontend README](./frontend/README.md)

---

## Key Features

1. **Dashboard & Project Workspaces**: Live analytics, tracking milestone progress, remaining balances, and tasks.
2. **AI Chat Interface**: Interactive chat with session memory, voice transcription, and natural language commands for creating projects, tasks, payments, and more.
3. **Payments Ledger**: Dedicated ledger standardizing transactions exclusively in Indian Rupees (₹) with status tracking and revenue charts.
4. **AI Report Engine**: Generates comprehensive PDF summaries (notepad compilations, task logs, payments ledgers) in 6 custom design themes (navy, teal, emerald, charcoal, ruby, dark).
5. **Reminders & SMS Notifications**: Background daemon that sends automated reminders via Twilio SMS.
6. **Third-Party Integrations**: Synchronize tasks and events with Google Calendar, Google Sheets (legacy, disabled), and GitHub repository updates.

---

## Tech Stack

- **Frontend**: React 19, Vite 8, Lucide React (icons), vanilla CSS (glassmorphism design system).
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), LangGraph (agentic workflows), Uvicorn.
- **Database**: PostgreSQL (via `asyncpg`).
- **AI**: Groq API (`llama-3.3-70b-versatile`), Groq Whisper (audio transcription).
- **PDF Generation**: ReportLab with 6 theme templates.
- **SMS**: Twilio.

---

## Directory Structure

```
├── backend/          # FastAPI application, AI agents, database schemas
├── frontend/         # React + Vite interface and API services
├── uploads/          # Local storage for documents, contracts, and generated reports
├── run.sh            # Root starter script to spin up services concurrently
├── .gitignore        # Root gitignore rules
└── README.md         # This file
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** instance running locally or remotely

### 1. Configure Environment Variables

#### Backend
```bash
cd backend
cp .env.example .env
# Edit .env with your keys
```

Key variables:
- `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql+asyncpg://vixx:password@localhost:5432/work_os`)
- `GROQ_API_KEY`: Groq Cloud API Key
- `JWT_SECRET_KEY`: Secret for JWT signing
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN`: Twilio credentials for SMS reminders

#### Frontend (Optional)
```bash
cd frontend
cp .env.example .env
# Default: VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Install Dependencies

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 3. Run the Services

```bash
# From root directory
chmod +x run.sh
./run.sh
```

- **Frontend App**: http://localhost:5173
- **API Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Version Control and Commit Best Practices

- `.env` files are gitignored — never commit credentials.
- Replace secrets with placeholders or configure via environment variables.
- Run `npm run lint` in `frontend/` before pushing.
