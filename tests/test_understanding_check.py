import unittest
import sys
from pathlib import Path
from unittest.mock import patch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from campusflow.understanding_check import (
    CHOICES,
    MIN_EXPLANATIONS,
    QUESTIONS,
    explained_question_numbers,
    max_score,
    normalise_choice,
    question_numbers,
    score_answers,
    understanding_check_menu,
)


def correct_answers():
    """The answer key, read from the bank itself."""
    return {question["number"]: question["answer"] for question in QUESTIONS}


def a_wrong_choice_for(question):
    """Any valid letter that is not this question's answer."""
    for letter in CHOICES:
        if letter != question["answer"]:
            return letter
    raise AssertionError("every choice was correct, which cannot happen")


def play(answers, explanations):
    """Build the input sequence the menu will consume."""
    sequence = list(answers)
    for number, text in explanations:
        sequence.append(str(number))
        sequence.append(text)
    return sequence


class TestQuestionBank(unittest.TestCase):
    def test_bank_has_six_questions_numbered_one_to_six(self):
        self.assertEqual(len(QUESTIONS), 6)
        self.assertEqual(question_numbers(), (1, 2, 3, 4, 5, 6))

    def test_every_question_offers_exactly_the_four_choices(self):
        for question in QUESTIONS:
            with self.subTest(question=question["number"]):
                self.assertEqual(tuple(question["options"]), CHOICES)

    def test_every_answer_names_one_of_that_questions_own_options(self):
        for question in QUESTIONS:
            with self.subTest(question=question["number"]):
                self.assertIn(question["answer"], CHOICES)
                self.assertIn(question["answer"], question["options"])

    def test_answer_key_matches_the_behaviour_of_this_application(self):
        # Guards the bank against drifting from what the code actually does.
        expected_answers = ("B", "C", "B", "C", "C", "B")
        actual_answers = tuple(question["answer"] for question in QUESTIONS)

        self.assertEqual(actual_answers, expected_answers)


class TestNormaliseChoice(unittest.TestCase):
    def test_accepts_each_valid_letter_in_any_case_with_padding(self):
        for letter in CHOICES:
            for typed in (letter, letter.lower(), f"  {letter}  "):
                with self.subTest(typed=typed):
                    self.assertEqual(normalise_choice(typed), letter)

    def test_rejects_anything_that_is_not_abcd(self):
        for typed in ("E", "AB", "", "   ", "1", "yes", None, 3):
            with self.subTest(typed=typed):
                self.assertEqual(normalise_choice(typed), "")


class TestScoreAnswers(unittest.TestCase):
    def test_all_correct_scores_full_marks(self):
        self.assertEqual(score_answers(correct_answers()), max_score())

    def test_all_wrong_scores_zero(self):
        answers = {
            question["number"]: a_wrong_choice_for(question)
            for question in QUESTIONS
        }

        self.assertEqual(score_answers(answers), 0)

    def test_partial_answers_score_one_point_each(self):
        answers = correct_answers()
        answers[1] = a_wrong_choice_for(QUESTIONS[0])
        answers[4] = a_wrong_choice_for(QUESTIONS[3])

        self.assertEqual(score_answers(answers), max_score() - 2)

    def test_answers_are_scored_whatever_case_they_are_written_in(self):
        answers = {
            number: letter.lower()
            for number, letter in correct_answers().items()
        }

        self.assertEqual(score_answers(answers), max_score())

    def test_missing_answers_score_zero_rather_than_failing(self):
        self.assertEqual(score_answers({}), 0)

    def test_unanswered_questions_do_not_shift_the_other_scores(self):
        answers = {1: "B", 2: "C"}

        self.assertEqual(score_answers(answers), 2)

    def test_scoring_never_asks_for_input(self):
        # The brief requires the question bank to stay separate from the
        # scoring logic. Scoring must be a pure function of the answers.
        with patch(
            "builtins.input",
            side_effect=AssertionError("scoring must not read input"),
        ):
            with patch("builtins.print") as printed:
                self.assertEqual(score_answers(correct_answers()), max_score())

        printed.assert_not_called()


