---
name: github-actions-replacements
description: Inventory and replace GitHub Actions tests, schedules, backups, and reports with verified external Claude routines while preserving required checks, trust boundaries, and rollback coverage.
---

# GitHub Actions Replacements

Use deterministic runners for execution and Claude routines for bounded coordination and diagnosis. Scope each migration to the repositories and services the user names. Saving or installing this skill does not authorize recurring automation, production changes, workflow disablement, or deployment across other projects.

## Establish the contract

Inspect repository instructions and every existing workflow, including reusable workflows and callers. Classify PR tests, default-branch tests, schedules, backups, reports, releases, and deployments separately. Inventory triggers and filters, required status contexts, command order, runtime versions, permissions, secret names only, concurrency, artifacts, output consumers, and failure notifications. Preserve any function outside the replacement scope.

Record a per-project coverage table: original behavior, replacement runner, trigger, trust boundary, required evidence, owner, gap, and rollback. A daily default-branch fallback does not provide immediate direct-push coverage. Comments do not replace required check contexts. Resolve either gap before claiming equivalent coverage or disabling the affected workflow.

Use these evidence states per replacement:

`INVENTORIED -> IMPLEMENTED -> MANUALLY VERIFIED -> EVENT VERIFIED -> SCHEDULE VERIFIED -> CUT OVER -> MONITORED`

Apply event and schedule gates where relevant; explain any inapplicable gate. A failed gate is `BLOCKED`; record the last verified state and exact missing action.

## Implement and configure

Read [implementation.md](references/implementation.md) when building runners or configuring routines. Establish isolated, deterministic execution before model orchestration. Reuse existing routines where appropriate; read their current settings before changing them.

Keep PR-controlled code outside the trusted orchestration context. Pin the trusted harness revision independently of the tested revision. Preserve the existing workflow command sequence and runtime versions. Retain `ci.yml` or any other workflow YAML if the replacement runner uses it as its manifest.

Use least-privilege repository access, connectors, network rules, and protected credentials. Backups must be encrypted, private, collision-protected, and independently verifiable without exposing customer contents. Do not automatically delete old backups. Reports must use an explicit aggregate-only output allowlist.

## Select economical models honestly

Treat **Haiku 5.5 with medium reasoning** as the originating user's preference, subject to current runtime availability and any later user choice. Verify available model IDs, effort controls, plan access, and current official documentation in the actual execution surface. Do not promise availability or silently substitute another model.

Where only one routine model is configurable, prefer a single eligible agent that invokes deterministic scripts. If the user selects and the runtime supports a coordinator/worker design, verify Sonnet 5.5 medium coordination and Haiku 5.5 medium workers separately. Do not create workers just to launch one script. Check current support and enforcement rather than copying environment variable recipes from another runtime.

Save each selection, reopen the actual routine, and read back model and effort. Repository settings alone do not establish cloud settings, especially in multi-repository sessions. Test a fresh execution after changing models; saved configuration is not runtime acceptance. Record selected and observed settings when exposed, elapsed time, retries, worker calls, outcome, and available usage. Compare representative successful and failing runs before claiming savings or equivalent behavior. Keep quality gates unchanged; quota consumption and API charges are different measures.

## Verify, cut over, and hand off

Read [acceptance.md](references/acceptance.md) for manual, real-event, scheduled, artifact, and terminal-receipt acceptance. Verify each relevant trigger independently. Do not infer automatic invocation from a manual run or a scheduled pass from a Run Now action.

Only disable legacy workflows after replacement coverage is verified and the user has authorized cutover. Preserve YAML, audit history, and required protections; read back the disabled state. Resolve required-check integration without weakening branch protection. Do not delete artifacts or cancel unrelated runs as incidental cleanup.

Observe the agreed follow-up invocation and monitor failures, usage, storage growth, and notification delivery within a bounded window. Under agreed rollback authority, re-enable the affected legacy workflow if essential coverage fails, prevent duplicate side effects, and retain receipts.

Report changed scope, verified evidence, skips, gaps, blocked actions, model acceptance, restored schedules, and cutover status. Keep evidence links in the project's restricted audit location; never publish private operational receipts, identities, secrets, or customer data in this reusable skill. Each new project needs its own access, configuration, and proof. Cloud execution does not imply access to a user's local computer.
