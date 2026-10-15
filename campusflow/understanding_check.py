"""The Engineering Understanding Check (sprint section 05).

An interactive multiple-choice check on how this application behaves, plus
a written explanation of at least two answers.

The question bank is data -- the QUESTIONS tuple below -- and the scoring
is a pure function, score_answers(). The brief requires the bank not to
carry the scoring logic, so the score can be tested without going anywhere
near input() or print(). The menu functions at the bottom do the asking
and the printing and nothing else.
"""

# The bank. Each entry is a scenario, four lettered options, and the
# correct letter. Answer keys are checked against the code, not guessed:
#   Q1  workflow.apply_status_change rejects an unassigned move to "in progress"
#   Q2  report resolution_percent is 0.0 when there are no tickets
#   Q3  search_tickets requires every supplied filter to match
#   Q4  Requirement B: only open or in progress tickets accept a note
#   Q5  Requirement E: an invalid collection is rejected without changing
#       what is already in memory
#   Q6  A review that accepts untested validation is not a review
QUESTIONS = (
    {
        "number": 1,
        "scenario": (
            "Ticket T001 is open and has no assignee. A user tries to move "
            "it to in progress."
        ),
        "options": {
            "A": "Accept it",
            "B": "Reject it and preserve all data",
            "C": "Resolve it automatically",
            "D": "Remove the ticket",
        },
        "answer": "B",
    },
    {
        "number": 2,
        "scenario": (
            "The application has zero tickets. What should the resolution "
            "percentage display?"
        ),
        "options": {
            "A": "Crash",
            "B": "100%",
            "C": "0%",
            "D": "Divide by one without explanation",
        },
        "answer": "C",
    },
    {
        "number": 3,
        "scenario": (
            "A search is run with title='wifi', category='Network', "
            "status='open'. Which records should match?"
        ),
        "options": {
            "A": "Any record matching one of the filters",
            "B": "Only records matching all the supplied filters",
            "C": "All network records",
            "D": "All open records",
        },
        "answer": "B",
    },
    {
        "number": 4,
        "scenario": "A resolved ticket receives 'Add Follow-up Note'.",
        "options": {
            "A": "Append the note anyway",
            "B": "Delete the ticket's older notes",
            "C": "Reject the note until the ticket is reopened",
            "D": "Change the status silently",
        },
        "answer": "C",
    },
    {
        "number": 5,
        "scenario": (
            "The JSON file contains two tickets with the same ID. What "
            "should loading do?"
        ),
        "options": {
            "A": "Keep both tickets",
            "B": "Replace memory with the duplicates",
            "C": "Reject the load without changing current memory",
            "D": "Rename the IDs silently",
        },
        "answer": "C",
    },
    {
        "number": 6,
        "scenario": (
            "A pull request changes validation but adds no negative-case "
            "tests. What is the best review action?"
        ),
        "options": {
            "A": "Approve it because it runs",
            "B": "Request focused tests and the reasoning behind the change",
            "C": "Merge it immediately",
            "D": "Ask an AI to approve it",
        },
        "answer": "B",
    },
)

CHOICES = ("A", "B", "C", "D")

# The brief asks for an explanation of at least two answers.
MIN_EXPLANATIONS = 2


def question_numbers():
    """The question numbers in the bank, in order."""
    return tuple(question["number"] for question in QUESTIONS)


def max_score():
    """The highest score the bank can award."""
    return len(QUESTIONS)


def normalise_choice(value):
    """Return a valid A/B/C/D choice, or "" when the input is not one.

    The menu retries on "", which is how an invalid choice is rejected.
    """
    text = value.strip().upper() if isinstance(value, str) else ""
    return text if text in CHOICES else ""


def score_answers(answers):
    """Score a mapping of question number -> chosen letter. Pure.

    One point per correct answer, so the result is 0..max_score().
    """
    return sum(
        1
        for question in QUESTIONS
        if normalise_choice(answers.get(question["number"])) == question["answer"]
    )


def explained_question_numbers(explanations):
    """Question numbers that have a non-blank explanation, in bank order."""
    return [
        number
        for number in question_numbers()
        if isinstance(explanations.get(number), str)
        and explanations[number].strip()
    ]


# ---------------------------------------------------------------------------
# Menu functions: input() and print() only, no scoring logic.
# ---------------------------------------------------------------------------

def _ask_question(question):
    """Print one scenario and return a valid choice, retrying if needed."""
    print(f"\nQ{question['number']}. {question['scenario']}")
    for letter in CHOICES:
        print(f"   {letter}. {question['options'][letter]}")

    while True:
        choice = normalise_choice(input("Answer (A/B/C/D): "))
        if choice:
            return choice
        print("Invalid choice. Please enter A, B, C or D.")


def _ask_for_explanations():
    """Collect at least MIN_EXPLANATIONS written explanations."""
    print(
        f"\nNow explain at least {MIN_EXPLANATIONS} of your answers in your "
        "own words."
    )
    explanations = {}

    while len(explained_question_numbers(explanations)) < MIN_EXPLANATIONS:
        raw_number = input(
            f"Which question number? (1-{max_score()}): "
        ).strip()
        number = int(raw_number) if raw_number.isdigit() else 0

        if number not in question_numbers():
            print(f"Please choose a number between 1 and {max_score()}.")
            continue

        explanation = input("Your explanation: ").strip()
        if not explanation:
            print("An explanation cannot be blank.")
            continue

        explanations[number] = explanation

    return explanations


def _print_summary(answers, explanations):
    """Print the score and the review, without grading the explanations."""
    score = score_answers(answers)

    print("\n" + "=" * 40)
    print(f"Result: {score}/{max_score()}")
    print("=" * 40)

    for question in QUESTIONS:
        number = question["number"]
        chosen = answers.get(number, "-")
        if chosen == question["answer"]:
            verdict = "correct"
        else:
            verdict = f"answer given: {chosen}; correct answer: {question['answer']}"
        print(f"  Q{number}: {verdict}")

    print("\nYour explanations, for mentor discussion:")
    for number in explained_question_numbers(explanations):
        print(f"  Q{number}: {explanations[number]}")

    print(
        "\nExplanations are recorded, not graded. A matching keyword does not "
        "make an explanation correct -- discuss them with your mentor."
    )
    return score


def understanding_check_menu():
    """Run the Engineering Understanding Check. Returns the attempt."""
    print("\nEngineering Understanding Check")
    print("=" * 32)
    print(f"{max_score()} questions on how this application behaves.")

    answers = {question["number"]: _ask_question(question) for question in QUESTIONS}
    explanations = _ask_for_explanations()
    score = _print_summary(answers, explanations)

    return {"answers": answers, "explanations": explanations, "score": score}


if __name__ == "__main__":
    understanding_check_menu()
