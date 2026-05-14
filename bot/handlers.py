from __future__ import annotations

import asyncio
import logging
import os
import re

from vkbottle import BuiltinStateDispenser
from vkbottle.bot import Bot, Message

from bot.config import (
    ALREADY_VOTED_TEXT,
    ALREADY_VOTED_BY_USER_TEXT,
    ADMIN_ONLY_TEXT,
    ADMIN_HELP_TEXT,
    ADMIN_RESULTS_TITLE,
    ADMIN_STATUS_TEXT_TEMPLATE,
    CHOOSE_PARTICIPANT_TEXT,
    CONFIRM_PLACE_BUTTON_TEXT,
    HELP_BUTTON_TEXT,
    HELP_TEXT,
    INVALID_CONFIRMATION_TEXT,
    INVALID_PARTICIPANT_TEXT,
    INVALID_ROW_BUTTON_TEXT,
    INVALID_ROW_TEXT,
    INVALID_SEAT_BUTTON_TEXT,
    NO_RESULTS_TEXT,
    PARTICIPANTS,
    RESELECT_PLACE_BUTTON_TEXT,
    RESULTS_BUTTON_TEXT,
    START_BUTTON_TEXT,
    STATUS_BUTTON_TEXT,
    STOPPED_TEXT,
    STOP_BUTTON_TEXT,
    STOP_EXIT_CODE,
    STOP_FLAG_PATH,
    THANK_YOU_TEXT,
    UNKNOWN_COMMAND_TEXT,
    USER_RESTART_TEXT,
    VALID_SEATS_PATH,
    VOTES_PATH,
    WELCOME_TEXT,
    get_admin_ids,
)
from bot.keyboards import (
    build_participants_keyboard,
    build_confirmation_keyboard,
    build_row_keyboard,
    build_seat_keyboard,
    build_user_menu_keyboard,
)
from bot.presentation import (
    build_confirmation_text,
    build_invalid_seat_text,
    format_results_message,
)
from bot.states import VotingStates
from bot.storage import VoteRegistry

state_dispenser = BuiltinStateDispenser()
registry = VoteRegistry(VALID_SEATS_PATH, VOTES_PATH)
logger = logging.getLogger(__name__)
ROW_PATTERN = re.compile(r"^(?:Ряд\s+)?(\d+)$")
SEAT_PATTERN = re.compile(r"^(?:Место\s+)?(\d+)$")
PARTICIPANT_PATTERN = re.compile(r"^(\d+)\.\s+(.+)$")


def build_menu_keyboard(is_admin: bool) -> str:
    return build_user_menu_keyboard(
        START_BUTTON_TEXT,
        HELP_BUTTON_TEXT,
        STATUS_BUTTON_TEXT if is_admin else None,
        RESULTS_BUTTON_TEXT if is_admin else None,
        STOP_BUTTON_TEXT if is_admin else None,
    )


def build_rows_keyboard(is_admin: bool) -> str:
    return build_row_keyboard(
        registry.get_rows(),
        START_BUTTON_TEXT,
        HELP_BUTTON_TEXT,
        STATUS_BUTTON_TEXT if is_admin else None,
        RESULTS_BUTTON_TEXT if is_admin else None,
        STOP_BUTTON_TEXT if is_admin else None,
    )


def build_seats_keyboard(row: int, is_admin: bool) -> str:
    return build_seat_keyboard(
        registry.get_seats_for_row(row),
        START_BUTTON_TEXT,
        HELP_BUTTON_TEXT,
        STATUS_BUTTON_TEXT if is_admin else None,
        RESULTS_BUTTON_TEXT if is_admin else None,
        STOP_BUTTON_TEXT if is_admin else None,
    )


def build_vote_confirmation_keyboard(is_admin: bool) -> str:
    return build_confirmation_keyboard(
        CONFIRM_PLACE_BUTTON_TEXT,
        RESELECT_PLACE_BUTTON_TEXT,
        HELP_BUTTON_TEXT,
        STATUS_BUTTON_TEXT if is_admin else None,
        RESULTS_BUTTON_TEXT if is_admin else None,
        STOP_BUTTON_TEXT if is_admin else None,
    )


def build_candidates_keyboard(is_admin: bool) -> str:
    return build_participants_keyboard(
        PARTICIPANTS,
        HELP_BUTTON_TEXT,
        STATUS_BUTTON_TEXT if is_admin else None,
        RESULTS_BUTTON_TEXT if is_admin else None,
        STOP_BUTTON_TEXT if is_admin else None,
    )


def is_help_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {"помощь", "/help", "help", "?"}


