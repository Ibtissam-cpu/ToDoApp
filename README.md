# TaskFlow

A persistent todo app with priorities, filters, and productivity stats.
Built with Python + Flask + SQLite — no external services needed.

---

## Quick start (one command)

```bash
pip install flask && python app.py
```

Then open **http://localhost:5000** in your browser.

> **Requirements:** Python 3.8+ and pip (that's it — SQLite is built into Python).

---

## Full steps (fresh machine)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd taskflow

# 2. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install the single dependency
pip install -r requirements.txt

# 4. Run
python app.py
```

Open **http://localhost:5000**.

---

## Features

| Feature | Details |
|---|---|
| Create / edit / delete tasks | Inline editing — click **edit** on any task |
| Priority levels | 🔴 high · ⚡ medium · 🔵 low |
| Filter by status | all · active · done |
| Filter by priority | any combination |
| Sort | newest first · by priority · A–Z |
| Bulk actions | "complete all" and "clear done" |
| Productivity ring | Live % completion with animated SVG |
| **Persistence** | SQLite file `tasks.db` — survives restarts |

---

## Persistence test

```bash
python app.py         # start, add some tasks, stop with Ctrl+C
python app.py         # restart — your tasks are still there
```

The database is stored as `tasks.db` next to `app.py`.
To reset it: `rm tasks.db` (it will be recreated on next run).
