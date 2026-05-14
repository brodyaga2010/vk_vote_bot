import logging
import asyncio
import random

from bot.config import get_token, get_admin_ids, EVENT_TITLE
from bot.handlers import create_bot


async def notify_admins_start(bot) -> None:
    admin_ids = get_admin_ids()
    if not admin_ids:
        return
    text = f"Бот запущен и готов принимать сообщения.\n{EVENT_TITLE}"
    for admin in admin_ids:
        try:
            await bot.api.messages.send(peer_id=admin, message=text, random_id=random.randint(1, 2**31 - 1))
        except Exception:
            logging.exception("Не удалось отправить уведомление админу: %s", admin)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    bot = create_bot(get_token())

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(notify_admins_start(bot))
    except Exception:
        logging.exception("Ошибка при отправке стартовых уведомлений администраторам")

    bot.run_forever()


if __name__ == "__main__":
    main()
