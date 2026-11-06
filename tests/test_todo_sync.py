from __future__ import annotations

import copy
import io
import json
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import pytest

from scripts import todo_sync as sync


class FakeGitHub:
    def __init__(self):
        self.issues = []
        self.items = []
        self.writes = []
        self.fail_add = False
        self.timeout_create = False
        self.fail_inventory = False

    def inventory(self, config):
        if self.fail_inventory:
            raise sync.SyncError("permission/read failure")
        return "fixture", copy.deepcopy(self.issues), copy.deepcopy(self.items)

    def issue(self, identifier):
        return copy.deepcopy(next(item for item in self.issues if item["id"] == identifier))

    def item(self, identifier):
        return copy.deepcopy(next(item for item in self.items if item["id"] == identifier))

    def create_issue(self, repository, title, body):
        number = len(self.issues) + 1
        issue = {
            "id": f"I{number}",
            "number": number,
            "title": title,
            "body": body,
            "state": "OPEN",
            "stateReason": None,
            "url": f"https://github.com/example/fixture/issues/{number}",
        }
        self.issues.append(issue)
        self.writes.append("create")
        if self.timeout_create:
            self.timeout_create = False
            raise sync.SyncError("uncertain create timeout")
        return copy.deepcopy(issue)

    def update_issue(self, identifier, title, body):
        issue = next(item for item in self.issues if item["id"] == identifier)
        issue.update(title=title, body=body)
        self.writes.append("body")

    def lifecycle(self, identifier, state, reason):
        issue = next(item for item in self.issues if item["id"] == identifier)
        issue.update(state=state, stateReason=reason)
        self.writes.append("lifecycle")

    def add_item(self, project, issue):
        if self.fail_add:
            self.fail_add = False
            raise sync.SyncError("Project permission failure")
        item = {
            "id": f"P{len(self.items) + 1}",
            "isArchived": False,
            "content": {"id": issue},
            "fieldValueByName": None,
        }
        self.items.append(item)
        self.writes.append("add")
        return item["id"]

    def set_status(self, project, identifier, field, option):
        item = next(item for item in self.items if item["id"] == identifier)
        item["fieldValueByName"] = {"optionId": option}
        self.writes.append("status")


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path
    (root / "TODO").mkdir()
    options = {
        stage: f"option-{index}"
        for index, stage in enumerate(("Backlog", "Ready", "In progress", "In review", "Done"))
    }
    config = {
        "schema": 1,
        "repository": "example/fixture",
        "repository_id": "repository-fixture",
        "branch": "main",
        "project": {
            "id": "project-fixture",
            "url": "https://github.com/users/example/projects/1",
            "view_id": "view-fixture",
            "status_field_id": "status-fixture",
            "options": options,
        },
        "state_file": "state.json",
        "workstreams": {"kc-01": "01_FOUNDATION.todo"},
        "exclude": {},
        "reviewed_statuses": {},
        "status_map": {
            "NOT_STARTED": ["OPEN", None, "Backlog"],
            "DEFERRED": ["OPEN", None, "Backlog"],
            "READY": ["OPEN", None, "Ready"],
            "IN_PROGRESS": ["OPEN", None, "In progress"],
            "IN_REVIEW": ["OPEN", None, "In review"],
            "DONE": ["CLOSED", "COMPLETED", "Done"],
            "CANCELLED": ["CLOSED", "NOT_PLANNED", "Backlog"],
            "SUPERSEDED": ["CLOSED", "NOT_PLANNED", "Backlog"],
        },
    }
    path = root / "TODO" / "01_FOUNDATION.todo"
    initial = (
        "Status: DONE\nMilestone: Bounded outcome\nDependencies: None\n"
        "Purpose: Public fixture\n\nTasks:\n  [x] Actual task\n\n"
        "Acceptance criteria:\n  Bounded result\n\nCompletion evidence:\n"
        "  Synthetic evidence, not human acceptance\n\n"
        "Completion log:\n  2020-01-01: Actual history\n"
    )
    path.write_text(initial, encoding="utf-8")
    config_path = root / "config.json"
    sync.save_json(config_path, config)
    return Harness(root, config, config_path, path, initial)


