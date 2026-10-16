# CampusFlow-TJP

CampusFlow-TJP is a dependency-free command-line application for managing
campus IT and facilities support tickets. It lets a support team create,
prioritise, assign, search, progress, and report on tickets stored in a local
JSON file.

## Features

- Create tickets with a title, category, urgency, and affected-user count.
- Validate ticket fields before a ticket is saved.
- Calculate priority automatically:
  - `critical`: high urgency and at least 10 affected users.
  - `high`: high urgency or at least 10 affected users.
  - `medium`: medium urgency or at least 3 affected users.
  - `low`: all remaining valid tickets.
- Generate sequential ticket IDs such as `T001`, `T002`, and `T011`.
- List all stored tickets.
- Search for a ticket by ID.
- Search stored tickets by title, category, status, and priority, with the
  results optionally reordered most-urgent-first.
- Assign tickets to staff members.
- Add shared or internal notes, restricted to the assigned staff member, the
  student/fellow who created the ticket, or a support lead. Reading follows the
  same rule: `get_visible_notes()` shows shared notes only to those same users,
  and internal notes only to support roles.
- A student/fellow may include one optional initial note while creating a
  ticket; notes added after creation must contain text.
- Student/fellow notes are always shared; only support staff and support leads
  can create internal notes.
- `add_note()` is the no-argument interactive note-entry function. It prompts
  for the ticket and message; author and role come from the logged-in user,
  and support roles choose visibility interactively.
- Display an unresolved work queue ordered by priority and then ticket number.
- Enforce the status lifecycle:
  - `open` -> `in progress` -> `resolved`
  - A resolved ticket can be explicitly reopened to `open`.
- Require an assignee before a ticket can move to `in progress`.
- Generate status, priority and category reports.
- Generate status and priority reports.
- Run an in-app Engineering Understanding Check on the application's own
  behaviour.
- Persist tickets in human-readable `tickets.json`.

## Requirements

- Python 3.12 or 3.13 (the versions continuous integration verifies)
- No third-party Python packages are required.

## Project structure

```text
.
├── campusflow/
│   ├── __init__.py             # JSON storage and public package exports
│   ├── assign.py               # Ticket assignment
│   ├── auth.py                 # User registration, login and session state
│   ├── create_tickets.py       # Ticket model and ticket creation
│   ├── list_view.py            # Listing and ticket lookup
│   ├── migrate.py              # One-time ticket store migration (decision D2)
│   ├── notes.py                # Ticket notes
│   ├── report.py               # Ticket reporting
│   ├── search.py               # Read-only ticket search
│   ├── understanding_check.py  # Engineering Understanding Check
│   ├── validate_note.py        # Note validation and note permissions
│   ├── validate_ticket.py      # Input validation
│   └── workflow.py             # Status transitions and work queue
├── docs/
│   ├── ai-learning-log.md
│   ├── baseline-check.md       # Behaviour of the app before this sprint
│   └── design-decisions.md     # Decisions and the evidence behind them
├── tests/
│   ├── test_assign.py
│   ├── test_auth.py
│   ├── test_bug_hunter.py
│   ├── test_cli_integration.py
│   ├── test_create_and_validate.py
│   ├── test_list_view.py
│   ├── test_notes.py
│   ├── test_report.py
│   ├── test_robustness.py
│   ├── test_search.py
│   ├── test_storage_integration.py
│   ├── test_understanding_check.py
│   └── test_workflow.py
├── .github/workflows/tests.yml # Continuous integration workflow
├── main.py                      # Interactive CLI entry point
├── tickets.json                 # Local ticket store and sample data
└── users.json                   # User accounts for registration and login
```

## Running the application

Run the CLI from the repository root:

```bash
python main.py
```

The application displays this menu:

| Option | Action |
| --- | --- |
| 1 | Raise a ticket |
| 2 | List all tickets |
| 3 | Search and view a ticket by ID |
| 4 | Assign a ticket |
| 5 | View the work queue |
| 6 | Update ticket status |
| 7 | Generate a ticket report |
| 8 | Search tickets |
| 9 | Engineering Understanding Check |
| 10 | Exit |

The application reads and writes `./tickets.json` relative to the directory
where `main.py` is started. If the file does not exist, reads return an empty
ticket list. A valid existing JSON array is expected when creating or updating
tickets.

## Ticket storage format and migration

