"""
Smoke test — runs against a live API instance.

Prerequisites:
  1. App must be running (docker compose up OR uvicorn locally)
  2. .env must be configured with valid DATABASE_URL, FERNET_KEY, DASHBOARD_API_KEY

Usage:
    python scripts/smoke_test.py

    # Override default URL:
    API_URL=http://localhost:8000 python scripts/smoke_test.py
"""

import os
import sys
import json

import httpx

API_URL = os.environ.get("API_URL", "http://localhost:8000")
API_KEY = os.environ.get("DASHBOARD_API_KEY", "")

HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def check(name: str, response: httpx.Response, expected_status: int = 200):
    status = "✅" if response.status_code == expected_status else "❌"
    print(f"{status} [{response.status_code}] {name}")
    if response.status_code != expected_status:
        print(f"   Response: {response.text[:300]}")
        return False
    return True


def main():
    print()
    print("=" * 60)
    print(f"  Smoke Test — {API_URL}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    with httpx.Client(base_url=API_URL, timeout=10.0) as client:

        # ----------------------------------------------------------------
        # 1. Health check (no auth)
        # ----------------------------------------------------------------
        r = client.get("/health")
        ok = check("GET /health (public)", r, 200)
        if ok:
            data = r.json()
            db_ok = data.get("db") == "connected"
            print(f"   status={data.get('status')} db={data.get('db')}")
            if not db_ok:
                print("   ⚠️  Database not connected — check DATABASE_URL")
        passed += ok
        failed += not ok

        # ----------------------------------------------------------------
        # 2. Auth check — reject unauthenticated request
        # ----------------------------------------------------------------
        r = client.get("/api/v1/providers/")
        ok = check("GET /api/v1/providers/ (no auth → 401)", r, 401)
        passed += ok
        failed += not ok

        # ----------------------------------------------------------------
        # 3. Create a provider
        # ----------------------------------------------------------------
        r = client.post(
            "/api/v1/providers/",
            headers=HEADERS,
            json={
                "name": "Smoke Test Provider",
                "slug": "smoke-test",
                "base_url": "https://api.smoketest.example.com",
                "notes": "Created by smoke_test.py — safe to delete",
            },
        )
        ok = check("POST /api/v1/providers/ (create)", r, 201)
        passed += ok
        failed += not ok

        provider_id = None
        if ok:
            provider_id = r.json()["id"]
            print(f"   Created provider id={provider_id}")

        # ----------------------------------------------------------------
        # 4. Insert a usage log directly via ORM
        # ----------------------------------------------------------------
        if provider_id:
            # We'll call the usage list endpoint to verify the DB connection
            r = client.get("/api/v1/usage/", headers=HEADERS)
            ok = check("GET /api/v1/usage/ (list)", r, 200)
            passed += ok
            failed += not ok

        # ----------------------------------------------------------------
        # 5. Usage summary
        # ----------------------------------------------------------------
        r = client.get("/api/v1/usage/summary", headers=HEADERS)
        ok = check("GET /api/v1/usage/summary", r, 200)
        if ok:
            print(f"   Summary: {r.json()}")
        passed += ok
        failed += not ok

        # ----------------------------------------------------------------
        # 6. Delete the test provider (cleanup)
        # ----------------------------------------------------------------
        if provider_id:
            r = client.delete(f"/api/v1/providers/{provider_id}", headers=HEADERS)
            ok = check(f"DELETE /api/v1/providers/{provider_id}", r, 204)
            passed += ok
            failed += not ok

    print()
    print(f"Results: {passed} passed, {failed} failed")
    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
