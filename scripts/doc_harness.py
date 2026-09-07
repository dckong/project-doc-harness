#!/usr/bin/env python3
"""Scaffold and audit an agent-readable, resumable project documentation harness."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


CONFIG_NAME = "doc-harness.json"
# File roles and directory roles share one selection and path mapping.
ARTIFACT_PATHS = {
    "architecture": "ARCHITECTURE.md",
    "project-state": "docs/PROJECT_STATE.md",
    "design-docs": "docs/design-docs",
    "product-specs": "docs/product-specs",
    "plans": "docs/exec-plans",
    "tech-debt": "docs/exec-plans/tech-debt-tracker.md",
    "operations": "docs/operations",
    "generated": "docs/generated",
    "references": "docs/references",
    "quality": "docs/QUALITY_SCORE.md",
    "reliability": "docs/RELIABILITY.md",
    "security": "docs/SECURITY.md",
}
DIRECTORY_ROLES = {"design-docs", "product-specs", "plans", "operations", "generated", "references"}


class Layout:
    def __init__(self, root: Path, artifacts: dict[str, str]) -> None:
        self.root = root
        self.artifacts = dict(artifacts)
        for role, relative in self.artifacts.items():
            if role not in ARTIFACT_PATHS:
                raise ValueError(f"unknown artifact role: {role}")
            if not isinstance(relative, str) or not relative.strip():
                raise ValueError(f"artifact {role} requires a nonempty repository-relative path")
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts or path.as_posix() == ".":
                raise ValueError(f"artifact {role} must stay inside the repository: {relative}")
            if not (root / path).resolve().is_relative_to(root.resolve()):
                raise ValueError(f"artifact {role} resolves outside the repository: {relative}")
            self.artifacts[role] = path.as_posix()
        values = list(self.artifacts.values())
        if len(values) != len(set(values)) or any(Path(value).parts[0] in {"AGENTS.md", CONFIG_NAME} for value in values):
            raise ValueError("artifact paths must be distinct and must not replace AGENTS.md or the config")
        for parent_role, parent in self.artifacts.items():
            for child_role, child in self.artifacts.items():
                if child.startswith(parent + "/"):
                    # Preserve intentional nesting (plans + debt), but reject
                    # overlaps that would apply unrelated directory contracts.
                    if parent_role not in DIRECTORY_ROLES or not ARTIFACT_PATHS[child_role].startswith(ARTIFACT_PATHS[parent_role] + "/"):
                        raise ValueError(f"overlapping artifact paths: {parent_role} and {child_role}")

    @classmethod
    def load(cls, root: Path) -> "Layout":
        config = root / CONFIG_NAME
        if config.exists():
            data = json.loads(config.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or set(data) != {"artifacts"} or not isinstance(data["artifacts"], dict):
                raise ValueError(f"{CONFIG_NAME} must contain an artifacts object")
            return cls(root, data["artifacts"])
        # Without a declaration, check only optional roles already present.
        artifacts = {role: path for role, path in ARTIFACT_PATHS.items() if (root / path).exists()}
        if "plans" in artifacts and not any((root / artifacts["plans"] / area).exists() for area in ("active", "completed")):
            artifacts.pop("plans")  # A debt tracker alone does not adopt plans.
        return cls(root, artifacts)

    def role_for(self, canonical: str) -> str | None:
        for role, base in sorted(ARTIFACT_PATHS.items(), key=lambda item: -len(item[1])):
            if canonical == base or (role in DIRECTORY_ROLES and canonical.startswith(base + "/")):
                return role
        return None

    def includes(self, canonical: str) -> bool:
        return canonical == "AGENTS.md" or self.role_for(canonical) in self.artifacts

    def relative(self, canonical: str) -> str:
        role = self.role_for(canonical)
        if role in self.artifacts:
            return self.artifacts[role] + canonical[len(ARTIFACT_PATHS[role]):]
        return canonical

    def path(self, canonical: str) -> Path:
        return self.root / self.relative(canonical)

    def files(self) -> list[str]:
        result = ["AGENTS.md"]
        for role, canonical in ARTIFACT_PATHS.items():
            if role not in self.artifacts:
                continue
            if role == "plans":
                result.extend([canonical + "/active/index.md", canonical + "/completed/index.md"])
            elif role in {"design-docs", "product-specs"}:
                result.append(canonical + "/index.md")
            elif role not in DIRECTORY_ROLES:
                result.append(canonical)
        return result

    def directories(self) -> list[str]:
        return [base for role, base in ARTIFACT_PATHS.items() if role in self.artifacts and role in DIRECTORY_ROLES]


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
work_status: active
owner: TBD
last_reviewed: TBD
verified_commit: Unknown
---

# Project State

## Current phase

TODO

## Now

TODO: Summarize current facts and link their authoritative documents.

## Next action

TODO: Link the priority plan snapshot, or state the next action if no plan exists. For waiting/idle, set work_status and add Resume when.

## Blocked or awaiting

Unknown — inventory blockers and dependencies.

## Active work

Unknown — inventory active plans.

## Environment divergence

Unknown — environments have not been compared.

## Last verified

Unknown — no verification recorded. Link task/environment evidence when available; do not copy every plan result.

## Decisions and review conditions

Unknown — identify applicable decisions, their assumptions and review conditions.
"""

