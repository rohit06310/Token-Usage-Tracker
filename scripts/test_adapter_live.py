"""
Live adapter test script — tests one adapter against a real Supabase instance.

Prerequisites:
  1. .env configured (DATABASE_URL, FERNET_KEY, DASHBOARD_API_KEY)
  2. Provider seeded: python scripts/seed_providers.py
  3. API key stored: POST /api/v1/api-keys/  (or pass --api-key directly)
  4. Real provider API key in .env (OPENAI_API_KEY, etc.)

Usage:
    python scripts/test_adapter_live.py --provider openai --model gpt-4o-mini
    python scripts/test_adapter_live.py --provider anthropic --model claude-3-5-haiku-20241022
    python scripts/test_adapter_live.py --provider groq --model llama-3.1-8b-instant
    python scripts/test_adapter_live.py --provider gemini --model gemini-1.5-flash
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_test(provider_slug: str, model: str, prompt: str, raw_key: str) -> None:
    from decimal import Decimal
    from app.adapters import get_adapter_class
    from app.models.provider import Provider
    from app.models.usage_log import UsageLog
    from app.services.db import get_session_factory

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        provider = db.query(Provider).filter(Provider.slug == provider_slug).first()
        if not provider:
            print(f"ERROR: Provider '{provider_slug}' not in DB. Run seed_providers.py first.")
            return

        adapter_cls = get_adapter_class(provider_slug)
        adapter = adapter_cls(provider_id=provider.id, api_key=raw_key)

        print(f"\n{'='*60}")
        print(f"  Provider : {provider_slug}")
        print(f"  Model    : {model}")
        print(f"  Prompt   : {prompt[:60]}...")
        print(f"{'='*60}\n")

        response = await adapter.execute(
            prompt=prompt,
            model=model,
            db=db,
            project_tag="live-test",
        )

        print(f"  Status   : {response.status}")
        print(f"  Content  : {response.content[:200]}")
        print(f"  Tokens   : {response.tokens_in} in / {response.tokens_out} out")
        print(f"  Cost     : ${response.cost}")

        # Verify the row was written to Supabase
        log = (
            db.query(UsageLog)
            .filter(UsageLog.provider_id == provider.id)
            .order_by(UsageLog.created_at.desc())
            .first()
        )
        if log:
            print(f"\n  ✅ UsageLog written to Supabase:")
            print(f"     id={log.id}")
            print(f"     status={log.status}")
            print(f"     cost=${log.cost}")
            print(f"     pricing_used={log.raw_response.get('_pricing_used', {})}")
        else:
            print("  ❌ No UsageLog found in DB — check DB connection")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Live adapter test")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "groq", "gemini"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", default="Say 'Hello from the AI usage dashboard!' in one sentence.")
    parser.add_argument("--api-key", help="Provider API key (overrides env var)")
    args = parser.parse_args()

    # Resolve API key
    env_key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    raw_key = args.api_key or os.environ.get(env_key_map[args.provider])
    if not raw_key:
        print(
            f"ERROR: No API key for {args.provider}. "
            f"Set {env_key_map[args.provider]} in .env or pass --api-key",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(run_test(args.provider, args.model, args.prompt, raw_key))


if __name__ == "__main__":
    main()
