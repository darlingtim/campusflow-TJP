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