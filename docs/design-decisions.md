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

**Status.** Partly implemented 2026-10-14. `campusflow/report.py` now calls
`workflow.normalise_status` instead of its own `replace(" ", "_")`, so a reported
status matches the stored one. Promoting the spelling to a single shared
constant still needs Engineer A's sign-off.

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

## D7 — The `closed` status is removed from reports

**Context.** The report printed `Closed ticket: 0`, and `tests/test_report.py`
asserted on `closed`. But `closed` is not a legal status anywhere in the
application — `workflow.VALID_STATUSES` is open / in progress / resolved — so the
line always prints zero.

**Decision.** **Removed.** `closed` is not in `VALID_STATUSES`, no transition
produces it, and no validator accepts it, so the line was structurally incapable
of printing anything except zero. The brief's lifecycle is
`open -> in progress -> resolved`, which leaves no room for a fifth state.
Removing it and implementing it are different products, and there is no evidence
for the latter.

**Evidence.** Baseline input 2; `campusflow/report.py:39`; confirmed defect 3.

**Consequences.** The breakdown is now driven by `VALID_STATUSES` rather than by
three hardcoded lines, so this class of defect cannot recur. The `closed` line
and the assertion in `tests/test_report.py` are deleted rather than left in
place. Removing the line also exposed a second defect in the same block: the
breakdown counted `open`, `in progress` and `closed`, so **`resolved` tickets
were counted nowhere** — they appeared in the total and then vanished from the
status counts. That is fixed in the same change.

**Status.** Decided and implemented 2026-10-14 (`campusflow/report.py`,
`tests/test_report.py`).

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

## D9 — The printed report and the structured report are one result

**Context.** `report.py` built a structured result in `_build_ticket_report`,
but the printing path did not use it: it recomputed every count inline with its
own `len([ticket for ticket in ...])` comprehensions. Two independent
calculations over the same data, in the same module.

**Decision.** Build once, format once. `_build_ticket_report()` produces the
only report dictionary; `_format_report()` renders that dictionary and counts
nothing. Requirement D's figures exist in exactly one place.

**Evidence.** At baseline the two paths already disagreed:
`_build_ticket_report` produced the key `in_progress` (via
`status.replace(" ", "_")`), while the printed block tested for both
`in progress` and `in_progress` and separately counted `closed`. A caller and an
operator could therefore read different figures from the same data.

**Consequences.** Adding a figure means adding it to one dictionary. The printer
cannot invent a number or omit one, and a test asserting on the returned
dictionary is asserting on what the CLI prints.

**Status.** Implemented 2026-10-14 (`campusflow/report.py`).

## D10 — Category counts are matched case-insensitively

**Context.** `create_tickets.raise_ticket` applies `.lower()` to urgency but not
to category, so the category is stored exactly as the operator typed it:
`Network`, `network` and `NETWORK` are three different stored strings for one
category. The validator accepts all of them. A count keyed on the stored string
would therefore split one category into three rows.

**Decision.** Group categories on a case-folded, stripped key. The four legal
categories are emitted in a fixed order including zeros, so the section has the
same shape for every dataset. Priority and status keys are folded the same way
for consistency.

**Evidence.** `campusflow/create_tickets.py:50` reads the category with no
normalisation, unlike line 51 for urgency. Verified end to end: a fixture
containing `"category": "Network"` and `"category": "network"` reports
`Network: 2`, not two rows of `1`.

**Consequences.** The bucket keys are lowercase, so output is title-cased for
display. An unrecognised category still gets its own row rather than being
dropped, which keeps the section's rows adding up to the ticket total. The
underlying storage inconsistency is left alone — normalising on write is
Engineer A's call, and changing what is stored is a separate decision.

**Status.** Implemented 2026-10-14 (`campusflow/report.py`).

## D11 — The notes menu adapts to the API that exists, and shows every note

**Context.** Requirement B describes a note as `{note_id, author, message}` and
§04 says Engineer A will expose `add_note(ticket_id, author, message)`. What
landed in #51 is different in shape: `notes.add_ticket_note(ticket, author,
role=None, message=None, visibility="shared")` takes the ticket dictionary
rather than an ID, and requires a `role` drawn from a fixed set. The stored note
carries `id` (not `note_id`) alongside `role`, `visibility` and `created_at`.
The CLI has to bridge that gap rather than assume the shape the contract
describes.

**Decision.** Three parts.

1. The menu passes a fixed `OPERATOR_ROLE = "support_staff"` and the default
   `shared` visibility instead of prompting for them. This application has no
   login, so there is no honest role to collect, and a prompt would ask the
   operator a question the system cannot check the answer to.
2. Option 10 prints **every** note, including `internal` ones, and does not call
   `get_visible_notes`. Requirement B asks that the user "read all notes for a
   ticket in ID order"; with no login there is no role to filter by, and
   filtering on a role nobody supplied would hide notes arbitrarily.
3. The blank-author rule and the 5-300 character rule live in
   `notes_menu.validate_note_text`, which runs before the store is touched,
   because `notes.add_ticket_note` checks neither.

**Evidence.** `campusflow/notes.py:65` shows the signature and `:87` the role
set the CLI must satisfy. `:90` rejects a blank message but sets no length
bound, and `author` is used to build the note without ever being validated, so
both of Requirement B's input rules would go unenforced if the CLI did not add
them. `campusflow/notes.py:52` computes the next ID with
`max(existing, default=0) + 1`, and it is called only when the note object is
constructed, which is after every check — so a rejected note consumes no ID.
Verified end to end in a scratch copy of the repository: a store holding `N001`
rejects a short message, and the next accepted note is `N002`, not `N003`.

**Consequences.** The 5-300 rule and the blank-author rule are enforced in the
CLI rather than in the note model, so a caller that skips the menu can still
store a one-character note. Requirement B is satisfied for the CLI, which is
what it asks for, but the rule belongs in the model. This and the `id` versus
`note_id` naming are recorded as review observations for Engineer A rather than
patched here, because `notes.py` is A's module.

**Status.** Implemented 2026-10-15 (`campusflow/notes_menu.py`).
