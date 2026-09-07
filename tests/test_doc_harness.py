from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "doc_harness.py"
SPEC = importlib.util.spec_from_file_location("doc_harness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
doc_harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doc_harness)


def metadata(doc_type: str, status: str, extra: str = "") -> str:
    today = dt.date.today().isoformat()
    return (
        "---\n"
        f"doc_type: {doc_type}\n"
        f"status: {status}\n"
        "owner: project-team\n"
        f"last_reviewed: {today}\n"
        f"{extra}"
        "---\n\n"
    )


class HarnessFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        for relative in ("docs/design-docs", "docs/product-specs", "docs/exec-plans/active", "docs/exec-plans/completed", "docs/generated", "docs/references"):
            (root / relative).mkdir(parents=True, exist_ok=True)
        self.write(
            "AGENTS.md",
            """# Repository Guide

## Mission and boundaries

Build a verified example.

## Commands

- Test: `python3 -m unittest`

## Non-negotiable rules

- Keep current state verified.

## Documentation map

- [Project state](docs/PROJECT_STATE.md)
- [Architecture](ARCHITECTURE.md)
- [Design](docs/design-docs/index.md)
- [Product](docs/product-specs/index.md)
- [Active plans](docs/exec-plans/active/index.md)

## Task routing

- Read the owning documents before changing behavior.

## Before finishing

- Run strict documentation checks.
""",
        )
        self.write(
            "ARCHITECTURE.md",
            metadata("architecture", "active")
            + "# Architecture\n\n## Context and scope\n\nCurrent system map.\n",
        )
        self.write(
            "docs/PROJECT_STATE.md",
            metadata("project-state", "active", "verified_commit: abc123\n")
            + """# Project State

## Current phase

Implementing the verified example.

## Now

The architecture is active.

## Next action

Run the focused API regression and record its result.

## Blocked or awaiting

None

## Active work

[Example plan](exec-plans/active/example.md)

## Environment divergence

None

## Last verified

Commit `abc123`, local environment, focused unit command passed today.

## Decisions and review conditions

None
""",
        )
        self.write(
            "docs/design-docs/index.md",
            "# Design documents\n\n- [Example decision](example.md)\n",
        )
        self.write(
            "docs/design-docs/example.md",
            metadata("decision", "implemented")
            + """# Example decision

## Context

The project needs one owner.

## Decision or proposal

Use one owner.

## Alternatives considered

Duplicating ownership was rejected.

## Consequences

The current source remains unique.

## Verification

The focused test pins the behavior.
""",
        )
        self.write("docs/product-specs/index.md", "# Product specifications\n\nNo product specs.\n")
        self.write(
            "docs/exec-plans/active/index.md",
            "# Active execution plans\n\n- [Example](example.md)\n",
        )
        self.write(
            "docs/exec-plans/active/example.md",
            metadata("plan", "active")
            + f"""# Outcome

Ship the verified example.

## Resume snapshot

- Current state: The fixture is implemented.
- Next action: Run the focused API regression and record its result.
- Blocked by: None
- Awaiting: None
- Last verified:
  - commit: abc123
  - environment: local
  - commands: python3 -m unittest
  - date: {dt.date.today().isoformat()}

## Context

Exercise the resumability contract.

## Scope and non-goals

Only the fixture.

## Milestones

- Validate the fixture.

## Progress

- [{dt.date.today().isoformat()}] Fixture created.

## Discoveries

None

## Decision log

See the implemented decision.

## Validation

Run the focused unit command.

## Completion notes

Pending while active.
""",
        )
        self.write("docs/exec-plans/completed/index.md", "# Completed execution plans\n\nNone.\n")
        self.write(
            "docs/exec-plans/tech-debt-tracker.md",
            metadata("tech-debt", "active")
            + "# Technical debt tracker\n\nNo known debt.\n",
        )
        self.write("docs/QUALITY_SCORE.md", "# Documentation quality score\n\nCurrent.\n")
        self.write(
            "docs/RELIABILITY.md",
            metadata("reliability", "active") + "# Reliability\n\nVerified locally.\n",
        )
        self.write(
            "docs/SECURITY.md",
            metadata("security", "active") + "# Security\n\nNo sensitive data.\n",
        )

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class DocHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture = HarnessFixture(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def audit(self, strict: bool = True) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = doc_harness.audit(self.root, strict=strict, stale_days=90)
        return result, output.getvalue()

    def test_complete_resumable_fixture_passes_strict(self) -> None:
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_active_plan_requires_project_state(self) -> None:
        (self.root / "docs/PROJECT_STATE.md").unlink()
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("active execution plans require docs/PROJECT_STATE.md", output)

    def test_active_plan_requires_resume_snapshot(self) -> None:
        path = self.root / "docs/exec-plans/active/example.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("## Resume snapshot", "## Working status"),
            encoding="utf-8",
        )
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("has no Resume snapshot", output)

    def test_active_plan_requires_executable_next_action(self) -> None:
        path = self.root / "docs/exec-plans/active/example.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "- Next action: Run the focused API regression and record its result.",
                "- Next action: None",
            ),
            encoding="utf-8",
        )
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("has a missing or placeholder Next action", output)

    def test_completed_plan_requires_closure_sections(self) -> None:
        active = self.root / "docs/exec-plans/active/example.md"
        completed = self.root / "docs/exec-plans/completed/example.md"
        completed.write_text(
            active.read_text(encoding="utf-8").replace("status: active", "status: completed"),
            encoding="utf-8",
        )
        active.unlink()
        self.fixture.write(
            "docs/exec-plans/active/index.md",
            "# Active execution plans\n\nNo active plans.\n",
        )
        self.fixture.write(
            "docs/exec-plans/completed/index.md",
            "# Completed execution plans\n\n- [Example](example.md)\n",
        )
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("Completion notes is missing heading: Durable decisions promoted", output)

    def test_plan_directory_and_status_must_agree(self) -> None:
        path = self.root / "docs/exec-plans/active/example.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("status: active", "status: completed"),
            encoding="utf-8",
        )
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("is in active/ but status is completed", output)

    def test_current_owner_tbd_fails_strict_only(self) -> None:
        path = self.root / "docs/PROJECT_STATE.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("owner: project-team", "owner: TBD"),
            encoding="utf-8",
        )
        strict_result, strict_output = self.audit(strict=True)
        normal_result, normal_output = self.audit(strict=False)
        self.assertEqual(strict_result, 1, strict_output)
        self.assertEqual(normal_result, 0, normal_output)
        self.assertIn("owner is TBD", strict_output)

    def test_superseded_document_requires_existing_replacement(self) -> None:
        path = self.root / "docs/design-docs/example.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("status: implemented", "status: superseded"),
            encoding="utf-8",
        )
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("has no superseded_by target", output)

    def test_scaffold_with_project_state_links_entry_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                result = doc_harness.scaffold(root, with_project_state=True)
            self.assertEqual(result, 0)
            self.assertTrue((root / "docs/PROJECT_STATE.md").is_file())
            self.assertIn(
                "docs/PROJECT_STATE.md",
                (root / "AGENTS.md").read_text(encoding="utf-8"),
            )


class OptionalLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def audit(self) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = doc_harness.audit(self.root, True, 90)
        return result, output.getvalue()

    def scaffold(self, **kwargs) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            doc_harness.scaffold(self.root, **kwargs)

    def configure(self, artifacts: dict[str, str]) -> None:
        (self.root / "doc-harness.json").write_text(json.dumps({"artifacts": artifacts}))

    def test_default_scaffold_creates_only_entry_and_passes_structure(self) -> None:
        self.scaffold()
        self.assertEqual({p.name for p in self.root.iterdir()}, {"AGENTS.md"})
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.assertNotIn("docs/", (self.root / "AGENTS.md").read_text())

    def test_entry_is_still_required(self) -> None:
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("missing required file: AGENTS.md", output)

    def test_explicit_selection_persists_and_missing_file_fails(self) -> None:
        self.scaffold(selected=["architecture"])
        self.assertEqual({p.name for p in self.root.iterdir()}, {"AGENTS.md", "ARCHITECTURE.md", "doc-harness.json"})
        (self.root / "ARCHITECTURE.md").unlink()
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("missing required file: ARCHITECTURE.md", output)
        self.assertNotIn("product-specs", output)

    def test_existing_optional_document_is_checked_without_config(self) -> None:
        self.scaffold()
        (self.root / "ARCHITECTURE.md").write_text("# Missing metadata\n")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("has no YAML frontmatter", output)
        self.assertNotIn("product-specs", output)

    def test_custom_paths_generate_valid_links_without_default_duplicates(self) -> None:
        self.configure({"architecture": "handbook/system.md", "design-docs": "handbook/decisions"})
        self.scaffold()
        architecture = self.root / "handbook/system.md"
        self.assertTrue(architecture.is_file())
        self.assertTrue((self.root / "handbook/decisions/index.md").is_file())
        self.assertFalse((self.root / "docs").exists())
        self.assertFalse((self.root / "ARCHITECTURE.md").exists())
        self.assertIn("](decisions/index.md)", architecture.read_text())
        self.assertIn("](handbook/system.md)", (self.root / "AGENTS.md").read_text())
        architecture.write_text(metadata("architecture", "active") + "# System\n")
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_custom_plan_and_state_contracts_remain_enforced(self) -> None:
        self.configure({"plans": "handbook/work", "project-state": "handbook/now.md"})
        self.scaffold()
        plan = self.root / "handbook/work/active/task.md"
        plan.write_text(metadata("plan", "active") + "# Task\n")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("handbook/work/active/task.md is active work but has no Resume snapshot", output)
        (self.root / "handbook/now.md").unlink()
        result, output = self.audit()
        self.assertIn("active execution plans require handbook/now.md", output)
        self.assertFalse((self.root / "docs").exists())

    def test_config_cannot_hide_state_requirement_for_active_plans(self) -> None:
        self.configure({"plans": "work-items"})
        self.scaffold()
        (self.root / "work-items/active/task.md").write_text(metadata("plan", "active") + "# Task\n")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("active execution plans require docs/PROJECT_STATE.md", output)

    def test_init_is_idempotent_and_preserves_existing_content(self) -> None:
        self.scaffold(selected=["architecture"])
        path = self.root / "ARCHITECTURE.md"
        path.write_text("# Existing user content\n")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.scaffold(selected=["architecture"])
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_invalid_configuration_fails_before_creating_files(self) -> None:
        for artifacts in ({"unknown": "docs/x"}, {"architecture": "../outside.md"}, {"architecture": "AGENTS.md"}, {"design-docs": "handbook", "product-specs": "handbook/specs"}):
            with self.subTest(artifacts=artifacts):
                self.configure(artifacts)
                result, output = self.audit()
                self.assertEqual(result, 2, output)
                with self.assertRaises(ValueError):
                    self.scaffold()
                self.assertFalse((self.root / "AGENTS.md").exists())

    def test_debt_tracker_alone_does_not_require_plan_directories(self) -> None:
        self.scaffold()
        debt = self.root / "docs/exec-plans/tech-debt-tracker.md"
        debt.parent.mkdir(parents=True)
        debt.write_text(metadata("tech-debt", "active") + "# Debt\n\nNo known debt.\n")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.scaffold()
        self.assertFalse((debt.parent / "active").exists())

    def test_complete_fixture_passes_after_custom_path_migration(self) -> None:
        HarnessFixture(self.root)
        artifacts = dict(doc_harness.ARTIFACT_PATHS)
        artifacts.pop("operations")  # Not used by this fixture.
        artifacts.update({"architecture": "handbook/system.md", "project-state": "handbook/now.md", "design-docs": "handbook/decisions", "product-specs": "handbook/specs", "plans": "handbook/tasks", "tech-debt": "handbook/debt.md"})
        layout = doc_harness.Layout(self.root, artifacts)
        old_files = [(path, path.read_text()) for path in self.root.rglob("*.md")]
        for path, content in old_files:
            relative = path.relative_to(self.root).as_posix()
            dest = layout.path(relative)
            for target in doc_harness.LINK_RE.findall(content):
                canonical = (path.parent / target).resolve().relative_to(self.root.resolve()).as_posix()
                mapped = os.path.relpath(layout.path(canonical), dest.parent).replace(os.sep, "/")
                content = content.replace("](" + target + ")", "](" + mapped + ")")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
            if dest != path:
                path.unlink()
        self.configure(artifacts)
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_cli_selection_is_shared_with_check(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "init", "--root", str(self.root), "--with", "references"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.root / "docs/references").rmdir()
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "check", "--root", str(self.root), "--strict"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("missing required directory: docs/references", result.stdout)


