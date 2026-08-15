# Memory / Caching Layer — the browser-use side

This branch adds the **caching hook**: the piece that records what the agent actually did, so an
`agentic_task` can be replayed later with no LLM in the loop.

**Measured on roboform:** 27.7s → 16.2s, **2 agent LLM calls → 0**.

## What is in this PR

Four files, ~177 lines:

| File | Role |
|---|---|
| `browser_use/memory_cache/choke.py` | `cached_execute_action` — wraps the dispatch choke point and records each action with the real locator it resolved to |
| `browser_use/memory_cache/models.py` | `CachedStep`, one JSON line per action |
| `browser_use/memory_cache/__init__.py` | package exports |
| `browser_use/tools/registry/service.py` | one import, one decorator on `Registry.execute_action` |

`Registry.execute_action` is the single point every action passes through between "the LLM chose
this" and "Playwright did it" — so one wrapper covers every action, with no per-action patching and
no parsing of model output. What gets recorded is deliberately **not** the transient `[n]` DOM index
the LLM saw, but the durable locator that index resolved to.

## Branch base

This branch is cut from the **`optexity` branch** (`optexity-browser-use 0.9.5.4`), not `main`.
`main` is a copy of public browser-use `0.11.4`, which `optexity` cannot drive — it lacks API such as
`get_browser_state_summary(include_full_page=...)`, and an agentic task run against it silently does
nothing.

Consequently the PR targets `optexity`. Against `main` the diff would be 198 files and −34,628 lines,
because `main` is a different lineage.

## The rest of the pipeline

The filter, converter and comparison tooling live in the **optexity** fork, because they validate
against `optexity.schema.automation.Automation`. Keeping them there avoids vendoring Optexity's
schema into this repo.

| Doc | What it answers |
|---|---|
| [01_what_i_implemented.md](01_what_i_implemented.md) | What was built end to end, and what changed once it was run |
| [03_trial_run_results.md](03_trial_run_results.md) | Real caches, generated automations, measured numbers |
| [04_future_production_considerations.md](04_future_production_considerations.md) | What is missing: there is no cache *lookup* step yet |
| [05_setup_guide_feedback.md](05_setup_guide_feedback.md) | Setup notes: two things that fail silently, worth adding to the brief |
