# Peer Review — Engineer A (ticket notes, storage and users)

Written by Engineer B (Okoh Daniel Oche). This is the reciprocal review the
sprint brief asks for in section 08.

| | |
| --- | --- |
| Reviewer | Engineer B — Okoh Daniel Oche |
| Author reviewed | Engineer A — Timothy Ododo (ticket safety and storage) |
| PRs reviewed | #51 `feat/ticket_notes` (merged `3f64a78`), #53 `feat/users` (merged `9615afc`) |
| Review date | 2026-10-15 |
| Suite at review time | 58 tests, OK |

## 1. What I read and ran

Read in full: `campusflow/notes.py`, the `notes` changes to
`campusflow/create_tickets.py` and `campusflow/__init__.py` from PR #51,
`campusflow/auth.py` from PR #53, and `tests/test_notes.py`.

Ran:

```bash
python3 -m unittest discover -s tests        # 58 tests, OK
python3 -m unittest discover -s tests -p 'test_notes.py'   # 14 tests, OK
```

Every observation below was reproduced by running the code, not by reading it
alone. The probes ran against a scratch copy of the repository; the tracked
`tickets.json` was never written.

## 2. What is good, and I want it kept

- **`add_and_save_note` checks its own result.** `notes.py:157-161` calls
  `update_ticket`, compares the result string, and raises rather than letting a
  silent failure through. That is the brief's *"failed operations must not
  silently change data"* taken seriously, and `test_add_and_save_note_reports_persistence_failure`
  locks it in.
- **`_ticket_value` and `_note_value` accept both a `Ticket` object and a stored
  dict** (`notes.py:29-49`). This is a real accommodation for the CLI, which
  works with the dictionaries that come out of `read_ticket_file()`.
- **Role and visibility are separated properly.** `get_visible_notes` raising
  `PermissionError` for an unknown role, and `internal` notes being refused to a
  `student_fellow`, are both correct and both tested.
- **`Note.created_at` is timezone-aware UTC** with `timespec="seconds"`
  (`notes.py:14-16`). Storing naive local time would have been the easy mistake.
- The refactor commits (`4ddfec7`, `bb260f9`, `c22660b`) removed unused imports
  before merging. Small thing, but it means the diff I read had no dead weight.

## 3. Observations

Ordered by severity. Each one names a file, quotes the behaviour, and gives the
reproduction.

### O1 — `add_ticket_note` does not validate the author label (blocking)

Requirement B: *"The author label cannot be blank."* `notes.py:65-119` validates
the role, the message, the visibility and the status, but never `author`. A
blank or missing author is accepted and stored as-is.

```python
add_ticket_note(ticket, "", "support_staff", "A valid message")
# -> accepted, stored note has "author": ""
add_ticket_note(ticket, None, "support_staff", "A valid message")
# -> accepted, stored note has "author": None
```

The dict-author path at `notes.py:69-74` is the hole: `author.get("name") or
author.get("username")` yields `None` when a user record carries neither key,
and nothing downstream checks it.

B's evidence for this: `campusflow/notes_menu.py` has to apply the rule in
`validate_note_text` before calling into `notes.py`, because the data layer does
not. Section 04 gives note data validation to Engineer A, so the rule belongs in
`notes.py` and the CLI check is a second line of defence, not the first.

### O2 — the 5–300 character message rule is not implemented (blocking)

Requirement B: *"Message length must be 5-300 characters after trimming."*
`notes.py:90-91` rejects only a message that is not a string or is blank after
trimming. Both ends of the range are unbounded:

```python
add_ticket_note(ticket, "Ada", "support_staff", "abcd")        # 4 chars -> accepted
add_ticket_note(ticket, "Ada", "support_staff", "x" * 301)     # 301 chars -> accepted
```

Same resolution as O1: the bound belongs in `notes.py` alongside the empty check
it already has, three lines below it.

### O3 — a failed save leaves the note in memory (blocking)

Requirement A: *"Invalid create, assignment, status or note actions must leave
the entire ticket collection unchanged."*

`add_ticket_note` appends to the ticket at `notes.py:117`. `add_and_save_note`
calls it *first* and only afterwards tries to persist (`notes.py:147-163`). When
the save fails it raises — but the in-memory ticket has already changed:

```python
ticket = {"id": "T999", ..., "status": "open"}
try:
    add_and_save_note(ticket, "Ada", "support_staff", "This should not persist")
except TicketValidationError as exc:
    print(exc)          # Unable to save notes for ticket T999.
print(ticket["notes"])  # [{'id': 'N001', ..., 'message': 'This should not persist'}]
```

