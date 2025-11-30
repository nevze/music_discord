# Music Discord Bot

A basic Discord music bot using `discord.py` and `Wavelink` to connect to a Lavalink server.

## Prerequisites

- Python 3.11+
- A Discord bot token
- Access to a running Lavalink server

## Setup

1. Clone the repository and install dependencies:

```bash
pip install -e .
```

2. Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required settings:

- `DISCORD_TOKEN`: Your Discord bot token.
- `LAVALINK_URI`: Lavalink server URI (e.g., `http://localhost:2333`).
- `LAVALINK_PASSWORD`: Lavalink server password (default: `youshallnotpass`).

## Running the bot

```bash
python -m src.bot
```

The bot uses the `!` prefix and requires the `message_content` intent to be enabled for the bot in the Discord Developer Portal.

## Lavalink server

1. Download Lavalink (v4) from the [official releases](https://github.com/freyacodes/Lavalink/releases).
2. Add the following snippet to your `application.yml` if it is not present:

```yaml
server:
  port: 2333
lavalink:
  server:
    password: youshallnotpass
    sources:
      youtube: true
      soundcloud: true
      spotify: true
```

3. Start Lavalink:

```bash
java -jar Lavalink.jar
```

Ensure the URI and password match the values in your `.env` file.

## Commands

- `!join`: Connect the bot to your current voice channel.
- `!play <query or URL>`: Play or queue a track.
- `!pause`: Pause playback.
- `!resume`: Resume playback.
- `!skip`: Skip the current track.
- `!stop`: Stop playback and clear the queue.
- `!queue`: Show the next tracks in the queue.
- `!disconnect` / `!leave`: Disconnect from the voice channel.

## Logging and shutdown

The bot logs basic events to stdout and handles SIGINT/SIGTERM for a graceful shutdown, closing the Lavalink node connections before exiting.
