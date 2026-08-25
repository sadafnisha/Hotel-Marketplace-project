HotelLease Marketplace

A professional hotel leasing and investment marketplace built with Django, PostgreSQL,
Django REST Framework, and Bootstrap 5.

Overview

A full-stack Django web application implementing a hotel leasing/investment marketplace:
Hotel Owners publish leasing opportunities, Buyers/Investors browse, bid, negotiate and
message owners, and an Admin moderates the platform. Built as an MVP against the assignment
specification (see ASSIGNMENT_SPEC reference below).

The project is server-rendered (Django Templates + Bootstrap 5) with a REST API layer added
on top of the same models and business logic, so the exact same app can be driven from the
browser UI or from any API client (mobile app, script, Postman, a future SPA, etc.) without
any duplication of rules.

Technology Stack

Backend / Frontend: Django 5.2 (server-rendered templates, Bootstrap 5)

REST API: Django REST Framework 3.15, mounted at /api/ alongside the existing views

Database: PostgreSQL — configured as the primary relational database through Django's
PostgreSQL backend. Connection settings are environment-driven for secure and flexible
development/production deployments.

Auth: Django's built-in auth with a custom User model (role-based: Owner / Buyer / Admin),
hashed passwords (PBKDF2 by default), session-based login for the website, and DRF
Token Authentication for the API, password reset flow

Images: Local media/ storage via ImageField (swap for S3/Cloudinary in production)

Styling: Bootstrap 5 (CDN) + custom CSS in static/css/style.css

Config: Secrets/config read from environment variables (optionally via a local .env
file, auto-loaded with python-dotenv)

Database Architecture

PostgreSQL is the application's primary database and is integrated directly with Django's ORM.
All core marketplace entities—including users, hotel listings, favourites, offers, offer history,
conversations, and messages—are persisted through Django models backed by PostgreSQL.

The database configuration is environment-driven, making it suitable for local development,
staging, and production deployments without changing application code. Django migrations are
used to manage and version the database schema.

Apps / Modules

App

Responsibility

accounts

Custom User model, Owner/Buyer profiles, registration, login, password reset

listings

HotelListing, HotelImage, Favourite — CRUD, marketplace search/filter, status workflow

offers

Offer + OfferHistory — bidding, accept/reject/counter/withdraw, negotiation trail

chat

Conversation + Message — buyer/owner messaging linked to a listing

dashboard

Owner dashboard, Buyer dashboard, custom Admin dashboard + moderation

api

New. DRF serializers/views/permissions exposing the above models as a REST API. Contains no models of its own — it's a pure read/write layer over the existing apps.

Django's built-in admin (/django-admin/) is also enabled for full data management as a bonus.

Project Architecture

The application follows Django's modular architecture:

Presentation layer: Django Templates + Bootstrap 5

Application layer: Domain-specific Django apps for accounts, listings, offers, chat, and dashboards

API layer: Django REST Framework serializers, views, permissions, and authentication

Persistence layer: Django ORM backed by PostgreSQL

Configuration: Environment-based settings for secrets, database credentials, email, and API options

The REST API and server-rendered website share the same underlying models and business rules,
which helps keep authorization, workflows, and marketplace behavior consistent across clients.

Setup Instructions

1. Clone & create a virtual environment

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

2. Install dependencies

pip install -r requirements.txt

This installs Django, Pillow, Django REST Framework, python-dotenv, and the PostgreSQL database driver required by the application.

3. Configure environment variables

The application is configured to use PostgreSQL as its database. Database credentials and
application secrets should be supplied through environment variables rather than hard-coded
in the project.

Copy the example environment file and update it with your local PostgreSQL configuration:

cp .env.example .env

cp .env.example .env

Variable

Default

Purpose

DJANGO_SECRET_KEY

dev key baked into settings.py

Django secret key

DJANGO_DEBUG

True

Set to False in production

DJANGO_ALLOWED_HOSTS

*

Comma-separated allowed hosts

API_PAGE_SIZE

10

DRF pagination page size

DJANGO_EMAIL_BACKEND

console backend (prints emails to stdout)

Email backend for password reset

DJANGO_DEFAULT_FROM_EMAIL

no-reply@hotellease.demo

From-address for outgoing email

DJANGO_EMAIL_HOST / _PORT / _HOST_USER / _HOST_PASSWORD / _USE_TLS

empty / 587 / empty / empty / True

SMTP config, only used if you switch away from the console backend

DJANGO_DB_NAME

hotel_marketplace

PostgreSQL database name

DJANGO_DB_USER

postgres

