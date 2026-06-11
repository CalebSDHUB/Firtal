-- Firetal Agent – Supabase schema
-- Run this once in the Supabase SQL editor to set up the database.

-- ─────────────────────────────────────────
-- 1. Conversation logs
-- ─────────────────────────────────────────
create table if not exists conversations (
    id               uuid primary key default gen_random_uuid(),
    conversation_id  text        not null,
    user_id          text        not null default 'anonymous',
    user_message     text        not null,
    agent_reply      text        not null,
    tokens_used      integer     not null default 0,
    turn_number      integer     not null default 1,
    created_at       timestamptz not null default now()
);

create index if not exists idx_conversations_conversation_id
    on conversations (conversation_id);

create index if not exists idx_conversations_created_at
    on conversations (created_at desc);

-- ─────────────────────────────────────────
-- 2. Agent configurations
-- (lets non-technical builders tweak settings without redeploying)
-- ─────────────────────────────────────────
create table if not exists agent_configs (
    id                          uuid primary key default gen_random_uuid(),
    agent_name                  text        not null unique,
    system_prompt               text        not null,
    max_tokens                  integer     not null default 512,
    max_turns                   integer     not null default 10,
    max_requests_per_minute     integer     not null default 20,
    is_active                   boolean     not null default true,
    created_at                  timestamptz not null default now(),
    updated_at                  timestamptz not null default now()
);

-- ─────────────────────────────────────────
-- 3. Knowledge base (FAQ entries the agent can reference)
-- ─────────────────────────────────────────
create table if not exists knowledge_base (
    id          uuid primary key default gen_random_uuid(),
    category    text        not null,
    question    text        not null,
    answer      text        not null,
    created_at  timestamptz not null default now()
);
