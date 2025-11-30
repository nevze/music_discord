import logging
from typing import Optional

import discord
from discord.ext import commands
import wavelink


log = logging.getLogger(__name__)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def ensure_voice(self, ctx: commands.Context) -> wavelink.Player:
        if not ctx.guild:
            raise commands.NoPrivateMessage("This command can only be used in a server.")

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You need to be in a voice channel to use this command.")

        player: Optional[wavelink.Player] = ctx.voice_client  # type: ignore[assignment]
        if not player:
            channel = ctx.author.voice.channel
            player = await channel.connect(cls=wavelink.Player)
            player.queue = wavelink.Queue()  # type: ignore[attr-defined]
        return player

    @commands.command(name="join")
    async def join(self, ctx: commands.Context) -> None:
        """Join the author's voice channel."""

        player = ctx.voice_client
        if player and ctx.author.voice and player.channel == ctx.author.voice.channel:
            await ctx.reply("I'm already in your voice channel!")
            return

        try:
            player = await self.ensure_voice(ctx)
        except commands.CommandError as error:
            await ctx.reply(str(error))
            return

        await ctx.reply(f"Joined {player.channel.mention}.")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Queue up a track from a search query or URL."""

        try:
            player = await self.ensure_voice(ctx)
        except commands.CommandError as error:
            await ctx.reply(str(error))
            return

        tracks = await wavelink.Pool.fetch_tracks(query)
        if not tracks:
            await ctx.reply("No results found for that query.")
            return

        track = tracks[0]
        if not getattr(player, "queue", None):
            player.queue = wavelink.Queue()  # type: ignore[attr-defined]

        if not player.playing and not player.paused:
            await player.play(track)
            await ctx.reply(f"Now playing: **{track}**")
        else:
            player.queue.put(track)  # type: ignore[attr-defined]
            await ctx.reply(f"Added to queue: **{track}**")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if not player:
            await ctx.reply("I'm not connected to a voice channel.")
            return

        if player.is_paused():
            await ctx.reply("Playback is already paused.")
            return

        await player.pause()
        await ctx.reply("Paused playback.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if not player:
            await ctx.reply("I'm not connected to a voice channel.")
            return

        if not player.is_paused():
            await ctx.reply("Playback isn't paused.")
            return

        await player.resume()
        await ctx.reply("Resumed playback.")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if not player or not player.playing:
            await ctx.reply("There's nothing to skip.")
            return

        await ctx.reply("Skipping current track…")
        await player.stop()

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if not player:
            await ctx.reply("I'm not connected to a voice channel.")
            return

        queue = getattr(player, "queue", None)
        if queue:
            queue.clear()

        await player.stop()
        await ctx.reply("Stopped playback and cleared the queue.")

    @commands.command(name="queue")
    async def queue_list(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if not player:
            await ctx.reply("I'm not connected to a voice channel.")
            return

        queue = getattr(player, "queue", None)
        if not queue or not len(queue):
            await ctx.reply("The queue is currently empty.")
            return

        upcoming = list(queue)[:10]
        description = "\n".join(f"`{index + 1}.` {track}" for index, track in enumerate(upcoming))
        await ctx.reply(f"Upcoming tracks:\n{description}")

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if not player:
            await ctx.reply("I'm not connected to a voice channel.")
            return

        queue = getattr(player, "queue", None)
        if queue:
            queue.clear()

        await player.disconnect()
        await ctx.reply("Disconnected from the voice channel.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player = payload.player
        queue = getattr(player, "queue", None)
        if queue and len(queue):
            next_track = queue.pop(0)
            await player.play(next_track)
            channel = player.channel
            if isinstance(channel, discord.VoiceChannel):
                text_channel = self._find_text_channel(channel.guild)
                if text_channel:
                    await text_channel.send(f"Now playing: **{next_track}**")
        else:
            log.info("Queue exhausted for guild %s", player.guild.id)

    def _find_text_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel
        return None

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.reply("This command can only be used in a server.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f"Missing argument: {error.param.name}")
            return

        log.exception("Error handling command %s", ctx.command, exc_info=error)
        await ctx.reply("An error occurred while processing the command.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