PostgreSQL username

DJANGO_DB_PASSWORD

—

PostgreSQL password

DJANGO_DB_HOST

localhost

PostgreSQL server hostname

DJANGO_DB_PORT

5432

PostgreSQL server port

4. PostgreSQL database setup

The project uses PostgreSQL as the configured database backend. Django connects to the
database through django.db.backends.postgresql, with connection details supplied through
environment variables.

Make sure PostgreSQL is installed and running, then create the application database if it
does not already exist:

CREATE DATABASE hotel_marketplace;

The Django database configuration follows this structure:

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DJANGO_DB_NAME", "hotel_marketplace"),
        "USER": os.environ.get("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
        "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
        "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
    }
}

After configuring the PostgreSQL credentials, apply the Django migrations:

python manage.py migrate

To verify that the database configuration is working correctly:

python manage.py check
python manage.py showmigrations

Production recommendation: Keep database credentials in environment variables or a
managed secrets service. Do not commit .env files, passwords, or other credentials to Git.

5. Seed demo data

Creates 1 admin (superuser), 5 hotel owners, 5 buyers, ~10 hotel listings (published +
draft/pending), sample offers with negotiation history, and sample conversations.

python manage.py seed_demo_data

Safe to re-run — it skips users/listings that already exist.

6. Run the development server

python manage.py runserver

Visit http://127.0.0.1:8000/ for the website, or http://127.0.0.1:8000/api/ for the
browsable API root.

Demo credentials (created by seed_demo_data)

Role

Username

Password

Admin

admin

AdminPass123

Owner

owner1 – owner5

Password123

Buyer

buyer1 – buyer5

Password123

Key URLs (website)

Page

URL

Marketplace (public)

/

Register

/accounts/register/

Login

/accounts/login/

Owner: My Listings

/mine/

Owner: Create Listing

/create/

Buyer: Saved Hotels

/saved/

Offers: My Offers (buyer)

/offers/mine/

Offers: Received (owner)

/offers/received/

Messages / Inbox

/messages/

Role-aware Dashboard

/dashboard/

Admin Dashboard

/dashboard/admin/

Django Admin

/django-admin/

REST API

Mounted at /api/. It sits entirely alongside the routes above — nothing about the
website changed. Every endpoint enforces the same business rules as the equivalent
template view (see "Business Rules Implemented" below); the API layer reuses the models
and re-implements the same checks rather than introducing a second, divergent set of rules.

Authentication: DRF Token Authentication (Authorization: Token <key> header) for API
clients, plus Session Authentication so an already-logged-in browser can call the API too.
Passwords are always handled by Django's built-in hashing (PBKDF2) — the API never sees or
stores plaintext passwords beyond the single request that creates/verifies them.

Responses are JSON; list endpoints are paginated (?page=, page size via API_PAGE_SIZE).
A browsable version of the API (handy for manual testing) is available at /api/ and
/api/auth-browsable/ once logged in through the browser.

Authentication & current user

Method

Endpoint

Access

Notes

POST

/api/auth/register/

Public

{"username","email","password","role":"owner"|"buyer","business_name"?,"company_name"?} — creates the account + matching Owner/Buyer profile, returns a token

POST

/api/auth/login/

Public

{"username","password"} → {"token","user"}

POST

/api/auth/logout/

Authenticated

Deletes the caller's token

GET

/api/users/me/

Authenticated

Current user + role-specific profile

PATCH

/api/users/me/

Authenticated

Update own name/email/phone

Hotel Listings

Method

Endpoint

Access

Notes

GET

/api/listings/

Public

Published listings only for anonymous/buyers; owners also see their own of any status; admins see all. Supports ?q=&city=&property_type=&min_price=&max_price=&min_rooms=&sort=newest|price_low|price_high|rooms

POST

/api/listings/

Owner only

Creates a new listing with status=draft

GET

/api/listings/{id}/

Public (published) / owner / admin

Non-published listings 404 for everyone except the owner/admin

PATCH/PUT

/api/listings/{id}/

Owning owner / admin

403 for anyone else

DELETE

/api/listings/{id}/

Owning owner / admin



GET

/api/listings/mine/

Owner

All of the caller's own listings, any status

POST

/api/listings/{id}/publish/

Owning owner

Draft → Pending Approval

POST

/api/listings/{id}/unpublish/

Owning owner

→ Draft

POST

/api/listings/{id}/close/

Owning owner

→ Closed (stops new offers)

Favourites

Method

Endpoint

Access

Notes

GET

/api/favourites/

Buyer

The caller's saved listings

