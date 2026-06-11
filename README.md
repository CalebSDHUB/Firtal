# Firetal Internal Assistant – AI Agent PoC

> Proof-of-concept for secure AI agent deployment with guardrails.
> Stack: FastAPI · Uvicorn · Anthropic Claude · Supabase · Docker · GitHub Actions · Sliplane

**[Try the live demo →](https://firtal-fxj1pf.sliplane.app/)**

---

## What is this?

A simple internal AI assistant that helps Firetal employees navigate internal systems, processes and tools (Supabase, GitHub, Sliplane, BigQuery, etc.).

The purpose of this PoC is **not** the agent's domain – but the structure around it: deployment, secrets management, guardrails, and a foundation other builders can stand on.

---

## Flow diagram: commit → deploy → runtime

```
Developer
    │
    ▼
git push → main branch
    │
    ▼
┌─────────────────────────────────────────────────┐
│               GitHub Actions (CI)               │
│                                                 │
│  1. pytest (unit tests)                         │
│  2. Build backend + frontend Docker images      │
│  3. Push both → ghcr.io                         │
│  4. Trigger Sliplane deploy (backend + frontend)│
└──────────┬──────────────────────────┬───────────┘
           │ webhook (backend)        │ webhook (frontend)
           ▼                          ▼
┌─────────────────────┐   ┌─────────────────────┐
│  Sliplane – Backend │   │ Sliplane – Frontend  │
│                     │   │                      │
│  Clone repo         │   │  Clone repo          │
│  Build Dockerfile   │   │  Build Dockerfile    │
│  Inject secrets     │   │  Inject env vars     │
│  Start port 8000    │   │  Start port 3000     │
│  Health check       │   │                      │
│  /health            │   │                      │
└──────────┬──────────┘   └──────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│           Backend Runtime (container)           │
│                                                 │
│  POST /chat                                     │
│    │                                            │
│    ├─ Guardrail: rate limit (429 if exceeded)  │
│    ├─ Guardrail: input validation              │
│    ├─ Guardrail: max turns check (Supabase)    │
│    │                                            │
│    ├─ Claude API (single call, max_tokens cap) │
│    │                                            │
│    └─ Log to Supabase → return response        │
└─────────────────────────────────────────────────┘
```

> Backend health check: https://firtal.sliplane.app/health

---

## Guardrail choices: three layers

I chose to implement **three complementary guardrails** rather than one, because they each protect at a different level:

| Guardrail | Implementation | Protects against |
|-----------|---------------|-----------------|
| **Rate limiting** | In-memory sliding window, 20 req/min/IP | API abuse, unexpected load, cost spikes |
| **Max tokens** | `max_tokens=512` in the Claude API call | Runaway output, unexpected token usage |
| **Max turns** | Counts stored turns in Supabase per `conversation_id` | Infinite conversation loops |

**Primary guardrail: Rate limiting** – because it is the most practical first line of defence across all agents, regardless of domain. Costs scale linearly with requests; rate limiting is the simple dial that keeps the budget in check.

---

## How do we prevent an infinite loop against Claude?

An agent can end up in a loop if it:
1. Calls a tool, reads the response and calls the next tool in an automatic chain – without a stop condition
2. Re-prompts itself based on its own output

Our solution uses **three layers**:

```
1. max_turns per conversation (Supabase counter)
   → HTTP 400 after 10 turns – conversation is dead, start a new one

2. max_tokens per response (Claude API parameter)
   → Hard limit on output tokens – no runaway generation

3. Single-shot architecture
   → The agent is called exactly once per user turn
   → No tool loop, no auto-retry, no re-entry
   → run_agent() returns (reply, tokens) – that's it
```

Code in `app/agent.py`:
```python
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=settings.max_tokens_per_response,  # hard limit
    system=SYSTEM_PROMPT,
    messages=messages,  # finite list – no loop
)
# Return directly – no while-loop, no tool-dispatch
reply = response.content[0].text
```

If we add tool-use later: max tool calls per turn are configured explicitly, and `check_max_turns()` still applies as a safety net.

---

## How a non-technical builder deploys a new agent

1. **Create a new repo** – use this repo as a template (GitHub → "Use this template")

2. **Set up secrets** (once, in GitHub and Sliplane):
   - GitHub: `Settings → Secrets → Actions` → add the three keys from `.env.example`
   - Sliplane: `Environment Variables` in your service panel

3. **Update the system prompt** in `app/agent.py` – that is the only thing that defines what the agent *does*

4. **Push to main** – GitHub Actions runs tests and Sliplane deploys automatically

5. **Know your URL** – Sliplane provides a public URL (`https://firetal-agent.sliplane.app/chat`)

That's it. No terminal, no Docker commands, no cloud configuration.

> **Future improvement:** The system prompt can be moved to the `agent_configs` table in Supabase, so builders can change the agent's behaviour directly from a dashboard – without touching code at all.

---

## Local development

```bash
# 1. Clone and configure
git clone https://github.com/CalebSDHUB/Firtal
cd Firtal
cp .env.example .env
# Fill in .env with your keys

# 2. Start with Docker Compose
docker compose up --build

# 3. Test the agent
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I deploy a new app?"}'

# 4. Seed the database with sample data
python scripts/seed_db.py
```

API docs: http://localhost:8000/docs

---

## Supabase setup

```sql
-- Run once in the Supabase SQL Editor
-- File is located at supabase/schema.sql
```

Tables:
- `conversations` – logs all agent interactions (audit trail)
- `agent_configs` – configuration per agent (can be changed without redeployment)
- `knowledge_base` – FAQ content the agent can reference

---

## Secrets management

```
Local development:  .env file (in .gitignore – never committed)
CI/CD:              GitHub Secrets (encrypted, injected as env vars)
Runtime:            Sliplane Environment Variables (never visible in logs)
```

Secrets are **never** exposed in code, git history or container images.
`pydantic-settings` validates that all required secrets are present at startup – the container crashes with a clear error message if anything is missing, rather than starting with invalid configuration.

---

## Project structure

```
firetal-agent/
├── app/
│   ├── main.py          # FastAPI app + endpoints
│   ├── agent.py         # Claude integration
│   ├── guardrails.py    # Rate limit, max turns, input validation
│   ├── database.py      # Supabase queries
│   ├── models.py        # Pydantic request/response models
│   └── config.py        # Settings from env vars
├── scripts/
│   └── seed_db.py       # Seeds the database with sample data
├── supabase/
│   └── schema.sql       # Database schema
├── tests/
│   └── test_guardrails.py
├── .github/workflows/
│   └── deploy.yml       # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── sliplane.json
├── requirements.txt
└── .env.example
```

---

## If this were going to production

**What we would add:**

- [ ] **Authentication** – JWT or Supabase Auth on the `/chat` endpoint
- [ ] **Observability** – structured logs to Datadog/Loki + token usage dashboard
- [ ] **Persistent rate limiting** – Supabase/Redis instead of in-memory (survives container restarts)
- [ ] **Content moderation** – filter on input/output (Anthropic Guardrails API or custom)
- [ ] **Async agent** – `asyncio` + `httpx` for concurrent requests
- [ ] **Multi-agent routing** – one gateway that routes to specialised agents per domain
- [ ] **Prompt versioning** – system prompts in the `agent_configs` table with version numbers
- [ ] **Cost alerts** – Supabase Function that sends an alert if daily tokens exceed budget
- [ ] **Rollback** – Sliplane supports deploying previous image tags on failure

**Scaling:**
Sliplane supports auto-scaling at the container level. Stateless design (no local state, everything in Supabase) means we simply spin up more instances behind a load balancer.
