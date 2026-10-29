---
name: free-up-storage
description: Review storage on a user's computer, rank removal candidates by measured size and impact, and carry out approved cleanup with verified recovered space. Use for full disks, storage audits, caches, downloaded models, and Trash or Recycle Bin cleanup on macOS, Windows, or Linux.
---

# Free up storage

Work on the computer the user means, using its current evidence. This skill can be read as instructions by any agent; native skill discovery and permission to operate the computer depend on that agent's environment. A cloud sandbox's disk is not the user's disk. If the agent cannot reach the intended computer, say so and provide one scoped handoff instead of claiming an audit or cleanup.

## Review first

1. Identify the OS, target computer, relevant volume, and whether the request authorizes inspection only or specifies cleanup. Reuse approval already given for exact candidates. A request to find candidates does not approve deletion. Creating or invoking this skill does not authorize recurring cleanup.
2. Measure available space and record the time, volume, command or API, and unit. Prefer local filesystem or application APIs that preserve the user's focus. Do not install a scanner, elevate privileges, grant permissions, or take foreground control without the required authorization. Read only names, sizes, and necessary metadata; avoid private file contents and secrets.
3. Start with bounded, shallow measurements of local directories and expand the largest categories. Include application sizes, downloaded installers, caches, development downloads, hidden model caches, app support data, media, and project workspaces where accessible. Read only the relevant section of [platform guidance](references/platforms.md). Do not assume standard paths exist or suppress access errors and then report a complete scan.
4. Avoid following symlinks, crossing volumes, or downloading cloud placeholders during a scan. Identify cloud-synced locations before traversing them; use provider metadata where possible. Deleting a synced file can delete its cloud copy too. A provider's verified 'free up local space' operation is a separate option from deletion.
5. Present a short ranked table: candidate, exact path or app, measured size, expected impact, and confidence that it is disposable. Include the largest useful candidates, not just easy caches. Do not count a parent and its children twice, confuse logical file size with allocated space, or promise that folder totals equal recoverable space. Shared blocks, sparse files, hard links, snapshots, and open files can change the result.

## Judge candidates by contents and use

- Cached installers: verify that they are downloads or updater payloads, rather than the installed app or an active update. Do not infer that an arbitrary application-support folder is disposable from its name.
- Development caches: identify the owning tool and use its documented cleanup when available. Check whether a location contains installed runtimes, environments, linked package stores, or active jobs before treating it as a download cache. Do not remove a runtime being used by this agent or another active task.
- Downloaded AI models: measure individual models, identify likely consumers, and state what is verified versus inferred. Removing a model can disable offline features until it is downloaded again; do not automatically download replacements, start paid calls, or interrupt a running model process.
- App history, snapshots, virtual machines, databases, backups, and project workspaces: treat these as valuable state until inspected. Explain the consequence and investigate a supported cleanup mechanism. Preserve unpushed work and unique files; use a repository's required workspace cleanup tool.
- Apps: recommend removal only as a candidate until approved. Use the supported uninstall route, especially for apps with services or shared components. User projects and catalogs need separate consideration.
- OS files, swap, recovery data, and system snapshots: do not manually delete them as generic cleanup. Use a supported OS mechanism only within the approved scope.

Ask one plain question when a choice changes what will be lost, or when cleanup approval is still needed. Approval for one named category does not extend to every cache or unrelated Trash contents. Do not ask again for an already approved action.

## Perform the approved cleanup

1. Recheck the exact candidates and available space immediately before mutation. Resolve paths, reject unexpected symlinks or changed targets, and use a fixed explicit list rather than a broad deletion glob. Check active consumers; if stopping an app would interrupt work, obtain authorization first. Follow current OS/tool documentation when the cleanup behavior is uncertain.
2. Use the narrowest supported operation. Quarantine in Trash or Recycle Bin when useful, but distinguish that from permanent deletion. Use authorized direct permanent removal only where the available tools permit it. If an operation is rejected, use an allowed safer method; do not disguise the same denied operation through another interpreter, privilege change, or unprotected automation route.
3. Complete the approved deletion through its logical end. Moving within the same volume to Trash usually does not reclaim the intended space. If permanent deletion of the selected items is authorized, remove only those newly trashed items through a supported method, preserving unrelated contents. Empty the entire Trash or Recycle Bin only when that scope is explicitly approved. If only moving to Trash was approved, stop there and report that space recovery remains pending.
4. Track exact destination identities, including renamed collisions, if items pass through Trash. If exact selective permanent removal is unavailable, report the limitation rather than emptying everything. Respect OS access restrictions and human security prompts. Do not infer failure merely because shell access to Trash is denied if an authorized native app API can perform the task; do not claim success from an API return code alone.
5. Verify that each target is gone from its original location, that approved permanent deletions are gone from Trash or Recycle Bin, and that the same volume's available space has been measured again. Whole-bin emptying needs an item-count or equivalent native postcondition. An empty enumeration with an error is not proof of emptiness. If space has not increased as expected, report the measured result and investigate only bounded causes such as held-open files or snapshots; never force-quit apps or delete snapshots merely to make the number match.

## Report the outcome

Lead with available space before and after, measured difference, and what was removed. Use the same units and volume; give estimates separately from measured recovery. State whether items are only in Trash, permanently removed, failed, or still unverified. Include any feature that may require a download or reinstall, remaining access gaps, and one useful next action. Do not claim that an entire device was audited when protected, cloud-only, or other-volume locations were not inspected.