class Harness:
    def __init__(self, root, config, config_path, path, initial):
        self.root, self.config, self.config_path = root, config, config_path
        self.path, self.initial = path, initial
        self.api = FakeGitHub()
        self.output = ""

    def execute(self, apply=True, selected=None):
        sync.save_json(self.config_path, self.config)
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                return sync.run(self.config_path, apply, selected, self.api, self.root)
            finally:
                self.output = output.getvalue()

    def state(self):
        return sync.load_json(self.root / "state.json")

    def change(self, before, after):
        text = self.path.read_text(encoding="utf-8").replace(before, after)
        self.path.write_text(text, encoding="utf-8")


def test_preview_has_no_remote_or_workstream_writes(fixture):
    assert fixture.execute(False) == 0
    assert fixture.api.writes == []
    assert fixture.path.read_text(encoding="utf-8") == fixture.initial
    assert not (fixture.root / "state.json").exists()


def test_status_first_workstream_title_backlink_and_idempotence(fixture):
    assert fixture.execute() == 0
    issue, item = fixture.api.issues[0], fixture.api.items[0]
    assert issue["title"] == "[01] Bounded outcome"
    assert issue["stateReason"] == "COMPLETED"
    assert item["content"]["id"] == issue["id"]
    assert item["fieldValueByName"]["optionId"] == fixture.config["project"]["options"]["Done"]
    assert "GitHub-Issue: " + issue["url"] in fixture.path.read_text(encoding="utf-8")
    initial_state = (fixture.root / "state.json").read_bytes()
    initial_source = fixture.path.read_bytes()
    fixture.api.writes.clear()
    assert fixture.execute() == 0
    assert fixture.api.writes == []
    assert (len(fixture.api.issues), len(fixture.api.items)) == (1, 1)
    assert (fixture.root / "state.json").read_bytes() == initial_state
    assert fixture.path.read_bytes() == initial_source


def test_legacy_title_is_retained(fixture):
    fixture.path.write_text("Original title\n" + fixture.initial, encoding="utf-8")
    assert fixture.execute() == 0
    assert fixture.api.issues[0]["title"] == "[01] Original title"


def test_unpublished_local_workstream_has_no_misleading_remote_file_link(fixture):
    fixture.config["unpublished_workstreams"] = ["kc-01"]
    assert fixture.execute() == 0
    body = fixture.api.issues[0]["body"]
    assert "Local workstream: `TODO/01_FOUNDATION.todo` (not yet published" in body
    assert "/blob/" not in body
    assert "### Completion evidence" in body


def test_reopening_cancellation_and_supersession(fixture):
    assert fixture.execute() == 0
    for status, state, reason, stage in (
        ("IN_PROGRESS", "OPEN", None, "In progress"),
        ("CANCELLED", "CLOSED", "NOT_PLANNED", "Backlog"),
        ("DONE", "CLOSED", "COMPLETED", "Done"),
        ("SUPERSEDED", "CLOSED", "NOT_PLANNED", "Backlog"),
    ):
        text = sync.re.sub(
            r"^Status: .+$",
            "Status: " + status,
            fixture.path.read_text(encoding="utf-8"),
            flags=sync.re.M,
        )
        fixture.path.write_text(text, encoding="utf-8")
        assert fixture.execute() == 0, fixture.output
        issue = fixture.api.issues[0]
        assert (issue["state"], issue["stateReason"]) == (state, reason)
        assert (
            fixture.api.items[0]["fieldValueByName"]["optionId"]
            == (fixture.config["project"]["options"][stage])
        )