DOC_TYPE_STATUSES = {
    "project-state": {"active"},
    "architecture": {"draft", "active", "deprecated"},
    "product-spec": {"draft", "active", "deprecated"},
    "operations": {"draft", "active", "deprecated"},
    "reliability": {"draft", "active", "deprecated"},
    "security": {"draft", "active", "deprecated"},
    "decision": {"proposed", "accepted", "implemented", "rejected", "superseded"},
    "plan": {"active", "blocked", "completed", "cancelled"},
    "tech-debt": {"active", "deprecated"},
}
CURRENT_OWNER_STATUSES = {"active", "blocked", "accepted", "implemented"}
HISTORICAL_STATUSES = {"completed", "cancelled", "rejected", "superseded", "deprecated"}
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
    "Decisions and review conditions",
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


def scaffold(root: Path, with_project_state: bool = False, selected: list[str] | None = None) -> int:
    layout = Layout.load(root)
    requested = list(selected or [])
    if with_project_state:
        requested.append("project-state")
    for role in requested:
        layout.artifacts.setdefault(role, ARTIFACT_PATHS[role])
    layout = Layout(root, layout.artifacts)
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    # Explicit selection persists so later checks can detect a deleted artifact.
    if requested:
        config = root / CONFIG_NAME
        content = json.dumps({"artifacts": layout.artifacts}, indent=2, ensure_ascii=False) + "\n"
        if not config.exists() or config.read_text(encoding="utf-8") != content:
            config.write_text(content, encoding="utf-8")
            created.append(config)
    for canonical in layout.directories():
        path = layout.path(canonical)
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
    templates = dict(TEMPLATES)
    templates["docs/PROJECT_STATE.md"] = PROJECT_STATE_TEMPLATE
    templates["docs/design-docs/index.md"] = "# Design documents\n\nNo design decisions recorded.\n"
    if "project-state" in layout.artifacts:
        templates["AGENTS.md"] = AGENTS_TEMPLATE.replace(
            "## Documentation map\n\n", "## Documentation map\n\n" + PROJECT_STATE_LINK
        )
    for canonical in layout.files():
        path = layout.path(canonical)
        if path.exists():
            continue
        # Rewrite template links relative to the selected destination, omitting
        # navigation entries for roles the project has not adopted.
        lines = []
        for line in templates[canonical].splitlines(keepends=True):
            targets = LINK_RE.findall(line)
            omit = False
            for target in targets:
                source_target = (Path(canonical).parent / target).as_posix()
                if not layout.includes(source_target):
                    omit = True
                    break
                mapped = os.path.relpath(layout.path(source_target), path.parent).replace(os.sep, "/")
                line = line.replace("](" + target + ")", "](" + mapped + ")")
            if not omit:
                lines.append(line)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(lines), encoding="utf-8")
        created.append(path)
    # Existing Markdown remains unchanged. Surface the required follow-up even
    # when its author uses a different heading or navigation format.
    if "project-state" in layout.artifacts:
        agents = root / "AGENTS.md"
        target = layout.relative("docs/PROJECT_STATE.md")
        if target not in agents.read_text(encoding="utf-8"):
            print(f"ACTION_REQUIRED: add a link from AGENTS.md to {target}; existing Markdown was preserved")
    for path in created:
        print(f"CREATED_OR_UPDATED: {path.relative_to(root)}")
    if not created:
        print("No changes: all selected scaffold paths already exist.")
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


