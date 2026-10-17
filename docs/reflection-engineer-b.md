# Reflection — Engineer B

Okoh Daniel Oche. CampusFlow Next, issue #49, 2026-10-15.

One verified mistake, one learning gain, and one improvement received through
code review, as section 11 asks for.

## One verified mistake

**I submitted three features in one pull request.** The search view, the
Engineering Understanding Check and the notes CLI were built on a single branch
and raised together. Nothing was broken — the tests were green and the
application worked. The mistake was in the delivery, and I did not see it; the
reviewer did.

The evidence is the two things that exist side by side: one branch,
`feat/49-search-and-insights`, with one pull request covering all three
features; and the same code split into `feat/49-search`,
`feat/49-understanding-check` and `feat/49-notes-cli`, three PRs, no overlap.
The cost was concrete rather than theoretical. A reviewer could not accept the
search work without also accepting the quiz and the note menus, the README had
to describe all three at once, and a problem in any one of them would have
blocked the other two.

I had a habit of treating a green test suite as the finish line. It is not the
finish line; the change has to be reviewable, and three changes are not one
change.

## One learning gain

**A passing test suite says nothing about a rule nobody tested.** This is the
thing I would not have believed before this sprint.

`campusflow/notes.py` arrives with 14 passing tests, including a
persistence-failure test and a resolved-ticket rejection test. Reading them, I
assumed Requirement B's input rules were covered. They are not. Requirement B
says the author label cannot be blank and the message must be 5–300 characters
after trimming; the module checks neither, and I reproduced both:

```text
add_ticket_note(ticket, "", "support_staff", "A valid message")   -> accepted
add_ticket_note(ticket, "Ada", "support_staff", "abcd")           -> accepted
add_ticket_note(ticket, "Ada", "support_staff", "x" * 301)        -> accepted
```

Fourteen green tests, two unenforced rules, no contradiction anywhere. What I
took from it is a habit I now use on my own work: when I read a test suite, I
list the rules the requirement states and check which of them no test names.
Coverage was the wrong question. "Which rule has nothing standing behind it?"
is the right one.

The same lesson had a second half. A rejected action has to leave the record
untouched, and the honest way to check that is to compare the store before and
after rather than assert that an error was raised. I verified the search view
that way — hashing `tickets.json` before and after a full search — and that is
now the check I reach for first.

## One improvement received through code review

**Split the work, and let each pull request stand on its own.**

The review of the combined PR said the documentation, search and understanding
check had all gone into one branch, and asked for individual branches and
separate pull requests. That is now what exists: four branches, four PRs, each
one runnable and testable by itself.

What I did not expect was how much the split would force me to articulate. On
the combined branch it was enough that the code worked. On four branches, each
PR has to justify itself alone — what it changes, why, which tests prove it, and
what it depends on — and that is where I found the parts I had not really
thought through. The menu option numbers are local to each branch and have to be
reconciled at merge, which is a real cost of the split, and one I would pay
again.

The concrete result: 77, 72, 82 and 88 tests passing on the four branches
against a 58-test baseline, each suite run from the branch on its own.
