# Harvest scripts

Reproduce the Awesome ACP dataset straight from GitHub. Requires the
[`gh` CLI](https://cli.github.com/) authenticated (`gh auth status`) and Python 3.

| Script | Output | What it does |
| --- | --- | --- |
| [`fetch.py`](./fetch.py) | `data/repos.json` | Harvests every repo via the `agent-client-protocol` & `acp` topics, the phrase "agent client protocol", and code-search for the wire-level package names. Deduplicates by `full_name`, sorts by stars. |
| [`categorize.py`](./categorize.py) | `data/catalog.json` | Buckets the harvest into candidate categories and drops the unrelated "ACP" namespaces (Agentic Commerce, Agent Communication, PCA stats, admin panels…). A maintenance aid — final curation is by hand. |

```bash
python3 scripts/fetch.py            # ~2-3 min; respects search rate limits
python3 scripts/fetch.py --quick    # topic searches only (fast)
python3 scripts/categorize.py       # prints a report + writes data/catalog.json
```

The `data/registry/` folder additionally mirrors the official
[ACP registry](https://github.com/agentclientprotocol/registry) `agent.json`
metadata for the CI-verified agent list.
