# Vixx PA — Freelancing OS & AI Personal Assistant

Vixx PA is a premium, state-of-the-art Personal Assistant and Freelancing Operating System. It is built as a complete monorepo containing a high-performance **FastAPI backend** powered by **LangGraph AI Agents** and **PostgreSQL**, alongside a modern, rich **React + Vite frontend** styled with vanilla CSS glassmorphic components.

---

## Key Features

1. **Dashboard & Project Workspaces**: Live analytics, tracking milestone progress, remaining balances, and tasks.
2. **AI Chat Interface**: Interactive chat with local system context to execute actions like creating projects, adding tasks, and logging payments.
3. **Payments Ledger**: Dedicated ledger standardizing transactions exclusively in Indian Rupees (₹) with status tracking.
4. **AI Report Engine**: Generates comprehensive PDF summaries (notepad compilations, task logs, payments ledgers) in custom design styles (teal, navy, charcoal, etc.).
5. **Reminders & WhatsApp Sync**: Runs a background daemon that sends automated reminders via the Meta WhatsApp Cloud API.
6. **Third-Party Integrations**: Synchronize tasks and events with Google Calendar, Google Sheets, and GitHub repository updates.

---

## Tech Stack

- **Frontend**: React, Vite, Lucide React (icons), Recharts (charts).
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL ORM), LangGraph (Agentic workflows), Uvicorn.
- **Database**: PostgreSQL (via `asyncpg`).
- **AI**: Groq API (`llama-3.3-70b-versatile`).

---

## Directory Structure

```
├── backend/          # FastAPI application, database schemas, and AI agents
├── frontend/         # React + Vite interface and API services
├── uploads/          # Local storage for documents, contracts, and generated reports
├── run.sh            # Root starter script to spin up services concurrently
├── .gitignore        # Root gitignore rules
└── README.md         # Documentation
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** instance running locally or remotely

### 1. Configure Environment Variables

#### Backend configuration
Go to `backend/`, copy the template, and fill in your keys:
```bash
cd backend
cp .env.example .env
```
Key variables:
- `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql+asyncpg://vixx:password@localhost:5432/work_os`)
- `GROQ_API_KEY`: Groq Cloud API Key
- `META_WHATSAPP_ACCESS_TOKEN` / `PHONE_NUMBER_ID`: WhatsApp API credentials

#### Frontend configuration (Optional)
If you want to run the API on a non-standard port or hostname:
Create a `.env` file in the `frontend` directory:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Install Dependencies

#### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

### 3. Run the Services

Use the root launcher script to start both the FastAPI backend and Vite frontend concurrently:
```bash
# From root directory
chmod +x run.sh
./run.sh
```

- **Frontend App**: `http://localhost:5173`
- **FastAPI API Swagger Docs**: `http://localhost:8000/docs`

---

## Version Control and Commit Best Practices

Before pushing code, make sure:
- Local configurations and credentials in `.env` are not tracked (root and child `.gitignore` rules prevent this).
- Secrets are replaced with placeholders or configured via environmental variables.
- Code matches linting rules and passes initial smoke tests.
