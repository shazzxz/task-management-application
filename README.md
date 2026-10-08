# TaskFlow — Task Management Application

A focused full-stack task management web application built to match the internship brief for Task Management Application.

## Requirements covered

- **User authentication and authorization** — register, login, logout and protected task APIs.
- **CRUD operations for tasks** — create, view, update and delete tasks.
- **Task tracking** — To do, In progress and Completed states.
- **Responsive design** — desktop and mobile-friendly interface.
- **Dynamic data handling** — React frontend communicates with a Flask REST API and persistent database.
- **Real-time updates** — intentionally not included because WebSockets are marked optional in the brief.

## Stack

- **Frontend:** React + Vite + CSS
- **Backend:** Python + Flask REST API
- **Database:** SQLite for zero-setup local persistence
- **Authentication:** JWT
- **Password security:** Werkzeug password hashing

## Why SQLite?

The assignment does not require a specific database or hosting provider. SQLite keeps the project self-contained and easy for a reviewer to run locally without creating an external database account.

The database file (`taskflow.db`) is created automatically the first time the Flask backend starts.

## Project structure

```text
task-management-app/
├── backend/
│   ├── app.py
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── SUBMISSION_CHECKLIST.md
```

## Run locally

### 1. Backend

Open a terminal in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python backend/app.py
```

The API runs on:

`http://localhost:5000`

### 2. Frontend

Open a second terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open:

`http://localhost:5173`

The Vite development server proxies `/api` requests to Flask automatically.

## How to demonstrate the requirements

### Authentication

Register an account, log out, then log back in.

### Authorization

Create a task while logged in. A second account cannot read, update or delete the first account's task because every task API is scoped to the authenticated user ID.

### CRUD

Use **New task** to create a task, edit it, change its status or priority, and delete it.

### Task tracking

Use the status tabs to switch between **All**, **To do**, **In progress**, and **Completed**.

### Dynamic data

Refresh the page after creating a task. The task remains because it is stored in `taskflow.db`, not only in browser memory.

## API endpoints

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/<id>`
- `PATCH /api/tasks/<id>`
- `DELETE /api/tasks/<id>`

## Submission note

The Task Management Application brief shown in the internship portal does **not require deployment**, so this version is intentionally optimized as a clean, fully runnable local project rather than adding unnecessary hosting setup.
