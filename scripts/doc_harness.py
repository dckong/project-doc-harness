#!/usr/bin/env python3
"""Scaffold and audit an agent-readable, resumable project documentation harness."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


REQUIRED_DIRS = (
    "docs/design-docs",
    "docs/product-specs",
    "docs/exec-plans/active",
    "docs/exec-plans/completed",
    "docs/generated",
    "docs/references",
)

AGENTS_TEMPLATE = """# Repository Guide

## Mission and boundaries

- TODO: Describe the project in one sentence.
- TODO: Name the most important boundary or invariant.

## Commands

- Build: `TODO`
- Test: `TODO`
- Lint: `TODO`

## Non-negotiable rules

- Preserve existing user changes.
- Keep documentation aligned with executable behavior and observed environments.

## Documentation map

- [Architecture](ARCHITECTURE.md)
- [Design decisions](docs/design-docs/index.md)
- [Product specifications](docs/product-specs/index.md)
- [Active execution plans](docs/exec-plans/active/index.md)
- [Technical debt](docs/exec-plans/tech-debt-tracker.md)
- [Quality score](docs/QUALITY_SCORE.md)
- [Reliability](docs/RELIABILITY.md)
- [Security](docs/SECURITY.md)

## Task routing

- Before changing a subsystem, read its architecture and design documents.
- Before changing user-visible behavior, read the relevant product specification.
- For complex work, create or update a versioned execution plan and its Resume snapshot.

## Before finishing

- Run the relevant tests and documentation checks.
- Update affected state, documentation, plans, generated artifacts, and debt records.
"""

PROJECT_STATE_LINK = "- [Current project state](docs/PROJECT_STATE.md)\n"

TEMPLATES = {
    "AGENTS.md": AGENTS_TEMPLATE,
    "ARCHITECTURE.md": """---
doc_type: architecture
status: draft
owner: TBD
last_reviewed: TBD
---

# Architecture

## Context and scope

TODO

## Components and responsibilities

TODO

## Dependency direction

TODO

## Data and control flow

TODO

## Cross-cutting concerns

TODO

## Enforced invariants

TODO: Link lint rules, structure tests, schemas, or other executable constraints.

## Where to learn more

- [Design decisions](docs/design-docs/index.md)
""",
    "docs/design-docs/index.md": """# Design documents

| Document | Status | Owner | Last reviewed |
| --- | --- | --- | --- |
| [Core beliefs](core-beliefs.md) | proposed | TBD | TBD |
""",
    "docs/design-docs/core-beliefs.md": """---
doc_type: decision
status: proposed
owner: TBD
last_reviewed: TBD
---

# Core beliefs

## Context

TODO

## Goals and non-goals

TODO

## Constraints

TODO

## Decision or proposal

- TODO: Record a durable engineering or product principle and its rationale.

## Alternatives considered

TODO

## Consequences

TODO

## Verification

- TODO: Link the check that enforces each mechanical principle.

## Related sources

TODO
""",
    "docs/product-specs/index.md": """# Product specifications

| Capability | Status | Owner | Last reviewed |
| --- | --- | --- | --- |
| TODO | missing | TBD | TBD |
""",
    "docs/exec-plans/active/index.md": """# Active execution plans

No active plans. Add one Markdown file per complex task and link it here.
""",
    "docs/exec-plans/completed/index.md": """# Completed execution plans

Move completed or cancelled plans here only after promoting durable knowledge and recording closure evidence.
""",
    "docs/exec-plans/tech-debt-tracker.md": """---
doc_type: tech-debt
status: active
owner: TBD
last_reviewed: TBD
---

# Technical debt tracker

| ID | Scope | Risk and evidence | Recommended direction | Owner | Status | Last reviewed |
| --- | --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TBD | open | TBD |
""",
    "docs/QUALITY_SCORE.md": """# Documentation quality score

| Domain | Discoverability | Resumability | Correctness | Authority | Freshness | Next action | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Project-wide | partial | missing | partial | partial | missing | Replace starter TODOs with verified facts | TBD |
""",
    "docs/RELIABILITY.md": """---
doc_type: reliability
status: draft
owner: TBD
last_reviewed: TBD
---

# Reliability

## Service objectives

TODO

## Failure modes and recovery

