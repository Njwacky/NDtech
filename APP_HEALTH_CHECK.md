# NDtech App Health Check

Date: 2026-10-02 · Branch: `arena/01a0fcf8-ndtech` (HEAD `335c83a` = `origin/main`)

I installed the dependencies, booted the Django app, built the Next.js frontend, ran every
test suite and crawled all 118 reachable pages as an admin user. Below is what I found,
what I fixed, and what is still broken.

---

## TL;DR

| Area | Before | After |
| --- | --- | --- |
| Django system check | clean | clean |
| Django tests | 138/138 pass | 138/138 pass |
| Migrations | up to date | up to date |
| `/airtime/` dashboard | **500 crash** | 200 ✓ |
| `/offline/` (PWA fallback) | **500 crash** | 200 ✓ |
| Service worker | **never installs** | installs ✓ |
| `/warehouse/import/` | **500 NoReverseMatch** | 200 ✓ |
| `/ndtechtrack/performance/` | **500 KeyError** | 200 ✓ |
| `/api/health/` table report | wrong (`auth_user: false`) | correct ✓ |
| Frontend typecheck | clean | clean |
| Next.js build | clean | clean |
| Frontend tests | **could not run at all** | 8/8 pass ✓ |
| Reachable pages returning 200/302 | 92 of 118 | **95 of 118** |

