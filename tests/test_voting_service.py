import json
import tempfile
import unittest
from pathlib import Path

from bot.config import HELP_TEXT, PARTICIPANTS
from bot.presentation import format_results_message
from bot.storage import VoteRegistry, parse_positive_number


class ParsePositiveNumberTests(unittest.TestCase):
    def test_returns_number_for_valid_string(self) -> None:
        self.assertEqual(parse_positive_number("12"), 12)

    def test_returns_none_for_zero(self) -> None:
        self.assertIsNone(parse_positive_number("0"))

    def test_returns_none_for_text(self) -> None:
        self.assertIsNone(parse_positive_number("ряд 7"))


class VoteRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.valid_seats_path = root / "valid_seats.json"
        self.votes_path = root / "votes.json"
        self.valid_seats_path.write_text(
            json.dumps(
                {
                    "rows": [
                        {
                            "start_row": 1,
                            "end_row": 1,
                            "seat_from": 1,
                            "seat_to": 3,
                        },
                        {
                            "start_row": 2,
                            "end_row": 2,
                            "seat_from": 1,
                            "seat_to": 2,
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.original_votes = Path("bot/data/votes.json").read_text(encoding="utf-8")

    def tearDown(self) -> None:
        Path("bot/data/votes.json").write_text(self.original_votes, encoding="utf-8")
        self.temp_dir.cleanup()

    def test_rejects_vote_for_unknown_seat(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        result = registry.register_vote(1001, 3, 5, "Участник 1")

        self.assertFalse(result)
        self.assertFalse(registry.has_voted(3, 5))

    def test_rejects_second_vote_from_same_place(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)
        registry.register_vote(1001, 1, 2, "Участник 1")

        result = registry.register_vote(1002, 1, 2, "Участник 2")

        self.assertFalse(result)
        vote = registry.get_vote(1, 2)
        self.assertIsNotNone(vote)
        assert vote is not None
        self.assertEqual(vote.participant, "Участник 1")
        self.assertEqual(vote.user_id, 1001)

    def test_allows_same_participant_from_other_place(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        first_result = registry.register_vote(1001, 1, 1, "Участник 2")
        second_result = registry.register_vote(1002, 1, 2, "Участник 2")

        self.assertTrue(first_result)
        self.assertTrue(second_result)

    def test_rejects_second_vote_from_same_user(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        first_result = registry.register_vote(1001, 1, 1, "Участник 2")
        second_result = registry.register_vote(1001, 2, 1, "Участник 3")

        self.assertTrue(first_result)
        self.assertFalse(second_result)
        self.assertTrue(registry.has_user_voted(1001))

    def test_validates_allowed_seat(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        self.assertTrue(registry.is_valid_seat(1, 3))
        self.assertFalse(registry.is_valid_seat(3, 1))

    def test_validates_allowed_row(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        self.assertTrue(registry.is_valid_row(1))
        self.assertFalse(registry.is_valid_row(3))

    def test_returns_row_seat_range(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        self.assertEqual(registry.get_row_seat_range(1), (1, 3))
        self.assertIsNone(registry.get_row_seat_range(3))

    def test_returns_sorted_rows(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        self.assertEqual(registry.get_rows(), (1, 2))

    def test_returns_seats_for_row(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        self.assertEqual(registry.get_seats_for_row(2), (1, 2))
        self.assertEqual(registry.get_seats_for_row(3), ())

    def test_persists_votes_to_json_file(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        result = registry.register_vote(1003, 2, 2, "Участник 3")

        self.assertTrue(result)
        saved_votes = json.loads(self.votes_path.read_text(encoding="utf-8"))
        self.assertEqual(
            saved_votes,
            [{"user_id": 1003, "row": 2, "seat": 2, "participant": "Участник 3"}],
        )

    def test_loads_existing_votes_from_json_file(self) -> None:
        self.votes_path.write_text(
            json.dumps(
                [{"row": 1, "seat": 3, "participant": "Участник 4"}],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        registry = VoteRegistry(self.valid_seats_path, self.votes_path)

        self.assertTrue(registry.has_voted(1, 3))
        vote = registry.get_vote(1, 3)
        self.assertIsNotNone(vote)
        assert vote is not None
        self.assertEqual(vote.participant, "Участник 4")
        self.assertIsNone(vote.user_id)

    def test_returns_results_with_marked_leader(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)
        registry.register_vote(1001, 1, 1, "Участник 1")
        registry.register_vote(1002, 1, 2, "Участник 1")
        registry.register_vote(1003, 1, 3, "Участник 2")

        results = registry.get_results(("Участник 1", "Участник 2", "Участник 3"))

        self.assertEqual(
            results,
            [
                ("Участник 1", 2, True),
                ("Участник 2", 1, False),
                ("Участник 3", 0, False),
            ],
        )

    def test_returns_total_votes(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)
        registry.register_vote(1001, 1, 1, "Участник 1")
        registry.register_vote(1002, 1, 2, "Участник 2")

        self.assertEqual(registry.get_total_votes(), 2)

    def test_results_message_marks_unknown_records(self) -> None:
        Path("bot/data/votes.json").write_text(
            json.dumps(
                [
                    {"user_id": 1, "row": 1, "seat": 1, "participant": PARTICIPANTS[0]},
                    {"user_id": 2, "row": 1, "seat": 2, "participant": "Старое имя"},
                ],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        registry = VoteRegistry(
            Path("bot/data/valid_seats.json"),
            Path("bot/data/votes.json"),
        )

        text = format_results_message(registry, PARTICIPANTS)

        self.assertIn("Неактуальные записи: 1", text)

    def test_results_message_has_table_header(self) -> None:
        registry = VoteRegistry(self.valid_seats_path, self.votes_path)
        registry.register_vote(1001, 1, 1, "Щепина Злата")

        text = format_results_message(registry, ("Щепина Злата", "Дьяконова Екатерина"))

        self.assertIn("Результаты голосования:", text)
        self.assertIn("1. Щепина Злата", text)
        self.assertIn("Голоса", text)
        self.assertIn("Лидер", text)


class HelpTextTests(unittest.TestCase):
    def test_help_mentions_buttons_and_start(self) -> None:
        self.assertIn("Начать голосование", HELP_TEXT)
        self.assertIn("Выберите номер вашего ряда с помощью кнопок", HELP_TEXT)
        self.assertIn("Подтвердите правильность выбранных ряда и места", HELP_TEXT)


if __name__ == "__main__":
    unittest.main()
