# Defence Prep — Engineer B

Okoh Daniel Oche. A self-test sheet, not a submission document.

Each question below is followed by **the evidence to have open** while you
answer: the file, the line, and the test that holds the proof. The answers are
deliberately not written here — you have to say them, and the defence is
testing whether you can.

Line numbers are checked against `feat/49-reporting` and the three feature
branches as of 2026-10-15. If a number has drifted, search by the function
name.

---

## Part 1 — Section 04, questions for Engineer B

### 1. Why should search not edit the collection?

| | |
| --- | --- |
| Brief | Section 03, Requirement C — *"Search must not modify ticket records."* |
| Code | [campusflow/search.py:45-73](../campusflow/search.py#L45-L73) |
| Tests | `test_search_does_not_modify_the_collection` ([tests/test_search.py:84](../tests/test_search.py#L84)), `test_search_returns_a_new_list` (:89), `test_search_preserves_input_order` (:95) |
| Live proof | Hash `tickets.json`, run option 8, hash it again |

Be ready for the follow-up: what is the difference between *not changing the
list* and *not changing the tickets inside it*? (The returned list holds the
same dictionaries.)

### 2. When combining filters, should you use AND or OR?

| | |
| --- | --- |
| Brief | Section 03, Requirement C — *"If supplied, ALL must match."* |
| Code | [campusflow/search.py:63-73](../campusflow/search.py#L63-L73) |
| Tests | `test_all_supplied_filters_must_match` (:44), `test_a_mismatched_filter_excludes_the_ticket` (:49), `test_blank_filters_do_not_filter_anything` (:54) |

Also be ready for: what does a **blank** filter mean, and how is that different
from a filter that matches nothing?

### 3. Why does an empty report need special handling?

| | |
| --- | --- |
| Brief | Section 03, Requirement D — *"An empty dataset must report 0% without division errors."* |
| Code | [campusflow/report.py:63-93](../campusflow/report.py#L63-L93) (the resolution percentage), :130 (the menu entry) |
| Tests | `test_empty_report_reports_zero_percent_without_dividing_by_zero` (:34), `test_generating_a_tickets_report_with_no_tickets_returns_empty_report` (:28) |
| Live proof | Run option 7 against a store containing `[]` |

### 4. How does an `in progress` ticket affect the unresolved count?

| | |
| --- | --- |
| Brief | Section 03, Requirement D — unresolved = `open + in_progress` |
| Code | [campusflow/report.py:26](../campusflow/report.py#L26) (`UNRESOLVED_STATUSES`) |
| Tests | `test_tickets_report_counts_unresolved_as_open_plus_in_progress` (:123), `test_reopened_ticket_is_counted_under_its_current_status` (:113) |

The second test is the one worth knowing. A reopened ticket is counted by its
**current** status, so resolving and reopening a ticket must leave the totals
where they started.

### 5. Why is a resolved ticket forbidden from receiving new notes?

| | |
| --- | --- |
| Brief | Section 03 — *"A resolved ticket cannot accept notes or assignment changes unless it is reopened."* |
| Code | [campusflow/notes.py:82-85](../campusflow/notes.py#L82-L85) (Engineer A's guard), [campusflow/notes_menu.py:64](../campusflow/notes_menu.py#L64) (`require_noteable`) |
| Tests | `test_resolved_ticket_is_rejected_with_reopen_guidance` (:98), `test_note_on_a_resolved_ticket_is_rejected` (:200), `test_open_add_resolve_reject_reopen_add` (:274) |
| Status | The last test runs the brief's own worked example with nothing mocked |

### 6. How do you test CLI behaviour without repeatedly typing manually?

| | |
| --- | --- |
| Mechanism | `unittest.mock.patch` on `builtins.input`, plus patching the function `main.py` calls |
| Tests | [tests/test_cli_integration.py](../tests/test_cli_integration.py) — every menu option; the menu tests at [tests/test_search.py](../tests/test_search.py), [tests/test_notes_menu.py:167+](../tests/test_notes_menu.py#L167), [tests/test_understanding_check.py:144+](../tests/test_understanding_check.py#L144) |
| Strongest example | `test_scoring_never_asks_for_input` ([tests/test_understanding_check.py:116](../tests/test_understanding_check.py#L116)) patches `input` to **raise**, so the test fails if scoring ever reaches the interactive path |

Two layers, and be ready to say which is which: patching `builtins.input` tests
the *dialogue*; patching the function `main.py` calls tests the *routing*.

### 7. Which change from your partner's PR review improved your work?

| | |
| --- | --- |
| Evidence | [docs/peer-review-engineer-a.md](peer-review-engineer-a.md) (the review you wrote), [docs/design-decisions.md](design-decisions.md) D11 |
| What changed in your code | `validate_note_text` exists because reading `notes.py` showed the data layer enforces neither of Requirement B's input rules |
| Honest gap | **No review of your work has happened yet.** #51 and #53 were merged before you could review them, so neither the approval-before-merge gate nor a review of your PR is on record |

Do not paper over that last row. Say it, then say what you would do about it
(branch protection, and an agreement that neither engineer merges the other's
PR).

---

## Part 2 — Section 09, live defence prompts

Each engineer answers these independently. Same format.

### 1. What important invariant can your function guarantee?

Pick two, not five.

| Function | Invariant | Evidence |
| --- | --- | --- |
| `search_tickets` | returns a new list and changes neither the input list nor its order | [search.py:45](../campusflow/search.py#L45), tests :84, :89, :95 |
| `score_answers` | the same answers always give the same score, and it never asks for input | [understanding_check.py:131](../campusflow/understanding_check.py#L131), test :116 |
| `validate_note_text` | returns trimmed values or raises, before anything is written | [notes_menu.py:38](../campusflow/notes_menu.py#L38), tests :184, :192 |

### 2. Which test failed before you corrected a bug?

| | |
| --- | --- |
| Learning log | [docs/ai-learning-log.md](ai-learning-log.md) — the cycle where the test was wrong, not the code |
| Still-unfixed defect | `test_numeric_string_count_is_not_rejected_by_validation` ([tests/test_bug_hunter.py:26](../tests/test_bug_hunter.py#L26)) carries `@unittest.expectedFailure` |
| Why it is there | The suite stays green while the gap stays visible. Be ready to explain why you did not fix it, and who owns the module |

### 3. How does your code avoid modifying state on a rejected action?

| | |
| --- | --- |
| Code | `add_follow_up_note` validates **before** it calls into `notes.py` — [notes_menu.py:116-139](../campusflow/notes_menu.py#L116-L139) |
| Tests | `test_rejected_note_does_not_consume_a_note_id` (:215), `test_blank_author_is_rejected_and_nothing_is_stored` (:184), `test_short_message_is_rejected_and_nothing_is_stored` (:192) |
| Live proof | Hash the store, add a 3-character note, hash again |

Be ready for the hard version: is the *ticket* unchanged too, not just the file?
That is observation O3 in your review of Timothy's code — `add_and_save_note`
appends to the ticket in memory before it tries to save.

### 4. Demonstrate what happens when JSON loads duplicate IDs.

| | |
| --- | --- |
| Code | [campusflow/__init__.py:7-18](../campusflow/__init__.py#L7-L18) — `_load_tickets` returns the raw `json.load` |
| Whose | Engineer A's, Requirement E / milestone A5 |
| Your own record | [docs/baseline-check.md](baseline-check.md) section 3 |
| Prep a fixture | Two tickets both with `"id": "T001"`, different titles and priorities |

Load that fixture, then run option 2 and option 3. Say what you see, including
that nothing rejects it. **You are not expected to have fixed this** — it is
A's module. What you are expected to do is say who owns it and what the brief
requires, without claiming it works.

### 5. Why do multiple filters use logical AND?

| | |
| --- | --- |
| Brief | Section 03, Requirement C |
| Code | [campusflow/search.py:63-73](../campusflow/search.py#L63-L73) |
| Tests | tests/test_search.py:44, :49 |

The same question as Part 1 number 2. Have a second example ready: the unknown
quiz answer in the bank, Q3, tests the identical rule.

### 6. How did you check an AI recommendation?

| | |
| --- | --- |
| Learning log | [docs/ai-learning-log.md](ai-learning-log.md) — all cycles record the experiment or the result |
| Concrete cases | the casefold string-sort experiment; the notes.py probes behind [docs/peer-review-engineer-a.md](peer-review-engineer-a.md) section 3; hashing `tickets.json` to prove search is read-only |
| The line to have ready | Never by reading the code alone — every claim in that review was reproduced by running it |

### 7. Show your PR and a substantive review you gave your partner.

| | |
| --- | --- |
| Your PR | the `feat/49-reporting` pull request (or whichever is open) |
| Your review | [docs/peer-review-engineer-a.md](peer-review-engineer-a.md) |
| A review comment that is not "LGTM" | O1, O2 and O3 each name a file, quote the behaviour and give the reproduction |

Be ready for the question "which of your partner's PRs did you approve before
merge?" — the answer is none, and section 5 of that document says so.

### 8. If the mentor changes one business rule, identify the function and test to update.

Read the rule from the table, then name the constant and the tests in one
breath. This is the table to memorise.

| If the rule changes | Change this | These tests move with it |
| --- | --- | --- |
| Note message must be 5–300 | `NOTE_MIN_LENGTH`, `NOTE_MAX_LENGTH` — [notes_menu.py:21-22](../campusflow/notes_menu.py#L21-L22) | test_notes_menu.py:54, :59, :65, :70, :74 |
| Only open / in progress accept notes | `NOTEABLE_STATUSES` — [notes_menu.py:25](../campusflow/notes_menu.py#L25) | test_notes_menu.py:91, :98, :104 |
| Unresolved means open + in progress | `UNRESOLVED_STATUSES` — [report.py:26](../campusflow/report.py#L26) | test_report.py:123, :113 |
| Filters combine with AND | the guard chain — [search.py:63-73](../campusflow/search.py#L63-L73) | test_search.py:44, :49 |
| The quiz bank or its answer key | `QUESTIONS` — [understanding_check.py](../campusflow/understanding_check.py) | test_understanding_check.py:45, :54, :60 |
| Exit moves to another menu number | [main.py](../main.py) and every test in [tests/test_cli_integration.py](../tests/test_cli_integration.py) | all of them |

---

## Part 3 — Have ready before you start

```bash
git branch --show-current                        # know which branch you are on
python3 -m unittest discover -s tests            # 77 / 72 / 82 / 88 depending on branch
python3 -m compileall -q .
```

- A scratch copy with a four-ticket fixture (one per status), so the
  demonstration never touches the tracked `tickets.json`.
- The duplicate-ID fixture for prompt 4.
- `docs/baseline-check.md` open — the baseline numbers come from there.
- Know the count on the branch you are standing on. The four suites are 77, 72,
  82 and 88; the pre-sprint baseline is 58.

## Part 4 — Section 05, the quiz

You take it live, on your own: once running it, once explaining two answers
from your own code. Rehearse these two, because both are in the bank and both
have a file behind them:

- **Q3** (which records match) — [search.py:63-73](../campusflow/search.py#L63-L73),
  `test_a_mismatched_filter_excludes_the_ticket`.
- **Q4** (a resolved ticket receives a note) — [notes.py:82-85](../campusflow/notes.py#L82-L85),
  `require_noteable` at [notes_menu.py:64](../campusflow/notes_menu.py#L64), and
  `test_open_add_resolve_reject_reopen_add`.

The check prints your explanations at the end, so whatever you type during the
demo is what gets discussed.
