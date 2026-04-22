import discord
from discord.ext import commands
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
IVAO_API_KEY = os.getenv("IVAO_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_ivao_data():
    url = "https://api.ivao.aero/v2/tracker/whazzup"

    headers = {
        "apiKey": IVAO_API_KEY
    }

    return requests.get(url, headers=headers).json()

# ✈️ inbound
@bot.command()
async def inbound(ctx, icao):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        fp = p.get("flightPlan") or {}
        track = p.get("lastTrack") or {}

        if fp.get("arrivalId") == icao.upper():
            status = track.get("state", "Unknown")
            dep = fp.get("departureId", "----")
            result.append(f"{p['callsign']} from {dep} - {status}")

    if not result:
        await ctx.send(f"No inbound traffic to {icao.upper()}")
    else:
        await ctx.send(f"✈️ Inbound {icao.upper()}:\n" + "\n".join(result[:15]))

# ✈️ outbound
@bot.command()
async def outbound(ctx, icao):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        fp = p.get("flightPlan") or {}
        track = p.get("lastTrack") or {}

        if fp.get("departureId") == icao.upper():
            status = track.get("state", "Unknown")
            arr = fp.get("arrivalId", "----")
            result.append(f"{p['callsign']} to {arr} - {status}")

    if not result:
        await ctx.send(f"No outbound traffic from {icao.upper()}")
    else:
        await ctx.send(f"🛫 Outbound {icao.upper()}:\n" + "\n".join(result[:15]))

# ✈️ route
@bot.command()
async def route(ctx, dep, arr):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        fp = p.get("flightPlan") or {}
        track = p.get("lastTrack") or {}

        if fp.get("departureId") == dep.upper() and fp.get("arrivalId") == arr.upper():
            result.append(f"{p['callsign']} - {track.get('state','Unknown')}")

    if not result:
        await ctx.send(f"No flights from {dep.upper()} to {arr.upper()}")
    else:
        await ctx.send(f"✈️ {dep.upper()} → {arr.upper()}:\n" + "\n".join(result))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")    


bot.run(TOKEN)