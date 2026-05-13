#!/bin/sh
set -eu

STOP_FLAG_PATH="${STOP_FLAG_PATH:-/app/bot/data/bot_stopped.flag}"
STOP_EXIT_CODE="${STOP_EXIT_CODE:-42}"

while true
do
  if [ -f "$STOP_FLAG_PATH" ]; then
    echo "Bot is stopped by admin command. Remove $STOP_FLAG_PATH to start it again."
    sleep infinity
  fi

  set +e
  python -m bot.main
  exit_code=$?
  set -e

  if [ "$exit_code" -eq "$STOP_EXIT_CODE" ]; then
    mkdir -p "$(dirname "$STOP_FLAG_PATH")"
    touch "$STOP_FLAG_PATH"
    echo "Bot stopped by admin command. Container will stay idle."
    sleep infinity
  fi

  echo "Bot exited with code $exit_code. Restarting in 5 seconds..."
  sleep 5
done
