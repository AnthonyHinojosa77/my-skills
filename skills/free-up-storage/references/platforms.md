# Platform routes

These are discovery starting points, not deletion commands or guarantees about installed tools. Check live command help, current official documentation, target paths, and permissions before relying on a route. Use bounded scans and surface inaccessible areas. No command here authorizes cleanup.

## macOS

- Use `sw_vers` to identify the OS, `df -k` for volume availability, and `diskutil apfs list` when shared APFS container accounting needs clarification. Do not interpret the sealed System volume's used size as all user data.
- Use `du -k -d 1` on selected local directories, recording permission failures. Likely starting points include `/Applications`, the user's Downloads, `~/Library/Caches`, `~/Library/Application Support`, and selected hidden cache directories such as `~/.cache`. Check individual app/model subdirectories before making candidates.
- Finder's app API may be available for Trash operations without changing focus; use the runtime's permitted native interface and verify the specific operation. Shell denial on `~/.Trash` is not a Trash count. Preserve unrelated Trash contents and handle confirmations as actual pending gates.
- CloudStorage and iCloud locations require placeholder-aware inspection. System Data is a broad category, not a folder to erase. Do not manually remove swap, APFS internals, or app virtual-machine bundles as generic caches.

## Windows

- Identify the actual machine and OS through the permitted system API or PowerShell. `Get-PSDrive -PSProvider FileSystem` can identify filesystem drives; use the applicable volume API for consistent before/after free space. Distinguish local, removable, mapped, and cloud-backed storage.
- Use bounded `Get-ChildItem -LiteralPath` enumeration of selected local directories. Avoid unrestricted recursive scans, reparse points/junctions, and cloud placeholders. File `Length` is logical size, so label it when allocated bytes are unavailable.
- Examine actual Downloads, application sizes, user temporary/cache locations, package-manager caches, and local model downloads. Resolve known folders and environment variables rather than hardcoding a username or assuming the system drive is C:.
- Prefer the application's uninstaller or verified Windows storage cleanup for OS-managed categories. `Clear-RecycleBin` clears a bin scope rather than just selected candidates: do not use it for selective deletion without the broader authorization. Verify with an available native Recycle Bin API; an inaccessible `$Recycle.Bin` is not proof of emptiness.
- Do not manually erase Windows, WinSxS, installer databases, paging/hibernation files, or cloud copies as cache cleanup.

## Linux

- Identify the actual host and distro using a permitted system interface, `uname`, and OS-release metadata. Use `df -k` on the target mount for before/after availability; do not confuse a container overlay with the user's host filesystem.
- Use `du` on selected local directories, checking the installed variant's options for shallow scanning and staying on one filesystem. Common starting points include Downloads, the configured user cache directory (often `~/.cache`), package caches, model stores, and user development workspaces.
- Query the installed package/container manager before proposing its cleanup. Broad prune commands may delete stopped containers, build state, images, or volumes: approve those resources explicitly, especially persistent volumes. Do not equate 'unused' with valueless.
- Trash is desktop/tool/mount dependent. Detect the available supported interface and verify its semantics. Avoid deleting the entire configured Trash path to remove selected files; use exact entries or report a selective-removal limitation. Do not install a trash utility just to complete the task without approval.
- Use supported tools for system package caches and logs; do not manually erase system directories, live databases, swap, or journal data.
