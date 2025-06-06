import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from detoxy.app.config import Config
from detoxy.app.logger import setup_logger

load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_GUILD = discord.Object(id=1380173035952410624)

logger = setup_logger("bot", Config.log_dir)
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())


async def load():
    """Load cogs as extensions."""
    for filename in os.listdir(os.path.join(os.path.dirname(__file__), "cogs")):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"detoxy.app.cogs.{filename[:-3]}")
                logger.info(f"Loaded extension: {filename[:-3]}")
            except Exception as e:
                logger.error(f"Failed to load extension {filename[:-3]}: {str(e)}")


async def main():
    async with bot:
        await load()
        logger.info("Starting bot...")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
