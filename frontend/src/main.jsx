import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const api = async (path, options = {}, token = "") => {
  const headers = { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const error = new Error(data.error || "Something went wrong.");
    error.payload = data;
    error.status = res.status;
    throw error;
  }
  return data;
};

const emptyTask = { title: "", description: "", status: "todo", priority: "medium", due_date: "" };

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("taskflow_token") || "");
  const [user, setUser] = useState(null);
  const [mode, setMode] = useState("register");
  const [auth, setAuth] = useState({ name: "", email: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState("all");
  const [priority, setPriority] = useState("all");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyTask);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(false);

  const logout = () => {
    localStorage.removeItem("taskflow_token");
    setToken("");
    setUser(null);
    setTasks([]);
  };

  const loadTasks = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (filter !== "all") qs.set("status", filter);
      if (priority !== "all") qs.set("priority", priority);
      if (search.trim()) qs.set("search", search.trim());
      const data = await api(`/api/tasks?${qs}`, {}, token);
      setTasks(data.tasks || []);
    } catch (e) {
      if (e.status === 401) logout();
      else setToast(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    api("/api/auth/me", {}, token).then(d => setUser(d.user)).catch(logout);
  }, [token]);

  useEffect(() => { loadTasks(); }, [token, filter, priority, search]);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(""), 2800);
    return () => clearTimeout(id);
  }, [toast]);

  const stats = useMemo(() => ({
    all: tasks.length,
    todo: tasks.filter(t => t.status === "todo").length,
    in_progress: tasks.filter(t => t.status === "in_progress").length,
    completed: tasks.filter(t => t.status === "completed").length,
  }), [tasks]);

  const submitAuth = async e => {
    e.preventDefault();
    setAuthError("");
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const data = await api(endpoint, { method: "POST", body: JSON.stringify(auth) });
      localStorage.setItem("taskflow_token", data.token);
      setToken(data.token);
      setUser(data.user);
      setAuth({ name: "", email: "", password: "" });
    } catch (e) {
      setAuthError(e.payload?.errors ? Object.values(e.payload.errors).join(" ") : e.message);
    }
  };

  const saveTask = async e => {
    e.preventDefault();
    setError("");
    try {
      const endpoint = editing ? `/api/tasks/${editing}` : "/api/tasks";
      await api(endpoint, {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify(form),
      }, token);
      setModal(false);
      setEditing(null);
      setForm(emptyTask);
      setToast(editing ? "Task updated." : "Task created.");
      loadTasks();
    } catch (e) {
      setError(e.payload?.errors ? Object.values(e.payload.errors).join(" ") : e.message);
    }
  };

  const editTask = task => {
    setEditing(task.id);
    setForm({
      title: task.title,
      description: task.description,
      status: task.status,
      priority: task.priority,
      due_date: task.due_date || "",
    });
    setError("");
    setModal(true);
  };

  const deleteTask = async task => {
    if (!confirm(`Delete "${task.title}"?`)) return;
    try {
      await api(`/api/tasks/${task.id}`, { method: "DELETE" }, token);
      setToast("Task deleted.");
      loadTasks();
    } catch (e) {
      setToast(e.message);
    }
  };

  const statusUpdate = async (task, status) => {
    try {
      await api(`/api/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ status }) }, token);
      loadTasks();
    } catch (e) {
      setToast(e.message);
    }
  };

  if (!token || !user) {
    return (
      <main className="auth">
        <section className="auth-card">
          <div className="logo"><span>TF</span><b>TaskFlow</b></div>
          <p className="eyebrow">TASK MANAGEMENT APPLICATION</p>
          <h1>{mode === "register" ? "Turn a messy list into a plan." : "Welcome back."}</h1>
          <p className="muted">Plan tasks, track progress and keep work moving from one focused dashboard.</p>
          <form onSubmit={submitAuth}>
            {mode === "register" && <label>Name<input value={auth.name} onChange={e => setAuth({ ...auth, name: e.target.value })} placeholder="Your name" /></label>}
            <label>Email<input type="email" value={auth.email} onChange={e => setAuth({ ...auth, email: e.target.value })} placeholder="you@example.com" /></label>
            <label>Password<input type="password" value={auth.password} onChange={e => setAuth({ ...auth, password: e.target.value })} placeholder="At least 8 characters" /></label>
            {authError && <div className="error">{authError}</div>}
            <button className="primary">{mode === "register" ? "Create account" : "Log in"}</button>
          </form>
          <button className="link" onClick={() => { setMode(mode === "register" ? "login" : "register"); setAuthError(""); }}>
            {mode === "register" ? "Already have an account? Log in" : "Need an account? Register"}
          </button>
        </section>
        <section className="auth-art"><div className="orbit"></div><div className="float-card a"><small>01</small><b>Plan</b><span>Break work into tasks.</span></div><div className="float-card b"><small>02</small><b>Move</b><span>Change status as you work.</span></div><div className="float-card c"><small>03</small><b>Finish</b><span>Keep a clean done list.</span></div></section>
      </main>
    );
  }

  return (
    <main>
      <header className="topbar"><div className="logo"><span>TF</span><b>TaskFlow</b></div><div className="top-actions"><span>{user.name}</span><button className="secondary" onClick={logout}>Log out</button></div></header>
      <div className="wrap">
        <section className="hero"><div><p className="eyebrow">PERSONAL WORKSPACE</p><h1>Good to see you, {user.name.split(" ")[0]}.</h1><p className="muted">Plan the work. Track the work. Finish the work.</p></div><button className="primary" onClick={() => { setEditing(null); setForm(emptyTask); setError(""); setModal(true); }}>+ New task</button></section>

        <section className="stats">
          {[[stats.all, "All tasks", ""], [stats.todo, "To do", "blue"], [stats.in_progress, "In progress", "amber"], [stats.completed, "Completed", "green"]].map(([value, label, cls]) => <div className="stat" key={label}><span>{label}</span><b className={cls}>{value}</b></div>)}
        </section>

        <section className="toolbar">
          <div className="tabs">{[["all","All"],["todo","To do"],["in_progress","In progress"],["completed","Completed"]].map(([v,l]) => <button key={v} className={filter === v ? "active":""} onClick={() => setFilter(v)}>{l}</button>)}</div>
          <div className="filters"><select value={priority} onChange={e => setPriority(e.target.value)}><option value="all">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search tasks..." /></div>
        </section>

        <section className="grid">
          <div className="panel"><div className="panel-head"><div><p className="eyebrow">TASKS</p><h2>{loading ? "Loading..." : `${tasks.length} task${tasks.length === 1 ? "" : "s"}`}</h2></div><span>Your tasks only</span></div>
            {tasks.length === 0 && !loading ? <div className="empty"><div className="check">✓</div><h3>No tasks here yet.</h3><p>Create one to start tracking your work.</p><button className="primary" onClick={() => { setEditing(null); setForm(emptyTask); setModal(true); }}>Create a task</button></div> :
              <div className="task-list">{tasks.map(task => <article className="task" key={task.id}><div className="task-info"><span className={`status ${task.status}`}>{task.status === "todo" ? "To do" : task.status === "in_progress" ? "In progress" : "Completed"}</span><h3>{task.title}</h3>{task.description && <p>{task.description}</p>}<div className="meta"><span className={`priority ${task.priority}`}>{task.priority} priority</span><span>{task.due_date || "No due date"}</span></div></div><div className="task-actions"><select value={task.status} onChange={e => statusUpdate(task,e.target.value)}><option value="todo">To do</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select><button className="icon" onClick={() => editTask(task)}>Edit</button><button className="icon danger" onClick={() => deleteTask(task)}>Delete</button></div></article>)}</div>}
          </div>
          <aside className="panel side"><p className="eyebrow">WORKFLOW</p><h2>Status</h2><div className="workflow"><p><span className="dot blue"></span>To do <b>{stats.todo}</b></p><p><span className="dot amber"></span>In progress <b>{stats.in_progress}</b></p><p><span className="dot green"></span>Completed <b>{stats.completed}</b></p></div><div className="note"><b>Authorization built in</b><p>Every task query is scoped to the logged-in user's ID.</p></div></aside>
        </section>
      </div>

      {modal && <div className="backdrop" onMouseDown={e => e.target === e.currentTarget && setModal(false)}><form className="modal" onSubmit={saveTask}><div className="panel-head"><div><p className="eyebrow">{editing ? "EDIT TASK" : "NEW TASK"}</p><h2>{editing ? "Update task" : "Create a task"}</h2></div><button type="button" className="close" onClick={() => setModal(false)}>×</button></div><label>Title<input autoFocus value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></label><label>Description<textarea rows="4" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label><div className="two"><label>Status<select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}><option value="todo">To do</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></label><label>Priority<select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label></div><label>Due date<input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} /></label>{error && <div className="error">{error}</div>}<div className="modal-actions"><button type="button" className="secondary" onClick={() => setModal(false)}>Cancel</button><button className="primary">{editing ? "Save changes" : "Create task"}</button></div></form></div>}
      {toast && <div className="toast">{toast}</div>}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
