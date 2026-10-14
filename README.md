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
- Search tickets by title substring, with optional filters for category,
  status and priority that combine with AND.
- Assign tickets to staff members.
- Display an unresolved work queue ordered by priority and then ticket number.
- Enforce the status lifecycle:
  - `open` -> `in progress` -> `resolved`
  - A resolved ticket can be explicitly reopened to `open`.
- Require an assignee before a ticket can move to `in progress`.
- Generate status, priority and category reports.
- Run an interactive Engineering Understanding Check on the application's
  own behaviour.
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
│   ├── create_tickets.py       # Ticket model and ticket creation
│   ├── list_view.py             # Listing and ticket lookup
│   ├── report.py                # Ticket reporting
│   ├── search.py                # Read-only search and priority sorting
│   ├── understanding_check.py   # Engineering Understanding Check
│   ├── validate_ticket.py       # Input validation
│   └── workflow.py              # Status transitions and work queue
├── docs/
│   ├── ai-learning-log.md
│   ├── baseline-check.md        # Behaviour of the app before this sprint
│   └── design-decisions.md      # Decisions and the evidence behind them
├── tests/
│   ├── test_assign.py
│   ├── test_bug_hunter.py
│   ├── test_cli_integration.py
│   ├── test_create_and_validate.py
│   ├── test_list_view.py
│   ├── test_report.py
│   ├── test_search.py
│   ├── test_storage_integration.py
│   ├── test_understanding_check.py
│   └── test_workflow.py
├── .github/workflows/tests.yml # Continuous integration workflow
├── main.py                      # Interactive CLI entry point
└── tickets.json                 # Local ticket store and sample data
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

## Ticket validation

The following values are accepted:

- Title: non-blank text.
- Category: `Network`, `Hardware`, `Software`, or `Other` (case-insensitive).
- Urgency: `low`, `medium`, or `high` (case-insensitive).
- Affected users: a positive whole number.

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

Menu option 9 runs a six-question multiple-choice check on how this
application is meant to behave. Answers must be `A`, `B`, `C` or `D`; an
invalid entry is rejected and the question is asked again. The check scores
one point per correct answer and reports a result out of six.

It then asks for a written explanation of at least two answers and prints
them for mentor discussion. Explanations are recorded, not graded: a
matching keyword does not make an explanation correct. The check writes
nothing to disk.

The question bank (`QUESTIONS`) is data and the scoring (`score_answers`)
is a pure function that reads nothing but the answers, so the score can be
tested without going through `input()` or `print()`.

## Testing

The project uses Python's standard `unittest` framework. The suite currently
contains 95 tests covering:

- Ticket priority boundaries and serialization.
- Validation success, validation errors, and malformed values.
- Ticket ID generation and creation failures.
- Assignment and ticket lookup edge cases.
- Full JSON persistence round trips.
- Missing stores and failed updates.
- Status lifecycle rules and invalid transitions.
- Work queue filtering, ordering, and immutability.
- Search matching, combined filters, and read-only behaviour.
- Priority sorting and non-numeric-safe tie-breaking.
- Report totals, per-status/priority/category counts, unresolved and
  resolved counts, resolution percentage, and the empty-dataset case.
- Understanding check scoring, invalid-answer retry, and the explanation
  rules.
- Bug-hunter boundary tests for the accepted types of `affected_users`.
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
tests Python 3.12 and 3.13. Each matrix job:

1. Checks out the repository.
2. Installs the selected Python version.
3. Compiles all Python sources.
4. Runs the complete unit and integration test suite.

## Team members and collaborators

Use this table to record the people contributing to the project and their
responsibilities.

| Name | Role | Responsibilities |
| --- | --- | --- |
|  Timothy Ododo | Team Lead |  |
|  Wuese Joy Ayande | member |  |
|  Patrick Sean Odugboche | member  |

## Current implementation notes

- This is a local CLI application; it does not currently provide a web API,
  database server, authentication, or multi-user locking.
- `tickets.json` is the persistence layer and should be backed up before
  manual bulk edits.
- The application is intentionally small and uses the Python standard
  library so it can run without dependency installation.
