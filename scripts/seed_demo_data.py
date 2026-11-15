"""Load the sample enquiries into a RUNNING backend through its public API, so a demo has data to show.

    backend\\.venv\\Scripts\\python scripts\\seed_demo_data.py            (Windows)
    backend/.venv/bin/python scripts/seed_demo_data.py                  (macOS / Linux)

Options:
    --base-url URL     backend address (default http://127.0.0.1:8000)
    --no-wait          return right after submitting instead of waiting for the AI to finish
    --statuses         also move two enquiries to "Converted" / "In Progress" so the dashboard shows variety

Every enquiry goes through the real pipeline (real AI, real database). Sample people and numbers are fictional.
Needs a backend with at least one admin (ADMIN_USERNAME / ADMIN_PASSWORD in backend/.env) only for --statuses and
for printing results; submitting enquiries itself is public.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "backend" / "sample_data" / "enquiries.json"


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, val = line.partition("=")
                values[key.strip()] = val.split(" #")[0].strip()
    return values


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--statuses", action="store_true")
    args = ap.parse_args()

    client = httpx.Client(base_url=args.base_url, timeout=60)
    try:
        client.get("/health").raise_for_status()
    except httpx.HTTPError:
        print(f"Cannot reach the backend at {args.base_url}. Start it first (see README: Quick start).")
        return 1

    env = read_env(ROOT / "backend" / ".env")
    headers: dict[str, str] = {}
    if env.get("ADMIN_USERNAME") and env.get("ADMIN_PASSWORD"):
        r = client.post("/api/auth/login", json={"username": env["ADMIN_USERNAME"], "password": env["ADMIN_PASSWORD"]})
        if r.status_code == 200:
            headers = {"Authorization": "Bearer " + r.json()["data"]["access_token"]}
    if not headers:
        print("(No admin credentials found in backend/.env - enquiries will be submitted, but results can't be listed.)")

    ids = []
    for sample in json.loads(SAMPLES.read_text(encoding="utf-8")):
        r = client.post("/api/enquiries", json={**sample, "source": "demo-seed"})
        if r.status_code != 201:
            print(f"  ! could not submit {sample['customer_name']}: {r.status_code} {r.text[:120]}")
            continue
        ids.append(r.json()["data"]["id"])
        print(f"  submitted #{ids[-1]:<3} {sample['customer_name']}")
    if args.no_wait or not headers:
        return 0

    print("Waiting for the AI to finish (free-tier limits may make this take a minute or two)...")
    deadline = time.time() + 600
    rows: list[dict] = []
    while time.time() < deadline:
        rows = [client.get(f"/api/enquiries/{i}", headers=headers).json()["data"] for i in ids]
        if all(r["ai_status"] in ("completed", "failed") for r in rows):
            break
        time.sleep(3)

    if args.statuses and len(rows) >= 4:
        client.put(f"/api/enquiries/{ids[0]}/status", json={"status": "Converted"}, headers=headers)
        client.put(f"/api/enquiries/{ids[3]}/status", json={"status": "In Progress"}, headers=headers)

    print(f"\n{'#':<4}{'Customer':<16}{'Category':<32}{'Priority':<9}{'Lead':<10}{'AI':<10}")
    for r in rows:
        lead = f"{r['lead_temperature']} {r['lead_score_total']}" if r["lead_temperature"] else "-"
        print(f"{r['id']:<4}{r['customer_name'][:15]:<16}{(r['service_category'] or '-')[:31]:<32}{(r['priority'] or '-'):<9}{lead:<10}{r['ai_status']:<10}")
    failed = [r["id"] for r in rows if r["ai_status"] == "failed"]
    if failed:
        print(f"\n{len(failed)} enquiry(ies) failed AI analysis (usually free-tier rate limits). Open them in the admin console and press Retry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
