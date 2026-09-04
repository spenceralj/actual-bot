import asyncio
import os
import sys
from datetime import date

from dotenv import load_dotenv

import bot

load_dotenv()

if os.getenv("DISCORD_BOT_TOKEN") is None:
    print("MISSING DISCORD_BOT_TOKEN IN .env!!!!!!!")
    sys.exit(1)

if __name__ == "__main__":
    bot.client.run(os.getenv("DISCORD_BOT_TOKEN", ""))