POST

/api/favourites/

Buyer

{"listing": <id>} — must be a published listing

DELETE

/api/favourites/{id}/

Owning buyer



Offers

Method

Endpoint

Access

Notes

GET

/api/offers/

Buyer/owner (own offers) / admin (all)



POST

/api/offers/

Buyer only

{"listing","amount","proposed_terms"?,"message"?}. Rejected if the listing isn't published, or the buyer already has an active (pending/countered) offer on it

GET

/api/offers/{id}/

Buyer, owner, or admin involved

404 for anyone else

GET

/api/offers/mine/

Buyer

Offers the caller submitted

GET

/api/offers/received/

Owner

Offers received on the caller's listings

POST

/api/offers/{id}/respond/

Participant only

{"action":"accept"|"reject"|"counter"|"withdraw"|"accept_counter"|"reject_counter","amount"?,"message"?}. accept/reject/counter are owner-only; withdraw/accept_counter/reject_counter are buyer-only

Conversations & Messages

Method

Endpoint

Access

Notes

GET

/api/conversations/

Buyer/owner (own threads) / admin

Inbox list

POST

/api/conversations/

Buyer only

{"listing": <id>} — starts (or reuses) a thread with the listing's owner

GET

/api/conversations/{id}/

The two participants / admin

Includes messages; marks the other party's unread messages as read

POST

/api/conversations/{id}/messages/

The two participants

{"body": "..."}

Admin (protected, role=admin/staff/superuser only)

Method

Endpoint

Notes

GET

/api/admin/users/

?role=owner|buyer filter

POST

/api/admin/users/{id}/toggle-status/

Suspend/reactivate a user

GET

/api/admin/listings/

?status= filter, any status

POST

/api/admin/listings/{id}/moderate/

{"action":"approve"|"reject"|"suspend"}

Business Rules Implemented

Only authenticated Owners can create/edit their own hotel listings (enforced in both
the website views and the API).

Only Published listings appear in the public marketplace / API list & retrieve.

Listing lifecycle: Draft → Pending Approval → Published / Rejected → Closed.

Only authenticated Buyers can submit offers; duplicate active offers on the same
listing by the same buyer are blocked; Closed listings reject new offers.

Owners can Accept / Reject / Counter a pending offer; buyers can Accept / Reject
a counter-offer or Withdraw their own pending offer.

Every offer action is recorded in OfferHistory for full negotiation traceability.

Messaging is scoped to a specific listing + buyer + owner pair; only the two parties
(or an admin) can view or post into a conversation.

Admin-only routes (moderation, user management) are protected by role in both the
Django views (user_passes_test) and the API (IsAdminRole permission).

Passwords are always created/verified through Django's built-in auth system
(set_password / authenticate), so hashing and validation rules are identical
everywhere — website, admin, and API.

Testing

Automated tests

python manage.py test            # full suite
python manage.py test api        # API tests only (61 tests)

api/tests/ covers, with each file focused on one concern:

test_auth.py — registration (incl. password hashing, weak-password/duplicate-email
rejection), login/logout, /api/users/me/, and admin-route protection

test_listings.py — visibility rules (published vs. draft, owner vs. stranger vs. admin),
create/edit/delete authorization, status transitions

test_offers.py — submission rules (buyer-only, published-only, closed-listing block,
duplicate-offer guard), and the full accept/reject/counter/withdraw negotiation flow with
authorization checks

test_favourites.py — buyer-only save/list/remove, ownership scoping

test_chat.py — buyer-initiated conversations, thread reuse, participant-only access,
sending messages, unread/read-marking

Existing per-app tests.py files (accounts, listings, offers, chat, dashboard)
are left as-is (django.test.TestCase scaffolding) for any template/view-level tests you
want to add alongside the new API suite.

Manual/website testing

The website flows were exercised via automated HTTP requests against the running dev server,
covering: registration/login for each role, listing creation (draft + image formset),
marketplace search/filter, offer submission + duplicate-offer guard, owner counter-offer,
buyer accept/reject-counter and withdraw, messaging (start conversation + send message),
favouriting, and admin listing approval.

Scope Notes

This is an MVP built for evaluation purposes, not a production-ready commercial platform.
Payment processing, legal contract signing, KYC/identity verification, automated property
valuation, and production-grade real-time infrastructure are intentionally out of scope.
Real-time chat (Socket.IO/WebSockets), email notifications, and map integration are listed
as optional bonus enhancements in the spec and are not implemented here — messaging uses
standard request/response (refresh-based) polling on the website, and simple poll/refresh
on the API side.