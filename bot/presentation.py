from __future__ import annotations

from bot.config import (
    ADMIN_RESULTS_TITLE,
    CONFIRM_PLACE_TEXT_TEMPLATE,
    INVALID_ROW_TEXT,
    INVALID_SEAT_TEXT_TEMPLATE,
    NO_RESULTS_TEXT,
)
from bot.storage import VoteRegistry


def build_invalid_seat_text(registry: VoteRegistry, row: int, seat: int) -> str:
    seat_range = registry.get_row_seat_range(row)
    if seat_range is None:
        return INVALID_ROW_TEXT
    seat_from, seat_to = seat_range
    return INVALID_SEAT_TEXT_TEMPLATE.format(
        row=row,
        seat=seat,
        seat_from=seat_from,
        seat_to=seat_to,
    )


def build_confirmation_text(row: int, seat: int) -> str:
    return CONFIRM_PLACE_TEXT_TEMPLATE.format(row=row, seat=seat)


def format_results_message(registry: VoteRegistry, participants: tuple[str, ...]) -> str:
    results = registry.get_results(participants)
    if not results:
        return NO_RESULTS_TEXT

    total_votes = registry.get_total_votes()
    unknown_votes = total_votes - sum(votes_count for _, votes_count, _ in results)
    leader_votes = max(votes_count for _, votes_count, _ in results)
    lines = [
        "Результаты голосования:",
        "",
    ]
    for index, (participant, votes_count, is_leader) in enumerate(results, start=1):
        leader_mark = " Лидер" if is_leader and votes_count > 0 else ""
        lines.append(f"{index}. {participant}")
        lines.append(f"Голоса: {votes_count}{leader_mark}")
        lines.append("")
    lines.append(f"Всего голосов: {total_votes}")
    lines.append(f"Лучший результат: {leader_votes}")
    lines.append(ADMIN_RESULTS_TITLE)
    if unknown_votes > 0:
        lines.append("")
        lines.append(
            "Неактуальные записи: "
            f"{unknown_votes}. Эти голоса сохранены в файле, "
            "но не совпадают с текущим списком финалисток."
        )
    if lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
