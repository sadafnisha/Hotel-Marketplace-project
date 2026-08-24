-- =========================================================
-- PostgreSQL schema reference for the Property Listing +
-- Admin Approval + Chat flow.
--
-- This mirrors the Django models that already exist in this project
-- (accounts.User, listings.HotelListing, chat.Conversation/Message) --
-- it is documentation of the real schema Django's migrations create,
-- not a replacement for them. Run migrations to actually build the
-- database; use this file to see the shape at a glance or to seed a
-- raw psql session for testing.
-- =========================================================

-- ---------------------------------------------------------
-- USERS  (accounts.User -> "users" table via AUTH_USER_MODEL)
-- ---------------------------------------------------------
CREATE TYPE user_role AS ENUM ('owner', 'buyer', 'admin');
CREATE TYPE user_status AS ENUM ('active', 'suspended');

CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(150) UNIQUE NOT NULL,
    email           VARCHAR(254) NOT NULL,
    password        VARCHAR(128) NOT NULL,     -- Django's hashed password
    first_name      VARCHAR(150) DEFAULT '',
    last_name       VARCHAR(150) DEFAULT '',
    phone           VARCHAR(20)  DEFAULT '',
    role            user_role    NOT NULL DEFAULT 'buyer',
    status          user_status  NOT NULL DEFAULT 'active',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_staff        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_superuser    BOOLEAN      NOT NULL DEFAULT FALSE,
    date_joined     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_role ON users(role);

-- ---------------------------------------------------------
-- PROPERTIES  (listings.HotelListing -> "properties" table)
-- ---------------------------------------------------------
CREATE TYPE property_status AS ENUM ('draft', 'pending', 'published', 'rejected', 'closed');

CREATE TABLE properties (
    id                  BIGSERIAL PRIMARY KEY,
    reference_number    VARCHAR(20) UNIQUE NOT NULL,
    owner_id            BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    title               VARCHAR(150) NOT NULL,
    description         TEXT NOT NULL,
    property_type       VARCHAR(30)  NOT NULL,

    address             VARCHAR(255) NOT NULL,
    city                VARCHAR(100) NOT NULL,
    state               VARCHAR(100) NOT NULL,
    country             VARCHAR(100) NOT NULL DEFAULT 'India',
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),

    rooms               INTEGER NOT NULL CHECK (rooms >= 0),
    asking_amount       NUMERIC(14,2) NOT NULL,

    -- status is the field the approval workflow revolves around
    status              property_status NOT NULL DEFAULT 'pending',
    rejection_reason    VARCHAR(255) DEFAULT '',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at        TIMESTAMPTZ           -- set when admin approves
);
CREATE INDEX idx_properties_status ON properties(status);
CREATE INDEX idx_properties_owner ON properties(owner_id);

-- ---------------------------------------------------------
-- CHAT  (chat.Conversation + chat.Message -> "chat_*" tables)
-- A conversation is a thread scoped to one property between its
-- buyer and its owner; admins can view/post into any conversation
-- (enforced in application code, not by a DB constraint).
-- ---------------------------------------------------------
CREATE TABLE chat_conversations (
    id           BIGSERIAL PRIMARY KEY,
    property_id  BIGINT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    buyer_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    owner_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (property_id, buyer_id, owner_id)
);

CREATE TABLE chat_messages (
    id               BIGSERIAL PRIMARY KEY,
    conversation_id  BIGINT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    sender_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body             TEXT NOT NULL,
    read_at          TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id, created_at);
CREATE INDEX idx_chat_messages_unread ON chat_messages(conversation_id) WHERE read_at IS NULL;

-- ---------------------------------------------------------
-- Notes
-- ---------------------------------------------------------
-- * In this project, Django names the actual tables accounts_user,
--   listings_hotellisting and chat_conversation/chat_message -- the
--   ORM and migrations already create/manage the equivalent of the
--   above. This file exists as a plain-SQL reference for the same
--   shape, e.g. for onboarding, diagramming, or a raw psql sandbox.
-- * "pending -> published" is the approval transition the Admin
--   Approval Dashboard performs; "pending -> rejected" and
--   "published -> closed" are the other two transitions it exposes.
