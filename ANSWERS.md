# ANSWERS.md

---

## 1. How to run

**One-liner (assumes Python 3.8+ and pip):**

```bash
pip install flask && python app.py
```

Then open **http://localhost:5000** (or **http://127.0.0.1:5000/**).

**Full steps on a truly fresh machine:**

```bash
git clone https://github.com/Ibtissam-cpu/ToDoApp.git && cd taskflow
python -m venv venv
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# Windows (cmd):        venv\Scripts\activate
# macOS/Linux:          source venv/bin/activate
pip install -r requirements.txt
python app.py
```

No database setup required — SQLite is part of Python's standard library.
`tasks.db` is created automatically on first run, in the same directory as `app.py`.

---

## 2. Stack choice

**Why Python + Flask + SQLite:**

- **SQLite** is the right choice for a single-user persistent app: zero configuration,
  no server process, the database is a plain file that survives restarts by design.
  Python ships SQLite in its standard library, so there is literally no extra install.
- **Flask** is the thinnest reasonable web framework: one file, clear routing, and
  nothing fighting me when I want to write plain SQL. The whole backend fits in ~160 lines.
- **Vanilla JS frontend** avoids a build step entirely. The evaluator runs `python app.py`
  and it works — no `npm install`, no bundler, no transpilation.

**What would have been a worse choice — Node.js + a file-based JSON store:**

Using `fs.writeFileSync` on a JSON file seems simple, but it introduces a real corruption
risk: if the process is killed mid-write the file ends up truncated. SQLite uses
write-ahead logging and atomic commits, so it is safe by default. A JSON file store
would fail the evaluator's "close the app unexpectedly and restart" test at some point.

A React/Next.js frontend would have been worse here too: it adds `npm install` and a
build step for a project where the entire UI is 250 lines of HTML+CSS+JS.

---

## 3. One real edge case

**Empty-title validation — `app.py` line 71:**

```python
if not title:
    return jsonify({"error": "Title cannot be empty"}), 400
```

The same check is repeated for PATCH updates at line 97.

**What it handles:**  
A user (or a script) can POST `{"title": "   "}` — a string of spaces.
The code calls `.strip()` on the raw input before this check, so a whitespace-only
title is treated as empty and rejected with HTTP 400 before reaching the database.

**Without this handling:**  
SQLite has a `CHECK(length(trim(title)) > 0)` constraint at the schema level (line 15),
so the database *would* reject it, but it would raise an `sqlite3.IntegrityError`
exception that Flask would turn into an unformatted 500 error.  
Worse, the frontend would receive a 500 with no useful message, and the error toast
would show "Internal Server Error" instead of "Title cannot be empty".  
The explicit Python check gives a clean 400 with a human-readable error before the
database layer is ever touched.

---

## 4. AI usage

I used **Claude (claude.ai)** throughout this project.

| Where | What I asked | What it gave me |
|---|---|---|
| Initial scaffold | "SQLite CRUD app skeleton" |`init_db` |
| Frontend design | "Todo UI with priority dots and animated SVG ring" | CSS |

**One thing I changed about the AI output:**

The initial `update_task` function the AI generated used a Python `dict` to build the
`SET` clause, which iterated in insertion order but silently dropped unknown keys without
error. I replaced it with an explicit `fields / params` list approach (current lines 82–112)
so that:

1. Unknown keys are ignored without masking bugs.
2. The `updated_at` timestamp is always appended *last*, making the SQL construction
   order predictable and easy to read in a debugger.

---

## 5. Honest gap

**The gap: no authentication / multi-user isolation.**

Right now, `tasks.db` is a single shared file. If two people open the app on the same
machine (or the same server is exposed to the internet), they see each other's tasks.
For the assessment this is fine — it is a single-user local app — but it is the first
thing that would break in any real deployment.

**What I would do with another day:**

Add a minimal session-based auth layer:

1. A `users` table with `id`, `username`, `password_hash` (bcrypt).
2. A `user_id` foreign key on `tasks`.
3. Flask-Login (or a hand-rolled session cookie) so every API route filters by
   `current_user.id`.
4. A simple `/register` and `/login` page — no OAuth, just username + password.

This would make the app genuinely multi-user without adding a new dependency beyond
`flask-login` and `bcrypt`, both of which are `pip install` one-liners.