def metadata_paths(root: Path, layout: Layout) -> list[Path]:
    paths: set[Path] = set()
    for relative in (
        "ARCHITECTURE.md",
        "docs/PROJECT_STATE.md",
        "docs/RELIABILITY.md",
        "docs/SECURITY.md",
        "docs/exec-plans/tech-debt-tracker.md",
    ):
        path = layout.path(relative)
        if layout.includes(relative) and path.is_file():
            paths.add(path)
    for relative in (
        "docs/design-docs",
        "docs/product-specs",
        "docs/exec-plans/active",
        "docs/exec-plans/completed",
        "docs/operations",
    ):
        directory = layout.path(relative)
        if not layout.includes(relative) or not directory.is_dir():
            continue
        for path in directory.rglob("*.md"):
            if path.name.lower() not in {"index.md", "readme.md", "agents.md"}:
                paths.add(path)
    return sorted(paths)


def expected_doc_type(root: Path, path: Path, layout: Layout) -> str | None:
    relative = path.relative_to(root).as_posix()
    for role, mapped in sorted(layout.artifacts.items(), key=lambda item: -len(item[1])):
        if relative == mapped or (role in DIRECTORY_ROLES and relative.startswith(mapped + "/")):
            relative = ARTIFACT_PATHS[role] + relative[len(mapped):]
            break
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


def check_date(
    path: Path, root: Path, value: str, stale_days: int | None, report: Report,
    field: str = "last_reviewed",
) -> None:
    display = path.relative_to(root)
    if value in ("", "TBD", "TODO"):
        report.warnings.append(f"{display} has no verified {field} date")
        return
    if value == "Unknown":
        report.info.append(f"{display} {field} is Unknown; freshness has not been established")
        return
    try:
        if field == "observed_at" and "T" in value:
            date = dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        else:
            date = dt.date.fromisoformat(value)
    except ValueError:
        report.warnings.append(f"{display} has invalid {field} date: {value}")
        return
    age = (dt.date.today() - date).days
    if age < 0:
        report.warnings.append(f"{display} has future {field} date: {value}")
    elif stale_days is not None and age > stale_days:
        report.warnings.append(f"{display} {field} is {age} days old (limit {stale_days})")


def freshness_limit(data: dict[str, str], field: str, default: int, display: Path, report: Report) -> int:
    if field not in data:
        return default
    try:
        value = int(data[field])
        if value <= 0:
            raise ValueError
    except ValueError:
        report.errors.append(f"{display} {field} must be a positive integer")
        return default
    return value


def check_freshness(root: Path, path: Path, data: dict[str, str], report: Report, stale_days: int) -> None:
    historical = data.get("status") in HISTORICAL_STATUSES
    display = path.relative_to(root)
    limit = freshness_limit(data, "review_after_days", stale_days, display, report)
    has_progress_date = data.get("doc_type") in {"plan", "project-state"} and "updated_at" in data
    # Archive dates retain their evidence meaning. Validate their format without
    # requiring periodic edits just to keep historical records under an age limit.
    check_date(path, root, data.get("last_reviewed", ""), None if historical or has_progress_date else limit, report)
    if has_progress_date:
        check_date(path, root, data["updated_at"], None if historical else limit, report, "updated_at")
    if "observed_at" in data or "observation_max_age_days" in data:
        observation_limit = freshness_limit(data, "observation_max_age_days", stale_days, display, report)
        check_date(path, root, data.get("observed_at", ""), None if historical else observation_limit, report, "observed_at")


def check_replacement(root: Path, path: Path, data: dict[str, str], report: Report) -> None:
    if data.get("status") not in {"deprecated", "superseded"}:
        return
    replacement = data.get("superseded_by", "")
    display = path.relative_to(root)
    if data.get("status") == "deprecated":
        reason = data.get("deprecation_reason", "")
        if is_placeholder_action(reason):
            report.errors.append(f"{display} is deprecated but has no deprecation_reason")
        if not replacement:
            return
    if not replacement or replacement in {"TBD", "None", "Unknown", "Not applicable"}:
        report.errors.append(f"{display} is {data.get('status')} but has no superseded_by target")
        return
    target = (root / replacement).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        report.errors.append(f"{display} has superseded_by outside repository: {replacement}")
        return
    if target == path.resolve():
        report.errors.append(f"{display} cannot supersede itself")
    elif not target.is_file():
        report.errors.append(f"{display} has missing superseded_by target: {replacement}")


