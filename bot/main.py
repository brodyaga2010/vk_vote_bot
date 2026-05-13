import logging

from bot.config import get_token
from bot.handlers import create_bot


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    bot = create_bot(get_token())
    bot.run_forever()


if __name__ == "__main__":
    main()
