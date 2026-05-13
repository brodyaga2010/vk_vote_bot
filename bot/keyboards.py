from __future__ import annotations

from vkbottle import Keyboard, KeyboardButtonColor, Text


def build_user_menu_keyboard(
    start_button_text: str,
    help_button_text: str,
    status_button_text: str | None = None,
    results_button_text: str | None = None,
    stop_button_text: str | None = None,
) -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text(start_button_text), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text(help_button_text), color=KeyboardButtonColor.SECONDARY)
    if status_button_text or results_button_text or stop_button_text:
        keyboard.row()
        if status_button_text:
            keyboard.add(Text(status_button_text), color=KeyboardButtonColor.POSITIVE)
        if results_button_text:
            keyboard.add(Text(results_button_text), color=KeyboardButtonColor.PRIMARY)
        if stop_button_text:
            keyboard.add(Text(stop_button_text), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


def build_row_keyboard(
    rows: tuple[int, ...],
    start_button_text: str,
    help_button_text: str,
    status_button_text: str | None = None,
    results_button_text: str | None = None,
    stop_button_text: str | None = None,
) -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    for index, row in enumerate(rows):
        if index and index % 5 == 0:
            keyboard.row()
        keyboard.add(Text(str(row)), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text(start_button_text), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text(help_button_text), color=KeyboardButtonColor.SECONDARY)
    if status_button_text or results_button_text or stop_button_text:
        keyboard.row()
        if status_button_text:
            keyboard.add(Text(status_button_text), color=KeyboardButtonColor.POSITIVE)
        if results_button_text:
            keyboard.add(Text(results_button_text), color=KeyboardButtonColor.PRIMARY)
        if stop_button_text:
            keyboard.add(Text(stop_button_text), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


def build_seat_keyboard(
    seats: tuple[int, ...],
    start_button_text: str,
    help_button_text: str,
    status_button_text: str | None = None,
    results_button_text: str | None = None,
    stop_button_text: str | None = None,
) -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    for index, seat in enumerate(seats):
        if index and index % 5 == 0:
            keyboard.row()
        keyboard.add(Text(str(seat)), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text(start_button_text), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text(help_button_text), color=KeyboardButtonColor.SECONDARY)
    if status_button_text or results_button_text or stop_button_text:
        keyboard.row()
        if status_button_text:
            keyboard.add(Text(status_button_text), color=KeyboardButtonColor.POSITIVE)
        if results_button_text:
            keyboard.add(Text(results_button_text), color=KeyboardButtonColor.PRIMARY)
        if stop_button_text:
            keyboard.add(Text(stop_button_text), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


def build_confirmation_keyboard(
    confirm_button_text: str,
    reselect_button_text: str,
    help_button_text: str,
    status_button_text: str | None = None,
    results_button_text: str | None = None,
    stop_button_text: str | None = None,
) -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text(confirm_button_text), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text(reselect_button_text), color=KeyboardButtonColor.NEGATIVE)
    keyboard.row()
    keyboard.add(Text(help_button_text), color=KeyboardButtonColor.SECONDARY)
    if status_button_text or results_button_text or stop_button_text:
        keyboard.row()
        if status_button_text:
            keyboard.add(Text(status_button_text), color=KeyboardButtonColor.POSITIVE)
        if results_button_text:
            keyboard.add(Text(results_button_text), color=KeyboardButtonColor.PRIMARY)
        if stop_button_text:
            keyboard.add(Text(stop_button_text), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


def build_participants_keyboard(
    participants: tuple[str, ...],
    help_button_text: str,
    status_button_text: str | None = None,
    results_button_text: str | None = None,
    stop_button_text: str | None = None,
) -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    for index, participant in enumerate(participants):
        if index and index % 2 == 0:
            keyboard.row()
        keyboard.add(Text(f"{index + 1}. {participant}"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text(help_button_text), color=KeyboardButtonColor.SECONDARY)
    if status_button_text or results_button_text or stop_button_text:
        keyboard.row()
        if status_button_text:
            keyboard.add(Text(status_button_text), color=KeyboardButtonColor.POSITIVE)
        if results_button_text:
            keyboard.add(Text(results_button_text), color=KeyboardButtonColor.PRIMARY)
        if stop_button_text:
            keyboard.add(Text(stop_button_text), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()
