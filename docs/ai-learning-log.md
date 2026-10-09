# AI Learning Log

## Fellow: [Your Name] — F4 Workflow & F5 Work Queue

### Interaction #1 — Git feature branches
Problem: I needed to work on my features without changing main.
My initial understanding: [what you knew about branches before]
Prompt to AI: Asked how to create my own branch and merge to main after review.
Useful AI guidance: Create a branch from the latest main named <type>/<issue>-<description>, push it, open a PR, and merge only after approval.
My independent experiment/test: Created feat/4-workflow-and-queue, then checked the Issues page and found my issues were #2 and #5, not #4 or #6. Renamed the branch with git branch -m.
Verification source or result: Terminal prompt showed feat/2-workflow-and-queue; git log showed my commits on the branch, not main.
Decision: Improved. The AI's example issue number was wrong for our repo, so I checked GitHub and corrected it.
Related file/commit: branch feat/2-workflow-and-queue
What I can now explain without AI: [in your words]

### Interaction #2 — Debugging failing tests
Problem: After writing tests, 3 tests failed or errored.
My initial understanding: [what you thought was wrong]
Prompt to AI: Shared a screenshot of the failing test output.
Useful AI guidance: The errors ('NoneType' object is not iterable, ValueError not raised) meant the functions still contained only `pass` and returned None.
My independent experiment/test: Opened workflow.py, confirmed it still held the skeleton, replaced it with the full implementation, and reran the tests.
Verification source or result: python -m unittest discover -s tests -v → Ran 13 tests, OK
Decision: Accepted after verifying with the test run.
Related file/commit: campusflow/workflow.py, tests/test_workflow.py, commit 818cc3c
What I can now explain without AI: [e.g. what a traceback tells you, why a function with only `pass` returns None]

### Interaction #3 — Sorting tickets by numeric ID
Problem: The queue must break priority ties by the earlier ticket number.
My initial understanding: [e.g. I thought sorting the ID strings would work]
Prompt to AI: Asked how to sort by priority and then by ticket ID.
Useful AI guidance: Use sorted() with a tuple key (priority rank, numeric ID), and convert the ID with int() instead of comparing strings.
My independent experiment/test: Ran python3 -c "print(sorted(['T999','T1000']))" and got [your output].
Verification source or result: [what the output proved]; test_queue_sorted_by_priority_then_id passes.
Decision: Accepted after the experiment showed string sorting puts T1000 before T999.
Related file/commit: campusflow/workflow.py (ticket_number, get_work_queue)
What I can now explain without AI: [in your words]

### Note on AI use
The AI wrote the code in workflow.py and test_workflow.py. I ran every test, read the failures, and checked the results myself.