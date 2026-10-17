# AI Learning Log

## Fellow: [Wuese Joy Ayande] — F4 Workflow & F5 Work Queue

### Interaction #1 — Git feature branches
Problem: I needed to work on my features without changing main.
My initial understanding: I knew GitHub was where we put our code, but I thought everyone just worked on main and pushed their changes there. I wasn’t sure what a branch really was or why we needed one. I was also worried that if I pushed something wrong, I would break my teammates’ work. I didn’t know that branch names were supposed to follow a pattern or be linked to an issue number.
Prompt to AI: Asked how to create my own branch and merge to main after review.
Useful AI guidance: Create a branch from the latest main named <type>/<issue>-<description>, push it, open a PR, and merge only after approval.
My independent experiment/test: Created feat/4-workflow-and-queue, then checked the Issues page and found my issues were #2 and #5, not #4 or #6. Renamed the branch with git branch -m.
Verification source or result: Terminal prompt showed feat/2-workflow-and-queue; git log showed my commits on the branch, not main.
Decision: Improved. The AI's example issue number was wrong for our repo, so I checked GitHub and corrected it.
Related file/commit: branch feat/2-workflow-and-queue
What I can now explain without AI: A branch is my own copy of the project where I can make changes without touching main. My teammates’ work stays safe while I build my feature. The branch name should say what kind of work it is and which issue it belongs to, like feat/2-workflow-and-queue. If I name it wrong, I can rename it with git branch -m before pushing. My code only reaches main through a pull request after a teammate reviews and approves it.

### Interaction #2 — Debugging failing tests
Problem: After writing my first tests, 3 tests failed or errored.
My initial understanding: When I saw the red FAIL and ERROR messages, I thought my tests were written wrongly or that something was broken in Codespaces. I didn’t know how to read a traceback. It looked like a lot of confusing text, so I didn’t know where to start looking for the problem.
Prompt to AI: Shared a screenshot of the failing test output.
Useful AI guidance: The errors ('NoneType' object is not iterable, ValueError not raised) meant the functions in workflow.py still contained only `pass` and returned None.
My independent experiment/test: Opened workflow.py, confirmed it still held the skeleton, replaced it with the full implementation, and reran the tests.
Verification source or result: python -m unittest discover -s tests -v → Ran 13 tests, OK
Decision: Accepted after verifying with the test run.
Related file/commit: campusflow/workflow.py, tests/test_workflow.py, commit 818cc3c
What I can now explain without AI: A traceback shows where the error happened, with the file name and line number, and the last line tells me what went wrong. “‘NoneType’ object is not iterable” meant my function returned nothing. A function that only contains pass does nothing and returns None. “ValueError not raised” meant the function didn’t check the input the way the test expected. A failing test is useful because it shows me exactly what is missing.

### Interaction #3 — Sorting tickets by numeric ID
Problem: The work queue must break priority ties by the earlier ticket number.
My initial understanding: I thought sorting the ticket IDs as they are would put them in the right order, because T001, T002, T003 already look like they’re in order. I didn’t know that Python compares text letter by letter, not by the number value. I also didn’t know how to sort by two things at once (priority first, then ID).
Prompt to AI: Asked how to sort by priority and then by ticket ID.
Useful AI guidance: Use sorted() with a tuple key (priority rank, numeric ID), and convert the ID with int() instead of comparing strings.
My independent experiment/test: Ran python3 -c "print(sorted(['T999','T1000']))" and got [your output].
Verification source or result: [what the output proved]; test_queue_sorted_by_priority_then_id passes.
Decision: Accepted after the experiment showed string sorting puts T1000 before T999.
Related file/commit: campusflow/workflow.py (ticket_number, get_work_queue)
What I can now explain without AI: When Python sorts text, it compares one character at a time, so “T1000” comes before “T999” because “1” is smaller than “9”. To sort by the real number, I take off the “T” and convert the rest with int(). To sort by two things, I give sorted() a key that returns a pair, (priority rank, ticket number). Python compares the first item, and only uses the second when the first is a tie. I use sorted() instead of .sort() so the original list isn’t changed.