TODO

## Observability and verification

TODO
""",
    "docs/SECURITY.md": """---
doc_type: security
status: draft
owner: TBD
last_reviewed: TBD
---

# Security

## Trust boundaries and sensitive data

TODO

## Required controls

TODO

## Verification and response

TODO
""",
}

PROJECT_STATE_TEMPLATE = """---
doc_type: project-state
status: active
owner: TBD
last_reviewed: TBD
verified_commit: TBD
---

# Project State

## Current phase

TODO

## Now

TODO: Summarize current facts and link their authoritative documents.

## Next action

TODO: Name one directly executable and verifiable action.

## Blocked or awaiting

None

## Active work

None

## Environment divergence

None

## Last verified

TODO: Record date, commit or worktree, environment, commands, result, and limitations.

## Do not reopen

None
"""

DOC_TYPE_STATUSES = {
    "project-state": {"active"},
    "architecture": {"draft", "active", "deprecated"},
    "product-spec": {"draft", "active", "deprecated"},
    "operations": {"draft", "active", "deprecated"},
    "reliability": {"draft", "active", "deprecated"},
    "security": {"draft", "active", "deprecated"},
    "decision": {"proposed", "implemented", "rejected", "superseded"},
    "plan": {"active", "blocked", "completed", "cancelled"},
    "tech-debt": {"active", "deprecated"},
}
CURRENT_OWNER_STATUSES = {"active", "blocked", "implemented"}
META_FIELDS = ("doc_type", "status", "owner", "last_reviewed")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD)\b")

PROJECT_STATE_HEADINGS = (
    "Current phase",
    "Now",
    "Next action",
    "Blocked or awaiting",
    "Active work",
    "Environment divergence",
    "Last verified",
    "Do not reopen",
)
RESUME_LABELS = (
    "Current state",
    "Next action",
    "Blocked by",
    "Awaiting",
    "Last verified",
)
VERIFICATION_LABELS = ("commit", "environment", "commands", "date")
COMPLETION_HEADINGS = (
    "Outcome",
    "Durable decisions promoted",
    "Product or architecture updates",
    "Remaining work transferred",
    "Rejected alternatives recorded",
    "Final validation",
)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def print(self) -> None:
        for label, items in (("ERROR", self.errors), ("WARN", self.warnings), ("INFO", self.info)):
            for item in items:
                print(f"{label}: {item}")
        print(
            f"SUMMARY: {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s), {len(self.info)} info message(s)"
        )


def scaffold(root: Path, with_project_state: bool) -> int:
    created: list[Path] = []
    for relative in REQUIRED_DIRS:
        path = root / relative
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)

    templates = dict(TEMPLATES)
    if with_project_state:
        templates["docs/PROJECT_STATE.md"] = PROJECT_STATE_TEMPLATE
        templates["AGENTS.md"] = AGENTS_TEMPLATE.replace(
            "## Documentation map\n\n",
            "## Documentation map\n\n" + PROJECT_STATE_LINK,
        )

    for relative, content in templates.items():
        path = root / relative
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path)

    if with_project_state:
        agents = root / "AGENTS.md"
        if agents.is_file():
            text = agents.read_text(encoding="utf-8")
            if "docs/PROJECT_STATE.md" not in text and "## Documentation map\n" in text:
                text = text.replace(
                    "## Documentation map\n",
                    "## Documentation map\n\n" + PROJECT_STATE_LINK.rstrip() + "\n",
                    1,
                )
                agents.write_text(text, encoding="utf-8")
                if agents not in created:
                    created.append(agents)

    if created:
        for path in created:
            print(f"CREATED_OR_UPDATED: {path.relative_to(root)}")
    else:
        print("No changes: all scaffold paths already exist.")
    print("Next: replace TODO/TBD placeholders with verified project facts, then run check --strict.")
    return 0


def frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def body_without_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text[end + 5 :] if end >= 0 else text


def markdown_files(root: Path) -> list[Path]:
    ignored = {".git", "node_modules", "vendor", ".venv", "venv"}
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in ignored for part in path.relative_to(root).parts)
    )


def check_links(root: Path, paths: list[Path], report: Report) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                report.warnings.append(f"{path.relative_to(root)} links outside repository: {target}")
                continue
            if not resolved.exists():
                report.errors.append(f"broken link in {path.relative_to(root)}: {target}")


def metadata_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for relative in (
        "ARCHITECTURE.md",
        "docs/PROJECT_STATE.md",
        "docs/RELIABILITY.md",
        "docs/SECURITY.md",
        "docs/exec-plans/tech-debt-tracker.md",
    ):
        path = root / relative
        if path.is_file():
            paths.add(path)
    for relative in (
        "docs/design-docs",
        "docs/product-specs",
        "docs/exec-plans/active",
        "docs/exec-plans/completed",
        "docs/operations",
    ):
        directory = root / relative
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.md"):
            if path.name.lower() not in {"index.md", "readme.md", "agents.md"}:
                paths.add(path)
    return sorted(paths)


def expected_doc_type(root: Path, path: Path) -> str | None:
    relative = path.relative_to(root).as_posix()
    if relative == "ARCHITECTURE.md":
        return "architecture"
    if relative == "docs/PROJECT_STATE.md":
        return "project-state"
    if relative == "docs/RELIABILITY.md":
        return "reliability"
    if relative == "docs/SECURITY.md":
        return "security"
    if relative == "docs/exec-plans/tech-debt-tracker.md":
        return "tech-debt"
    if relative.startswith("docs/design-docs/"):
        return "decision"
    if relative.startswith("docs/product-specs/"):
        return "product-spec"
    if relative.startswith("docs/exec-plans/"):
        return "plan"
    if relative.startswith("docs/operations/"):
        return "operations"
    return None


def check_date(path: Path, root: Path, value: str, stale_days: int, report: Report) -> None:
    display = path.relative_to(root)
    if value in ("", "TBD"):
        report.warnings.append(f"{display} has no verified last_reviewed date")
        return
    try:
        reviewed_date = dt.date.fromisoformat(value)
    except ValueError:
        report.warnings.append(f"{display} has invalid last_reviewed date: {value}")
        return
    age = (dt.date.today() - reviewed_date).days
    if age > stale_days:
        report.warnings.append(f"{display} was last reviewed {age} days ago")


def check_replacement(root: Path, path: Path, data: dict[str, str], report: Report) -> None:
    if data.get("status") not in {"deprecated", "superseded"}:
        return
    replacement = data.get("superseded_by", "")
    display = path.relative_to(root)
    if not replacement or replacement == "TBD":
        report.errors.append(f"{display} is {data.get('status')} but has no superseded_by target")
        return
    target = (root / replacement).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        report.errors.append(f"{display} has superseded_by outside repository: {replacement}")
        return
    if not target.exists():
        report.errors.append(f"{display} has missing superseded_by target: {replacement}")


def check_metadata(root: Path, report: Report, stale_days: int) -> None:
    for path in metadata_paths(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        data = frontmatter(text)
        display = path.relative_to(root)
        if data is None:
            report.warnings.append(f"{display} has no YAML frontmatter")
            continue
        for field in META_FIELDS:
            if not data.get(field):
                report.warnings.append(f"{display} is missing metadata: {field}")

        doc_type = data.get("doc_type", "")
        expected = expected_doc_type(root, path)
        if expected and doc_type and doc_type != expected:
            report.errors.append(f"{display} has doc_type {doc_type}; expected {expected}")
        if doc_type and doc_type not in DOC_TYPE_STATUSES:
            report.errors.append(f"{display} has unknown doc_type: {doc_type}")
        status = data.get("status", "")
        allowed = DOC_TYPE_STATUSES.get(doc_type)
        if allowed is not None and status not in allowed:
            report.errors.append(
                f"{display} has invalid status {status or '<missing>'} for {doc_type}; "
                f"expected one of {', '.join(sorted(allowed))}"
            )
        owner = data.get("owner", "")
        if status in CURRENT_OWNER_STATUSES and owner in ("", "TBD"):
            report.warnings.append(f"{display} is current work or authority but owner is {owner or 'missing'}")
        check_date(path, root, data.get("last_reviewed", ""), stale_days, report)
        if doc_type == "project-state" and data.get("verified_commit", "") in ("", "TBD"):
            report.warnings.append(f"{display} has no verified_commit")
        check_replacement(root, path, data, report)

        placeholders = len(PLACEHOLDER_RE.findall(text))
        if status in CURRENT_OWNER_STATUSES and placeholders:
            report.warnings.append(f"{display} is current but contains {placeholders} TODO/TBD placeholder(s)")


def heading_names(text: str) -> list[str]:
    return [match.group(2).strip().rstrip("#").strip() for match in HEADING_RE.finditer(text)]


def section_text(text: str, heading: str) -> str | None:
    matches = list(HEADING_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group(2).strip().rstrip("#").strip().casefold() != heading.casefold():
            continue
        level = len(match.group(1))
        start = match.end()
        end = len(text)
        for following in matches[index + 1 :]:
            if len(following.group(1)) <= level:
                end = following.start()
                break
        return text[start:end].strip()
    return None


def bullet_value(text: str, label: str) -> str | None:
    match = re.search(rf"^\s*-\s*{re.escape(label)}\s*:\s*(.*?)\s*$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"^\s*-?\s*{re.escape(label)}\s*:\s*(.*?)\s*$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def is_placeholder_action(value: str) -> bool:
    normalized = value.strip().casefold()
    return (
        not normalized
        or normalized in {"none", "todo", "tbd", "n/a"}
        or "继续开发" in value
        or "continue development" in normalized
        or bool(PLACEHOLDER_RE.search(value))
    )


def plan_files(root: Path, area: str) -> list[Path]:
    directory = root / area
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.glob("*.md")
        if path.name.lower() not in {"index.md", "readme.md"}
    )


def check_resume_snapshot(root: Path, path: Path, report: Report) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    display = path.relative_to(root)
    snapshot = section_text(text, "Resume snapshot")
    if snapshot is None:
        report.errors.append(f"{display} is active work but has no Resume snapshot")
        return
    for label in RESUME_LABELS:
        if bullet_value(snapshot, label) is None:
            report.errors.append(f"{display} Resume snapshot is missing label: {label}")
    next_action = bullet_value(snapshot, "Next action")
    if next_action is not None and is_placeholder_action(next_action):
        report.errors.append(f"{display} Resume snapshot has no executable Next action")
    for label in VERIFICATION_LABELS:
        value = field_value(snapshot, label)
        if value is None:
            report.errors.append(f"{display} Resume snapshot Last verified is missing: {label}")
        elif value in ("", "TBD", "TODO"):
            report.warnings.append(f"{display} Resume snapshot Last verified has no value for: {label}")


def check_completion_notes(root: Path, path: Path, report: Report) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    display = path.relative_to(root)
    completion = section_text(text, "Completion notes")
    if completion is None:
        report.errors.append(f"{display} is completed or cancelled but has no Completion notes")
        return
    names = {name.casefold() for name in heading_names(completion)}
    for heading in COMPLETION_HEADINGS:
        if heading.casefold() not in names:
            report.errors.append(f"{display} Completion notes is missing heading: {heading}")
            continue
        content = section_text(completion, heading)
        if content is not None and not content.strip():
            report.errors.append(f"{display} Completion notes has empty section: {heading}")


def check_plan_contracts(root: Path, report: Report) -> list[Path]:
    active = plan_files(root, "docs/exec-plans/active")
    completed = plan_files(root, "docs/exec-plans/completed")
    for path in active:
        data = frontmatter(path.read_text(encoding="utf-8", errors="replace")) or {}
        if data.get("status") not in {"active", "blocked"}:
            report.errors.append(
                f"{path.relative_to(root)} is in active/ but status is {data.get('status') or 'missing'}"
            )
        check_resume_snapshot(root, path, report)
    for path in completed:
        data = frontmatter(path.read_text(encoding="utf-8", errors="replace")) or {}
        if data.get("status") not in {"completed", "cancelled"}:
            report.errors.append(
                f"{path.relative_to(root)} is in completed/ but status is {data.get('status') or 'missing'}"
            )
        check_completion_notes(root, path, report)
    return active


def check_project_state(root: Path, active_plans: list[Path], report: Report) -> None:
    path = root / "docs/PROJECT_STATE.md"
    if active_plans and not path.is_file():
        report.errors.append("active execution plans require docs/PROJECT_STATE.md")
        return
    if not path.is_file():
        return

    agents = root / "AGENTS.md"
    if agents.is_file() and "docs/PROJECT_STATE.md" not in agents.read_text(
        encoding="utf-8", errors="replace"
    ):
        report.errors.append("AGENTS.md does not link docs/PROJECT_STATE.md")

    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text.splitlines()) > 100:
        report.warnings.append(
            f"docs/PROJECT_STATE.md is {len(text.splitlines())} lines; keep the state capsule at or below 100"
        )
    for heading in PROJECT_STATE_HEADINGS:
        content = section_text(text, heading)
        if content is None:
            report.errors.append(f"docs/PROJECT_STATE.md is missing heading: {heading}")
        elif not content.strip():
            report.errors.append(f"docs/PROJECT_STATE.md has empty section: {heading}")
    next_action = section_text(text, "Next action")
    if next_action is not None and is_placeholder_action(next_action):
        report.errors.append("docs/PROJECT_STATE.md has no executable Next action")


def check_decision_contracts(root: Path, report: Report) -> None:
    for path in metadata_paths(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        data = frontmatter(text) or {}
        if data.get("doc_type") != "decision":
            continue
        if section_text(text, "Alternatives considered") is None:
            report.warnings.append(f"{path.relative_to(root)} decision has no Alternatives considered section")


def check_indexes(root: Path, report: Report) -> None:
    for area in (
        "docs/design-docs",
        "docs/product-specs",
        "docs/exec-plans/active",
        "docs/exec-plans/completed",
    ):
        directory = root / area
        index = directory / "index.md"
        if not directory.is_dir() or not index.is_file():
            continue
        index_text = index.read_text(encoding="utf-8", errors="replace")
        for path in sorted(directory.glob("*.md")):
            if path.name == "index.md":
                continue
            if path.name not in index_text:
                report.warnings.append(
                    f"{path.relative_to(root)} is not mentioned in {index.relative_to(root)}"
                )


def audit(root: Path, strict: bool, stale_days: int) -> int:
    report = Report()
    if not root.is_dir():
        print(f"ERROR: repository root does not exist: {root}", file=sys.stderr)
        return 2

    for relative in (
        "AGENTS.md",
        "ARCHITECTURE.md",
        "docs/design-docs/index.md",
        "docs/product-specs/index.md",
    ):
        if not (root / relative).is_file():
            report.errors.append(f"missing required file: {relative}")
    for relative in REQUIRED_DIRS:
        if not (root / relative).is_dir():
            report.errors.append(f"missing required directory: {relative}")

    agents = root / "AGENTS.md"
    if agents.is_file():
        lines = len(agents.read_text(encoding="utf-8", errors="replace").splitlines())
        if lines > 150:
            report.errors.append(f"AGENTS.md is {lines} lines; keep the root map at or below 150")
        elif lines > 120:
            report.warnings.append(f"AGENTS.md is {lines} lines; consider moving detail into docs/")
        else:
            report.info.append(f"AGENTS.md length is {lines} lines")

    paths = markdown_files(root)
    check_links(root, paths, report)
    check_metadata(root, report, stale_days)
    active_plans = check_plan_contracts(root, report)
    check_project_state(root, active_plans, report)
    check_decision_contracts(root, report)
    check_indexes(root, report)

    placeholders = sum(
        len(PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
        for path in paths
    )
    if placeholders:
        report.info.append(f"found {placeholders} TODO/TBD placeholder(s) requiring project knowledge")

    report.print()
    if report.errors or (strict and report.warnings):
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Scaffold or audit resumable repository documentation for AI development."
    )
    sub = result.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create missing documentation files without overwriting")
    init.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    init.add_argument(
        "--with-project-state",
        action="store_true",
        help="Create and link docs/PROJECT_STATE.md for cross-session or complex work",
    )
    check = sub.add_parser(
        "check", help="Audit structure, links, lifecycle, resumability, metadata, and freshness"
    )
    check.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    check.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    check.add_argument("--stale-days", type=int, default=90, help="Warn after this many days")
    return result


def main() -> int:
    args = parser().parse_args()
    root = args.root.expanduser().resolve()
    if args.command == "init":
        return scaffold(root, args.with_project_state)
    return audit(root, args.strict, args.stale_days)


if __name__ == "__main__":
    raise SystemExit(main())
