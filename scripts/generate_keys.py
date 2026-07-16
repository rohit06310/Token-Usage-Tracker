"""
Generate a new FERNET_KEY and DASHBOARD_API_KEY for use in .env.

Run: python scripts/generate_keys.py
"""

import secrets
from cryptography.fernet import Fernet


def main():
    fernet_key = Fernet.generate_key().decode()
    dashboard_key = f"sk_{secrets.token_hex(32)}"

    print("=" * 60)
    print("Generated keys — add these to your .env file")
    print("=" * 60)
    print()
    print(f"FERNET_KEY={fernet_key}")
    print()
    print(f"DASHBOARD_API_KEY={dashboard_key}")
    print()
    print("=" * 60)
    print("⚠️  Store these securely. NEVER commit them to git.")
    print("=" * 60)


if __name__ == "__main__":
    main()
