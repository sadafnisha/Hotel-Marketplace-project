# HotelLease Marketplace

A full-stack Django web application implementing a hotel leasing/investment marketplace:
Hotel Owners publish leasing opportunities, Buyers/Investors browse, bid, negotiate and
message owners, and an Admin moderates the platform. Built as an MVP against the assignment
specification (see `ASSIGNMENT_SPEC` reference below).

The project is server-rendered (Django Templates + Bootstrap 5) with a **REST API layer added
on top of the same models and business logic**, so the exact same app can be driven from the
browser UI or from any API client (mobile app, script, Postman, a future SPA, etc.) without
any duplication of rules.

## Tech Stack

- **Backend / Frontend:** Django 5.2 (server-rendered templates, Bootstrap 5)
- **REST API:** Django REST Framework 3.15, mounted at `/api/` alongside the existing views
- **Database:** SQLite (default, zero-config for demo/evaluation — swap to PostgreSQL by
  changing `DATABASES` in `hotel_marketplace/settings.py`)
- **Auth:** Django's built-in auth with a custom `User` model (role-based: Owner / Buyer / Admin),
  hashed passwords (PBKDF2 by default), session-based login for the website, and DRF
  Token Authentication for the API, password reset flow
- **Images:** Local `media/` storage via `ImageField` (swap for S3/Cloudinary in production)
- **Styling:** Bootstrap 5 (CDN) + custom CSS in `static/css/style.css`
- **Config:** Secrets/config read from environment variables (optionally via a local `.env`
  file, auto-loaded with `python-dotenv`)

## Apps / Modules

| App          | Responsibility                                                        |
|--------------|-------------------------------------------------------------------------|
| `accounts`   | Custom User model, Owner/Buyer profiles, registration, login, password reset |
| `listings`   | HotelListing, HotelImage, Favourite — CRUD, marketplace search/filter, status workflow |
| `offers`     | Offer + OfferHistory — bidding, accept/reject/counter/withdraw, negotiation trail |
| `chat`       | Conversation + Message — buyer/owner messaging linked to a listing     |
| `dashboard`  | Owner dashboard, Buyer dashboard, custom Admin dashboard + moderation   |
| `api`        | **New.** DRF serializers/views/permissions exposing the above models as a REST API. Contains no models of its own — it's a pure read/write layer over the existing apps. |

Django's built-in admin (`/django-admin/`) is also enabled for full data management as a bonus.

## Setup Instructions

### 1. Clone & create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
This installs Django, Pillow, Django REST Framework, and python-dotenv.

### 3. Environment variables (optional)
The app runs out-of-the-box with safe development defaults — nothing below is required for
local/demo use. For anything beyond that, copy `.env.example` to `.env` and adjust values;
it's loaded automatically on startup (and is already git-ignored):

```bash
cp .env.example .env
```

| Variable                    | Default                                            | Purpose                          |
|------------------------------|-----------------------------------------------------|-----------------------------------|
| `DJANGO_SECRET_KEY`          | dev key baked into settings.py                     | Django secret key                 |
| `DJANGO_DEBUG`               | `True`                                              | Set to `False` in production      |
| `DJANGO_ALLOWED_HOSTS`       | `*`                                                 | Comma-separated allowed hosts     |
| `API_PAGE_SIZE`              | `10`                                                | DRF pagination page size          |
| `DJANGO_EMAIL_BACKEND`       | console backend (prints emails to stdout)           | Email backend for password reset  |
| `DJANGO_DEFAULT_FROM_EMAIL`  | `no-reply@hotellease.demo`                          | From-address for outgoing email   |
| `DJANGO_EMAIL_HOST` / `_PORT` / `_HOST_USER` / `_HOST_PASSWORD` / `_USE_TLS` | empty / `587` / empty / empty / `True` | SMTP config, only used if you switch away from the console backend |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | — | Only needed if you switch `DATABASES` to PostgreSQL (see below) |

### 4. Database setup
Uses SQLite by default — no external database server required.
```bash
python manage.py migrate
```

