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
- Generate status and priority reports.
- Persist tickets in human-readable `tickets.json`.

## Requirements

- Python 3.11, 3.12, or 3.13
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
│   ├── validate_ticket.py       # Input validation
│   └── workflow.py              # Status transitions and work queue
├── docs/
│   ├── ai-learning-log.md
│   ├── baseline-check.md        # Behaviour of the app before this sprint
│   └── design-decisions.md      # Decisions and the evidence behind them
├── tests/
│   ├── test_assign.py
│   ├── test_cli_integration.py
│   ├── test_create_and_validate.py
│   ├── test_list_view.py
│   ├── test_report.py
│   ├── test_search.py
│   ├── test_storage_integration.py
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
| 9 | Exit |

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

The report feature can:

- Return a structured report for supplied ticket data with total count,
  original tickets, and counts grouped by normalized status.
- Print a report from the stored JSON file, including totals by status and
  priority.

An empty stored ticket file produces a `No tickets found in the report.`
message.

## Testing

The project uses Python's standard `unittest` framework. The suite currently
contains 52 tests covering:

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
- Report generation.
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
