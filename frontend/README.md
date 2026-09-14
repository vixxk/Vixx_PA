# Vixx PA — Frontend

The frontend for Vixx PA, a glassmorphic dark-theme React SPA that provides a dashboard, AI chat interface, project workspaces, payments ledger, report engine, reminders, and third-party integrations.

---

## Tech Stack

- **React 19** with Vite 8
- **Lucide React** — icon library
- **Vanilla CSS** — glassmorphism design system, no Tailwind or CSS modules
- **Hash-based routing** — no React Router dependency; navigation via `window.location.hash`

---

## Project Structure

```
frontend/
├── public/                     # Static assets (favicon, icons)
├── src/
│   ├── main.jsx                # Entry point, renders <App />
│   ├── App.jsx                 # Root component — auth, routing, global state, layout
│   ├── index.css               # Global design system (1100+ lines of CSS variables, glassmorphism, animations)
│   ├── App.css                 # Legacy Vite template styles (unused)
│   ├── assets/                 # Images (hero, logos)
│   ├── components/
│   │   ├── ChatInterface.jsx       # AI chat console with voice, sessions, markdown
│   │   ├── DashboardAnalytics.jsx  # Financial donut chart + budget progress bars
│   │   ├── DashboardStats.jsx      # Stat cards (active projects, pending tasks, events)
│   │   ├── FilesView.jsx           # Pending things tracker by project
│   │   ├── IntegrationsView.jsx    # Google OAuth connection status
│   │   ├── PaymentsView.jsx        # Payments ledger with revenue chart
│   │   ├── ProjectDetailWorkspace.jsx  # Single project workspace (tasks, payments, notepad)
│   │   ├── ProjectsView.jsx        # Portfolio grid of all projects
│   │   ├── RemindersView.jsx       # Scheduled reminders with channel filters
│   │   └── ReportsEngineView.jsx   # PDF report generator with theme picker
│   └── services/
│       └── api.js              # All API client functions (auth, CRUD, AI, sync)
├── .env.example                # Environment variable template
├── eslint.config.js            # ESLint flat config with React hooks + refresh plugins
├── index.html                  # HTML shell
├── package.json                # Dependencies and scripts
└── vite.config.js              # Vite config (React plugin only)
```

---

## Getting Started

### Prerequisites

- **Node.js 18+**
- A running Vixx PA backend (see `../backend/README.md`)

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Base URL for the FastAPI backend |

### 3. Run the Development Server

```bash
npm run dev
```

The app starts at **http://localhost:5173**.

### Other Scripts

| Command | Description |
|---|---|
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint |

---

## Architecture

### State Management

All state lives in `App.jsx` via `useState` — no Redux, Zustand, or Context API. Data flows down through props. On mount, the app auto-boots authentication by calling `/auth/me`, falling back to login, then to a hardcoded default user.

### Navigation

Hash-based routing (no React Router):

| Hash | View |
|---|---|
| `#/` | Dashboard (stats + chat + analytics) |
| `#/projects` | Project portfolio grid |
| `#/projects/:id` | Project detail workspace |
| `#/payments` | Payments ledger |
| `#/reports` | PDF report engine |
| `#/reminders` | Reminders manager |
| `#/files` | Pending things / file tracker |
| `#/integrations` | Google integrations |

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Cmd+K` / `Ctrl+K` | Open command palette |
| `Ctrl+Alt+H` | Dashboard |
| `Ctrl+Alt+P` | Projects |
| `Ctrl+Alt+B` | Payments |
| `Ctrl+Alt+R` | Reports |
| `Ctrl+Alt+A` | Reminders |
| `Ctrl+Alt+F` | Files |
| `Ctrl+Alt+I` | Integrations |

### API Client (`src/services/api.js`)

All backend communication is centralized in the `api` object. Auth tokens are stored in `localStorage`. The client supports:

- **Auth**: register, login, logout, profile
- **CRUD**: projects, todos, timeline events, payments, contracts, pending things, reminders
- **AI**: process commands, transcribe audio, session management, feedback
- **Sync**: Google Calendar, Google Sheets (disabled), GitHub issues

### Design System (`src/index.css`)

A fixed dark-theme glassmorphism system with CSS custom properties:

- **Fonts**: Space Grotesk (headings) + Geist (body)
- **Palette**: Matte black backgrounds (`#09090B`), indigo accent (`#6366f1`), ice blue secondary (`#38bdf8`)
- **Glass panels**: Semi-transparent backgrounds with `backdrop-filter: blur` and subtle borders
- **Aurora blobs**: Animated gradient orbs for ambient background
- **Responsive**: Breakpoints at 1024px and 768px; all grids collapse to single column on mobile

---

## Components Overview

| Component | Lines | Purpose |
|---|---|---|
| `App.jsx` | 1036 | Root — auth, routing, global state, layout, command palette |
| `ProjectDetailWorkspace.jsx` | 1855+ | Largest — single project with tasks, payments, notepad, integrations |
| `ChatInterface.jsx` | 1468 | AI chat with voice, sessions, markdown, reasoning timeline |
| `PaymentsView.jsx` | 562 | Ledger with revenue chart and aggregate stats |
| `ReportsEngineView.jsx` | 454 | PDF report generator with theme selector |
| `RemindersView.jsx` | 775 | Reminders with overdue detection and channel filters |
| `FilesView.jsx` | 383 | Pending things organized by project folders |
| `ProjectsView.jsx` | 367 | Project grid with creation modal |
| `DashboardAnalytics.jsx` | 267 | Donut chart + budget progress bars |
| `IntegrationsView.jsx` | 153 | Google OAuth connection management |
| `DashboardStats.jsx` | 36 | Three stat cards |