def check_metadata(root: Path, report: Report, stale_days: int, layout: Layout) -> None:
    for path in metadata_paths(root, layout):
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
        expected = expected_doc_type(root, path, layout)
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
        if status in CURRENT_OWNER_STATUSES and owner.strip().casefold() in {"", "tbd", "todo", "unknown", "none", "not applicable"}:
            report.warnings.append(f"{display} is current work or authority but owner is {owner or 'missing'}")
        check_freshness(root, path, data, report, stale_days)
        if doc_type == "project-state":
            commit = data.get("verified_commit", "")
            if commit == "Unknown":
                report.info.append(f"{display} verified_commit is Unknown; no verified revision claimed")
            elif is_placeholder_action(commit):
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
    match = re.search(rf"^[ \t]*-[ \t]*{re.escape(label)}[ \t]*:[ \t]*(.*?)[ \t]*$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"^[ \t]*-?[ \t]*{re.escape(label)}[ \t]*:[ \t]*(.*?)[ \t]*$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def is_placeholder_action(value: str) -> bool:
    normalized = value.strip().casefold()
    return (
        not normalized
        or normalized in {"none", "todo", "tbd", "n/a", "unknown", "not applicable"}
        or "继续开发" in value
        or "continue development" in normalized
        or bool(PLACEHOLDER_RE.search(value))
    )


def plan_files(root: Path, area: str, layout: Layout) -> list[Path]:
    directory = layout.path(area)
    if not layout.includes(area) or not directory.is_dir():
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
        report.errors.append(f"{display} Resume snapshot has a missing or placeholder Next action")
    data = frontmatter(text) or {}
    if data.get("status") == "blocked":
        resume = bullet_value(snapshot, "Resume when") or ""
        blockers = [bullet_value(snapshot, label) or "" for label in ("Blocked by", "Awaiting")]
        if is_placeholder_action(resume):
            report.errors.append(f"{display} blocked plan needs a Resume when condition")
        if all(is_placeholder_action(value) for value in blockers):
            report.errors.append(f"{display} blocked plan needs a blocker or waiting object")
    for label in VERIFICATION_LABELS:
        value = field_value(snapshot, label)
        if value is None:
            report.errors.append(f"{display} Resume snapshot Last verified is missing: {label}")
        elif value in ("", "TBD", "TODO"):
            report.warnings.append(f"{display} Resume snapshot Last verified has no value for: {label}")
        elif value == "Unknown":
            report.info.append(f"{display} Resume snapshot {label} is Unknown; evidence is incomplete")


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


def check_plan_contracts(root: Path, report: Report, layout: Layout) -> list[Path]:
    active = plan_files(root, "docs/exec-plans/active", layout)
    completed = plan_files(root, "docs/exec-plans/completed", layout)
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


def check_project_state(root: Path, active_plans: list[Path], report: Report, layout: Layout) -> None:
    path = layout.path("docs/PROJECT_STATE.md")
    display = layout.relative("docs/PROJECT_STATE.md")
    selected = "project-state" in layout.artifacts
    if active_plans and (not selected or not path.is_file()):
        report.errors.append(f"active execution plans require {display} (select the project-state role)")
        return
    if not selected or not path.is_file():
        return

    agents = root / "AGENTS.md"
    if agents.is_file() and display not in agents.read_text(
        encoding="utf-8", errors="replace"
    ):
        report.errors.append(f"AGENTS.md does not link {display}")

    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text.splitlines()) > 100:
        report.warnings.append(
            f"{display} is {len(text.splitlines())} lines; keep the state capsule at or below 100"
        )
    for heading in PROJECT_STATE_HEADINGS:
        content = section_text(text, heading)
        if content is None and heading == "Decisions and review conditions":
            content = section_text(text, "Do not reopen")  # Legacy title; retain existing documents.
        if content is None:
            report.errors.append(f"{display} is missing heading: {heading}")
        elif not content.strip():
            report.errors.append(f"{display} has empty section: {heading}")
    data = frontmatter(text) or {}
    work_status = data.get("work_status", "active")
    if work_status not in {"active", "waiting", "idle"}:
        report.errors.append(f"{display} has invalid work_status: {work_status}")
    next_action = section_text(text, "Next action")
    if work_status == "idle":
        if active_plans:
            report.errors.append(f"{display} cannot be idle while active or blocked plans exist")
        if (next_action or "").strip().casefold() != "none":
            report.errors.append(f"{display} idle state must record Next action: None")
        if (section_text(text, "Active work") or "").strip().casefold() != "none":
            report.errors.append(f"{display} idle state must record Active work: None")
    elif next_action is not None and is_placeholder_action(next_action):
        report.errors.append(f"{display} has a missing or placeholder Next action")
    if work_status in {"waiting", "idle"}:
        if is_placeholder_action(section_text(text, "Resume when") or ""):
            report.errors.append(f"{display} {work_status} state needs a Resume when condition")
    if work_status == "waiting" and is_placeholder_action(section_text(text, "Blocked or awaiting") or ""):
        report.errors.append(f"{display} waiting state needs a blocker or waiting object")


