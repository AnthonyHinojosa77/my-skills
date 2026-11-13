# Reusable AI Skills

A small, reviewed collection of generic skills and a project installer for Codex, Claude Code, Cursor, GitHub Copilot, and Gemini CLI. Runtime adapters write the files each runtime expects; confirm discovery and behavior in the runtime you use.

## Included skills

- `adhd`: on explicit request (`/adhd`), replace everything the agent sent since the user's last message with one ADHD-friendly message.
- `babysit-pr`: bounded pull-request monitoring after an explicit request.
- `brief-me`: create or refresh a project's `BRIEFME.html`, a visual brief of what the project is, its goal, where it stands and what comes next, readable by the owner and agents on a phone or a computer; agents also refresh it after changing a project.
- `capability-check`: on explicit request (`$capability-check` in Codex or `/capability-check` where supported), verify a capability in its exact runtime and account. The public copy disables implicit invocation in its runtime metadata.
- `file-pr`: on explicit request, deliver a finished change: validate it, have a fresh independent reviewer check the committed change, and on an In Spec verdict push it straight to the default branch. Pull requests only where a task or repository requires one, with no auto-merge or standing watchers.
- `frontend-design`: Anthropic's official skill for distinctive, intentional visual design in new or reshaped UI, included unchanged under the Apache License 2.0 (the license is in its folder). Agents may use it without being asked.
- `html-communication`: create a self-contained HTML decision artifact after an explicit request.
- `talk-normal`: on explicit request (`/talk-normal`), replace everything the agent sent since the user's last message with one plain-language message.
- `teardown`: on explicit request (`/teardown`), turn raw incident notes, error logs, and bottlenecks from AI agent workflows into an unbranded operational teardown: system context and goal, failure mechanics, architectural resolution, and one generalized operating rule.

- `free-up-storage`: review macOS, Windows, or Linux storage and verify approved cleanup, including permanent deletion status.
- `github-actions-replacements`: replace workflow responsibilities with verified external Claude routines and reversible cutover.
- `stop-texting-and-emailing-me-campaign`: reduce unwanted political texts and email, and postal mail when requested.

## Operating model

[OPERATING_MODEL.md](OPERATING_MODEL.md) describes the one-owner setup these skills come from: the single mode-free way of working (questions get answers, instructions get the work done, one thread talks to the owner, cloud side branches are pushed every turn, and `SUM.md` stays the discussion record), the roles of the owner and the AI agents, the single reviewed direct-push delivery path, the records each project keeps, and the gates every change and every release passes.

## Install into an existing project

Requires Python 3.10+ and Git. Clone this repository, then preview an installation:

```bash
python3 scripts/install-project.py --target /path/to/project --profile public-safe --runtimes codex,claude
```

Add `--apply` to install. Choose `cursor`, `copilot`, or `gemini` when that is the target runtime. The `gemini` adapter writes a `GEMINI.md` import of `AGENTS.md` and skills under `.gemini/skills/`. Use `--skills capability-check,file-pr` to install a subset.

The installer preserves existing project instructions, adds a marked working agreement, writes runtime-specific skills, and records the source version and file hashes in `.ai-agent-system.json`. Conflicting skill edits require `--replace-existing`; backups are stored outside the project in `~/.local/state/ai-agent-system/backups/`.

The profile controls only this toolkit's payload. It does not inspect or sanitize the rest of your project for publication. Runtime discovery and model behavior should be checked in the runtime you use. A cloud agent must have access to the project and the files must be committed there.

For an agent without native skill support, give it the contents of `skills/free-up-storage/SKILL.md` and the linked platform reference as instructions. It still needs authorized access to the intended computer; reading the skill does not grant that access.

The repository contains no personal history, original private inputs, global instruction backups, credentials, or user-specific working context. No additional redistribution license has been selected for the toolkit's own files; `frontend-design` keeps Anthropic's Apache License 2.0.
