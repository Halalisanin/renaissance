#!/usr/bin/env python3
"""Lulu Print API client for Renaissance of the Poor Soul.

Usage:
  python3 lulu_print_api.py token
  python3 lulu_print_api.py list
  python3 lulu_print_api.py stats
  python3 lulu_print_api.py shipping --country US --page-count 95 --quantity 1
  python3 lulu_print_api.py validate-interior --url <public_url>
  python3 lulu_print_api.py validate-cover --url <public_url>
  python3 lulu_print_api.py create [--dry-run]
  python3 lulu_print_api.py status <job_id>
  python3 lulu_print_api.py costs <job_id>
  python3 lulu_print_api.py md5

Credentials come from LULU_CLIENT_KEY / LULU_CLIENT_SECRET env vars,
or fall back to the values in CONFIG below.
"""

import argparse
import hashlib
import json
import os
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("LULU_BASE_URL", "https://api.lulu.com")
TOKEN_URL = f"{BASE_URL}/auth/realms/glasstree/protocol/openid-connect/token"

CONFIG = {
    "client_key": os.environ.get("LULU_CLIENT_KEY", "65c0da88-e284-405f-a7ae-6d979c3e4223"),
    "client_secret": os.environ.get("LULU_CLIENT_SECRET", "CKUhTRYSqikNANOdptpnSnjCGXygxHbG"),
    # 6"x9" B&W standard quality, 60# white paper, perfect binding
    "pod_package_id": "0600X0900BWSTDPB060UW444MXX",
    "interior_path": "print/cover1/book/interior.pdf",
    "cover_path": "print/cover1/cover/cover.pdf",
    # Print job defaults (override with --external-id, --email, --quantity, --shipping-level)
    "external_id": "external_order-1",
    "contact_email": "test@test.com",
    "shipping_level": "MAIL",
    "quantity": 20,
    "shipping_address": {
        "name": "John Doe",
        "street1": "123 Test Street",
        "city": "Testtown",
        "state_code": "NC",
        "country_code": "US",
        "postcode": "12345",
        "phone_number": "844-212-0689",
    },
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def get_token():
    """Fetch an OAuth2 access token using client credentials."""
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(CONFIG["client_key"], CONFIG["client_secret"]),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def api(method, path, token=None, payload=None, params=None):
    """Make an authenticated request to the Lulu API."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers=headers,
        json=payload,
        params=params,
        timeout=60,
    )
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text[:500]
        raise RuntimeError(f"{method} {path} -> {resp.status_code}: {detail}")
    return resp.json() if resp.text else None


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_token(_args):
    token = get_token()
    print(json.dumps({"access_token": token[:40] + "...", "token_length": len(token)}, indent=2))


def cmd_md5(_args):
    for key in ("interior_path", "cover_path"):
        path = CONFIG[key]
        print(f"{md5(path)}  {path}")


def cmd_list(args):
    token = get_token()
    data = api("GET", "/print-jobs/", token=token, params={"limit": args.limit})
    print(json.dumps(data, indent=2))


def cmd_stats(_args):
    token = get_token()
    data = api("GET", "/print-jobs/statistics/", token=token)
    print(json.dumps(data, indent=2))


def cmd_shipping(args):
    token = get_token()
    payload = {
        "line_items": [
            {
                "pod_package_id": CONFIG["pod_package_id"],
                "quantity": args.quantity,
                "page_count": args.page_count,
            }
        ],
        "shipping_address": {"country": args.country},
    }
    data = api("POST", "/shipping-options/", token=token, payload=payload)
    print(json.dumps(data, indent=2))


def cmd_validate_interior(args):
    token = get_token()
    payload = {
        "pod_package_id": CONFIG["pod_package_id"],
        "source_url": args.url,
        "source_md5sum": args.md5 or md5(CONFIG["interior_path"]),
    }
    data = api("POST", "/print-job-cost-calculations/validate-interior/", token=token, payload=payload)
    print(json.dumps(data, indent=2))


def cmd_validate_cover(args):
    token = get_token()
    payload = {
        "pod_package_id": CONFIG["pod_package_id"],
        "source_url": args.url,
        "source_md5sum": args.md5 or md5(CONFIG["cover_path"]),
    }
    data = api("POST", "/print-job-cost-calculations/validate-cover/", token=token, payload=payload)
    print(json.dumps(data, indent=2))


def build_print_job_payload(args):
    return {
        "external_id": args.external_id,
        "contact_email": args.email,
        "shipping_level": args.shipping_level,
        "line_items": [
            {
                "external_id": args.item_external_id,
                "pod_package_id": CONFIG["pod_package_id"],
                "quantity": args.quantity,
                "interior": {
                    "source_url": args.interior_url,
                    "source_md5sum": args.interior_md5 or md5(CONFIG["interior_path"]),
                },
                "cover": {
                    "source_url": args.cover_url,
                    "source_md5sum": args.cover_md5 or md5(CONFIG["cover_path"]),
                },
            }
        ],
        "shipping_address": CONFIG["shipping_address"],
    }


def cmd_create(args):
    payload = build_print_job_payload(args)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return
    token = get_token()
    data = api("POST", "/print-jobs/", token=token, payload=payload)
    print(json.dumps(data, indent=2))


def cmd_status(args):
    token = get_token()
    data = api("GET", f"/print-jobs/{args.job_id}/status/", token=token)
    print(json.dumps(data, indent=2))


def cmd_costs(args):
    token = get_token()
    data = api("GET", f"/print-jobs/{args.job_id}/costs/", token=token)
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Lulu Print API client")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("token", help="Fetch and print an access token").set_defaults(func=cmd_token)
    sub.add_parser("md5", help="Print md5sums of the local print files").set_defaults(func=cmd_md5)

    p = sub.add_parser("list", help="List print jobs")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_list)

    sub.add_parser("stats", help="Print job statistics").set_defaults(func=cmd_stats)

    p = sub.add_parser("shipping", help="List shipping options")
    p.add_argument("--country", default="US")
    p.add_argument("--page-count", type=int, default=95)
    p.add_argument("--quantity", type=int, default=1)
    p.set_defaults(func=cmd_shipping)

    p = sub.add_parser("validate-interior", help="Validate interior PDF (needs public URL)")
    p.add_argument("--url", required=True)
    p.add_argument("--md5")
    p.set_defaults(func=cmd_validate_interior)

    p = sub.add_parser("validate-cover", help="Validate cover PDF (needs public URL)")
    p.add_argument("--url", required=True)
    p.add_argument("--md5")
    p.set_defaults(func=cmd_validate_cover)

    p = sub.add_parser("create", help="Create a print job (needs public URLs)")
    p.add_argument("--interior-url", required=True)
    p.add_argument("--cover-url", required=True)
    p.add_argument("--interior-md5")
    p.add_argument("--cover-md5")
    p.add_argument("--external-id", default=CONFIG["external_id"])
    p.add_argument("--item-external-id", default="item-1")
    p.add_argument("--email", default=CONFIG["contact_email"])
    p.add_argument("--shipping-level", default=CONFIG["shipping_level"])
    p.add_argument("--quantity", type=int, default=CONFIG["quantity"])
    p.add_argument("--dry-run", action="store_true", help="Print payload without calling the API")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("status", help="Get print job status")
    p.add_argument("job_id")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("costs", help="Get print job costs")
    p.add_argument("job_id")
    p.set_defaults(func=cmd_costs)

    args = parser.parse_args()
    try:
        args.func(args)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()