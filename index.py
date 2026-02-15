import discord
from discord.ext import commands
import yt_dlp
import asyncio

TOKEN = "MTQ2OTIxMTczNTYwODI2NjkzNA.G-wMhV.D1aBR0GkXRNJT88Jhusuhx9isytKsJ5pLAwI34"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True,
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
@classmethod
async def from_url(cls, url, *, loop=None, stream=True):
    loop = loop or asyncio.get_event_loop()

    # If not a URL, search YouTube
    if not url.startswith("http"):
        url = f"ytsearch:{url}"

    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(url, download=not stream)
    )

    if 'entries' in data:
        data = data['entries'][0]

    filename = data['url'] if stream else ytdl.prepare_filename(data)
    return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def play(ctx, *, url):
    if ctx.author.voice is None:
        await ctx.send("Join a voice channel first.")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player)
        await ctx.send(f'Now playing: {player.title}')


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Stopped.")


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the channel.")


bot.run(TOKEN)
