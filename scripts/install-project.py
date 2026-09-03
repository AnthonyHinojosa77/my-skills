#!/usr/bin/env python3
"""Install a versioned AI toolkit into a project. Dry-run unless --apply is given."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- ai-agent-system:begin -->"
END = "<!-- ai-agent-system:end -->"
LOCK = ".ai-agent-system.json"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"source path escapes the toolkit: {relative}")
    return path


def target_path(target: Path, relative: str) -> Path:
    allowed_files = {"AGENTS.md", "CLAUDE.md", LOCK, ".cursor/rules/ai-agent-system.mdc", ".github/copilot-instructions.md"}
    allowed_roots = (".agents/skills/", ".claude/skills/", ".cursor/skills/", ".github/skills/")
    if relative not in allowed_files and not relative.startswith(allowed_roots):
        raise ValueError(f"not a managed destination: {relative}")
    if ".." in Path(relative).parts:
        raise ValueError(f"invalid managed destination: {relative}")
    path = target / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(target.resolve()):
        raise ValueError(f"target path escapes the project: {relative}")
    if path.is_symlink():
        raise ValueError(f"refusing to replace a symlink: {relative}")
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


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


def render_skill(source: Path, runtime_format: str) -> bytes:
    text = source.read_text()
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"invalid skill frontmatter: {source}")
    if runtime_format == "codex":
        return text.encode()
    metadata = source.parent / "agents/openai.yaml"
    manual = metadata.exists() and re.search(r"(?m)^\s*allow_implicit_invocation:\s*false\s*$", metadata.read_text())
    end = text.index("\n---\n", 4)
    frontmatter = text[4:end]
    if manual and not re.search(r"(?m)^disable-model-invocation:", frontmatter):
        frontmatter += "\ndisable-model-invocation: true"
    return ("---\n" + frontmatter + text[end:]).encode()


def plan(root: Path, target: Path, profile_name: str, runtimes: list[str], selected: list[str] | None = None) -> tuple[dict, dict[str, bytes], set[str]]:
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
    old_files = old_lock.get("files", {})
    if not isinstance(old_files, dict):
        raise ValueError("invalid project lock file")
    body = source_path(root, profile["instruction_file"]).read_text()
    instruction_bodies = {"AGENTS.md": body}
    files: dict[str, bytes] = {}
    for name, adapter in adapters.items():
        if "instruction_template" in adapter:
            instruction_bodies[adapter["instruction_path"]] = source_path(root, adapter["instruction_template"]).read_text()
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
    for rel, content in instruction_bodies.items():
        path = target_path(target, rel)
        existing = path.read_text() if path.exists() else ""
        # Cursor's frontmatter must remain at the start of the dedicated rule.
        if rel.endswith(".mdc"):
            files[rel] = content.encode()
        else:
            files[rel] = merge_block(existing, content).encode()
    stale = set(old_files) - set(files)
    lock = {
        "schema_version": 1,
        "toolkit_version": manifest["version"],
        "source_repository": manifest[profile["repository_key"]],
        "source_commit": source_commit(root) if manifest[profile["repository_key"]] == manifest["repository"] else None,
        "profile": profile_name,
        "runtimes": runtimes,
        "skills": skills,
        "files": {rel: sha(data) for rel, data in sorted(files.items())},
    }
    lock["content_sha256"] = sha(json.dumps(lock["files"], sort_keys=True).encode())
    return lock, files, stale


def install(root: Path, target: Path, profile_name: str, runtimes: list[str], selected: list[str] | None, apply: bool, replace_existing: bool, backup_base: Path | None = None) -> dict:
    target = target.resolve()
    if not target.is_dir() or target.is_relative_to(root.resolve()) or root.resolve().is_relative_to(target):
        raise ValueError("target must be an existing project directory outside the toolkit")
    lock, files, stale = plan(root, target, profile_name, runtimes, selected)
    lock_path = target_path(target, LOCK)
    old_lock = read_json(lock_path) if lock_path.exists() else {}
    old_files = old_lock.get("files", {})
    instructions = {"AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"}
    conflicts = []
    changes = []
    for rel, data in files.items():
        path = target_path(target, rel)
        if path.exists() and not path.is_file():
            raise ValueError(f"file destination is not a file: {rel}")
        if not path.exists() or path.read_bytes() != data:
            changes.append(rel)
            if path.exists() and rel not in instructions and old_files.get(rel) != sha(path.read_bytes()):
                conflicts.append(rel)
    removals = []
    for rel in sorted(stale):
        path = target_path(target, rel)
        if not path.exists():
            continue
        if rel in instructions:
            text = path.read_text()
            if BEGIN in text or END in text:
                if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(END) < text.index(BEGIN):
                    raise ValueError(f"invalid or duplicate managed instruction markers: {rel}")
                start, end = text.index(BEGIN), text.index(END) + len(END)
                files[rel] = (text[:start] + text[end:]).strip().encode() + b"\n"
                changes.append(rel)
        else:
            if old_files.get(rel) != sha(path.read_bytes()):
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
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            handle.write(files[rel])
            temporary = Path(handle.name)
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
    parser.add_argument("--runtimes", default="codex,claude", help="comma-separated codex,claude,cursor,copilot")
    parser.add_argument("--skills", help="optional comma-separated subset from the profile")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--replace-existing", action="store_true", help="back up and replace conflicting skill files")
    args = parser.parse_args()
    try:
        install(ROOT, args.target, args.profile, args.runtimes.split(","), args.skills.split(",") if args.skills else None, args.apply, args.replace_existing)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
