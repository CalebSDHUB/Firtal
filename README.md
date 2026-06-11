# Firetal Internal Assistant – AI Agent PoC

> Proof-of-concept for sikker AI-agent deployment med guardrails.
> Stack: FastAPI · Uvicorn · Anthropic Claude · Supabase · Docker · GitHub Actions · Sliplane

---

## Hvad er det?

En simpel intern AI-assistent der hjælper Firetal-medarbejdere med at navigere interne systemer, processer og værktøjer (Supabase, GitHub, Sliplane, BigQuery osv.).

Formålet med dette PoC er **ikke** agentens domæne – men strukturen rundt om den: deployment, secrets, guardrails og et fundament andre builders kan stå på.

---

## Flow-diagram: commit → deploy → runtime

```
Developer
    │
    ▼
git push → main branch
    │
    ▼
┌─────────────────────────────┐
│     GitHub Actions (CI)     │
│                             │
│  1. pytest (unit tests)     │
│  2. Build Docker image      │
│  3. Push → ghcr.io          │
│  4. Trigger Sliplane deploy │
└─────────────┬───────────────┘
              │  webhook
              ▼
┌─────────────────────────────┐
│         Sliplane            │
│                             │
│  Pull image from ghcr.io    │
│  Inject env vars (secrets)  │
│  Start container port 8000  │
│  Health check /health       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│              Runtime (container)                │
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

---

## Guardrail-valg: tre lag

Jeg valgte at implementere **tre komplementære guardrails** fremfor én, fordi de beskytter på hvert sit niveau:

| Guardrail | Implementering | Beskytter mod |
|-----------|---------------|---------------|
| **Rate limiting** | In-memory sliding window, 20 req/min/IP | API-misbrug, uventet load, cost spike |
| **Max tokens** | `max_tokens=512` i Claude API-kaldet | Runaway output, uventet token-forbrug |
| **Max turns** | Tæller gemte turns i Supabase per `conversation_id` | Uendelige samtale-loops |

**Primær guardrail: Rate limiting** – fordi det er den mest praktiske første forsvarslinje på tværs af alle agenter, uanset domæne. Kostnader skalerer lineært med requests; rate limiting er den enkle knap der holder budgettet i check.

---

## Hvordan forhindrer vi en uendelig loop mod Claude?

En agent kan ende i en loop hvis den:
1. Kalder et tool, læser svaret og kalder næste tool i en automatisk kæde – uden stop-betingelse
2. Re-prompter sig selv baseret på sit eget output

Vores løsning bruger **tre lag**:

```
1. max_turns per conversation (Supabase-tæller)
   → HTTP 400 efter 10 turns – samtalen er død, start en ny

2. max_tokens per response (Claude API-parameter)
   → Hård grænse på output-tokens – ingen runaway generation

3. Single-shot arkitektur
   → Agenten kaldes præcis én gang per bruger-turn
   → Ingen tool-loop, ingen auto-retry, ingen re-entry
   → run_agent() returnerer (reply, tokens) – det var det
```

Koden i `app/agent.py`:
```python
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=settings.max_tokens_per_response,  # hård grænse
    system=SYSTEM_PROMPT,
    messages=messages,  # endelig liste – ingen loop
)
# Returner direkte – ingen while-løkke, ingen tool-dispatch
reply = response.content[0].text
```

Hvis vi tilføjer tool-use senere: max tool-kald pr. turn konfigureres eksplicit, og `check_max_turns()` gælder stadig som sikkerhedsnet.

---

## Sådan deployer en ikke-teknisk builder en ny agent

1. **Opret et nyt repo** – brug dette repo som template (GitHub → "Use this template")

2. **Sæt secrets op** (én gang, i GitHub og Sliplane):
   - GitHub: `Settings → Secrets → Actions` → tilføj de tre nøgler fra `.env.example`
   - Sliplane: `Environment Variables` i dit service-panel

3. **Opdater system-prompten** i `app/agent.py` – det er det eneste der definerer hvad agenten *gør*

4. **Push til main** – GitHub Actions kører tests og Sliplane deployer automatisk

5. **Kend din URL** – Sliplane giver en offentlig URL (`https://firetal-agent.sliplane.app/chat`)

Det er det. Ingen terminal, ingen Docker-kommandoer, ingen cloud-konfiguration.

> **Fremtidigt:** Systemprompten kan flyttes til `agent_configs`-tabellen i Supabase, så builders kan ændre agentens adfærd direkte fra et dashboard – uden at røre kode overhovedet.

---

## Lokal udvikling

```bash
# 1. Klon og konfigurer
git clone https://github.com/<org>/firetal-agent
cd firetal-agent
cp .env.example .env
# Udfyld .env med dine nøgler

# 2. Start med Docker Compose
docker compose up --build

# 3. Test agenten
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hvordan deployer jeg en ny app?"}'

# 4. Seed databasen med sample data
python scripts/seed_db.py
```

API docs: http://localhost:8000/docs

---

## Supabase opsætning

```sql
-- Kør én gang i Supabase SQL Editor
-- Filen ligger i supabase/schema.sql
```

Tabeller:
- `conversations` – logger alle agent-interaktioner (audit trail)
- `agent_configs` – konfiguration per agent (kan ændres uden redeploy)
- `knowledge_base` – FAQ-indhold agenten kan referere til

---

## Secrets-håndtering

```
Lokal udvikling:  .env fil (i .gitignore – aldrig committed)
CI/CD:            GitHub Secrets (krypteret, injektet som env vars)
Runtime:          Sliplane Environment Variables (aldrig synlige i logs)
```

Secrets eksponeres **aldrig** i kode, git-historik eller container-images.
`pydantic-settings` validerer at alle nødvendige secrets er til stede ved opstart – containeren crasher med en klar fejlbesked hvis noget mangler, fremfor at starte med ugyldig konfiguration.

---

## Projektstruktur

```
firetal-agent/
├── app/
│   ├── main.py          # FastAPI app + endpoints
│   ├── agent.py         # Claude-integration
│   ├── guardrails.py    # Rate limit, max turns, input-validering
│   ├── database.py      # Supabase queries
│   ├── models.py        # Pydantic request/response modeller
│   └── config.py        # Settings fra env vars
├── scripts/
│   └── seed_db.py       # Fylder databasen med sample data
├── supabase/
│   └── schema.sql       # Database-schema
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

## Hvis dette skulle i produktion

**Hvad vi ville tilføje:**

- [ ] **Autentificering** – JWT eller Supabase Auth på `/chat` endpoint
- [ ] **Observability** – strukturerede logs til Datadog/Loki + token-usage dashboard
- [ ] **Persistent rate limiting** – Supabase/Redis fremfor in-memory (overlever container-restart)
- [ ] **Content moderation** – filter på input/output (Anthropic Guardrails API eller custom)
- [ ] **Async agent** – `asyncio` + `httpx` for concurrent requests
- [ ] **Multi-agent routing** – én gateway der router til specialiserede agenter pr. domæne
- [ ] **Prompt versioning** – system-prompts i `agent_configs`-tabellen med versionsnummer
- [ ] **Cost alerts** – Supabase Function der sender alarm hvis daglige tokens overstiger budget
- [ ] **Rollback** – Sliplane understøtter deploy af tidligere image-tags ved fejl

**Skalering:**
Sliplane understøtter auto-scaling på container-niveau. Stateless design (ingen lokal state, alt i Supabase) betyder at vi bare spinner flere instanser op bag en load balancer.
