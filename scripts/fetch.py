#!/usr/bin/env python3
"""
fetch.py — Harvest the Agent Client Protocol (ACP) ecosystem from GitHub.

ACP = Agent Client Protocol (https://agentclientprotocol.com), the open
protocol that connects any code editor to any AI coding agent.

This script queries the GitHub API along several axes and merges the results
into a single deduplicated JSON file (data/repos.json):

  1. Repos with the `agent-client-protocol` topic        (high signal)
  2. Repos with the `acp` topic                          (noisy — includes
     the unrelated IBM "Agent Communication Protocol")
  3. Full-text repo search for "agent client protocol"
  4. Code search for the wire-level magic strings
     ("session/prompt", "fs/read_text_file", agent-client-protocol package
     names) to surface editors/agents that *implement* ACP without tagging it.

Requires: `gh` authenticated (gh auth status).

Usage:
    python3 scripts/fetch.py            # full harvest -> data/repos.json
    python3 scripts/fetch.py --quick    # topic searches only (fast)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

# ---- search axes -----------------------------------------------------------

REPO_SEARCHES = [
    # (label, q)
    ("topic:agent-client-protocol", "topic:agent-client-protocol"),
    ("topic:acp", "topic:acp"),
    ('"agent client protocol"', '"agent client protocol" in:name,description,readme'),
    ("agent-client-protocol pkg", "agent-client-protocol in:name,description,readme"),
    ("zed acp", "zed agent protocol in:name,description,readme"),
]

# Code search: finds repos that import / implement ACP even when untagged.
CODE_SEARCHES = [
    "agent-client-protocol language:rust",
    "agent-client-protocol language:typescript",
    "\"@zed-industries/agent-client-protocol\"",
    "agent_client_protocol",
]


def gh_json(args: list[str]) -> dict | list:
    """Run a gh command and parse JSON, returning {} on failure."""
    try:
        out = subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=True
        ).stdout
        return json.loads(out) if out.strip() else {}
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"  ! gh error: {e.stderr.strip()[:200]}\n")
        return {}


def paginate_repos(q: str, cap: int = 300) -> list[dict]:
    """Page through the repository search API up to `cap` results."""
    results: list[dict] = []
    page = 1
    while len(results) < cap:
        data = gh_json(
            [
                "api", "-X", "GET", "search/repositories",
                "-f", f"q={q}",
                "-f", "sort=stars",
                "-f", "order=desc",
                "-f", "per_page=100",
                "-f", f"page={page}",
            ]
        )
        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            break
        results.extend(items)
        if len(items) < 100:
            break
        page += 1
        time.sleep(1.5)  # be gentle with the search rate limit
    return results


def paginate_code(q: str, cap: int = 100) -> list[dict]:
    """Code search -> the owning repos."""
    repos: list[dict] = []
    page = 1
    while len(repos) < cap:
        data = gh_json(
            [
                "api", "-X", "GET", "search/code",
                "-f", f"q={q}",
                "-f", "per_page=100",
                "-f", f"page={page}",
            ]
        )
        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            break
        repos.extend(it["repository"] for it in items if "repository" in it)
        if len(items) < 100:
            break
        page += 1
        time.sleep(2.0)
    return repos


def norm(repo: dict, source: str) -> dict:
    """Normalize a repo record to the fields we care about."""
    return {
        "full_name": repo.get("full_name"),
        "name": repo.get("name"),
        "owner": (repo.get("owner") or {}).get("login"),
        "description": (repo.get("description") or "").strip(),
        "url": repo.get("html_url"),
        "homepage": (repo.get("homepage") or "").strip(),
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language"),
        "topics": repo.get("topics", []) or [],
        "archived": repo.get("archived", False),
        "fork": repo.get("fork", False),
        "pushed_at": repo.get("pushed_at"),
        "sources": {source},
    }


def main() -> None:
    quick = "--quick" in sys.argv
    merged: dict[str, dict] = {}

    def add(repo: dict, source: str) -> None:
        if not repo.get("full_name"):
            return
        key = repo["full_name"].lower()
        if key in merged:
            merged[key]["sources"].add(source)
            # topic search returns richer topic data — keep the longest list
            if len(repo.get("topics", []) or []) > len(merged[key]["topics"]):
                merged[key]["topics"] = repo["topics"]
        else:
            merged[key] = norm(repo, source)

    for label, q in REPO_SEARCHES:
        print(f"[repo] {label} …", flush=True)
        for r in paginate_repos(q):
            add(r, label)
        print(f"       total unique so far: {len(merged)}", flush=True)
        time.sleep(1.0)

    if not quick:
        for q in CODE_SEARCHES:
            print(f"[code] {q} …", flush=True)
            for r in paginate_code(q):
                add(r, f"code:{q}")
            print(f"       total unique so far: {len(merged)}", flush=True)
            time.sleep(2.0)

    rows = sorted(merged.values(), key=lambda r: r["stars"], reverse=True)
    for r in rows:
        r["sources"] = sorted(r["sources"])

    out = DATA / "repos.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nWrote {len(rows)} repos -> {out}")


if __name__ == "__main__":
    main()
