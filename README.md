# Reusable AI Skills

A small, reviewed collection of generic skills and a project installer for Codex, Claude Code, Cursor, and GitHub Copilot.

## Included skills

- `babysit-pr`: bounded pull-request monitoring after an explicit request.
- `capability-check`: verify a capability in its exact runtime and account.
- `file-pr`: prepare and file a pull request after an explicit request.
- `github-actions-replacements`: replace workflow responsibilities with verified external Claude routines and reversible cutover.
- `html-communication`: create a self-contained HTML decision artifact after an explicit request.
- `stop-texting-and-emailing-me-gov`: reduce unwanted political texts and email, and postal mail when requested.

## Install into an existing project

Requires Python 3.10+ and Git. Clone this repository, then preview an installation:

```bash
python3 scripts/install-project.py --target /path/to/project --profile public-safe --runtimes codex,claude
```

Add `--apply` to install. Choose `cursor` or `copilot` when that is the target runtime. Use `--skills capability-check,file-pr` to install a subset.

The installer preserves existing project instructions, adds a marked working agreement, writes runtime-specific skills, and records the source version and file hashes in `.ai-agent-system.json`. Conflicting skill edits require `--replace-existing`; backups are stored outside the project in `~/.local/state/ai-agent-system/backups/`.

The profile controls only this toolkit's payload. It does not inspect or sanitize the rest of your project for publication. Runtime discovery and model behavior should be checked in the runtime you use. A cloud agent must have access to the project and the files must be committed there.

The repository contains no personal history, original private inputs, global instruction backups, credentials, or user-specific working context. No additional redistribution license has been selected.
