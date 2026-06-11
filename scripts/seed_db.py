"""
Seed the Supabase database with sample data.

Usage:
    python scripts/seed_db.py

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env (or env vars).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from app.database import get_supabase  # noqa: E402

AGENT_CONFIG = {
    "agent_name": "firetal-internal-assistant",
    "system_prompt": (
        "Du er Firetal's interne assistent. Du hjælper medarbejdere med interne systemer og processer."
    ),
    "max_tokens": 512,
    "max_turns": 10,
    "max_requests_per_minute": 20,
    "is_active": True,
}

KNOWLEDGE_BASE = [
    {
        "category": "deployment",
        "question": "Hvordan deployer jeg en ny app?",
        "answer": "Push til main-branchen på GitHub. GitHub Actions kører tests automatisk, og Sliplane deployer containeren når tests er grønne.",
    },
    {
        "category": "deployment",
        "question": "Hvor finder jeg deployment-logs?",
        "answer": "Log ind på Sliplane (sliplane.io), vælg dit projekt og klik på 'Logs' i venstre menu.",
    },
    {
        "category": "database",
        "question": "Hvordan opretter jeg en ny tabel i Supabase?",
        "answer": "Gå til Supabase Dashboard → Table Editor → New Table. Eller skriv SQL i SQL Editor og kør det.",
    },
    {
        "category": "database",
        "question": "Hvor ligger vores BigQuery data?",
        "answer": "BigQuery data ligger i GCP-projektet under datasets opdelt pr. domæne (salg, lager, marketing). Kontakt data-teamet for adgang.",
    },
    {
        "category": "secrets",
        "question": "Hvordan håndterer vi API-nøgler?",
        "answer": "Alle secrets gemmes i GitHub Secrets (til CI/CD) og som Environment Variables i Sliplane. Aldrig i kode eller git.",
    },
    {
        "category": "github",
        "question": "Hvad er vores branching-strategi?",
        "answer": "Vi bruger trunk-based development: feature-branches merges til main via Pull Request. Main deployes automatisk til produktion.",
    },
    {
        "category": "github",
        "question": "Hvad sker der hvis CI fejler?",
        "answer": "Deploy stoppes automatisk. Fix fejlen i din branch, push igen, og CI kører forfra. Sliplane deployer kun ved grønne tests.",
    },
    {
        "category": "agent",
        "question": "Hvordan tilføjer jeg en ny AI-agent?",
        "answer": "Opret et nyt repo baseret på firetal-agent-template, konfigurer secrets i GitHub og Sliplane, og push til main.",
    },
    {
        "category": "agent",
        "question": "Hvad er rate limiting?",
        "answer": "Rate limiting begrænser antal requests per bruger/IP per minut. Det forhindrer misbrug og holder API-omkostningerne nede.",
    },
    {
        "category": "onboarding",
        "question": "Hvilke systemer skal jeg have adgang til som ny medarbejder?",
        "answer": "GitHub organisation, Supabase project, Sliplane workspace, GCP/BigQuery, og Henosia/Next.js deployment. Kontakt din leder for invitations.",
    },
]

SAMPLE_CONVERSATIONS = [
    {
        "conversation_id": "demo-conv-001",
        "user_id": "user-demo-1",
        "user_message": "Hvordan deployer jeg min nye app?",
        "agent_reply": "Push din kode til main-branchen på GitHub. GitHub Actions kører automatisk tests, og Sliplane deployer containeren når alt er grønt. Du kan følge status på Sliplane dashboardet.",
        "tokens_used": 245,
        "turn_number": 1,
    },
    {
        "conversation_id": "demo-conv-001",
        "user_id": "user-demo-1",
        "user_message": "Og hvad hvis det fejler?",
        "agent_reply": "Hvis CI fejler, stopper deploy automatisk. Du kan se fejlen direkte i GitHub Actions under dit repository. Fix koden, push igen, og pipelinen starter forfra.",
        "tokens_used": 198,
        "turn_number": 2,
    },
    {
        "conversation_id": "demo-conv-002",
        "user_id": "user-demo-2",
        "user_message": "Hvor gemmer vi secrets?",
        "agent_reply": "Alle secrets gemmes i GitHub Secrets til CI/CD og som Environment Variables i Sliplane til runtime. Aldrig direkte i koden eller i git-historikken.",
        "tokens_used": 167,
        "turn_number": 1,
    },
]


def seed():
    client = get_supabase()

    print("Seeding agent_configs...")
    client.table("agent_configs").upsert(AGENT_CONFIG, on_conflict="agent_name").execute()
    print("  ✓ 1 agent config inserted")

    print("Seeding knowledge_base...")
    client.table("knowledge_base").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    client.table("knowledge_base").insert(KNOWLEDGE_BASE).execute()
    print(f"  ✓ {len(KNOWLEDGE_BASE)} knowledge base entries inserted")

    print("Seeding sample conversations...")
    client.table("conversations").delete().like("conversation_id", "demo-conv-%").execute()
    client.table("conversations").insert(SAMPLE_CONVERSATIONS).execute()
    print(f"  ✓ {len(SAMPLE_CONVERSATIONS)} sample conversations inserted")

    print("\nDone! Database is ready.")


if __name__ == "__main__":
    seed()
