import asyncio
import logging
import os
import signal
from dataclasses import dataclass

import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

from cogs.music import Music


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    token: str
    lavalink_uri: str
    lavalink_password: str


class MusicBot(commands.Bot):
    def __init__(self, *, config: BotConfig) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = config

    async def setup_hook(self) -> None:
        await self._connect_nodes()
        await self.add_cog(Music(self))
        logger.info("Music cog loaded and nodes requested")

    async def _connect_nodes(self) -> None:
        node = wavelink.Node(
            identifier="MAIN",
            uri=self.config.lavalink_uri,
            password=self.config.lavalink_password,
        )
        await wavelink.Pool.connect(client=self, nodes=[node])
        logger.info("Wavelink node connection initiated")

    async def close(self) -> None:
        logger.info("Closing bot and disconnecting from Lavalink")
        if wavelink.Pool.is_connected():
            await wavelink.Pool.close()
        await super().close()

    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        logger.info("Wavelink node %s is ready", node.identifier)

    async def on_wavelink_node_disconnect(self, node: wavelink.Node) -> None:
        logger.warning("Wavelink node %s disconnected", node.identifier)


def create_config() -> BotConfig:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    lavalink_uri = os.getenv("LAVALINK_URI", "http://localhost:2333")
    lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

    if not token:
        raise RuntimeError("DISCORD_TOKEN is required to start the bot")

    return BotConfig(
        token=token,
        lavalink_uri=lavalink_uri,
        lavalink_password=lavalink_password,
    )


def main() -> None:
    config = create_config()
    bot = MusicBot(config=config)

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(bot.close()))
        except NotImplementedError:
            # Windows compatibility
            pass

    bot.run(config.token)


if __name__ == "__main__":
    main()
