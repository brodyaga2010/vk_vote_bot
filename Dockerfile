FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY bot ./bot
COPY run_bot.sh ./run_bot.sh

RUN python -m pip install --upgrade pip && \
    python -m pip install . && \
    chmod +x /app/run_bot.sh

CMD ["/app/run_bot.sh"]
