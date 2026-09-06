import os
import sys

# Change working directory and sys.path to cipher-bot-hosting-main
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_DIR = os.path.join(BASE_DIR, "cipher-bot-hosting-main")

if os.path.exists(BOT_DIR):
    os.chdir(BOT_DIR)
    if BOT_DIR not in sys.path:
        sys.path.insert(0, BOT_DIR)

import bot

if __name__ == "__main__":
    sys.exit(bot.main())
