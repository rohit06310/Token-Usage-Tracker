"""
Seed the rate_limits table with documented provider rate limits.

Source: Provider documentation (as of 2025-07).
All limits are tier-specific — edit tiers below to match your actual account tier.

Usage:
    python scripts/seed_rate_limits.py

This is idempotent — uses effective_date to avoid duplicates.
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.provider import Provider
from app.models.rate_limit import RateLimit
from app.services.db import get_session_factory

# Effective date for this seeding run
EFFECTIVE_DATE = date(2025, 7, 1)

RATE_LIMITS = [
    # ==========================================================================
    # OpenAI — https://platform.openai.com/docs/guides/rate-limits
    # Adjust tier_name to match your account (check platform.openai.com/limits)
    # ==========================================================================
    {
        "provider_slug": "openai",
        "tiers": [
            {
                "tier_name": "Free",
                "rpm": 3,
                "tpm": 40_000,
                "rpd": 200,
            },
            {
                "tier_name": "Tier 1",
                "rpm": 500,
                "tpm": 30_000,
                "rpd": 10_000,
            },
            {
                "tier_name": "Tier 2",
                "rpm": 5_000,
                "tpm": 450_000,
                "rpd": None,
            },
            {
                "tier_name": "Tier 3",
                "rpm": 5_000,
                "tpm": 800_000,
                "rpd": None,
            },
            {
                "tier_name": "Tier 4",
                "rpm": 10_000,
                "tpm": 2_000_000,
                "rpd": None,
            },
            {
                "tier_name": "Tier 5",
                "rpm": 30_000,
                "tpm": 150_000_000,
                "rpd": None,
            },
        ],
    },

    # ==========================================================================
    # Anthropic — https://docs.anthropic.com/en/api/rate-limits
    # ==========================================================================
    {
        "provider_slug": "anthropic",
        "tiers": [
            {
                "tier_name": "Build (Tier 1)",
                "rpm": 50,
                "tpm": 40_000,
                "rpd": 1_000,
            },
            {
                "tier_name": "Build (Tier 2)",
                "rpm": 1_000,
                "tpm": 80_000,
                "rpd": None,
            },
            {
                "tier_name": "Scale (Tier 3)",
                "rpm": 2_000,
                "tpm": 160_000,
                "rpd": None,
            },
            {
                "tier_name": "Scale (Tier 4)",
                "rpm": 4_000,
                "tpm": 400_000,
                "rpd": None,
            },
        ],
    },

    # ==========================================================================
    # Groq — https://console.groq.com/docs/rate-limits
    # ==========================================================================
    {
        "provider_slug": "groq",
        "tiers": [
            {
                "tier_name": "Free",
                "rpm": 30,
                "tpm": 6_000,
                "rpd": 14_400,
            },
            {
                "tier_name": "Developer",
                "rpm": 100,
                "tpm": 200_000,
                "rpd": None,
            },
            {
                "tier_name": "Team",
                "rpm": 1_000,
                "tpm": 1_000_000,
                "rpd": None,
            },
        ],
    },

    # ==========================================================================
    # Gemini — https://ai.google.dev/gemini-api/docs/rate-limits
    # ==========================================================================
    {
        "provider_slug": "gemini",
        "tiers": [
            {
                "tier_name": "Free (Gemini 1.5 Flash)",
                "rpm": 15,
                "tpm": 1_000_000,
                "rpd": 1_500,
            },
            {
                "tier_name": "Free (Gemini 1.5 Pro)",
                "rpm": 2,
                "tpm": 32_000,
                "rpd": 50,
            },
            {
                "tier_name": "Pay-as-you-go (Gemini 1.5 Flash)",
                "rpm": 2_000,
                "tpm": 4_000_000,
                "rpd": None,
            },
            {
                "tier_name": "Pay-as-you-go (Gemini 1.5 Pro)",
                "rpm": 1_000,
                "tpm": 4_000_000,
                "rpd": None,
            },
        ],
    },
]


def main() -> None:
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        created = 0
        skipped = 0

        for provider_data in RATE_LIMITS:
            slug = provider_data["provider_slug"]
            provider = db.query(Provider).filter(Provider.slug == slug).first()
            if not provider:
                print(f"  WARN  Provider '{slug}' not found — run seed_providers.py first")
                continue

            for tier in provider_data["tiers"]:
                # Check for existing entry (same provider + tier_name + effective_date)
                existing = (
                    db.query(RateLimit)
                    .filter(
                        RateLimit.provider_id == provider.id,
                        RateLimit.tier_name == tier["tier_name"],
                        RateLimit.effective_date == EFFECTIVE_DATE,
                    )
                    .first()
                )
                if existing:
                    print(f"  SKIP  {slug} / {tier['tier_name']} (already exists)")
                    skipped += 1
                    continue

                rl = RateLimit(
                    provider_id=provider.id,
                    tier_name=tier["tier_name"],
                    rpm=tier.get("rpm"),
                    tpm=tier.get("tpm"),
                    rpd=tier.get("rpd"),
                    effective_date=EFFECTIVE_DATE,
                )
                db.add(rl)
                print(
                    f"  CREATE {slug} / {tier['tier_name']}: "
                    f"rpm={tier.get('rpm')} tpm={tier.get('tpm')} rpd={tier.get('rpd')}"
                )
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
    print(f"Seeding rate_limits table (effective_date={EFFECTIVE_DATE})...")
    main()
