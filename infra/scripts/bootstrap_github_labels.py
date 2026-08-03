#!/usr/bin/env python3
"""Idempotently create the AI Dev Factory GitHub labels.

Usage:
    GITHUB_USER_TOKEN=... GITHUB_OWNER=... GITHUB_TARGET_REPO=... \\
        python infra/scripts/bootstrap_github_labels.py

Requires a token with `repo` scope. Running twice is safe: existing labels are
updated in place, missing ones are created. No secret is printed.
"""

from __future__ import annotations

import os
import sys

import httpx

LABELS: list[tuple[str, str]] = [
    ("type:epic", "5319e7"),
    ("type:story", "1d76db"),
    ("type:bug", "d73a4a"),
    ("type:technical", "0e8a16"),
    ("status:needs-clarification", "fbca04"),
    ("status:ready", "0e8a16"),
    ("status:in-progress", "1d76db"),
    ("status:in-review", "5319e7"),
    ("status:blocked", "d73a4a"),
    ("status:ready-for-human", "e99695"),
    ("agent:product-owner", "c5def5"),
    ("agent:architect", "c5def5"),
    ("agent:developer", "c5def5"),
    ("agent:reviewer", "c5def5"),
    ("agent:qa", "c5def5"),
    ("agent:documentation", "c5def5"),
    ("priority:critical", "b60205"),
    ("priority:high", "d93f0b"),
    ("priority:medium", "fbca04"),
    ("priority:low", "0e8a16"),
]


def main() -> int:
    token = os.environ.get("GITHUB_USER_TOKEN")
    owner = os.environ.get("GITHUB_OWNER")
    repo = os.environ.get("GITHUB_TARGET_REPO")
    if not (token and owner and repo):
        print("GITHUB_USER_TOKEN, GITHUB_OWNER and GITHUB_TARGET_REPO are required.")
        return 2

    base = f"https://api.github.com/repos/{owner}/{repo}/labels"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    created = updated = 0
    with httpx.Client(timeout=30) as client:
        for name, color in LABELS:
            resp = client.post(base, headers=headers, json={"name": name, "color": color})
            if resp.status_code == 201:
                created += 1
            elif resp.status_code == 422:  # already exists -> update color
                client.patch(
                    f"{base}/{name}", headers=headers, json={"new_name": name, "color": color}
                )
                updated += 1
            else:
                print(f"Label {name}: HTTP {resp.status_code}")
    print(f"Labels created={created} updated={updated} total={len(LABELS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
