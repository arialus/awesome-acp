#!/usr/bin/env python3
"""
categorize.py — Bucket the ACP harvest (data/repos.json) into candidate
categories and filter out the unrelated "ACP" namespaces.

This is a *maintenance aid*, not the source of truth. It produces a rough
categorization to surface new/changed projects; final curation into README.md
is done by hand to keep the list high quality.

Usage:
    python3 scripts/fetch.py        # first, to refresh data/repos.json
    python3 scripts/categorize.py   # -> data/catalog.json + prints a report
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOS = ROOT / "data" / "repos.json"
OUT = ROOT / "data" / "catalog.json"

# Repos whose "ACP" means something else entirely. Drop them.
NOISE = re.compile(
    r"""
    agentic.commerce | woocommerce | checkout | merchant | shopping | ucp\b |
    \bap2\b | x402 | antimicrobial | peptide | rayman | mybb | arduino |
    cisco | onem2m | smallworld | alibaba.cloud.certified | \bpca\b |
    analyse.des.donn | composantes.principales | telescope | exif | phpbb |
    admin.control.panel
    """,
    re.I | re.X,
)

# Ordered: first matching rule wins. (label, regex over name+desc+topics)
RULES: list[tuple[str, re.Pattern]] = [
    ("sdk_official", re.compile(r"agentclientprotocol/(rust|typescript|python|kotlin|java)-sdk", re.I)),
    ("library", re.compile(r"\bsdk\b|implementation|bindings?|crate|hooks?|components?|use-acp|client.kernel", re.I)),
    ("editor", re.compile(r"neovim|nvim|emacs|obsidian|vscode|vs.code|jetbrains|unity|godot|eclipse|netbeans|jupyter|kernel|browser.extension|chrome|editor|ide\b", re.I)),
    ("messaging", re.compile(r"wechat|telegram|discord|slack|lark|feishu|whatsapp|matrix|signal|chat.bridge|messaging", re.I)),
    ("mobile", re.compile(r"mobile|ios\b|android|phone|remote.control|on.the.go|teleport", re.I)),
    ("bridge", re.compile(r"adapter|bridge|wrap|gateway|expose.*acp|acp.*server|proxy", re.I)),
    ("orchestrator", re.compile(r"orchestrat|multi.agent|multiplex|manage.*agents|fleet|control.plane|workspace|parallel.*agents", re.I)),
    ("personal", re.compile(r"personal.assistant|memory|portfolio|stock|finance|knowledge|wiki|assistant", re.I)),
    ("tool", re.compile(r"inspector|devtools|debug|trace|observability|conformance|lifecycle|review|planning", re.I)),
    ("client", re.compile(r"\bclient\b|desktop|web.ui|tui|terminal|cli\b", re.I)),
    ("agent", re.compile(r"coding.agent|agent\b", re.I)),
]

ACP_SIGNAL = re.compile(r"\bacp\b|agent.client.protocol", re.I)


def blob(r: dict) -> str:
    return " ".join([r.get("full_name", ""), r.get("description") or "", " ".join(r.get("topics", []))])


def main() -> None:
    rows = json.loads(REPOS.read_text())
    catalog: dict[str, list] = {label: [] for label, _ in RULES}
    catalog["uncategorized"] = []
    dropped = 0

    for r in rows:
        b = blob(r)
        topic_tagged = "agent-client-protocol" in (r.get("topics") or [])
        # require a real ACP signal unless explicitly topic-tagged
        if not topic_tagged and not ACP_SIGNAL.search(b):
            continue
        if NOISE.search(b):
            dropped += 1
            continue
        if r.get("fork"):
            continue
        for label, rx in RULES:
            if rx.search(b):
                catalog[label].append(r)
                break
        else:
            catalog["uncategorized"].append(r)

    OUT.write_text(json.dumps(catalog, indent=2))
    print(f"Dropped {dropped} wrong-protocol repos.\n")
    for label, items in catalog.items():
        print(f"== {label} ({len(items)}) ==")
        for r in sorted(items, key=lambda r: -r["stars"])[:25]:
            print(f'  {r["stars"]:>6}  {r["full_name"]:<46} {(r["description"] or "")[:55]}')
        print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
