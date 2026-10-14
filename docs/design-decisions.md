# Design Decisions

Engineered decisions for the CampusFlow Next sprint. Each entry records the
context, the decision, the evidence behind it, and the consequences. Evidence
references `docs/baseline-check.md`, which was produced by running the code at
commit `0d5493e`.

## D1 — The work queue contains only `open` tickets

**Context.** The sprint brief states the original Open Work Queue must show only
`open` tickets, and that an `in progress` ticket must not appear. The code at
baseline does not behave that way. Requirement D also says the existing queue
must not be silently replaced with a different status filter.

**Decision.** The queue becomes `open`-only. The behaviour change is recorded
here and in `README.md` rather than made silently, and it is raised with the
mentor because it changes behaviour that was previously documented.

**Evidence.** Baseline input 1 (a fixture with one ticket per status) printed:

```text
Work queue (most urgent first):
  T004  critical  open         unassigned    Projector dead
  T001  high      open         unassigned    Wi-Fi router reboot
  T002  low       in progress  Ada           Laptop battery
```

`T002` is `in progress` and appears in the queue. The filter is
`QUEUE_STATUSES = {"open", "in progress"}` in `campusflow/workflow.py`.

**Consequences.** A ticket that has been started but not finished disappears
from the queue view. Anyone relying on the old queue must use the status filter
in the new search view (Requirement C) instead.

**Status.** Decided 2026-10-14. **Not yet implemented**, and it changes existing
code owned outside Engineer B's area, so it needs Engineer A's agreement before
either engineer commits it.

## D2 — The stored data is migrated once, and the validator stays strict

**Context.** Requirement A says `affected_users` must be a strictly positive
integer and that strings must be rejected. Requirement E says the whole
collection must be rejected on load if any record is invalid. The shipped
`tickets.json` stores `"affected_users": "12"` — a string — and has no `notes`
key at all. Implemented literally, the application would refuse to load the
ticket it ships with.

**Decision.** Migrate `tickets.json` once: convert `affected_users` to an
integer and add `notes: []` to every record. The validator and loader remain
strict, with no leniency for legacy shapes. Requirement E permits this provided
the format change is documented: *"you may refactor internally, but do not
discard old working tickets"* and *"if you change file format incompatibly,
include a small documented migration."*

**Evidence.** `tickets.json` line 7 at the audited commit:
`"affected_users": "12"`. Confirmed defect 6 in `docs/baseline-check.md`.

**Consequences.** The migration must run before the strict loader is merged, or
the application will not start against existing data. The README must describe
the format and the migration. Source data must be backed up before the
migration runs.

**Status.** Decided 2026-10-14. Migration not yet written.

## D3 — Errors are raised, not returned as strings

**Context.** The codebase currently mixes conventions. `update_ticket` returns
the literal string `"update failed"` and callers compare against it in three
places, while the workflow functions raise `ValueError`. The brief requires
agreeing on one convention and not creating inconsistent patterns.

**Decision.** Business-rule violations **raise** exceptions. `TicketValidationError`
is kept and extended for validation failures; state-machine violations continue
to raise `ValueError`, which `main.py` already catches. Functions must not
signal failure by returning a magic string.

**Evidence.** `campusflow/__init__.py:39` returns `"update failed"`, compared in
`assign.py:16` and `workflow.py:134`. Confirmed defect 9 in
`docs/baseline-check.md`.

**Consequences.** `update_ticket` should raise rather than return a sentinel, and
its callers must be updated in the same change. Existing tests that assert on
`"update failed"` (`tests/test_storage_integration.py:61`) must be updated
deliberately, not deleted.

**Status.** Proposed 2026-10-14. Needs Engineer A's sign-off — it changes the
storage layer.

## D4 — One canonical spelling for each status

**Context.** Statuses are written as `in_progress` in the brief, stored as
`in progress` with a space on disk, and normalised in one place but not another.

**Decision.** Keep `in progress` (with a space) as the stored form, since that is
what existing data contains and Requirement E permits keeping the current
format. Define it once as a shared constant that both engineers import, and use
`workflow.normalise_status` for all user input rather than re-implementing
normalisation.