def is_start_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        "начать",
        "старт",
        "привет",
        "/start",
        START_BUTTON_TEXT.lower(),
    }


def parse_row_selection(text: str) -> int | None:
    match = ROW_PATTERN.match(text.strip())
    if match is None:
        return None
    return int(match.group(1))


def parse_seat_selection(text: str) -> int | None:
    match = SEAT_PATTERN.match(text.strip())
    if match is None:
        return None
    return int(match.group(1))


def parse_participant_selection(text: str) -> str | None:
    match = PARTICIPANT_PATTERN.match(text.strip())
    if match is None:
        return None
    index = int(match.group(1))
    if index < 1 or index > len(PARTICIPANTS):
        return None
    return PARTICIPANTS[index - 1]


async def answer_help(message: Message, is_admin: bool) -> None:
    text = ADMIN_HELP_TEXT if is_admin else HELP_TEXT
    await message.answer(text, keyboard=build_menu_keyboard(is_admin))


def schedule_process_stop() -> None:
    loop = asyncio.get_running_loop()
    loop.call_later(1.0, lambda: os._exit(STOP_EXIT_CODE))


def create_bot(token: str) -> Bot:
    bot = Bot(token=token, state_dispenser=state_dispenser)
    admin_ids = get_admin_ids()

    @bot.on.private_message(
        text=[
            "начать",
            "Начать",
            START_BUTTON_TEXT,
            "старт",
            "Старт",
            "привет",
            "Привет",
            "/start",
        ]
    )
    async def start_voting(message: Message) -> None:
        user_id = message.from_id or 0
        is_admin = user_id in admin_ids
        logger.info("Старт диалога: user_id=%s peer_id=%s", user_id, message.peer_id)
        if user_id and registry.has_user_voted(user_id):
            logger.info("Повторная попытка старта от уже проголосовавшего user_id=%s", user_id)
            await message.answer(
                ALREADY_VOTED_BY_USER_TEXT,
                keyboard=build_menu_keyboard(is_admin),
            )
            return
        await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
        await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))

    @bot.on.private_message(text=[HELP_BUTTON_TEXT, "помощь", "Помощь", "/help", "help", "?"])
    async def show_help(message: Message) -> None:
        user_id = message.from_id or 0
        logger.info("Запрос помощи: user_id=%s peer_id=%s", user_id, message.peer_id)
        await answer_help(message, user_id in admin_ids)

    @bot.on.private_message(text=[STATUS_BUTTON_TEXT, "status", "Status"])
    async def show_status(message: Message) -> None:
        user_id = message.from_id or 0
        logger.info("Запрос статуса: user_id=%s peer_id=%s", user_id, message.peer_id)
        if user_id not in admin_ids:
            await message.answer(ADMIN_ONLY_TEXT, keyboard=build_menu_keyboard(False))
            return
        await message.answer(
            ADMIN_STATUS_TEXT_TEMPLATE.format(votes_count=registry.get_total_votes()),
            keyboard=build_menu_keyboard(True),
        )

    @bot.on.private_message(text=[RESULTS_BUTTON_TEXT, "итоги", "Итоги", "/results"])
    async def show_results(message: Message) -> None:
        user_id = message.from_id or 0
        logger.info("Запрос итогов: user_id=%s peer_id=%s", user_id, message.peer_id)
        if user_id not in admin_ids:
            await message.answer(ADMIN_ONLY_TEXT, keyboard=build_menu_keyboard(False))
            return
        body = format_results_message(registry, PARTICIPANTS)
        if body == NO_RESULTS_TEXT:
            text = f"{ADMIN_RESULTS_TITLE}\n\nГолосов пока нет."
        else:
            text = f"{ADMIN_RESULTS_TITLE}\n\n{body}"
        await message.answer(text, keyboard=build_menu_keyboard(True))

    @bot.on.private_message(text=[STOP_BUTTON_TEXT, "stop", "Stop", "/stop"])
    async def stop_bot(message: Message) -> None:
        user_id = message.from_id or 0
        logger.info("Запрос остановки: user_id=%s peer_id=%s", user_id, message.peer_id)
        if user_id not in admin_ids:
            await message.answer(ADMIN_ONLY_TEXT, keyboard=build_menu_keyboard(False))
            return
        body = format_results_message(registry, PARTICIPANTS)
        if body == NO_RESULTS_TEXT:
            results_text = f"{ADMIN_RESULTS_TITLE}\n\nГолосов пока нет."
        else:
            results_text = f"{ADMIN_RESULTS_TITLE}\n\n{body}"
        await message.answer(results_text, keyboard=build_menu_keyboard(True))
        STOP_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
        STOP_FLAG_PATH.write_text("stopped_by_admin\n", encoding="utf-8")
        await message.answer(STOPPED_TEXT)
        logger.info("Бот остановлен администратором, выставлен stop flag: %s", STOP_FLAG_PATH)
        schedule_process_stop()

    @bot.on.message(state=VotingStates.WAITING_ROW)
    async def receive_row(message: Message) -> None:
        user_id = message.from_id or 0
        is_admin = user_id in admin_ids
        text = (message.text or "").strip()
        logger.info(
            "Получен ряд: user_id=%s peer_id=%s text=%r",
            user_id,
            message.peer_id,
            message.text,
        )
        if user_id and registry.has_user_voted(user_id):
            await bot.state_dispenser.delete(message.peer_id)
            logger.info("Пользователь уже голосовал: user_id=%s", user_id)
            await message.answer(ALREADY_VOTED_BY_USER_TEXT, keyboard=build_menu_keyboard(is_admin))
            return
        if is_help_command(text):
            await answer_help(message, is_admin)
            return
        if is_start_command(text):
            await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
            await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))
            return

        row = parse_row_selection(text)
        if row is None:
            await message.answer(INVALID_ROW_BUTTON_TEXT, keyboard=build_rows_keyboard(is_admin))
            return
        if not registry.is_valid_row(row):
            logger.info("Отклонён несуществующий ряд: user_id=%s row=%s", user_id, row)
            await message.answer(INVALID_ROW_TEXT, keyboard=build_rows_keyboard(is_admin))
            return

        await bot.state_dispenser.set(
            message.peer_id,
            VotingStates.WAITING_SEAT,
            row=row,
        )
        seat_from, seat_to = registry.get_row_seat_range(row) or (0, 0)
        await message.answer(
            f"Ряд {row} принят.\n"
            f"Теперь выберите номер места.\n"
            f"Для этого ряда доступны места с {seat_from} по {seat_to}.",
            keyboard=build_seats_keyboard(row, is_admin),
        )

    @bot.on.message(state=VotingStates.WAITING_SEAT)
    async def receive_seat(message: Message) -> None:
        user_id = message.from_id or 0
        is_admin = user_id in admin_ids
        text = (message.text or "").strip()
        logger.info(
            "Получено место: user_id=%s peer_id=%s text=%r",
            user_id,
            message.peer_id,
            message.text,
        )
        if user_id and registry.has_user_voted(user_id):
            await bot.state_dispenser.delete(message.peer_id)
            logger.info("Пользователь уже голосовал: user_id=%s", user_id)
            await message.answer(ALREADY_VOTED_BY_USER_TEXT, keyboard=build_menu_keyboard(is_admin))
            return
        if is_help_command(text):
            await answer_help(message, is_admin)
            return
        if is_start_command(text):
            await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
            await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))
            return

        payload = message.state_peer.payload if message.state_peer else {}
        row = payload.get("row")
        if not isinstance(row, int):
            await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
            await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))
            return

        seat = parse_seat_selection(text)
        if seat is None:
            await message.answer(INVALID_SEAT_BUTTON_TEXT, keyboard=build_seats_keyboard(row, is_admin))
            return

        if not registry.is_valid_seat(row, seat):
            logger.info("Отклонено несуществующее место: user_id=%s row=%s seat=%s", user_id, row, seat)
            await message.answer(
                build_invalid_seat_text(registry, row, seat),
                keyboard=build_seats_keyboard(row, is_admin),
            )
            return

        if registry.has_voted(row, seat):
            await bot.state_dispenser.delete(message.peer_id)
            logger.info("Место уже голосовало: user_id=%s row=%s seat=%s", user_id, row, seat)
            await message.answer(ALREADY_VOTED_TEXT, keyboard=build_menu_keyboard(is_admin))
            return

        await bot.state_dispenser.set(
            message.peer_id,
            VotingStates.WAITING_CONFIRMATION,
            row=row,
            seat=seat,
        )
        await message.answer(
            build_confirmation_text(row, seat),
            keyboard=build_vote_confirmation_keyboard(is_admin),
        )

    @bot.on.message(state=VotingStates.WAITING_CONFIRMATION)
    async def confirm_place(message: Message) -> None:
        user_id = message.from_id or 0
        is_admin = user_id in admin_ids
        text = (message.text or "").strip()
        logger.info(
            "Подтверждение места: user_id=%s peer_id=%s text=%r",
            user_id,
            message.peer_id,
            message.text,
        )
        if user_id and registry.has_user_voted(user_id):
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer(ALREADY_VOTED_BY_USER_TEXT, keyboard=build_menu_keyboard(is_admin))
            return
        if is_help_command(text):
            await answer_help(message, is_admin)
            return
        if text == RESELECT_PLACE_BUTTON_TEXT:
            payload = message.state_peer.payload if message.state_peer else {}
            row = payload.get("row")
            if not isinstance(row, int):
                await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
                await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))
                return
            await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_SEAT, row=row)
            seat_from, seat_to = registry.get_row_seat_range(row) or (0, 0)
            await message.answer(
                f"Выберите место заново.\nДля ряда {row} доступны места с {seat_from} по {seat_to}.",
                keyboard=build_seats_keyboard(row, is_admin),
            )
            return
        if text != CONFIRM_PLACE_BUTTON_TEXT:
            await message.answer(
                INVALID_CONFIRMATION_TEXT,
                keyboard=build_vote_confirmation_keyboard(is_admin),
            )
            return

        payload = message.state_peer.payload if message.state_peer else {}
        row = payload.get("row")
        seat = payload.get("seat")
        if not isinstance(row, int) or not isinstance(seat, int):
            await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
            await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))
            return

        await bot.state_dispenser.set(
            message.peer_id,
            VotingStates.WAITING_PARTICIPANT,
            row=row,
            seat=seat,
        )
        await message.answer(
            CHOOSE_PARTICIPANT_TEXT,
            keyboard=build_candidates_keyboard(is_admin),
        )

    @bot.on.message(state=VotingStates.WAITING_PARTICIPANT)
    async def receive_participant(message: Message) -> None:
        user_id = message.from_id or 0
        is_admin = user_id in admin_ids
        text = (message.text or "").strip()
        logger.info(
            "Получен выбор участника: user_id=%s peer_id=%s text=%r",
            user_id,
            message.peer_id,
            message.text,
        )
        if user_id and registry.has_user_voted(user_id):
            await bot.state_dispenser.delete(message.peer_id)
            logger.info("Пользователь уже голосовал: user_id=%s", user_id)
            await message.answer(ALREADY_VOTED_BY_USER_TEXT, keyboard=build_menu_keyboard(is_admin))
            return
        if is_help_command(text):
            await answer_help(message, is_admin)
            return

        participant = parse_participant_selection(text)
        if participant not in PARTICIPANTS:
            await message.answer(
                INVALID_PARTICIPANT_TEXT,
                keyboard=build_candidates_keyboard(is_admin),
            )
            return

        payload = message.state_peer.payload if message.state_peer else {}
        row = payload.get("row")
        seat = payload.get("seat")
        if not isinstance(row, int) or not isinstance(seat, int):
            await bot.state_dispenser.set(message.peer_id, VotingStates.WAITING_ROW)
            await message.answer(WELCOME_TEXT, keyboard=build_rows_keyboard(is_admin))
            return

        if not registry.register_vote(user_id, row, seat, participant):
            await bot.state_dispenser.delete(message.peer_id)
            logger.info(
                "Отклонён повторный голос: user_id=%s row=%s seat=%s participant=%r",
                user_id,
                row,
                seat,
                participant,
            )
            if registry.has_user_voted(user_id):
                await message.answer(ALREADY_VOTED_BY_USER_TEXT, keyboard=build_menu_keyboard(is_admin))
            else:
                await message.answer(ALREADY_VOTED_TEXT, keyboard=build_menu_keyboard(is_admin))
            return

        await bot.state_dispenser.delete(message.peer_id)
        logger.info(
            "Голос сохранён: user_id=%s row=%s seat=%s participant=%r",
            user_id,
            row,
            seat,
            participant,
        )
        await message.answer(THANK_YOU_TEXT, keyboard=build_menu_keyboard(is_admin))

    @bot.on.private_message()
    async def fallback_private_message(message: Message) -> None:
        user_id = message.from_id or 0
        is_admin = user_id in admin_ids
        logger.info(
            "Fallback сообщение: user_id=%s peer_id=%s text=%r",
            user_id,
            message.peer_id,
            message.text,
        )
        if is_help_command(message.text or ""):
            await answer_help(message, is_admin)
            return
        if user_id and registry.has_user_voted(user_id):
            await message.answer(ALREADY_VOTED_BY_USER_TEXT, keyboard=build_menu_keyboard(is_admin))
            return
        if is_admin:
            await message.answer(ADMIN_HELP_TEXT, keyboard=build_menu_keyboard(True))
            return
        await message.answer(
            f"{UNKNOWN_COMMAND_TEXT}\n\n{HELP_TEXT}\n\n{USER_RESTART_TEXT}",
            keyboard=build_menu_keyboard(False),
        )

    return bot