### Interaction #4 — Connecting the workflow to the menu and tickets.json
Problem: My team's main.py calls change_status() with no arguments, and tickets are stored in tickets.json through read_ticket_file() and update_ticket(). My functions took a tickets list instead.
My initial understanding: I thought I could just put input() and read_ticket_file() inside change_status, and everything would work together. I thought “raise ValueError” was like printing an error message, so I tried to save it in a variable and print it. I didn’t understand why one wrong choice in the menu made the whole program stop.
Prompt to AI: Asked the AI to change workflow.py to use read_ticket_file. Later shared my edited file and the terminal errors.
Useful AI guidance: The AI first suggested new functions like change_status_and_save(). That did not match how our main.py calls change_status(), so I rewrote change_status myself to use input() and read_ticket_file(). Running it showed two problems: an invalid move (open → resolved) crashed the whole program with a traceback, and `error = raise ValueError(...)` caused a SyntaxError. The AI explained that raise cannot be assigned to a variable, and that errors must be caught with try/except in the menu function. It also pointed out that my version deleted find_ticket (which reopen_ticket needs), never imported update_ticket, ignored unknown IDs, and would break all 13 tests.
My independent experiment/test: Ran python3 main.py and chose option 5 with T001 → resolved, which crashed. After the fix, the checking logic moved to apply_status_change(tickets, ticket_id, new_status), and change_status() became the menu function that asks for input, catches ValueError, and saves. I renamed the function in the tests and reran them and the menu.
Verification source or result: [test result, e.g. Ran 13 tests, OK]; python3 main.py now prints "Error: Cannot move ticket T001 from open to resolved." and the menu keeps running. [Add what happened when you assigned T001 and moved it to in_progress then resolved.]
Decision: Changed. I rejected the AI's first design because it did not fit our main.py, and my own first rewrite had bugs. The final version keeps the logic testable and separate from input and the file.
Related file/commit: campusflow/workflow.py, tests/test_workflow.py, commit [SHA]
What I can now explain without AI: raise doesn’t print anything. It stops the function immediately and sends the error up to whoever called it. If nobody catches it, the whole program crashes. That’s why the menu function uses try/except: it catches the error, prints a friendly message, and the menu keeps running. I keep the checking logic (apply_status_change) separate from input() and the file, so the tests can give it tickets directly without anyone typing. The menu function (change_status) only asks questions, calls the logic, and saves.

### Note on AI use
The AI wrote the core logic in workflow.py (apply_status_change, reopen_ticket, get_work_queue) and the tests in test_workflow.py. I rewrote change_status to fit our team's menu and storage, found two errors by running the program, and worked with the AI to fix them. I ran every test, read the failures, and checked the results myself.

## Fellow: Okoh Daniel Oche — Engineer B: Search, Reporting and CLI (issue #49)

### Interaction #1 — Turning working code into commits

Problem: My search feature, its tests and the documentation were finished and passing, but they were sitting uncommitted in the working tree. I did not know how to turn them into commits, or how many commits were expected.

My initial understanding: I thought committing meant one `git add .` followed by one message summarising everything I had done that day. I did not know that a commit carries an author, so git needs to know who I am before it will create one. I also did not realise the sprint scores the number of focused commits, so one large commit would have quietly lost marks.

Prompt to AI: "How do i commit it?" — followed by "I'm confused on what to do?", because the first answer covered more ground than I could act on at once.

Useful AI guidance: A commit records an author, so `user.name` and `user.email` must be set or git refuses outright. The sprint requires at least two focused commits per engineer, so the work should be split by idea — documentation, then feature, then tests — rather than bundled. I was also shown how to inspect the tree before staging, and told the tracked `tickets.json` must not be swept into a commit.

My independent experiment/test: In a throwaway repository I tried to commit with the identity deliberately blank, then repeated the identical commit with an identity supplied. This had nothing to do with CampusFlow — I wanted to see the rule for myself rather than take it on trust.

Verification source or result: With no identity the commit was refused: `Author identity unknown / *** Please tell me who you are.` With an identity the same command produced `[master (root-commit) d91eaab] test / 1 file changed, 1 insertion(+)`. Same repository, same file, same message — the only change was the identity. I then checked my own repository and found `user.name = Symplythatguy` and `user.email = danielbriar369@gmail.com` already set.

Decision: Accepted, and acted on. I committed in three slices — documentation, then the feature, then its tests — and confirmed with `git log --oneline` that each commit described one idea and that `tickets.json` was never staged.

Which test guards this learning: None — a commit is not testable. The guard is the history itself: `git log --oneline main..HEAD` reads as a sequence of separate decisions, and that is what a reviewer sees.

Related file/commit: 88a4e82 (docs), 2fb4395 (feat), f0a210d (test)

What I can now explain without AI: A commit is a permanent record that names its author, so git will not make one until it knows who I am — and that identity is configuration, not code. One commit should carry one idea, which is why a feature, its tests and its documentation belong in separate commits with separate messages. Splitting the work this way is not cosmetic: a reviewer reading my branch can see what changed and why, one decision at a time, and can revert one idea without disturbing the others.

### Interaction #2 — The push failed, but reading the same repository worked

Problem: `git push` failed with `fatal: could not read Username for 'https://github.com': No such device or address`, even though I had been fetching from and reading that same repository all along.

My initial understanding: I thought pushing was simply sending my commits up to GitHub. If I could read the repository, publishing to it felt like the same kind of operation, so a failure made no sense to me. I did not know that reading and writing are authorised separately, and I assumed my GitHub account password would work if I was asked for one.

