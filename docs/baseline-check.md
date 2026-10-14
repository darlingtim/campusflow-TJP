# Baseline Check

What the existing CampusFlow does **before** any CampusFlow Next changes.
Every claim below was reproduced by running the code at the audited commit.

| | |
| --- | --- |
| Date recorded | 2026-10-14 |
| Repository | https://github.com/darlingtim/campusflow-TJP |
| Audited commit | `0d5493e997ee130dde83950dc8e7459513e2f485` (Merge PR #47) |
| Branch | `main` |
| Environment | Python 3.12.3, Linux |

## 1. Command and result

```bash
python3 -m unittest discover -s tests -v
```

```text
Ran 39 tests in 0.023s

OK
```

**Result: 39 passed, 0 failed, 0 errors.** The suite is green at the audited
commit, so any test that fails after this point is a regression introduced by
this sprint, not pre-existing breakage.

Two environment notes:

- `python` is not on `PATH` on this machine; the interpreter is `python3`.
  The sprint brief specifies `python -m unittest discover -s tests -v`.
- `README.md` states Python 3.11 is supported, but the CI matrix
  (`.github/workflows/tests.yml`) tests only 3.12 and 3.13, and
  `campusflow/assign.py:17` uses nested same-type quotes inside an f-string,
  which requires Python 3.12 (PEP 701). **The README overstates support.**

The suite also prints application output to stdout during the run
(`Ticket T001 has been assigned to Ada.`), because several tests do not
capture `print`. This makes a failing run harder to read but does not affect
pass/fail.

## 2. Inputs tested

Each input was run against a fixed four-ticket fixture in a scratch copy of the
repository, so the tracked `tickets.json` was never modified. The fixture
covered one ticket per status and two priorities:

```json
[
  {"id":"T001","title":"Wi-Fi router reboot","category":"Network","urgency":"medium","affected_users":"12","priority":"high","status":"open","assigned_to":null},
  {"id":"T002","title":"Laptop battery","category":"Hardware","urgency":"low","affected_users":1,"priority":"low","status":"in progress","assigned_to":"Ada"},
  {"id":"T003","title":"Software install","category":"Software","urgency":"high","affected_users":8,"priority":"high","status":"resolved","assigned_to":"Ada"},
  {"id":"T004","title":"Projector dead","category":"Hardware","urgency":"high","affected_users":12,"priority":"critical","status":"open","assigned_to":null}
]
```

### Input 1 — menu option 5 (work queue)

```bash
printf '5\n8\n' | python3 main.py
```

Observed:

```text
Work queue (most urgent first):
  T004  critical  open         unassigned    Projector dead
  T001  high      open         unassigned    Wi-Fi router reboot
  T002  low       in progress  Ada           Laptop battery
```

**Confirmed.** Priority ordering is correct (critical > high > low, ties by
ticket number) and the resolved ticket T003 is excluded. However, the
`in progress` ticket T002 **is** listed. The sprint brief states the original
Open Work Queue must show only `open` tickets and that an `in progress` ticket
must not appear. The queue filter in `campusflow/workflow.py`
(`QUEUE_STATUSES = {"open", "in progress"}`) therefore contradicts the brief.

### Input 2 — menu option 7 (report)

```bash
printf '7\n8\n' | python3 main.py
```

Observed:

```text
Ticket Report Generated.
---------------------
Total tickets:  4
=======================
Tickets By Status:
---------------------
Open ticket:  2
Tickets in Progress:  1
Closed ticket:  0
==============================
Tickets By Priority:
------------------------------
Critical priority:  1
High priority:  2
Medium priority:  0
Low priority:  1
==============================
```

**Confirmed.** Totals-by-priority are correct. Three gaps against the brief's
quality-insight requirements: there is **no breakdown by category**, no
unresolved count, and no resolution percentage. `Closed ticket: 0` is
**always 0** — `closed` is not a legal status anywhere in the application
(`VALID_STATUSES` in `workflow.py` is open / in progress / resolved), so the
line reports a state the program cannot produce. `tests/test_report.py`
also asserts on `closed`, so the test locks the dead value in.

### Input 3 — menu option 6, unassigned open ticket to `in progress`

```bash
printf '6\nT001\nin progress\n8\n' | python3 main.py
```

Observed:

```text
Please enter the ticket ID: Please enter the new status (open, in progress, resolved): Error: Ticket T001 must be assigned before status can be change.
```

**Confirmed, and this is correct behaviour to preserve.** The move is rejected,
the menu keeps running rather than crashing, and the fixture file is
byte-identical afterwards — so the "rejected action changes nothing" invariant
already holds on this path. The message contains a grammar error
("before status can be change") that should be corrected without changing the
rule.

## 3. Confirmed defects

Reproduced above, or by inspection of the code at the audited commit.

| # | Defect | Evidence |
| --- | --- | --- |
| 1 | Work queue includes `in progress` tickets, contrary to the brief | Input 1 |
| 2 | Report has no category breakdown, unresolved count, or resolution % | Input 2 |
| 3 | Report counts a non-existent `closed` status | Input 2; `report.py:39` |
| 4 | `README.md` claims 38 tests; there are 39 | §1 |
| 5 | `README.md` claims Python 3.11 support; code requires 3.12+ | §1; `assign.py:17` |
| 6 | `affected_users` is stored as a string (`"12"`) in `tickets.json` | fixture; `tickets.json:7` |
| 7 | Status normalisation is inconsistent: `workflow.normalise_status` lowercases, `report._build_ticket_report` only replaces spaces | `report.py:9` |
| 8 | "Find ticket by ID" has three implementations with different rules — `workflow.find_ticket` strips and upper-cases, `assign.py` and `list_view.py` match exactly, so `t001` behaves differently by menu option | `workflow.py:34`, `assign.py:12`, `list_view.py:13` |
| 9 | `save_ticket` is annotated `-> str` but returns `None` | `__init__.py:19` |
| 10 | `raise_ticket` catches bare `Exception` and prints, so a failed save never reaches the error handling in `main.py` | `create_tickets.py:72` |
| 11 | Assignment has no status guard; a `resolved` ticket can be assigned | `assign.py` |
| 12 | `./tickets.json` is hard-coded in three places and resolved against the process working directory, which is why tests must `os.chdir()` | `__init__.py:21,30,48`; `tests/test_storage_integration.py:19` |
| 13 | Menu labels in `main.py` do not match the README table, and option 5 has a double space (`"5. view  ticket queue "`) | `main.py:12` |

Additionally, `docs/design-decisions.md` is empty and `docs/ai-learning-log.md`
still contains unfilled placeholders (`[your output]`, `[what the output
proved]`) and a branch-name mismatch (`#4-workflow` in the heading versus
`feat/2-workflow-and-queue` in the body).

## 4. Decisions taken

**Work queue status filter.** The brief is explicit that the original Open Work
Queue must contain only `open` tickets and that `in progress` must not appear.
The current code includes `in progress`. We are following the brief: the queue
becomes `open`-only, and this deviation from the previous behaviour is recorded
in `README.md` and `docs/design-decisions.md` rather than changed silently.
See defect 1.

**Note on `closed`.** No decision yet on defect 3 — it is either a missing
feature or leftover code. It needs a decision, not a patch.

## 5. Audit observations

> **TO BE COMPLETED by the team.** The brief requires recording *what the audit
> said needed improvement*. Paste the audit's observations here verbatim, then
> mark each one as reproduced or not yet reproduced.
>
> Per the brief: *"Do not label a peer-reported bug as confirmed until you
> reproduce it."* Nothing in section 3 above is from the audit — every item was
> reproduced independently.