Each stored ticket is a JSON object. `affected_users` is a real integer, not a
string, and `notes` is always present:

```json
{
    "id": "T001",
    "title": "hello",
    "category": "Network",
    "urgency": "medium",
    "affected_users": 12,
    "priority": "high",
    "status": "open",
    "assigned_to": null,
    "notes": []
}
```

The store is loaded strictly. A file that is not valid JSON, is not a list of
objects, contains a ticket without a usable `id`, or repeats a ticket ID is
rejected as a whole with `TicketStorageError`, and the file is left untouched,
so a later save cannot overwrite recoverable data. Missing and zero-byte stores
are created as an empty list, as before.

Earlier versions stored `affected_users` as a numeric string and had no `notes`
key. Such a store must be migrated once before it can be loaded:

```bash
python -m campusflow.migrate            # migrates ./tickets.json
python -m campusflow.migrate path.json  # migrates another store
```

The migration copies the original file to `tickets.json.bak` before rewriting,
converts `affected_users` to an integer, and adds an empty `notes` list. A
count that is not a whole number is left untouched for the strict loader to
reject rather than being guessed at. This is the documented migration required
by decision D2 in `docs/design-decisions.md`.

## Ticket validation

The following values are accepted:

- Title: non-blank text.
- Category: `Network`, `Hardware`, `Software`, or `Other` (case-insensitive).
- Urgency: `low`, `medium`, or `high` (case-insensitive).
- Affected users: a positive whole number. Strings such as `"12"`, floats, and
  booleans are rejected even when the value looks numeric; the CLI converts the
  typed value to an integer.

Invalid tickets raise `TicketValidationError` before persistence. Blank staff
names and invalid or unknown ticket IDs are rejected by their respective
operations.

**Known gap.** `affected_users` rejects booleans, floats, zero and negative
counts, but a numeric *string* such as `"12"` is still accepted, because the
check is `str(value).isdigit()`. Requirement A requires an actual integer, so
this is a defect rather than a feature: the sample `tickets.json` in this
repository ships `"affected_users": "12"` and loads only for that reason.
`tests/test_bug_hunter.py` records the gap, and
`docs/design-decisions.md` D2 describes the migration that must land before
the validator is tightened.

## Status workflow and queue

Status input is normalized so values such as `In Progress`, `in-progress`, and
`in_progress` are treated as `in progress`.

Direct status changes follow these rules:

```text
open -> in progress -> resolved
resolved -> open       # explicit reopen operation
```

Invalid transitions do not modify the ticket. The work queue includes only
`open` and `in progress` tickets and returns a new sorted list, leaving the
stored list order unchanged. Sorting is:

1. `critical`
2. `high`
3. `medium`
4. `low`
5. Numeric ticket ID for ties

## Reporting

The report covers total tickets, counts by status, priority and category,
the unresolved count, the resolved count, and the resolution percentage:

```text
Total tickets:  5
=======================
Tickets By Status:
---------------------
Open:  2
In Progress:  1
Resolved:  2
Unresolved (open + in progress):  3
Resolved:  2
Resolution rate:  40.0%
==============================
Tickets By Priority:
------------------------------
Critical:  2
...
Tickets By Category:
------------------------------
Network:  2
...
```

- `unresolved` counts `open` plus `in progress` tickets.
- `resolution_percent` is `resolved / total * 100`, rounded to one decimal
  place. An empty dataset reports `0.0%` rather than failing.
- A ticket counts under its **current** status, so a reopened ticket counts
  as `open`. Status buckets never overlap, so they always add up to the
  total.
- Statuses are matched through `workflow.normalise_status`, so `In Progress`
  and `in_progress` land in the same bucket as `in progress`.
- Categories are matched case-insensitively, since ticket creation stores
  the category exactly as typed. `Network` and `network` are one bucket.
- There is no `closed` bucket: `closed` is not a legal status in this
  application (see `docs/design-decisions.md`, D7).

`generate_total_ticket_report(tickets)` returns the structured report as a
dictionary; called with no argument it prints the same report for the stored
file. Both paths format one shared result, so the printed figures and the
returned figures cannot disagree. An empty stored ticket file produces a
`No tickets found in the report.` message.

## Engineering Understanding Check

Menu option 8 runs a short multiple-choice check on how this application
behaves. All six questions come from the sprint brief's question bank; the
answer key is verified against this codebase, and each key is commented with
the behaviour that justifies it.