def test_unrelated_human_body_survives_managed_updates(fixture):
    assert fixture.execute() == 0
    fixture.api.issues[0]["body"] = (
        "Human preface\n\n" + fixture.api.issues[0]["body"] + "\n\nHuman tail"
    )
    fixture.change("Public fixture", "Public updated purpose")
    assert fixture.execute() == 0
    body = fixture.api.issues[0]["body"]
    assert body.startswith("Human preface\n\n") and body.endswith("\n\nHuman tail")
    assert "Public updated purpose" in body


def test_managed_human_edit_blocks_only_the_conflicting_workstream(fixture):
    assert fixture.execute() == 0
    fixture.api.issues[0]["body"] = fixture.api.issues[0]["body"].replace(
        "Public fixture",
        "Human edit",
    )
    fixture.config["workstreams"]["kc-02"] = "02_SECOND.todo"
    (fixture.root / "TODO" / "02_SECOND.todo").write_text(fixture.initial, encoding="utf-8")
    fixture.api.writes.clear()
    assert fixture.execute() == 1
    assert len(fixture.api.issues) == 2
    assert "Human edit" in fixture.api.issues[0]["body"]
    assert "Remote human edit" in fixture.output


def test_remote_lifecycle_and_board_moves_conflict(fixture):
    assert fixture.execute() == 0
    fixture.api.issues[0]["state"] = "OPEN"
    fixture.api.writes.clear()
    assert fixture.execute() == 1
    assert fixture.api.writes == []
    fixture.api.issues[0]["state"] = "CLOSED"
    fixture.api.items[0]["fieldValueByName"]["optionId"] = "human-option"
    assert fixture.execute() == 1
    assert fixture.api.writes == []


def test_partial_project_failure_retains_progress_until_explicit_reconciliation(fixture):
    fixture.api.fail_add = True
    assert fixture.execute() == 1
    assert len(fixture.api.issues) == 1
    assert "adding_item" in fixture.state()["workstreams"]["kc-01"]
    assert fixture.execute() == 1
    state = fixture.state()
    state["workstreams"]["kc-01"].pop("adding_item")
    sync.save_json(fixture.root / "state.json", state)
    assert fixture.execute() == 0
    assert (len(fixture.api.issues), len(fixture.api.items)) == (1, 1)


def test_uncertain_create_recovers_marker_without_duplicate(fixture):
    fixture.api.timeout_create = True
    assert fixture.execute() == 1
    assert "creating" in fixture.state()["workstreams"]["kc-01"]
    assert fixture.execute() == 0, fixture.output
    assert (len(fixture.api.issues), len(fixture.api.items)) == (1, 1)


def test_uncertain_add_recovers_visible_item_without_duplicate(fixture):
    add_item = fixture.api.add_item

    def uncertain_add(project, issue):
        add_item(project, issue)
        raise sync.SyncError("uncertain Project add")

    with patch.object(fixture.api, "add_item", side_effect=uncertain_add):
        assert fixture.execute() == 1
    assert "adding_item" in fixture.state()["workstreams"]["kc-01"]
    assert fixture.execute() == 0, fixture.output
    assert (len(fixture.api.issues), len(fixture.api.items)) == (1, 1)


def test_uncertain_create_without_visible_issue_never_retries(fixture):
    work = sync.parse_workstream(fixture.path, "kc-01", fixture.config, fixture.root)
    sync.save_json(
        fixture.root / "state.json",
        {
            "schema": 1,
            "repository_id": fixture.config["repository_id"],
            "project_id": fixture.config["project"]["id"],
            "workstreams": {
                "kc-01": {
                    "creating": {
                        "title": work["title"],
                        "managed": work["managed"],
                    }
                }
            },
        },
    )
    assert fixture.execute() == 1
    assert fixture.api.writes == []


def test_backlink_failure_recovers_verified_remote_progress(fixture):
    with patch.object(sync, "write_backlink", side_effect=OSError("disk unavailable")):
        assert fixture.execute() == 1
    assert "pending" in fixture.state()["workstreams"]["kc-01"]
    fixture.api.writes.clear()
    assert fixture.execute() == 0
    assert fixture.api.writes == []
    assert (len(fixture.api.issues), len(fixture.api.items)) == (1, 1)