**Evidence.** `workflow.normalise_status` lowercases and converts separators;
`report._build_ticket_report` only replaces spaces, so `"In Progress"` becomes
`In_Progress` while `"in progress"` becomes `in_progress`. Confirmed defect 7.

**Consequences.** The report must use the same normalisation as the workflow.
Any new status comparison must go through the shared helper.

**Status.** Proposed 2026-10-14. Needs Engineer A's sign-off.

## D5 — Note IDs are per ticket, not global

**Context.** Requirement B asks for note IDs `N001`, `N002`, ... and says a
rejected note must not consume an ID, and that resolve/reopen must preserve
notes.

**Decision.** `next_note_id(ticket)` returns one more than the highest existing
note ID **within that ticket**, so each ticket has its own `N001`. A rejected
note consumes nothing because the ID is derived from stored state, not from a
counter that is incremented on attempt.

**Evidence.** Requirement B: *"Use simple per-ticket note IDs N001, N002, etc.;
identify a note by its ticket ID plus note ID"* and *"A rejected note must not
consume a note ID."*

**Consequences.** Note IDs are only unique within a ticket, so any output or
lookup must pair the ticket ID with the note ID.

**Status.** Proposed 2026-10-14. Engineer A owns the implementation.

## D6 — Search is read-only and returns a new list

**Context.** Requirement C requires that search *"must not modify ticket
records"*, and the brief's Concept 3 asks for deterministic ordering.

**Decision.** `search_tickets()` is a pure function: it takes a list of ticket
dictionaries and returns a **new list** containing references to the same
dictionaries. It never asks for input, never touches the file, and never
mutates a ticket. Input order is preserved so results are deterministic.

**Evidence.** Requirement C. The same pattern is already established by
`workflow.get_work_queue`, and `tests/test_workflow.py` asserts the original
list is not reordered.

**Consequences.** Callers that need priority ordering call `sort_by_priority()`
explicitly, rather than search applying an order of its own.

**Status.** Implemented 2026-10-14 (`campusflow/search.py`, `tests/test_search.py`).

## D7 — Undecided: the `closed` status in reports

**Context.** The report prints `Closed ticket: 0`, and `tests/test_report.py`
asserts on `closed`. But `closed` is not a legal status anywhere in the
application — `workflow.VALID_STATUSES` is open / in progress / resolved — so the
line always prints zero.

**Decision.** **No decision yet.** This is either a missing feature (a fifth
status that was planned and never implemented) or leftover code from an earlier
draft. Removing it and adding it are different products, so it needs a decision
rather than a patch.

**Evidence.** Baseline input 2; `campusflow/report.py:39`; confirmed defect 3.

**Consequences.** Left alone, the report continues to display a count that can
never be non-zero, which undermines Requirement D's goal of trustworthy
insights.

**Status.** **Open.** To be decided by the team and recorded here.

## D8 — Reading the tickets must not create the store

**Context.** Requirement C specifies a read-only search view. The search menu
calls `read_ticket_file()`, which is expected to be a read.

**Decision.** A read must not write. When no store exists, the reader should
return an empty list without creating a file. Creating the store is the job of
the first save, not of a lookup.

**Evidence.** Running search in a directory with no `tickets.json` printed
"There are no tickets to search." and left a new empty `tickets.json` behind:

```text
before: campusflow  main.py
after:  campusflow  main.py  tickets.json
```

The cause is `_load_tickets` in `campusflow/__init__.py`, which creates the file
when it is missing. Search does **not** modify existing records -- verified by
hashing a fixture before and after a search run, which was byte-identical -- so
Requirement C is satisfied in the narrow sense. The side effect is still wrong.

**Consequences.** Any read path (`list`, `search`, `queue`, `report`) creates a
file as a side effect, and `tests/test_storage_integration.py:52` currently
asserts that behaviour, so the test must be changed deliberately alongside the
fix.

**Status.** **Open.** The fix belongs in the storage layer, so it needs
Engineer A.