class TestExplainedQuestionNumbers(unittest.TestCase):
    def test_counts_only_questions_with_real_text(self):
        explanations = {1: "because the ticket has no assignee", 2: "   ", 3: ""}

        self.assertEqual(explained_question_numbers(explanations), [1])

    def test_returns_question_numbers_in_bank_order(self):
        explanations = {5: "text", 2: "text"}

        self.assertEqual(explained_question_numbers(explanations), [2, 5])

    def test_ignores_question_numbers_that_are_not_in_the_bank(self):
        self.assertEqual(explained_question_numbers({99: "text"}), [])


class TestUnderstandingCheckMenu(unittest.TestCase):
    def test_perfect_run_reports_six_out_of_six(self):
        inputs = play(correct_answers().values(), [(1, "no assignee"), (2, "zero tickets")])

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as printed:
                attempt = understanding_check_menu()

        self.assertEqual(attempt["score"], 6)
        printed.assert_any_call(f"Result: 6/{max_score()}")

    def test_invalid_answer_is_rejected_then_scored_correctly(self):
        # Acceptance case 14. Q1 gets an invalid letter first, so the menu
        # must re-ask it; the retry then answers B, which is correct.
        inputs = play(
            ["E", "B", "C", "B", "C", "C", "B"],
            [(1, "no assignee"), (2, "zero tickets")],
        )

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as printed:
                attempt = understanding_check_menu()

        printed.assert_any_call("Invalid choice. Please enter A, B, C or D.")
        self.assertEqual(attempt["score"], 6)
        self.assertEqual(attempt["answers"][1], "B")

    def test_score_reflects_submitted_answers_not_corrected_ones(self):
        answers = {
            question["number"]: a_wrong_choice_for(question)
            for question in QUESTIONS
        }
        inputs = play(answers.values(), [(1, "a guess"), (2, "another guess")])

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as printed:
                attempt = understanding_check_menu()

        self.assertEqual(attempt["score"], 0)
        printed.assert_any_call(f"Result: 0/{max_score()}")

    def test_a_blank_explanation_is_rejected_and_asked_again(self):
        inputs = play(
            correct_answers().values(),
            [(1, "   "), (1, "no assignee"), (2, "zero tickets")],
        )

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as printed:
                attempt = understanding_check_menu()

        printed.assert_any_call("An explanation cannot be blank.")
        self.assertEqual(attempt["explanations"][1], "no assignee")

    def test_explanation_for_an_unknown_question_is_rejected(self):
        inputs = play(
            correct_answers().values(),
            [(99, "nowhere"), (1, "no assignee"), (2, "zero tickets")],
        )

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as printed:
                attempt = understanding_check_menu()

        printed.assert_any_call("Please choose a number between 1 and 6.")
        self.assertNotIn(99, attempt["explanations"])

    def test_the_attempt_records_the_required_number_of_explanations(self):
        inputs = play(correct_answers().values(), [(1, "first"), (3, "second")])

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                attempt = understanding_check_menu()

        self.assertEqual(
            len(explained_question_numbers(attempt["explanations"])),
            MIN_EXPLANATIONS,
        )

    def test_summary_shows_the_correct_answer_for_a_wrong_choice(self):
        answers = correct_answers()
        answers[1] = a_wrong_choice_for(QUESTIONS[0])
        inputs = play(answers.values(), [(1, "a guess"), (2, "another")])

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as printed:
                understanding_check_menu()

        # Q1's answer is B, so a wrong choice must report B as correct.
        printed.assert_any_call(
            f"  Q1: answer given: {answers[1]}; correct answer: {QUESTIONS[0]['answer']}"
        )


if __name__ == "__main__":
    unittest.main()
