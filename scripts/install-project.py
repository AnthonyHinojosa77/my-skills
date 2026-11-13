#!/usr/bin/env python3
"""Install a versioned AI toolkit into a project. Dry-run unless --apply is given."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- ai-agent-system:begin -->"
END = "<!-- ai-agent-system:end -->"
LOCK = ".ai-agent-system.json"
SETTINGS = ".claude/settings.json"
HOOK_DEST = ".claude/hooks/ai-agent-system.py"
HOOK_MARK = "ai-agent-system.py"
PROJECT_HOOK_COMMAND = ["python3", "${CLAUDE_PROJECT_DIR}/.claude/hooks/ai-agent-system.py"]
CONNECTOR_PERMISSIONS = "profiles/personal-private/claude-permissions.json"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GUIDE_DEST = ".ai-agent-system/instructions"
GUIDE_LINK = re.compile(r"(?<![\w/.-])instructions/([a-z0-9-]+\.md)")


def render_guide_links(text: str, destination: str) -> str:
    """Keep references usable outside the source checkout, without rewriting remote URLs."""
    def link(match):
        path = f"{destination.rstrip('/')}/{match[1]}"
        # Markdown destinations with spaces need brackets; code spans stay literal paths.
        return "](" + (f"<{path}>" if re.search(r"\s", path) else path) + ")"
    text = re.sub(r"\]\(instructions/([a-z0-9-]+\.md)\)", link, text)
    return GUIDE_LINK.sub(lambda match: f"{destination.rstrip('/')}/{match[1]}", text)


def instruction_guides(root: Path, relative: str) -> dict[str, str]:
    """Only real, flat Markdown guides are distributable; the profile explicitly opts in."""
    folder = source_path(root, relative)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError(f"instruction guide source is not a real directory: {relative}")
    files = {}
    for path in sorted(folder.iterdir()):
        if path.is_symlink() or not path.is_file() or not re.fullmatch(r"[a-z0-9-]+\.md", path.name):
            raise ValueError(f"invalid instruction guide source: {path.name}")
        files[path.name] = path.read_text(encoding="utf-8")
    if not files:
        raise ValueError("instruction guides must not be empty")
    return files


def codex_budget_config(existing: str, minimum: int = 262144) -> str:
    """Raise the top-level budget, preserving other settings and larger budgets.

    The private global, home and project instruction copies can accumulate.
    This delivers configuration; it does not reload an existing session.
    """
    top = re.split(r"(?m)^\s*\[", existing, maxsplit=1)[0]
    match = re.search(r"(?m)^\s*project_doc_max_bytes\s*=\s*(\d+)\s*(?:#.*)?$", top)
    if match:
        if int(match[1]) >= minimum:
            return existing
        return existing[:match.start(1)] + str(minimum) + existing[match.end(1):]
    if re.search(r"(?m)^\s*project_doc_max_bytes\s*=", top):
        raise ValueError("invalid project_doc_max_bytes; preserve and repair before installation")
    return f"project_doc_max_bytes = {minimum}\n" + existing


def budget_line(text: str) -> str | None:
    """Return only the top-level budget line, including its original formatting."""
    top = re.split(r"(?m)^\s*\[", text, maxsplit=1)[0]
    match = re.search(r"(?m)^[ \t]*project_doc_max_bytes[ \t]*=[^\r\n]*(?:\r?\n|$)", top)
    return match[0] if match else None


def budget_ownership(existing: str, rendered: str, existed: bool, previous: dict | None) -> dict | None:
    """Claim only a change we made, retaining its origin while our line is intact."""
    if previous is not None and not isinstance(previous, dict):
        raise ValueError("invalid Codex budget ownership in project lock")
    if previous and budget_line(existing) == previous.get("installed_line"):
        return previous
    if existing == rendered:
        return None
    return {"created": not existed, "original_line": budget_line(existing),
            "installed_line": budget_line(rendered)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unchanged(recorded: str | None, data: bytes) -> bool:
    """Whether a file on disk is still the one the lock recorded. Windows line endings alone do not count as a change:
    Git for Windows converts them on checkout by default (core.autocrlf), and the installer writes the file back as LF."""
    return recorded is not None and recorded in (sha(data), sha(data.replace(b"\r\n", b"\n")))


def source_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"source path escapes the toolkit: {relative}")
    return path


def target_path(target: Path, relative: str) -> Path:
    allowed_files = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", ".codex/config.toml", LOCK, SETTINGS, HOOK_DEST, ".cursor/rules/ai-agent-system.mdc", ".github/copilot-instructions.md"}
    allowed_roots = (".agents/skills/", ".claude/skills/", ".cursor/skills/", ".github/skills/", ".gemini/skills/", GUIDE_DEST + "/")
    if relative not in allowed_files and not relative.startswith(allowed_roots):
        raise ValueError(f"not a managed destination: {relative}")
    if ".." in Path(relative).parts:
        raise ValueError(f"invalid managed destination: {relative}")
    path = target / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(target.resolve()):
        raise ValueError(f"target path escapes the project: {relative}")
    if path.is_symlink():
        raise ValueError(f"refusing to replace a symlink: {relative}")
    if relative.startswith(GUIDE_DEST + "/"):
        if not re.fullmatch(re.escape(GUIDE_DEST) + r"/[a-z0-9-]+\.md", relative):
            raise ValueError(f"invalid instruction guide destination: {relative}")
        if any(parent.is_symlink() for parent in path.parents if parent != target and parent.is_relative_to(target)):
            raise ValueError(f"instruction guide destination contains a symlink: {relative}")
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_commit(root: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def merge_block(existing: str, body: str) -> str:
    block = f"{BEGIN}\n{body.rstrip()}\n{END}"
    if BEGIN in existing or END in existing:
        if existing.count(BEGIN) != 1 or existing.count(END) != 1 or existing.index(END) < existing.index(BEGIN):
            raise ValueError("invalid or duplicate managed instruction markers")
        start, end = existing.index(BEGIN), existing.index(END) + len(END)
        return existing[:start] + block + existing[end:]
    return (existing.rstrip() + "\n\n" if existing.strip() else "") + block + "\n"


def claude_additions(text: str) -> str:
    marker = "## Claude-specific additions"
    if marker not in text:
        raise ValueError(f"missing {marker!r} in the Claude additions source")
    return text[text.index(marker) :].strip() + "\n"


def hook_groups(command_base: str | list[str], global_install: bool = False) -> dict:
    """Claude Code hook registrations. command_base is the shell prefix that runs the hook script, or, for exec form,
    a list of the executable and its leading arguments (https://code.claude.com/docs/en/hooks.md, "Exec form and shell
    form"); Windows uses exec form so no shell has to find python3.

    The user-level (global) install also checks file edits (the workspace rules) and runs at session end, for checks only
    it performs. PowerShell is matched with Bash because on Windows without Git Bash it is the only shell tool."""
    def handler(event: str, timeout: int) -> dict:
        if isinstance(command_base, (list, tuple)):
            return {"type": "command", "command": command_base[0], "args": [*command_base[1:], event], "timeout": timeout}
        return {"type": "command", "command": f"{command_base} {event}", "timeout": timeout}
    screen = "mcp__computer-use__.*|mcp__claude-in-chrome__.*"
    tools = "Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit" if global_install else "Bash|PowerShell"
    groups = {
        "SessionStart": [{"matcher": "startup|resume|clear|compact|fork", "hooks": [handler("session-start", 10)]}],
        "PreToolUse": [{"matcher": f"{tools}|mcp__github__merge_pull_request|mcp__codex_apps__github_merge_pull_request|mcp__github__enable_pr_auto_merge|mcp__claude-code-remote__subscribe_pr_activity|{screen}", "hooks": [handler("pre-tool", 15)]}],
        "PostToolUse": [{"matcher": screen, "hooks": [handler("post-tool", 5)]}],
        "Stop": [{"hooks": [handler("stop", 40)]}],
    }
    if global_install:
        groups["SessionEnd"] = [{"hooks": [handler("session-end", 10)]}]
    return groups


def ours(handler) -> bool:
    """True for one of this toolkit's hook handlers: the hook script is named in its command (shell form) or in its
    args (exec form)."""
    if not isinstance(handler, dict):
        return False
    args = handler.get("args")
    return HOOK_MARK in str(handler.get("command", "")) or (isinstance(args, list) and any(HOOK_MARK in str(arg) for arg in args))


def connector_permissions(path: Path) -> dict[str, list[str]]:
    """Permission rules for the private profile's claude.ai connectors: allow every tool of each server, ask before the listed tools
    that delete, trash, archive, close or cancel something. A matching ask rule prompts even when the server's allow
    rule also matches (https://code.claude.com/docs/en/permissions, "Manage permissions")."""
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("connectors"), list) or not data["connectors"]:
        raise ValueError("connector permissions must contain a nonempty connectors list")
    allow, ask = [], []
    for connector in data["connectors"]:
        if not isinstance(connector, dict) or not isinstance(connector.get("name"), str) or not connector["name"].strip():
            raise ValueError("each connector must have a name")
        server = connector.get("server")
        if not isinstance(server, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", server) or "__" in server or server.endswith("_"):
            raise ValueError(f"invalid connector server name: {server!r}")
        if not isinstance(connector.get("ask"), list):
            raise ValueError(f"connector {connector['name']!r} ask must be a list")
        allow.append(f"mcp__{server}__*")
        for tool in connector["ask"]:
            if not isinstance(tool, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", tool):
                raise ValueError(f"invalid connector tool name: {tool!r}")
            ask.append(f"mcp__{server}__{tool}")
    return {"allow": list(dict.fromkeys(allow)), "ask": list(dict.fromkeys(ask))}


def read_permission_rules(value: object, label: str, kinds: tuple[str, ...] = ("allow", "ask", "deny")) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    for kind in kinds:
        if kind in value and (not isinstance(value[kind], list) or any(not isinstance(rule, str) or not rule.strip() for rule in value[kind])):
            raise ValueError(f"{label}.{kind} must be a list of nonempty strings")
    return value


def owned_permissions(lock: dict) -> dict[str, list[str]]:
    """Old locks without provenance own nothing; matching user rules must never be claimed by an upgrade."""
    owned = read_permission_rules(lock.get("claude_permissions", {}), "project lock claude_permissions", ("allow", "ask"))
    if set(owned) - {"allow", "ask"}:
        raise ValueError("project lock claude_permissions only supports allow and ask")
    for kind, rules in owned.items():
        for rule in rules:
            if not re.fullmatch(r"mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_*-]+", rule):
                raise ValueError(f"invalid owned connector permission: {rule!r}")
    return owned


def permission_ownership(existing: str, desired: dict[str, list[str]], previous: dict[str, list[str]]) -> dict[str, list[str]]:
    settings = json.loads(existing) if existing.strip() else {}
    if not isinstance(settings, dict):
        raise ValueError(f"{SETTINGS} must contain a JSON object")
    current = read_permission_rules(settings.get("permissions", {}), f"{SETTINGS}: permissions")
    # Keep ownership only for entries we added earlier or need to add now.
    # An identical preexisting rule remains the user's, including after reinstall.
    return {kind: [rule for rule in desired[kind] if rule in previous.get(kind, []) or rule not in current.get(kind, [])]
            for kind in ("allow", "ask")}


def merge_permissions(settings: dict, add: dict[str, list[str]] | None, drop: dict[str, list[str]] | None) -> None:
    """Remove the drop rules, then append the add rules that are missing, keeping every other entry and its order."""
    if not add and not drop:
        return
    permissions = read_permission_rules(settings.get("permissions", {}), f"{SETTINGS}: permissions")
    for kind in ("allow", "ask", "deny"):
        rules = permissions.get(kind, [])
        removed = set((drop or {}).get(kind, []))
        rules = list(dict.fromkeys(rule for rule in rules if rule not in removed))
        for rule in (add or {}).get(kind, []):
            if rule not in rules:
                rules.append(rule)
        if rules:
            permissions[kind] = rules
        else:
            permissions.pop(kind, None)
    if permissions:
        settings["permissions"] = permissions
    else:
        settings.pop("permissions", None)


def merge_settings(existing: str, command_base: str | list[str] | None, global_install: bool = False, permissions: dict[str, list[str]] | None = None, drop_permissions: dict[str, list[str]] | None = None) -> str:
    """Replace this toolkit's hook entries in a Claude settings file and keep everything else. Empty result means no file.
    permissions adds allow and ask rules without duplicates; drop_permissions contains only entries whose ownership
    the project lock recorded, never every rule in the current catalog."""
    try:
        settings = json.loads(existing) if existing.strip() else {}
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {SETTINGS}: {error}") from error
    if not isinstance(settings, dict):
        raise ValueError(f"{SETTINGS} must contain a JSON object")
    hooks = settings.get("hooks")
    if isinstance(hooks, dict):
        for event in list(hooks):
            if not isinstance(hooks[event], list):
                continue
            groups = []
            for group in hooks[event]:
                handlers = [item for item in group.get("hooks", []) if not ours(item)] if isinstance(group, dict) else None
                if handlers is None:
                    groups.append(group)
                elif handlers:
                    groups.append({**group, "hooks": handlers})
            if groups:
                hooks[event] = groups
            else:
                del hooks[event]
        if not hooks:
            del settings["hooks"]
    if command_base:
        merged = settings.setdefault("hooks", {})
        for event, groups in hook_groups(command_base, global_install).items():
            merged.setdefault(event, []).extend(groups)
    merge_permissions(settings, permissions, drop_permissions)
    return json.dumps(settings, indent=2) + "\n" if settings else ""


def render_skill(source: Path, runtime_format: str) -> bytes:
    text = source.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"invalid skill frontmatter: {source}")
    if runtime_format == "codex":
        return text.encode()
    metadata = source.parent / "agents/openai.yaml"
    manual = metadata.exists() and re.search(r"(?m)^\s*allow_implicit_invocation:\s*false\s*$", metadata.read_text(encoding="utf-8"))
    end = text.index("\n---\n", 4)
    frontmatter = text[4:end]
    if manual and not re.search(r"(?m)^disable-model-invocation:", frontmatter):
        frontmatter += "\ndisable-model-invocation: true"
    return ("---\n" + frontmatter + text[end:]).encode()


def plan(root: Path, target: Path, profile_name: str, runtimes: list[str], selected: list[str] | None = None, source_repository: str | None = None) -> tuple[dict, dict[str, bytes], set[str]]:
    if not NAME.fullmatch(profile_name):
        raise ValueError("invalid profile name")
    manifest = read_json(root / "system-manifest.json")
    profile = read_json(root / "profiles" / f"{profile_name}.json")
    skills = selected if selected is not None else profile["skills"]
    if len(skills) != len(set(skills)) or any(not NAME.fullmatch(x) or x not in profile["skills"] for x in skills):
        raise ValueError("selected skills must be unique names from the selected profile")
    if not runtimes or len(runtimes) != len(set(runtimes)) or any(not NAME.fullmatch(x) for x in runtimes):
        raise ValueError("select one or more unique runtime names")
    adapters = {name: read_json(root / "adapters" / name / "adapter.json") for name in runtimes}
    lock_path = target_path(target, LOCK)
    if lock_path.exists() and not lock_path.is_file():
        raise ValueError("project lock destination is not a file")
    old_lock = read_json(lock_path) if lock_path.exists() else {}
    if not isinstance(old_lock, dict):
        raise ValueError("invalid project lock file")
    old_files = old_lock.get("files", {})
    if not isinstance(old_files, dict):
        raise ValueError("invalid project lock file")
    previous_permissions = owned_permissions(old_lock)
    managed_permissions = None
    previous_instructions = old_lock.get("created_instructions", [])
    if not isinstance(previous_instructions, list) or any(not isinstance(item, str) for item in previous_instructions):
        raise ValueError("invalid instruction ownership in project lock")
    created_instructions = []
    config_ownership = None
    body = source_path(root, profile["instruction_file"]).read_text(encoding="utf-8")
    instruction_bodies = {"AGENTS.md": body}
    files: dict[str, bytes] = {}
    guides = instruction_guides(root, profile["instruction_guide_root"]) if profile.get("instruction_guide_root") else {}
    for filename, text in guides.items():
        for name in GUIDE_LINK.findall(text):
            if name not in guides:
                raise ValueError(f"instruction link has no guide: {name}")
        # Guides sit beside one another; their links resolve from that directory, not the project root.
        files[f"{GUIDE_DEST}/{filename}"] = render_guide_links(text, ".").encode()
    for name, adapter in adapters.items():
        if "instruction_template" in adapter:
            instruction_bodies[adapter["instruction_path"]] = source_path(root, adapter["instruction_template"]).read_text(encoding="utf-8")
        for skill in skills:
            source_dir = source_path(root, profile["skill_root"]) / skill
            if not (source_dir / "SKILL.md").is_file():
                raise ValueError(f"missing skill: {skill}")
            for item in sorted(source_dir.rglob("*")):
                if not item.is_file() or "__pycache__" in item.parts or item.name == ".DS_Store":
                    continue
                if item.is_symlink():
                    raise ValueError(f"skill resources must be real files: {item}")
                rel = item.relative_to(source_dir)
                if adapter["skill_format"] != "codex" and rel == Path("agents/openai.yaml"):
                    continue
                destination = (Path(adapter["skill_path"]) / skill / rel).as_posix()
                files[destination] = render_skill(item, adapter["skill_format"]) if rel == Path("SKILL.md") else item.read_bytes()
    if "claude" in adapters and profile.get("claude_additions"):
        additions = claude_additions(source_path(root, profile["claude_additions"]).read_text(encoding="utf-8"))
        instruction_bodies["CLAUDE.md"] = instruction_bodies["CLAUDE.md"].rstrip() + "\n\n" + additions
    if "claude" in adapters and (profile.get("claude_hooks") or profile.get("claude_permissions")):
        command = None
        if profile.get("claude_hooks"):
            files[HOOK_DEST] = source_path(root, profile["claude_hooks"]).read_bytes()
            command = PROJECT_HOOK_COMMAND
        permissions = connector_permissions(source_path(root, profile["claude_permissions"])) if profile_name == "personal-private" and profile.get("claude_permissions") else None
        settings_path = target_path(target, SETTINGS)
        existing = settings_path.read_text(encoding="utf-8") if settings_path.exists() else ""
        if permissions is not None:
            managed_permissions = permission_ownership(existing, permissions, previous_permissions)
        drop = {kind: [rule for rule in rules if rule not in (permissions or {}).get(kind, [])]
                for kind, rules in previous_permissions.items()}
        files[SETTINGS] = merge_settings(existing, command, permissions=permissions, drop_permissions=drop).encode()
    for rel, content in instruction_bodies.items():
        if guides:
            for name in GUIDE_LINK.findall(content):
                if name not in guides:
                    raise ValueError(f"instruction link has no guide: {name}")
            content = render_guide_links(content, GUIDE_DEST)
        path = target_path(target, rel)
        if rel.endswith(".md") and (rel in previous_instructions or not path.exists()):
            created_instructions.append(rel)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        # Cursor's frontmatter must remain at the start of the dedicated rule.
        if rel.endswith(".mdc"):
            files[rel] = content.encode()
        else:
            files[rel] = merge_block(existing, content).encode()
    if "codex" in adapters and profile_name == "personal-private":
        config = target_path(target, ".codex/config.toml")
        existing = config.read_text(encoding="utf-8") if config.exists() else ""
        rendered = codex_budget_config(existing)
        config_ownership = budget_ownership(existing, rendered, config.exists(), old_lock.get("codex_budget"))
        files[".codex/config.toml"] = rendered.encode()
    stale = set(old_files) - set(files)
    if source_repository is not None and source_repository not in (manifest["repository"], manifest[profile["repository_key"]]):
        raise ValueError("source repository must be this toolkit or the profile's declared source")
    repository = source_repository or manifest[profile["repository_key"]]
    lock = {
        "schema_version": 1,
        "toolkit_version": manifest["version"],
        "source_repository": repository,
        "source_commit": source_commit(root) if repository == manifest["repository"] else None,
        "profile": profile_name,
        "runtimes": runtimes,
        "skills": skills,
        "files": {rel: sha(data) for rel, data in sorted(files.items())},
    }
    lock["content_sha256"] = sha(json.dumps(lock["files"], sort_keys=True).encode())
    if managed_permissions is not None:
        lock["claude_permissions"] = managed_permissions
    if created_instructions:
        lock["created_instructions"] = sorted(created_instructions)
    if config_ownership is not None:
        lock["codex_budget"] = config_ownership
    return lock, files, stale


def install(root: Path, target: Path, profile_name: str, runtimes: list[str], selected: list[str] | None, apply: bool, replace_existing: bool, backup_base: Path | None = None, source_repository: str | None = None) -> dict:
    target = target.resolve()
    if not target.is_dir() or target.is_relative_to(root.resolve()) or root.resolve().is_relative_to(target):
        raise ValueError("target must be an existing project directory outside the toolkit")
    lock, files, stale = plan(root, target, profile_name, runtimes, selected, source_repository)
    lock_path = target_path(target, LOCK)
    old_lock = read_json(lock_path) if lock_path.exists() else {}
    old_files = old_lock.get("files", {})
    instructions = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", ".codex/config.toml", ".github/copilot-instructions.md", SETTINGS}
    conflicts = []
    changes = []
    for rel, data in files.items():
        path = target_path(target, rel)
        if path.exists() and not path.is_file():
            raise ValueError(f"file destination is not a file: {rel}")
        if not path.exists() or path.read_bytes() != data:
            changes.append(rel)
            if path.exists() and rel not in instructions and not unchanged(old_files.get(rel), path.read_bytes()):
                conflicts.append(rel)
    removals = []
    for rel in sorted(stale):
        path = target_path(target, rel)
        if not path.exists():
            continue
        if rel == ".codex/config.toml":
            text = path.read_text(encoding="utf-8")
            ownership = old_lock.get("codex_budget")
            if (not isinstance(ownership, dict) or not isinstance(ownership.get("installed_line"), str)
                    or budget_line(text) != ownership["installed_line"]):
                continue  # legacy locks and user-edited values do not prove ownership
            original = ownership.get("original_line")
            if original is not None and not isinstance(original, str):
                raise ValueError("invalid Codex budget ownership in project lock")
            remaining = text.replace(ownership["installed_line"], original or "", 1)
            if not remaining.strip() and ownership.get("created") is True:
                removals.append(rel)
            elif remaining != text:
                files[rel] = remaining.encode()
                changes.append(rel)
            continue
        if rel == SETTINGS:
            drop = owned_permissions(old_lock)
            remaining = merge_settings(path.read_text(encoding="utf-8"), None, drop_permissions=drop)
            if remaining:
                files[rel] = remaining.encode()
                changes.append(rel)
            else:
                removals.append(rel)
            continue
        if rel in instructions:
            text = path.read_text(encoding="utf-8")
            if BEGIN in text or END in text:
                if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(END) < text.index(BEGIN):
                    raise ValueError(f"invalid or duplicate managed instruction markers: {rel}")
                start, end = text.index(BEGIN), text.index(END) + len(END)
                remaining = (text[:start] + text[end:]).strip()
                if not remaining and rel in old_lock.get("created_instructions", []):
                    removals.append(rel)
                else:
                    files[rel] = remaining.encode() + b"\n"
                    changes.append(rel)
        else:
            if not unchanged(old_files.get(rel), path.read_bytes()):
                conflicts.append(rel)
            removals.append(rel)
    if conflicts and not replace_existing:
        raise ValueError("locally modified or unmanaged files would be replaced: " + ", ".join(conflicts) + ". Review them, then use --replace-existing if intended.")
    lock_data = (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode()
    if not lock_path.exists() or lock_path.read_bytes() != lock_data:
        files[LOCK] = lock_data
        changes.append(LOCK)
    for rel in changes:
        print(f"UPDATE {rel}")
    for rel in removals:
        print(f"REMOVE {rel}")
    if not apply:
        print(f"DRY_RUN {len(changes)} writes, {len(removals)} removals; pass --apply")
        return {"writes": len(changes), "removals": len(removals)}
    backup_base = backup_base or Path.home() / ".local/state/ai-agent-system/backups"
    backup = backup_base / sha(str(target).encode())[:12] / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for rel in dict.fromkeys(changes + removals):
        path = target_path(target, rel)
        if path.exists():
            destination = backup / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    for rel in dict.fromkeys(changes):
        path = target_path(target, rel)
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            handle.write(files[rel])
            temporary = Path(handle.name)
        if mode is not None:
            temporary.chmod(mode)
        temporary.replace(path)
    for rel in removals:
        target_path(target, rel).unlink()
    for rel, expected in lock["files"].items():
        if sha(target_path(target, rel).read_bytes()) != expected:
            raise ValueError(f"verification failed: {rel}")
    print(f"INSTALLED {len(lock['skills'])} skills for {', '.join(runtimes)}; {len(changes)} writes, {len(removals)} removals")
    if backup.exists():
        print(f"BACKUP {backup}")
    return {"writes": len(changes), "removals": len(removals)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--profile", required=True, help="personal-private or public-safe")
    parser.add_argument("--runtimes", default="codex,claude", help="comma-separated codex,claude,cursor,copilot,gemini")
    parser.add_argument("--skills", help="optional comma-separated subset from the profile")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--replace-existing", action="store_true", help="back up and replace conflicting skill files")
    args = parser.parse_args()
    try:
        install(ROOT, args.target, args.profile, args.runtimes.split(","), args.skills.split(",") if args.skills else ([] if args.skills == "" else None), args.apply, args.replace_existing)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