Prompt to AI: How do I push this branch? — then, after the failure, what the error actually meant.

Useful AI guidance: Reading a public repository requires no credentials at all, but pushing proves identity, so it does. Git first looks for a stored credential; finding none it tries to prompt for a username, and with no terminal attached there is nobody to ask — hence "No such device or address". I was told a GitHub account password will no longer work for this, and that either a Personal Access Token or an SSH key is required. I was also told not to paste a token into the chat, because it would end up in the transcript.

My independent experiment/test: I inspected both places git can find credentials on this machine, then reproduced the failure deliberately with prompting switched off, and compared that with a read of the same remote.

Verification source or result: `git config --show-origin --get-all credential.helper` returned nothing configured. `ls ~/.ssh/id_*` found no key. Then, with prompting disabled:

```text
$ GIT_TERMINAL_PROMPT=0 git push --dry-run origin feat/49-search-and-insights
fatal: could not read Username for 'https://github.com': terminal prompts disabled

$ GIT_TERMINAL_PROMPT=0 git ls-remote --heads origin feat/49-search-and-insights
f0a210dbe59d2a249ac607ea7a5525b9e9ee23f7	refs/heads/feat/49-search-and-insights
```

The read returned the branch tip with no credentials at all, while the write could not proceed. That isolated the problem to authentication on write — not the branch, not the network, and not GitHub being down.

Decision: Changed my approach. I ran the push from my own terminal, where git can prompt, and it succeeded; `git ls-remote` now reports `f0a210d`, the same commit as my local HEAD. I recorded SSH keys as the longer-term fix so I stop re-authenticating on every push.

Which test guards this learning: None — it is environment configuration, not application behaviour. What guards it is that the branch on the remote matches my local HEAD, which I check with `git rev-parse HEAD` against `git ls-remote`.

Related file/commit: branch `feat/49-search-and-insights`, remote tip f0a210d

What I can now explain without AI: Reading and writing to a remote are authorised separately. A public repository can be cloned and fetched by anyone, which is why my reads always worked, but publishing commits has to know who is doing it. Git needs either a stored credential or a terminal it can ask, and I had neither — so the error was about proving identity, not about the code I was pushing. I also understand why the password prompt would not have helped: GitHub no longer accepts account passwords for git operations.

### Interaction #3 — The test was wrong, not the code

Problem: I added a test for acceptance case 11, asserting that report counts agree with a known fixture after one ticket is resolved and another is resolved and reopened. It errored on the first line instead of reporting a count mismatch.

My initial understanding: A test that fails means the code under test is broken. I expected the traceback to lead me to a bug in the report or the workflow, and I was ready to change the application.

Prompt to AI: I asked for a test proving the report counts follow the CURRENT status after a ticket is resolved and another is reopened.

Useful AI guidance: None of it was about the counts. The test the AI wrote built its fixture with unassigned tickets.

My independent experiment/test: Instead of editing the application, I read the traceback, then reproduced the rejection directly to see whether the behaviour was deliberate.

Verification source or result:

```text
ValueError: Ticket T001 must be assigned before status can be change.
```

Reproducing it on its own:

```text
$ python3 -c "from campusflow.workflow import apply_status_change; ..."
rejected: Ticket T001 must be assigned before its status can be changed.
status after the attempt: open
```

The application refused the change and left the ticket untouched. That is required behaviour — the sprint explicitly forbids an unassigned ticket from starting — so the code was correct and my test's fixture was not.

Decision: Rejected the AI's test as written. I changed the fixture to assign the tickets it intended to progress, and the test then passed. I did not touch the application, because there was nothing wrong with it. The traceback also exposed a typo in the user-facing message ("can be change"), which I fixed separately and pinned with its own test.

Which test guards this learning: `test_report_counts_agree_with_a_known_fixture_after_resolve_and_reopen` in tests/test_report.py, which now assigns its tickets; and `test_unassigned_ticket_cannot_start` in tests/test_workflow.py, which already covered the rule my fixture had violated.

Related file/commit: tests/test_report.py (52bcb1a), campusflow/workflow.py (28835ec)

What I can now explain without AI: A failing test is evidence, not a verdict. It tells me that my expectation and the code disagree — not which of the two is wrong. Here the traceback named a rule that the sprint requires on purpose, so the disagreement was in my fixture. Reading the failure before editing the code is what stopped me from "fixing" correct behaviour and breaking a requirement. It also turned up a real defect that the test had been standing on top of.

### Note on AI use

The AI wrote the first draft of the search, report and understanding-check code and their tests, and drafted this log from evidence recorded during the session. I ran every command quoted above myself, read the output, chose the decision in each cycle, and corrected the parts that did not match what I actually thought or did. The decisions recorded as changed or rejected — the push approach in Interaction #2 and the test fixture in Interaction #3 — were rejected after reading evidence, not assumed.