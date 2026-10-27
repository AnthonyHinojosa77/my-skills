# Acceptance and reversible cutover

Keep one evidence record per responsibility. Include safe links, tested revision, harness revision, trigger source, timestamps/timezone, terminal outcome, steps, artifacts, selected/observed model and effort, retry count, and gaps. Store operational receipts in the project's restricted audit location, not the public skill.

| Gate | Required proof | Insufficient proof |
| --- | --- | --- |
| Saved configuration | Reopened trigger, scope, environment, model/effort, timezone, schedule, enabled state | Save click or intended settings |
| Manual execution | Awaited runner exit, correct revision, trusted harness revision, every required step | Agent/task success label |
| PR event | Real qualifying event starts intended PR test at actual head SHA | Manual invocation |
| Default-branch event | Real merge starts intended revision and produces complete PASS receipt | Daily fallback alone |
| Direct push, if required | Real qualifying push invokes correct revision and status contexts | Merge-trigger or daily evidence |
| Backup | Terminal write receipt plus independent private object metadata and byte count | Task summary or existence alone |
| Report | Terminal health/API evidence and inspection of aggregate-only output | Unfiltered JSON |
| Schedule | Existing routine starts from actual scheduled trigger | Run Now |
| Restoration | Original times, timezone, enabled state, and triggers reopened and read back | Planned restoration |
| Model change | Saved selection plus fresh representative execution under selected settings | Settings readback alone |
| Cutover | Complete coverage, user authority, only covered workflows disabled, required checks functioning | Workflow deletion or check-protection removal |

Inspect the actual terminal transcript and expected artifacts as well as the task summary. Record missing binary artifacts, unsupported triggers, delivery differences, and retention differences in the coverage table. Verify failure paths and status delivery as well as passing execution. A successful backup metadata check does not establish restoration success.

## Real events and scheduled tests

Use an authorized, harmless validation change to produce a qualifying PR event and, where authorized, a merge event. Follow repository contribution rules and never merge merely to test without authority. A validation-only filter must not remain active afterward. Avoid empty commits or duplicate tasks intended to bypass guards.

After manual and relevant event tests pass, and within approved schedule-editing scope:

1. Record the exact original settings of existing scheduled routines.
2. Temporarily accelerate those routines to near-future times supported by the scheduler; stagger jobs. Preserve timezone and other fields.
3. Wait within a bounded deadline for actual scheduled invocations. Verify trigger provenance, terminal receipts, artifacts, and side effects.
4. Restore every original schedule and enabled state even if a test fails. Reopen and read them back. If restoration is blocked, report the exact routine, remaining temporary state, and required action immediately.

A scheduled default-branch run can correctly skip because a matching revision is already running or completed. That proves scheduling and guard behavior, not a fresh complete test pass. Pair it with full event-triggered evidence only if the acceptance contract permits; otherwise leave the fresh scheduled-pass gate open.

## Cutover and rollback

Compare every inventoried workflow responsibility with verified replacement behavior. Keep uncovered responsibilities enabled. Required checks must work on the correct revisions; never weaken branch protection to conceal a mismatch. Preserve `ci.yml` when used as a manifest, other needed YAML, audit comments, and historical receipts.

Disable only covered workflows after user authorization, then read back their disabled state. Do not cancel unrelated runs or delete queued jobs, artifacts, or backups as incidental cleanup. Observe the next relevant replacement invocation within the agreed evidence window and check failure notifications, usage, and storage growth.

If essential execution, isolation, required checks, or delivery fails, follow the agreed rollback authority: re-enable the affected legacy workflow and prevent duplicate side effects while retaining all receipts. Credential rotation and backup deletion are not generic rollback steps.

## Handoff

Report each responsibility's last verified gate, tested/harness revisions, safe evidence links, model selection versus fresh runtime acceptance, restored schedule state, known gaps, cutover status, and rollback readiness. Distinguish a skip from a pass and saved settings from successful execution. Do not claim savings without measured usage or costs on the actual billing surface. Do not imply migration of other projects or fresh model acceptance from this template.

For a blocker, give the exact action and target, reason, completed work, last verified gate, and whether the action was denied, is pending, or has an uncertain outcome. Check uncertain outcomes before retrying. Do not bypass a denial or expand scope to work around it.