def check_decision_contracts(root: Path, report: Report, layout: Layout) -> None:
    for path in metadata_paths(root, layout):
        text = path.read_text(encoding="utf-8", errors="replace")
        data = frontmatter(text) or {}
        if data.get("doc_type") != "decision":
            continue
        if section_text(text, "Alternatives considered") is None:
            report.warnings.append(f"{path.relative_to(root)} decision has no Alternatives considered section")


def check_indexes(root: Path, report: Report, layout: Layout) -> None:
    for area in (
        "docs/design-docs",
        "docs/product-specs",
        "docs/exec-plans/active",
        "docs/exec-plans/completed",
    ):
        if not layout.includes(area):
            continue
        directory = layout.path(area)
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

    try:
        layout = Layout.load(root)
    except (ValueError, OSError) as exc:
        print(f"ERROR: invalid {CONFIG_NAME}: {exc}", file=sys.stderr)
        return 2
    for canonical in layout.files():
        if not layout.path(canonical).is_file():
            report.errors.append(f"missing required file: {layout.relative(canonical)}")
    for canonical in layout.directories():
        if not layout.path(canonical).is_dir():
            report.errors.append(f"missing required directory: {layout.relative(canonical)}")

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
    check_metadata(root, report, stale_days, layout)
    active_plans = check_plan_contracts(root, report, layout)
    check_project_state(root, active_plans, report, layout)
    check_decision_contracts(root, report, layout)
    check_indexes(root, report, layout)

    placeholders = sum(
        len(PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
        for path in paths
    )
    if placeholders:
        report.info.append(f"found {placeholders} TODO/TBD placeholder(s) requiring project knowledge")

    report.info.append("Mechanical checks only: supported local file-link targets, index filename mentions, metadata, dates, states and required sections. Not verified: anchors, evidence truth, action feasibility, freshness events or semantic agreement; content review is required.")
    report.print()
    if report.errors or (strict and report.warnings):
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Scaffold or audit resumable repository documentation for AI development."
    )
    sub = result.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create selected missing Markdown; preserve existing Markdown and persist explicit artifact selection")
    init.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    init.add_argument("--with", dest="selected", action="append", choices=sorted(ARTIFACT_PATHS), help="Adopt an optional role at its default path; repeatable and saved in doc-harness.json")
    init.add_argument(
        "--with-project-state",
        action="store_true",
        help="Select project-state; link it in a new AGENTS.md, or report a required link for an existing entry",
    )
    check = sub.add_parser(
        "check", help="Audit structure, links, lifecycle, resumability, metadata, and freshness"
    )
    check.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    check.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    check.add_argument("--stale-days", type=int, default=90, help="Default age limit for current documents/observations; historical records are exempt")
    return result


def main() -> int:
    args = parser().parse_args()
    root = args.root.expanduser().resolve()
    if args.command == "init":
        try:
            return scaffold(root, args.with_project_state, args.selected)
        except (ValueError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    return audit(root, args.strict, args.stale_days)


if __name__ == "__main__":
    raise SystemExit(main())