Remaining: **20 pages still return 500 because their templates were never committed to the repo**
(see [Still broken](#still-broken-20-pages--missing-templates)).

---

## Fixed in this pass

### 1. `/airtime/` crashed with a template syntax error (critical)
`nano/templates/nano/airtime_dashboard.html` had 4 Django tags mangled by an HTML
formatter — the `{%` and `%}` were split across lines and the stock check was rewritten
as `product.stock=""  ="0"`:

```django
{%
if
product.stock=""
="0"
%}disabled{%
endif
%}
```

Django's lexer cannot recover from tags split across lines, so the whole page raised
`TemplateSyntaxError: Invalid block tag on line 716: 'endfor', expected 'endif'` — a hard
500 for every cashier/manager opening the airtime dashboard. Repaired all 4 tags
(`{% if product.stock == 0 %}disabled{% endif %}`) and verified the page renders with
in-stock, out-of-stock and request-table data.

### 2. `/offline/` crashed — which also killed the whole PWA
The view renders `nano/offline.html`, which did not exist → 500. Because
`nano/static/nano/sw.js` includes `/offline/` in `cache.addAll(...)`, and `addAll()` is
**atomic** (one bad URL rejects the whole promise), this single missing template meant the
service worker could never install. Created a self-contained offline page (inline CSS/SVG,
no CDN) that shows connection status and auto-reloads when the network returns.

### 3. Service worker cached 5 URLs that don't exist
`sw.js` precached `/accounts/login/`, `/static/nano/styles.css`, `airtime.css`,
`notifications.css`, `hamburger.css`, `/offline/` and a CDN stylesheet. Four of those CSS
files live under `nano/static/nano/css/` (and `styles.css` doesn't exist at all), so
`cache.addAll` rejected and the worker never installed — no offline caching, no background
sync, no push. Fixes:

- replaced the precache list with 11 URLs that actually exist (all verified 200);
- switched to per-URL best-effort caching so one missing asset can never abort install;
- bumped `CACHE_NAME` to `ndtech-pos-v3` so clients pick up the change;
- fixed `respondWith()` resolving to `undefined` on failed non-navigation requests
  (that throws a `TypeError` in the worker) and made `isApiCall()` null-safe.

### 4. `/warehouse/import/` crashed with `NoReverseMatch`
`nano/templates/nano/warehouse_import.html:161` links to `{% url 'download_sample_csv' %}`,
but that URL was never registered. Added the `download_sample_csv` view (admin/manager
only, same rule as the import page) serving `sample_warehouse_import_test.csv`, exported it
through `nano/views/__init__.py` and registered
`/warehouse/import/sample-csv/` in `nano/urls.py`.

### 5. `/ndtechtrack/performance/` crashed with `KeyError: 'latest_score'`
`NDtechTrack/views.py` aggregated with `latest=...` but read the result as
`['latest_score']`. Corrected the key to `['latest']`.

### 6. `/api/health/` reported false table statuses
`database_status()` used `User.objects.exists()` / `SecurityAuditLog.objects.exists()` to
decide whether tables exist — so a healthy database with zero users reported
`"auth_user": false`, which is exactly the kind of signal that makes a deploy look broken.
Now checks `connection.introspection.table_names()`.

### 7. Frontend tests couldn't run
`frontend/` shipped two test files, Jest and Testing Library, but no Jest config, no
transform and no `test` script — `npx jest` failed with *"Support for the experimental
syntax 'jsx' isn't currently enabled"*. Added `jest.config.js` (via `next/jest`),
`jest.setup.js` (jest-dom matchers) and `npm test` / `npm run test:watch` scripts. One test
then failed on an ambiguous `getByText(/cart/i)` query (matched "Shopping Cart Demo",
"Cart" and every "Add to Cart" button); tightened it to the `Cart` heading. **8/8 tests pass.**

---

## Still broken: 20 pages — missing templates

These views render templates that do not exist anywhere in the repository. I confirmed
they are absent from `origin/main` too (not a local checkout problem) — 29 templates are
referenced in total, 20 of them by pages a logged-in admin can reach today. Each returns a
500 the moment someone opens it.

| Page (500) | Missing template |
| --- | --- |
| `/airtime/cashier-quick-sell/` | `nano/cashier_airtime_quick_sell.html` |
| `/audit/` | `nano/audit_dashboard.html` |
| `/audit/api-calls/` | `nano/api_calls.html` |
| `/audit/data-modifications/` | `nano/data_modifications.html` |
| `/audit/security-events/` | `nano/security_events.html` |
| `/audit/sensitive-data/` | `nano/sensitive_data_access.html` |
| `/food/menu/` | `nano/food_menu_browser.html` |
| `/food/scanner/` | `nano/food_scanner.html` |
| `/notifications/` | `nano/notifications_page.html` |
| `/test/fcm/` | `nano/fcm_test.html` |
| `/test/notifications/` | `nano/test_notifications_complete.html` |
| `/tracking/` | `nano/tracking_dashboard.html` |
| `/tracking/activities/` | `nano/user_activity_tracking.html` |
| `/tracking/devices/` | `nano/device_tracking.html` |
| `/tracking/errors/` | `nano/error_tracking.html` |
| `/upc/history/` | `nano/upc_history.html` |
| `/upc/lookup/` | `nano/upc_lookup.html` |
| `/upc/scanner/` | `nano/barcode_scanner.html` |
| `/warehouse/comparisons/marketing/` | `nano/price_comparisons_marketing.html` |

Also referenced but not reachable without extra URL parameters:
`food_ordering/restaurant_analytics.html`, `nano/approve_airtime_request.html`,
`nano/approve_airtime_sale.html`, `nano/audit_access_denied.html`, `nano/delete_user.html`,
`nano/error_details.html`, `nano/reject_airtime_request.html`, `nano/reject_airtime_sale.html`,
`nano/resolve_error.html`.

The backing views and their context variables all exist, and most of the supporting
JS/CSS assets are already in `nano/static/nano/` (e.g. `barcode_scanner.js`,
`food_scanner.js`) — these pages only need their HTML written.

---

## Not bugs (checked, expected)

- **`/login/` and `/dashboard/` return 404** on Django — those are routes of the separate
  Next.js app in `frontend/` (port 3000), not the Django app. Django's login is `/sign_in/`.
- **`/admin/logout/` and `/pos/complete-sale/` return 405** to `GET` — they are POST-only,
  which is correct.
- **No `staticfiles/staticfiles.json`** — production runs `collectstatic` during the build
  (`build.sh`, `render.yaml`, `Dockerfile.prod`), which generates it.
- **`/health/`, `/api/health/`, `/sw.js`, `/manifest.json`** all return 200.

## Minor issues worth queuing

- `nano/static/nano/icon-192.png`, `icon-512.png` and `icon-96.png` are the **same 1.9 MB
  image** (identical MD5). The manifest advertises 192px/512px icons; shipping 3 copies of a
  2 MB PNG is a heavy first-load for a POS app on mobile data.
- `staticfiles/` is committed to git (188 files) but is build output; it also contains
  CSS (`styles.css`, `auth.css`, …) whose source files no longer exist under
  `nano/static/nano/`, so those files cannot be regenerated.
- `nano/templates/registration/login.html` references missing `nano/auth.css` and is not
  rendered by any view (dead template).

---

## How to run it

```bash
# Django (backend + all server-rendered pages)  → http://localhost:8000
pip install -r requirements.txt
cp .env.example .env          # then set DJANGO_SECRET_KEY
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Next.js frontend (separate demo app)          → http://localhost:3000
cd frontend && npm install && npm run dev

# Tests
python manage.py test nano food_ordering NDtechTrack   # 138 pass
cd frontend && npm test                                # 8 pass
```

A local admin login exists in the dev database for exploring the UI:
**`crawl_admin` / `admin123`** (local SQLite only, never deployed).

---

## Getting into a hosted preview

Two problems stopped sign-in from working through a hosted HTTPS preview, and both are fixed.

### 1. Proxy/CSRF mismatch (this was the actual blocker)

`SECURE_PROXY_SSL_HEADER` was commented out, so Django saw every proxied request as plain
HTTP and built an `http://host` origin while the browser sent `https://host`. The mismatch
made **every POST fail** with `403 CSRF verification failed` — sign in, registration,
checkout, everything. The server log was explicit:

```
Forbidden (Origin checking failed - https://8000-xxxx.e2b.app does not match any trusted origins.): /sign_in/
```

Fixes in `confige/settings.py`:
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` is now enabled
  (this is also correct for the Render/nginx deployments, not just previews).
- `CSRF_TRUSTED_ORIGINS` now includes wildcard preview hosts
  (`https://*.e2b.app`, `https://*.arena.site`) in the DEBUG defaults.

### 2. Development-only access flags

Both are **hard-gated on `DEBUG`** in `settings.py`, so setting the environment variable in a
production deployment does nothing:

```python
ALLOW_OPEN_REGISTRATION = DEBUG and config('ALLOW_OPEN_REGISTRATION', default=False, cast=bool)
DEV_QUICK_LOGIN         = DEBUG and config('DEV_QUICK_LOGIN', default=False, cast=bool)
```

| Flag | Effect |
| --- | --- |
| `ALLOW_OPEN_REGISTRATION=True` | Registration stays open after the first account (normally it closes forever once one user exists). New self-registered accounts get **admin + superuser** so every page is reachable. |
| `DEV_QUICK_LOGIN=True` | Adds a **"Quick sign in as admin"** button to `/sign_in/` and a `/dev-login/` endpoint that logs you in as the first superuser. |

With `DJANGO_DEBUG=False` both are forced off, and `/dev-login/` returns a plain redirect to
`/sign_in/`. Verified by simulating production with the flags still set to `True`:

```
DEBUG=False  ALLOW_OPEN_REGISTRATION=False  DEV_QUICK_LOGIN=False   →   /dev-login/ = 302 /sign_in/
```

Both are enabled in the local, gitignored `.env` (and documented as `False` in `.env.example`).

**To get into the preview:** open the app, and either click **“Quick sign in as admin”** on the
sign-in page, or register a new account at `/sign_up/` — it will have full admin rights.
