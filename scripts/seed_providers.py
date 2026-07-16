"""
Seed the providers table with the 4 standard LLM providers.

Usage:
    python scripts/seed_providers.py

This is idempotent — running it multiple times is safe.
Requires DATABASE_URL, FERNET_KEY, and DASHBOARD_API_KEY to be set in .env
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.db import get_session_factory
from app.models.provider import Provider

PROVIDERS = [
    {
        "name": "OpenAI",
        "slug": "openai",
        "base_url": "https://api.openai.com/v1",
        "notes": "GPT-4o, GPT-4o-mini, o1, o3-mini. Tier 1-5 based on spend.",
    },
    {
        "name": "Anthropic",
        "slug": "anthropic",
        "base_url": "https://api.anthropic.com",
        "notes": "Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus.",
    },
    {
        "name": "Groq",
        "slug": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "notes": "Llama 3.3, Llama 3.1, Mixtral. Very low latency via custom silicon.",
    },
    {
        "name": "Gemini",
        "slug": "gemini",
        "base_url": "https://generativelanguage.googleapis.com",
        "notes": "Gemini 2.0 Flash, Gemini 1.5 Pro/Flash. Google AI Studio.",
    },
]


def main() -> None:
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        created = 0
        skipped = 0

        for pdata in PROVIDERS:
            existing = db.query(Provider).filter(Provider.slug == pdata["slug"]).first()
            if existing:
                print(f"  SKIP  {pdata['name']} (already exists, id={existing.id})")
                skipped += 1
                continue

            provider = Provider(**pdata)
            db.add(provider)
            db.flush()  # Get the id before commit
            print(f"  CREATE {pdata['name']} (id={provider.id})")
            created += 1

        db.commit()
        print(f"\nDone: {created} created, {skipped} skipped.")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding providers table...")
    main()