The store is unchanged, so a restart clears it — but for the rest of the session
the ticket carries a note that was reported as failed.

`test_add_and_save_note_reports_persistence_failure` asserts the exception and
stops there. Adding `self.assertEqual(ticket["notes"], [])` after the
`assertRaisesRegex` block fails against the current code, which is the cleanest
way to show the gap.

### O4 — a read mutates the ticket it reads (non-blocking, worth fixing)

`_ticket_notes` (`notes.py:36-43`) uses `ticket.setdefault("notes", [])`, so any
function that reaches it adds the key. That includes `get_visible_notes`, which
is a display path:

```python
ticket = {...}                          # no "notes" key
"notes" in ticket                       # False
get_visible_notes(ticket, "student_fellow")
"notes" in ticket                       # True  <- a read changed the record
```

It is convenient and harmless in the normal flow, but it means "just show me the
notes" and "the record changed" are no longer distinguishable. A `ticket.get("notes", [])`
read plus an explicit initialisation at write time would keep the two apart.

### O5 — the stored note key is `id`, not `note_id`

Section 03 says notes are identified by *"its ticket ID plus note ID"*. The
serialised note uses `id` (`notes.py:18-26`):

```json
{"id": "N001", "author": "Ada", "role": "support_staff", "message": "hi", "visibility": "shared", "created_at": "..."}
```

Inside the same JSON object the ticket already has its own `id`, so a stored
ticket now contains two different things both called `id`, one level apart.
`"note_id"` would read unambiguously. This is a rename before the format is
relied on, not a redesign — worth deciding now, while there is one writer.

Related: section 04 names the suggested helper `next_note_id(ticket)`, and the
implementation is `generate_note_id(ticket)`.

### O6 — the third positional argument is `role`, not `message`

Section 04 suggests `add_note(ticket_id, author, message)`. The implementation
is `add_ticket_note(ticket, author, role=None, message=None, visibility="shared")`
(`notes.py:65`), so calling it the obvious way misfires:

```python
add_ticket_note(ticket, "Ada", "Replaced the access point")
# TicketValidationError: Invalid user role.
```

`role` also defaults to `None`, which is never valid, so omitting it always
raises. The `if message is None: message = role` line at `notes.py:70-71` looks
like it exists to support the older call shape and quietly makes the two
positions interchangeable in one branch only. B's menu always passes all four
arguments by keyword, so this has not bitten yet, but it is the signature most
likely to be called wrongly from outside.

### O7 — `get_visible_notes` returns a shallow copy

`notes.py:138` returns `notes.copy()`, which copies the list and not the note
dictionaries inside it:

```python
visible = get_visible_notes(ticket, "support_staff")
visible[0]["message"] = "EDITED THROUGH THE RETURNED LIST"
ticket["notes"][0]["message"]   # 'EDITED THROUGH THE RETURNED LIST'
```

A caller holding the "read-only" result can rewrite the ticket. Low impact
today, because the only caller prints; worth a comment or a deep copy if any
caller will ever format or annotate a note.

### O8 — `campusflow/auth.py` is out of scope for this exercise

Not a code defect, and not part of PR #51, so I have not touched it. Section 01
lists what must not be introduced: *"Do not introduce Django, React, external
databases, web APIs, **authentication systems**, cloud infrastructure or paid AI
integrations."* PR #53 adds `campusflow/auth.py` (registration and login),
`tests/test_auth.py` and a tracked `users.json`.

Raising it rather than acting on it, because deleting another engineer's merged
work is not a review action. It needs a decision by the mentor: either the
brief's boundary is narrower than it reads, or the module needs to be moved out
of the sprint deliverable.

## 4. What I did about the review

I did not patch another engineer's module. O1 and O2 are applied on the CLI
side, in `validate_note_text` in `campusflow/notes_menu.py`, before the store is
touched, and O5, O6 and the fixed-role decision are recorded in
`docs/design-decisions.md` as D11. O3 and O4 are open in `notes.py` and are
Engineer A's call.

## 5. Approval status — recorded honestly

The brief's gate is *"record approval BEFORE merge"*, with branch protection
setting main to require PR approval.

I could not meet that gate for these PRs. PR #51 and PR #53 were both reviewed
and merged into `main` before this review was written; there was no open pull
request for me to approve, request changes on, or block. So this document is a
post-merge review: the observations are real and reproduced, but they arrived
after the code they describe was already on `main`.

Recording it rather than dressing it up, because the difference matters for
issue #49's submission: the review evidence exists, the approval-before-merge
gate did not happen. The right fix is branch protection plus a standing
agreement that neither engineer merges the other's PR — I would rather state
that plainly than let a review document imply a gate that was not in place.