def test_failed_inventory_is_never_an_empty_baseline(fixture):
    fixture.api.fail_inventory = True
    with pytest.raises(sync.SyncError, match="read failure"):
        fixture.execute()
    assert fixture.api.writes == []
    assert not (fixture.root / "state.json").exists()


def test_excluded_and_unadopted_files_never_enter_payloads(fixture):
    private = fixture.root / "TODO" / "13_PRIVATE.todo"
    private.write_text("private fixture not a workstream", encoding="utf-8")
    (fixture.root / "TODO" / "99_UNREVIEWED.todo").write_text(
        "unreviewed fixture not a workstream",
        encoding="utf-8",
    )
    fixture.config["exclude"]["13_PRIVATE.todo"] = "No approved public projection"
    assert fixture.execute() == 0
    assert len(fixture.api.issues) == 1
    assert "private fixture" not in fixture.api.issues[0]["body"]
    assert "unreviewed fixture" not in fixture.api.issues[0]["body"]
    assert "EXCLUDED 13_PRIVATE.todo" in fixture.output
    assert "UNADOPTED 99_UNREVIEWED.todo" in fixture.output


def test_rename_keeps_identity_and_missing_file_never_deletes(fixture):
    assert fixture.execute() == 0
    renamed = fixture.path.with_name("01_RENAMED.todo")
    fixture.path.rename(renamed)
    fixture.config["workstreams"]["kc-01"] = renamed.name
    assert fixture.execute() == 0
    assert len(fixture.api.issues) == 1
    renamed.unlink()
    fixture.api.writes.clear()
    assert fixture.execute() == 1
    assert fixture.api.writes == []


def test_unknown_composite_status_and_missing_schema_fail_closed(fixture):
    fixture.change("Status: DONE", "Status: DONE locally; publication BLOCKED")
    assert fixture.execute() == 1
    assert fixture.api.writes == []
    fixture.path.write_text(
        fixture.initial.replace("Completion log:", "History:"),
        encoding="utf-8",
    )
    assert fixture.execute() == 1
    assert fixture.api.writes == []


def test_blocker_metadata_preserves_stage_on_status_first_files(fixture):
    fixture.change(
        "Status: DONE",
        "Status: BLOCKED\nBlocked-stage: In review\nBlocker: Await owned fixture",
    )
    assert fixture.execute() == 0
    assert fixture.api.issues[0]["state"] == "OPEN"
    assert "Blocker: Await owned fixture" in fixture.api.issues[0]["body"]
    assert (
        fixture.api.items[0]["fieldValueByName"]["optionId"]
        == (fixture.config["project"]["options"]["In review"])
    )


def test_duplicate_markers_and_removed_membership_do_not_recreate(fixture):
    assert fixture.execute() == 0
    fixture.api.issues.append({**copy.deepcopy(fixture.api.issues[0]), "id": "duplicate"})
    fixture.api.writes.clear()
    assert fixture.execute() == 1
    assert fixture.api.writes == []
    fixture.api.issues.pop()
    fixture.api.items.clear()
    assert fixture.execute() == 1
    assert fixture.api.writes == []


def test_backlink_conflict_and_disclosed_public_path_projection(fixture):
    fixture.change("Public fixture", "Files: " + str(fixture.root) + "\\build\\example")
    assert fixture.execute() == 0
    assert str(fixture.root) not in fixture.api.issues[0]["body"]
    fixture.change(fixture.api.issues[0]["url"], "https://github.com/example/fixture/issues/999")
    fixture.api.writes.clear()
    assert fixture.execute() == 1
    assert fixture.api.writes == []


def test_unmapped_local_backlink_blocks_create(fixture):
    fixture.change(
        "Status: DONE",
        "Status: DONE\nGitHub-Issue: https://github.com/example/fixture/issues/7",
    )
    assert fixture.execute() == 1
    assert fixture.api.writes == []


