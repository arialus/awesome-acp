# Contributing to Awesome ACP

Thanks for helping grow the [Agent Client Protocol](https://agentclientprotocol.com) ecosystem list!

## Scope

This is a list for the **Agent _Client_ Protocol** (editor ↔ agent, by Zed).
Please do **not** add projects for the unrelated [Agent Communication Protocol](https://agentcommunicationprotocol.dev) (IBM/BeeAI) or [Agentic Commerce Protocol](https://www.agenticcommerce.dev) (OpenAI/Stripe) — they share the "ACP" acronym but are different protocols.

## Adding a project

1. Make sure the project genuinely implements, consumes, or extends ACP.
2. Add it to the most fitting section of [`README.md`](./README.md), keeping entries in the same format:
   ```
   - [owner/repo](https://github.com/owner/repo) — One-line description ending with a period.
   ```
3. Keep descriptions concise and factual (no marketing fluff).
4. Prefer ordering by relevance/popularity within a section.

## Quality bar

- Working link.
- Clear ACP relevance in the project's own README/description.
- Not a personal fork or an empty placeholder repo.

## Regenerating the dataset

The list is reproducible from the GitHub API. Requires the [`gh` CLI](https://cli.github.com/) authenticated (`gh auth status`).

```bash
# Harvest every repo by the ACP topics + full-text + code search
python3 scripts/fetch.py            # -> data/repos.json

# Bucket the harvest into candidate categories for review
python3 scripts/categorize.py       # -> data/catalog.json + prints a report
```

`fetch.py` queries the `agent-client-protocol` and `acp` topics, the phrase
"agent client protocol", and code-search for the wire-level package names, then
deduplicates by `full_name`. `categorize.py` applies keyword heuristics and
filters out the unrelated "ACP" namespaces. Use the output as a starting point —
final curation into `README.md` is done by hand to keep quality high.

## Reporting issues

Open an issue for dead links, miscategorized entries, or wrong-protocol projects that slipped in.