To use PostgreSQL instead, edit `DATABASES` in `hotel_marketplace/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### 5. Seed demo data
Creates 1 admin (superuser), 5 hotel owners, 5 buyers, ~10 hotel listings (published +
draft/pending), sample offers with negotiation history, and sample conversations.
```bash
python manage.py seed_demo_data
```
Safe to re-run — it skips users/listings that already exist.

### 6. Run the development server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** for the website, or **http://127.0.0.1:8000/api/** for the
browsable API root.

### Demo credentials (created by `seed_demo_data`)
| Role   | Username           | Password      |
|--------|---------------------|---------------|
| Admin  | `admin`             | `AdminPass123`|
| Owner  | `owner1` – `owner5`  | `Password123` |
| Buyer  | `buyer1` – `buyer5`  | `Password123` |

## Key URLs (website)

| Page                         | URL                          |
|-------------------------------|-------------------------------|
| Marketplace (public)          | `/`                            |
| Register                      | `/accounts/register/`          |
| Login                         | `/accounts/login/`             |
| Owner: My Listings            | `/mine/`                       |
| Owner: Create Listing         | `/create/`                     |
| Buyer: Saved Hotels           | `/saved/`                      |
| Offers: My Offers (buyer)     | `/offers/mine/`                |
| Offers: Received (owner)      | `/offers/received/`            |
| Messages / Inbox              | `/messages/`                   |
| Role-aware Dashboard          | `/dashboard/`                  |
| Admin Dashboard                | `/dashboard/admin/`            |
| Django Admin                  | `/django-admin/`               |

## REST API

Mounted at **`/api/`**. It sits entirely alongside the routes above — nothing about the
website changed. Every endpoint enforces the same business rules as the equivalent
template view (see "Business Rules Implemented" below); the API layer reuses the models
and re-implements the same checks rather than introducing a second, divergent set of rules.

**Authentication:** DRF Token Authentication (`Authorization: Token <key>` header) for API
clients, plus Session Authentication so an already-logged-in browser can call the API too.
Passwords are always handled by Django's built-in hashing (PBKDF2) — the API never sees or
stores plaintext passwords beyond the single request that creates/verifies them.

Responses are JSON; list endpoints are paginated (`?page=`, page size via `API_PAGE_SIZE`).
A browsable version of the API (handy for manual testing) is available at `/api/` and
`/api/auth-browsable/` once logged in through the browser.

### Authentication & current user
| Method | Endpoint                  | Access        | Notes |
|--------|-----------------------------|---------------|-------|
| POST   | `/api/auth/register/`      | Public        | `{"username","email","password","role":"owner"\|"buyer","business_name"?,"company_name"?}` — creates the account + matching Owner/Buyer profile, returns a token |
| POST   | `/api/auth/login/`         | Public        | `{"username","password"}` → `{"token","user"}` |
| POST   | `/api/auth/logout/`        | Authenticated | Deletes the caller's token |
| GET    | `/api/users/me/`           | Authenticated | Current user + role-specific profile |
| PATCH  | `/api/users/me/`           | Authenticated | Update own name/email/phone |

### Hotel Listings
| Method | Endpoint                        | Access                  | Notes |
|--------|-----------------------------------|--------------------------|-------|
| GET    | `/api/listings/`                  | Public                  | Published listings only for anonymous/buyers; owners also see their own of any status; admins see all. Supports `?q=&city=&property_type=&min_price=&max_price=&min_rooms=&sort=newest\|price_low\|price_high\|rooms` |
| POST   | `/api/listings/`                  | Owner only              | Creates a new listing with `status=draft` |
| GET    | `/api/listings/{id}/`             | Public (published) / owner / admin | Non-published listings 404 for everyone except the owner/admin |
| PATCH/PUT | `/api/listings/{id}/`          | Owning owner / admin    | 403 for anyone else |
| DELETE | `/api/listings/{id}/`             | Owning owner / admin    | |
| GET    | `/api/listings/mine/`             | Owner                   | All of the caller's own listings, any status |
| POST   | `/api/listings/{id}/publish/`     | Owning owner            | Draft → Pending Approval |
| POST   | `/api/listings/{id}/unpublish/`   | Owning owner            | → Draft |
| POST   | `/api/listings/{id}/close/`       | Owning owner            | → Closed (stops new offers) |

### Favourites
| Method | Endpoint                    | Access      | Notes |
|--------|-------------------------------|-------------|-------|
| GET    | `/api/favourites/`            | Buyer       | The caller's saved listings |
| POST   | `/api/favourites/`            | Buyer       | `{"listing": <id>}` — must be a published listing |
| DELETE | `/api/favourites/{id}/`       | Owning buyer | |

### Offers
| Method | Endpoint                     | Access                        | Notes |
|--------|--------------------------------|--------------------------------|-------|
| GET    | `/api/offers/`                 | Buyer/owner (own offers) / admin (all) | |
| POST   | `/api/offers/`                 | Buyer only                    | `{"listing","amount","proposed_terms"?,"message"?}`. Rejected if the listing isn't published, or the buyer already has an active (pending/countered) offer on it |
| GET    | `/api/offers/{id}/`            | Buyer, owner, or admin involved | 404 for anyone else |
| GET    | `/api/offers/mine/`            | Buyer                          | Offers the caller submitted |
| GET    | `/api/offers/received/`        | Owner                          | Offers received on the caller's listings |
| POST   | `/api/offers/{id}/respond/`    | Participant only               | `{"action":"accept"\|"reject"\|"counter"\|"withdraw"\|"accept_counter"\|"reject_counter","amount"?,"message"?}`. `accept`/`reject`/`counter` are owner-only; `withdraw`/`accept_counter`/`reject_counter` are buyer-only |

### Conversations & Messages
| Method | Endpoint                              | Access                     | Notes |
|--------|-----------------------------------------|-----------------------------|-------|
| GET    | `/api/conversations/`                   | Buyer/owner (own threads) / admin | Inbox list |
| POST   | `/api/conversations/`                   | Buyer only                 | `{"listing": <id>}` — starts (or reuses) a thread with the listing's owner |
| GET    | `/api/conversations/{id}/`              | The two participants / admin | Includes messages; marks the other party's unread messages as read |
| POST   | `/api/conversations/{id}/messages/`     | The two participants        | `{"body": "..."}` |

### Admin (protected, `role=admin`/staff/superuser only)
| Method | Endpoint                                   | Notes |
|--------|-----------------------------------------------|-------|
| GET    | `/api/admin/users/`                           | `?role=owner\|buyer` filter |
| POST   | `/api/admin/users/{id}/toggle-status/`        | Suspend/reactivate a user |
| GET    | `/api/admin/listings/`                        | `?status=` filter, any status |
| POST   | `/api/admin/listings/{id}/moderate/`          | `{"action":"approve"\|"reject"\|"suspend"}` |

## Business Rules Implemented

- Only authenticated **Owners** can create/edit their own hotel listings (enforced in both
  the website views and the API).
- Only **Published** listings appear in the public marketplace / API list & retrieve.
- Listing lifecycle: `Draft → Pending Approval → Published / Rejected → Closed`.
- Only authenticated **Buyers** can submit offers; duplicate active offers on the same
  listing by the same buyer are blocked; **Closed** listings reject new offers.
- Owners can **Accept / Reject / Counter** a pending offer; buyers can **Accept / Reject**
  a counter-offer or **Withdraw** their own pending offer.
- Every offer action is recorded in `OfferHistory` for full negotiation traceability.
- Messaging is scoped to a specific listing + buyer + owner pair; only the two parties
  (or an admin) can view or post into a conversation.
- Admin-only routes (moderation, user management) are protected by role in both the
  Django views (`user_passes_test`) and the API (`IsAdminRole` permission).
- Passwords are always created/verified through Django's built-in auth system
  (`set_password` / `authenticate`), so hashing and validation rules are identical
  everywhere — website, admin, and API.

## Testing

### Automated tests
```bash
python manage.py test            # full suite
python manage.py test api        # API tests only (61 tests)
```
`api/tests/` covers, with each file focused on one concern:
- `test_auth.py` — registration (incl. password hashing, weak-password/duplicate-email
  rejection), login/logout, `/api/users/me/`, and admin-route protection
- `test_listings.py` — visibility rules (published vs. draft, owner vs. stranger vs. admin),
  create/edit/delete authorization, status transitions
- `test_offers.py` — submission rules (buyer-only, published-only, closed-listing block,
  duplicate-offer guard), and the full accept/reject/counter/withdraw negotiation flow with
  authorization checks
- `test_favourites.py` — buyer-only save/list/remove, ownership scoping
- `test_chat.py` — buyer-initiated conversations, thread reuse, participant-only access,
  sending messages, unread/read-marking

Existing per-app `tests.py` files (`accounts`, `listings`, `offers`, `chat`, `dashboard`)
are left as-is (`django.test.TestCase` scaffolding) for any template/view-level tests you
want to add alongside the new API suite.

### Manual/website testing
The website flows were exercised via automated HTTP requests against the running dev server,
covering: registration/login for each role, listing creation (draft + image formset),
marketplace search/filter, offer submission + duplicate-offer guard, owner counter-offer,
buyer accept/reject-counter and withdraw, messaging (start conversation + send message),
favouriting, and admin listing approval.

## Scope Notes

This is an MVP built for evaluation purposes, not a production-ready commercial platform.
Payment processing, legal contract signing, KYC/identity verification, automated property
valuation, and production-grade real-time infrastructure are intentionally out of scope.
Real-time chat (Socket.IO/WebSockets), email notifications, and map integration are listed
as optional bonus enhancements in the spec and are not implemented here — messaging uses
standard request/response (refresh-based) polling on the website, and simple poll/refresh
on the API side.
