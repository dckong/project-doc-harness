from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
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
        for relative in doc_harness.REQUIRED_DIRS:
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

## Do not reopen

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
        self.assertIn("has no executable Next action", output)

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


if __name__ == "__main__":
    unittest.main()
