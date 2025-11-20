Project: futurePOS — quick instructions for AI coding agents

Summary
- This is a small Django project where a single app, `nano`, contains most business logic (views, models, templates, migrations).
- The Django project package is `confige` (settings in `confige/settings.py`). Database is SQLite (`db.sqlite3` at repo root).

What to edit and why
- App code: change behavior in `nano/views.py`, `nano/models.py`, `nano/urls.py` — `nano` is the primary app.
- Project wiring: `confige/settings.py` and `confige/urls.py` control global settings and root URL conf.
- Templates and static assets live under `templates/` and `static/nano/`.

Important patterns & examples
- URL organization: `nano/urls.py` groups routes by feature. Examples:
  - Notification APIs: `api/notifications/`, `api/check_role/` (see `nano/urls.py`)
  - Warehouse features under `warehouse/` (import/compare/export endpoints)
  - UPC lookup uses `nano/upc_views.py` and routes `upc/lookup/`
- Views: many view functions are plain Django function views (no class-based views). Prefer following the existing style (return HttpResponse/JsonResponse or render templates).

Developer workflows (how to run & debug)
- Activate the included venv (Windows PowerShell):
  - .\envi\Scripts\Activate.ps1
- Run dev server from project root (ensures `nano` module is importable):
  - python manage.py runserver
- Run Django tests (creates an isolated test DB):
  - python manage.py test
  (some repository tests may also be runnable with `pytest` if you install it)

Common issues and troubleshooting
- ModuleNotFoundError: No module named 'nano.urls'
  - Cause: running commands from outside the project root or without the venv activated so Python path doesn't include the repo root.
  - Fix: cd to the repository root (where `manage.py` lives) and activate `.\envi\Scripts\Activate.ps1`, then run `python manage.py runserver` or `python manage.py test`.
- DB / migrations: this repo uses SQLite at `db.sqlite3` and keeps migrations in `nano/migrations/`. Run `python manage.py migrate` after creating a venv.

Where to look for more context
- API & feature docs: markdown files in repo root (e.g., `UPC_INTEGRATION_GUIDE.md`, `MARKETING_DASHBOARD_GUIDE.md`) describe business rules.
- Tests: root-level `test_*.py` and `nano/tests.py` show expected behavior; read them to understand edge cases and data shapes.
- Management commands: `nano/management/commands/` contains custom commands.

Contract for changes
- Inputs: change only files inside `nano/` or `confige/` unless the change requires new top-level files.
- Outputs: keep migration files under `nano/migrations/` and do not modify `db.sqlite3` unless intentional.
- Error modes: prefer raising informative exceptions or returning JSON error payloads for API endpoints.

If unsure, ask these quick questions
1. Do you want a runtime change (views/templates) or data/schema change (models/migrations)?
2. Should I update tests or only the implementation? Point to a failing test if available.

---
Feedback request: tell me any missing files or conventions I should be aware of (CI, required env vars, 3rd-party services, or where secrets are stored).