@pytest.mark.parametrize(
    "private",
    [
        "ghp_" + "A" * 36,
        r"C:\Users\fixture\private.txt",
        "https://fixture:password@example.invalid/video",
    ],
)
def test_private_content_blocks_without_echoing(fixture, private):
    fixture.change("Public fixture", private)
    assert fixture.execute() == 1
    assert private not in fixture.output
    assert fixture.api.writes == []


def test_private_title_or_invalid_status_is_not_echoed(fixture):
    dummy = "ghp_" + "B" * 36
    fixture.path.write_text(dummy + "\n" + fixture.initial, encoding="utf-8")
    assert fixture.execute() == 1
    assert dummy not in fixture.output
    fixture.path.write_text(
        fixture.initial.replace("Status: DONE", "Status: " + dummy), encoding="utf-8"
    )
    assert fixture.execute() == 1
    assert dummy not in fixture.output
    assert fixture.api.writes == []


def test_paginated_inventory_reads_every_page():
    pages = [
        {"repo": {"nodes": [1], "pageInfo": {"hasNextPage": True, "endCursor": "next"}}},
        {"repo": {"nodes": [2], "pageInfo": {"hasNextPage": False, "endCursor": None}}},
    ]
    api = sync.GitHub()
    with patch.object(api, "request", side_effect=pages) as request:
        assert api.connection("query", ("repo",)) == [1, 2]
        assert request.call_args.kwargs["cursor"] == "next"


def test_repeated_pagination_cursor_is_an_error():
    page = {"repo": {"nodes": [], "pageInfo": {"hasNextPage": True, "endCursor": "same"}}}
    with patch.object(sync.GitHub, "request", return_value=page):
        with pytest.raises(sync.SyncError, match="pagination"):
            sync.GitHub().connection("query", ("repo",))


def test_mutation_timeout_is_never_retried():
    with patch.object(
        sync.subprocess,
        "run",
        side_effect=subprocess.TimeoutExpired("gh", 120),
    ) as command:
        with pytest.raises(sync.SyncError, match="uncertain"):
            sync.GitHub().request("mutation { fixture }")
        assert command.call_count == 1


def test_failure_messages_redact_child_credential():
    dummy = "fixture-only-secret"
    result = subprocess.CompletedProcess("gh", 1, "", "failure " + dummy)
    with (
        patch.dict(sync.os.environ, {"GH_TOKEN": dummy}),
        patch.object(sync.subprocess, "run", return_value=result),
    ):
        with pytest.raises(sync.SyncError) as raised:
            sync.GitHub().request("query { fixture }")
        assert dummy not in str(raised.value)


def test_graphql_error_does_not_create_empty_inventory():
    result = subprocess.CompletedProcess("gh", 0, json.dumps({"errors": [{"message": "no"}]}), "")
    with patch.object(sync.subprocess, "run", return_value=result):
        with pytest.raises(sync.SyncError, match="no empty baseline"):
            sync.GitHub().request("query { fixture }")


def test_kanban_requires_status_columns_and_preserves_a_valid_view(fixture):
    view = {
        "id": "view-fixture",
        "layout": "BOARD_LAYOUT",
        "verticalGroupByFields": {
            "nodes": [{"id": "status-fixture"}],
            "pageInfo": {"hasNextPage": False},
        },
    }
    sync.validate_kanban([view], fixture.config["project"])
    view["layout"] = "TABLE_LAYOUT"
    with pytest.raises(sync.SyncError, match="Kanban"):
        sync.validate_kanban([view], fixture.config["project"])
    view["layout"] = "BOARD_LAYOUT"
    view["verticalGroupByFields"]["nodes"] = [{"id": "assignees-fixture"}]
    with pytest.raises(sync.SyncError, match="Status field"):
        sync.validate_kanban([view], fixture.config["project"])
