from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VoteRecord:
    user_id: int | None
    row: int
    seat: int
    participant: str


class VoteRegistry:
    """Проверяет допустимые места и хранит голоса в JSON."""

    def __init__(self, valid_seats_path: Path, votes_path: Path) -> None:
        self._valid_seats_path = Path(valid_seats_path)
        self._votes_path = Path(votes_path)
        self._valid_seats = self._load_valid_seats()
        self._votes = self._load_votes()

    def is_valid_seat(self, row: int, seat: int) -> bool:
        return (row, seat) in self._valid_seats

    def is_valid_row(self, row: int) -> bool:
        return row in self._row_ranges

    def get_row_seat_range(self, row: int) -> tuple[int, int] | None:
        return self._row_ranges.get(row)

    def get_rows(self) -> tuple[int, ...]:
        return tuple(sorted(self._row_ranges))

    def get_seats_for_row(self, row: int) -> tuple[int, ...]:
        seat_range = self.get_row_seat_range(row)
        if seat_range is None:
            return ()
        seat_from, seat_to = seat_range
        return tuple(range(seat_from, seat_to + 1))

    def has_voted(self, row: int, seat: int) -> bool:
        return (row, seat) in self._votes

    def has_user_voted(self, user_id: int) -> bool:
        return user_id in self._user_votes

    def register_vote(
        self,
        user_id: int,
        row: int,
        seat: int,
        participant: str,
    ) -> bool:
        key = (row, seat)
        if key not in self._valid_seats:
            return False
        if key in self._votes:
            return False
        if user_id in self._user_votes:
            return False
        self._votes[key] = VoteRecord(
            user_id=user_id,
            row=row,
            seat=seat,
            participant=participant,
        )
        self._user_votes[user_id] = key
        self._save_votes()
        return True

    def get_vote(self, row: int, seat: int) -> VoteRecord | None:
        return self._votes.get((row, seat))

    def get_results(self, participants: tuple[str, ...]) -> list[tuple[str, int, bool]]:
        counts = Counter(vote.participant for vote in self._votes.values())
        if not counts:
            return []

        max_votes = max(counts.values())
        return [
            (participant, counts.get(participant, 0), counts.get(participant, 0) == max_votes)
            for participant in participants
        ]

    def get_total_votes(self) -> int:
        return len(self._votes)

    def _load_valid_seats(self) -> set[tuple[int, int]]:
        with self._valid_seats_path.open(encoding="utf-8") as source:
            data = json.load(source)

        seats: set[tuple[int, int]] = set()
        self._row_ranges: dict[int, tuple[int, int]] = {}
        for block in data["rows"]:
            start_row = int(block["start_row"])
            end_row = int(block["end_row"])
            seat_from = int(block["seat_from"])
            seat_to = int(block["seat_to"])
            for row in range(start_row, end_row + 1):
                self._row_ranges[row] = (seat_from, seat_to)
                for seat in range(seat_from, seat_to + 1):
                    seats.add((row, seat))
        return seats

    def _load_votes(self) -> dict[tuple[int, int], VoteRecord]:
        if not self._votes_path.exists():
            self._votes_path.parent.mkdir(parents=True, exist_ok=True)
            self._votes_path.write_text("[]\n", encoding="utf-8")
            self._user_votes: dict[int, tuple[int, int]] = {}
            return {}

        with self._votes_path.open(encoding="utf-8") as source:
            data = json.load(source)

        votes: dict[tuple[int, int], VoteRecord] = {}
        self._user_votes: dict[int, tuple[int, int]] = {}
        for item in data:
            user_id_raw = item.get("user_id")
            user_id = int(user_id_raw) if isinstance(user_id_raw, int) or str(user_id_raw).isdigit() else None
            row = int(item["row"])
            seat = int(item["seat"])
            participant = str(item["participant"])
            record = VoteRecord(
                user_id=user_id,
                row=row,
                seat=seat,
                participant=participant,
            )
            votes[(row, seat)] = record
            if user_id is not None:
                self._user_votes[user_id] = (row, seat)
        return votes

    def _save_votes(self) -> None:
        self._votes_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "user_id": vote.user_id,
                "row": row,
                "seat": seat,
                "participant": vote.participant,
            }
            for (row, seat), vote in sorted(self._votes.items())
        ]
        self._votes_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def parse_positive_number(raw_value: str) -> int | None:
    value = raw_value.strip()
    if not value.isdigit():
        return None
    number = int(value)
    if number <= 0:
        return None
    return number