- An answer that is not `A`, `B`, `C` or `D` is rejected and the question is
  asked again.
- One point is scored per correct answer, so the result is `0/6` to `6/6`.
- After the questions you are asked to explain at least two of your answers in
  your own words.

Explanations are **recorded, not graded**. A matching keyword does not make an
explanation correct; they are printed at the end so they can be discussed.

The question bank is plain data and `score_answers()` is a pure function that
takes a mapping of question number to chosen letter, so scoring is tested
without going near `input()` or `print()`. The check writes nothing to disk.

## Searching tickets

Search is **read-only**: it never changes a ticket, never saves, and never
changes the order of the stored file. It returns a new list.

Menu option 8 asks for four filters. Leave any of them blank to ignore it:

- **Title contains** — case-insensitive substring match.
- **Category** — `Network`, `Hardware`, `Software`, or `Other`.
- **Status** — `open`, `in progress`, or `resolved`.
- **Priority** — `critical`, `high`, `medium`, or `low`.

Supplied filters are combined with **AND**: a ticket must match every filter
you give. Category, status, and priority are case-insensitive exact matches,
and status also accepts separator variants such as `in_progress`. An invalid
filter value is re-prompted instead of being accepted or crashing the menu.

When more than one ticket matches, the view offers to sort the results by
priority (most urgent first, ties broken by ticket number):

1. `critical`
2. `high`
3. `medium`
4. `low`
5. Numeric ticket ID for ties

The search itself does not sort. `search_tickets` keeps the stored order and
`sort_by_priority` is a separate function, so the two behaviours stay testable
on their own. Both are pure functions over a list of ticket dictionaries;
`search_tickets_menu` is the only part that reads input or touches the file.

## Testing

The project uses Python's standard `unittest` framework. The suite currently
contains 82 tests covering:

- Ticket priority boundaries and serialization.
- Validation success, validation errors, and malformed values.
- Ticket ID generation and creation failures.
- Assignment and ticket lookup edge cases.
- Full JSON persistence round trips.
- Missing stores and failed updates.
- Status lifecycle rules and invalid transitions.
- Work queue filtering, ordering, and immutability.
- Report totals, per-status/priority/category counts, unresolved and
  resolved counts, resolution percentage, and the empty-dataset case.
- Report counts after one ticket is resolved and another is reopened.
- Bug-hunter boundary tests for the accepted types of `affected_users`.
- Report generation.
- Search filtering by title, category, status, and priority, including the
  "blank means no filter" rule and case/separator handling.
- Search result ordering and the guarantee that neither search nor sort
  modifies the stored tickets.
- Search menu re-prompting, the empty-store message, and the no-match message.
- The Understanding Check question bank, the A/B/C/D input guard, scoring,
  and the requirement that explanations are collected but never graded.
- Main menu exit and invalid-option behavior.

Run the complete suite:

```bash
python -m unittest discover -s tests -v
```

Compile all Python sources:

```bash
python -m compileall -q .
```

## Continuous integration

GitHub Actions is configured in
`.github/workflows/tests.yml`. It runs on every push and pull request and
tests Python 3.11, 3.12, and 3.13. Each matrix job:

1. Checks out the repository.
2. Installs the selected Python version.
3. Compiles all Python sources.
4. Runs the complete unit and integration test suite.

## Team members and collaborators

Use this table to record the people contributing to the project and their
responsibilities.

| Name | Role | Responsibilities |
| --- | --- | --- |
| Timothy Ododo | Team Lead | Engineer A — ticket safety and storage: validation helpers, follow-up notes, safe JSON load and save |
| Wuese Joy Ayande | Member | Original build — status workflow and the work queue |
| Patrick Sean Odugboche | Member | Original build |
| Okoh Daniel Oche | Member | Engineer B — search, reporting and CLI: search and filtering, quality reports, note menus, the Engineering Understanding Check |

The first version of CampusFlow was built by Wuese Joy Ayande, Patrick Sean
Odugboche and Timothy Ododo. The CampusFlow Next sprint continued the project
with a pairing of Timothy Ododo (Engineer A) and Okoh Daniel Oche (Engineer B).

## Current implementation notes

- This is a local CLI application; it does not currently provide a web API,
  database server, authentication, or multi-user locking.
- `tickets.json` is the persistence layer and should be backed up before
  manual bulk edits.
- The application is intentionally small and uses the Python standard
  library so it can run without dependency installation.
