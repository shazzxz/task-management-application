# TaskFlow — Task Management Application

**First Release · v1.0.0**

TaskFlow is a simple full-stack task manager built with React, Flask and SQLite.

The app covers the main requirements of the Task Management Application task: account creation and login, user-level authorization, task CRUD, status tracking and a responsive interface.

## Features

- Register and log in with email and password
- Passwords stored as hashes
- JWT-based authenticated sessions
- Each user sees only their own tasks
- Create, edit and delete tasks
- Task status: To do, In progress, Completed
- Task priority: Low, Medium, High
- Optional due dates
- Search and status/priority filters
- Responsive layout for desktop and mobile
- Persistent SQLite database

Real-time updates are not included because WebSocket updates are optional in the brief.

## Tech stack

- **Frontend:** React + Vite
- **Backend:** Python + Flask
- **Database:** SQLite
- **Authentication:** JWT
- **Password hashing:** Werkzeug

SQLite is used so the project can be cloned and run without setting up a separate database service.

## Project structure

```text
task-management-application/
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
├── setup.bat
├── run_backend.bat
├── run_frontend.bat
└── SUBMISSION_CHECKLIST.md
```

## Running the project

### Windows quick setup

From the project folder:

```bat
setup.bat
```

Then open two terminals:

```bat
run_backend.bat
```

and:

```bat
run_frontend.bat
```

Open **http://localhost:5173**.

### Manual setup

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python backend/app.py
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The Flask API runs on **http://localhost:5000** and Vite runs on **http://localhost:5173**.

The Vite dev server forwards `/api` requests to Flask.

## How to test the application

1. Register a first user.
2. Create a few tasks with different priorities and due dates.
3. Edit a task and move it to **In progress**.
4. Mark a task **Completed**.
5. Try the search and filters.
6. Log out.
7. Register a second user.
8. Verify the second user starts with an empty task list and cannot access the first user's tasks.

## API

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Tasks

- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/<id>`
- `PATCH /api/tasks/<id>`
- `DELETE /api/tasks/<id>`

### Health

- `GET /api/health`

## Data model

### User

```text
id
name
email
password_hash
created_at
```

### Task

```text
id
user_id
title
description
status
priority
due_date
created_at
updated_at
```

Task queries always include the authenticated user's ID, which is what enforces per-user authorization.

## Notes

- The SQLite database file `taskflow.db` is created automatically on first startup.
- `.env.example` documents optional local environment settings.
- The database file and local environment files are excluded from Git.
- No deployment service is required for this project.