class LifecycleAndRecoveryTests(unittest.TestCase):
    setUp = DocHarnessTests.setUp
    tearDown = DocHarnessTests.tearDown
    audit = DocHarnessTests.audit
    # The inherited fixture keeps all other contracts valid so failures here
    # reflect lifecycle/recovery behavior rather than absent infrastructure.
    def change(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        path.write_text(path.read_text().replace(old, new))

    def extra_document(self, area: str, name: str, body: str) -> None:
        self.fixture.write(f"{area}/{name}.md", body)
        index = self.root / area / "index.md"
        if index.exists():
            index.write_text(index.read_text() + f"\n- [{name}]({name}.md)\n")

    def old_metadata(self, doc_type: str, status: str, extra: str = "") -> str:
        old = (dt.date.today() - dt.timedelta(days=120)).isoformat()
        return metadata(doc_type, status, extra).replace(dt.date.today().isoformat(), old)

    def test_historical_records_do_not_expire_by_age(self) -> None:
        records = [
            ("decision", "rejected", "", "docs/design-docs"),
            ("decision", "superseded", "superseded_by: docs/design-docs/example.md\n", "docs/design-docs"),
            ("operations", "deprecated", "deprecation_reason: Service permanently retired\n", "docs/operations"),
            ("plan", "completed", "", "docs/exec-plans/completed"),
            ("plan", "cancelled", "", "docs/exec-plans/completed"),
        ]
        for kind, status, extra, area in records:
            body = self.old_metadata(kind, status, extra) + "# Historical record\n\n"
            if kind == "decision":
                body += "## Alternatives considered\n\nRecorded at decision time.\n"
            if kind == "plan":
                body += "## Completion notes\n\n" + "".join(f"### {heading}\n\nNone\n\n" for heading in doc_harness.COMPLETION_HEADINGS)
            self.extra_document(area, status, body)
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.assertNotIn("days old", output)

    def test_historical_dates_are_still_validated(self) -> None:
        self.extra_document("docs/design-docs", "bad-date", metadata("decision", "rejected").replace(dt.date.today().isoformat(), "not-a-date") + "# Rejection\n\n## Alternatives considered\n\nNone\n")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("invalid last_reviewed", output)

    def test_current_document_stays_subject_to_age_and_override(self) -> None:
        self.fixture.write("ARCHITECTURE.md", self.old_metadata("architecture", "active") + "# Architecture\n")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("last_reviewed is 120 days old", output)
        self.change("ARCHITECTURE.md", "owner: project-team", "owner: project-team\nreview_after_days: 180")
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_progress_timestamp_does_not_require_refreshing_review_date(self) -> None:
        today = dt.date.today().isoformat()
        old = (dt.date.today() - dt.timedelta(days=120)).isoformat()
        self.change("docs/exec-plans/active/example.md", f"last_reviewed: {today}", f"last_reviewed: {old}\nupdated_at: {today}")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/exec-plans/active/example.md", f"updated_at: {today}", f"updated_at: {old}")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("updated_at is 120 days old", output)

    def test_observation_freshness_is_independent_of_review_date(self) -> None:
        old = (dt.date.today() - dt.timedelta(days=4)).isoformat()
        self.fixture.write("docs/operations/live.md", metadata("operations", "active", f"observed_at: {old}T12:00:00Z\nobservation_max_age_days: 2\n") + "# Observation\n")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("observed_at is 4 days old", output)
        self.change("docs/operations/live.md", old, dt.date.today().isoformat())
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_invalid_freshness_limit_is_not_an_escape_hatch(self) -> None:
        self.change("ARCHITECTURE.md", "owner: project-team", "owner: project-team\nreview_after_days: 0")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("review_after_days must be a positive integer", output)

    def test_accepted_decision_is_valid_but_requires_current_owner(self) -> None:
        self.change("docs/design-docs/example.md", "status: implemented", "status: accepted")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/design-docs/example.md", "owner: project-team", "owner: TBD")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("owner is TBD", output)

    def test_unknown_owner_is_not_a_real_current_owner(self) -> None:
        self.change("docs/PROJECT_STATE.md", "owner: project-team", "owner: Unknown")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("owner is Unknown", output)

    def test_deprecated_requires_reason_but_not_replacement(self) -> None:
        self.change("docs/RELIABILITY.md", "status: active", "status: deprecated")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("has no deprecation_reason", output)
        self.change("docs/RELIABILITY.md", "status: deprecated", "status: deprecated\ndeprecation_reason: Runtime service retired")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/RELIABILITY.md", "status: deprecated", "status: deprecated\nsuperseded_by: docs/missing.md")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("missing superseded_by target", output)

    def test_replacement_cannot_be_self_or_directory(self) -> None:
        path = "docs/design-docs/example.md"
        original = (self.root / path).read_text()
        for replacement in (path, "docs/design-docs"):
            with self.subTest(replacement=replacement):
                self.fixture.write(path, original.replace("status: implemented", "status: superseded\nsuperseded_by: " + replacement))
                result, output = self.audit()
                self.assertEqual(result, 1, output)

    def remove_active_plan(self) -> None:
        (self.root / "docs/exec-plans/active/example.md").unlink()
        self.fixture.write("docs/exec-plans/active/index.md", "# Active plans\n\nNone\n")
        self.change("docs/PROJECT_STATE.md", "[Example plan](exec-plans/active/example.md)", "None")

    def test_idle_state_accepts_no_next_action_with_resume_condition(self) -> None:
        self.remove_active_plan()
        self.change("docs/PROJECT_STATE.md", "status: active", "status: active\nwork_status: idle")
        self.change("docs/PROJECT_STATE.md", "Run the focused API regression and record its result.", "None")
        self.change("docs/PROJECT_STATE.md", "## Decisions and review conditions", "## Resume when\n\nA new task with explicit scope is assigned.\n\n## Decisions and review conditions")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/PROJECT_STATE.md", "A new task with explicit scope is assigned.", "Unknown")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("idle state needs a Resume when condition", output)

    def test_idle_state_cannot_hide_active_plans(self) -> None:
        self.change("docs/PROJECT_STATE.md", "status: active", "status: active\nwork_status: idle")
        self.change("docs/PROJECT_STATE.md", "Run the focused API regression and record its result.", "None")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("cannot be idle while active or blocked plans exist", output)

    def test_waiting_state_needs_object_and_resume_condition(self) -> None:
        self.change("docs/PROJECT_STATE.md", "status: active", "status: active\nwork_status: waiting")
        self.change("docs/PROJECT_STATE.md", "## Blocked or awaiting\n\nNone", "## Blocked or awaiting\n\nRelease owner approval")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("waiting state needs a Resume when condition", output)
        self.change("docs/PROJECT_STATE.md", "## Decisions and review conditions", "## Resume when\n\nRelease owner approves the change.\n\n## Decisions and review conditions")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/PROJECT_STATE.md", "Release owner approval", "None")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("waiting state needs a blocker or waiting object", output)

    def test_blocked_plan_needs_unblocking_information(self) -> None:
        path = "docs/exec-plans/active/example.md"
        self.change(path, "status: active", "status: blocked")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("blocked plan needs a Resume when condition", output)
        self.change(path, "- Awaiting: None", "- Awaiting: Maintainer approval\n- Resume when: Maintainer approves the documented scope")
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_unknown_facts_are_explicit_without_becoming_actions(self) -> None:
        self.change("docs/PROJECT_STATE.md", "verified_commit: abc123", "verified_commit: Unknown")
        self.change("docs/PROJECT_STATE.md", "## Environment divergence\n\nNone", "## Environment divergence\n\nUnknown — production has not been inspected.")
        self.change("docs/PROJECT_STATE.md", "Commit `abc123`, local environment, focused unit command passed today.", "Unknown — no environment verification recorded.")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.assertIn("verified_commit is Unknown; no verified revision claimed", output)
        self.change("docs/PROJECT_STATE.md", "Run the focused API regression and record its result.", "Unknown")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("placeholder Next action", output)

    def test_project_can_route_to_plan_without_copying_task_state(self) -> None:
        self.change("docs/PROJECT_STATE.md", "Run the focused API regression and record its result.", "Priority: [Example task snapshot](exec-plans/active/example.md#resume-snapshot).")
        self.change("docs/PROJECT_STATE.md", "Commit `abc123`, local environment, focused unit command passed today.", "See [task validation](exec-plans/active/example.md#validation).")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/exec-plans/active/example.md", "Run the focused API regression and record its result.", "Verify the deployment manifest against the accepted decision.")
        result, output = self.audit()
        self.assertEqual(result, 0, output)

    def test_empty_next_action_does_not_consume_next_bullet(self) -> None:
        self.change("docs/exec-plans/active/example.md", "- Next action: Run the focused API regression and record its result.", "- Next action:")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("placeholder Next action", output)

    def test_init_preserves_existing_entry_and_reports_missing_link(self) -> None:
        for original in ("# Existing\n\n## Documentation map\n\nUser text.\n", "# Existing\n\n## 项目导航\n\n用户内容。\n"):
            with self.subTest(original=original), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "AGENTS.md"
                path.write_text(original)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    doc_harness.scaffold(root, with_project_state=True)
                self.assertEqual(path.read_text(), original)
                self.assertIn("ACTION_REQUIRED: add a link from AGENTS.md", output.getvalue())
                report = doc_harness.Report()
                doc_harness.check_project_state(root, [], report, doc_harness.Layout.load(root))
                self.assertIn("AGENTS.md does not link docs/PROJECT_STATE.md", report.errors)

    def test_legacy_decision_heading_remains_compatible(self) -> None:
        self.change("docs/PROJECT_STATE.md", "## Decisions and review conditions", "## Do not reopen")
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.change("docs/PROJECT_STATE.md", "## Do not reopen", "## Unrelated notes")
        result, output = self.audit()
        self.assertEqual(result, 1)
        self.assertIn("missing heading: Decisions and review conditions", output)

    def test_report_distinguishes_structure_from_content_review(self) -> None:
        result, output = self.audit()
        self.assertEqual(result, 0, output)
        self.assertIn("Mechanical checks only", output)
        self.assertIn("content review is required", output)


if __name__ == "__main__":
    unittest.main()
