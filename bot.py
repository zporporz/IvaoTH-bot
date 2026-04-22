import discord
from discord.ext import commands, tasks
import requests
import os

from db import init_db
from collector import process_data

TOKEN = os.getenv("DISCORD_TOKEN")
IVAO_API_KEY = os.getenv("IVAO_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------- API ----------------
def get_ivao_data():
    url = "https://api.ivao.aero/v2/tracker/whazzup"

    headers = {
        "apiKey": IVAO_API_KEY
    }

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


# ---------------- AUTO COLLECT ----------------
@tasks.loop(seconds=15)
async def auto_collect():
    try:
        data = get_ivao_data()
        process_data(data)
        print("Collector updated")

    except Exception as e:
        print("AUTO COLLECT ERROR:", e)


# ---------------- HELPERS ----------------
async def delete_command(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass


# ---------------- COMMANDS ----------------
@bot.command()
async def ping(ctx):
    await ctx.send("pong")
    await delete_command(ctx)


@bot.command()
async def inbound(ctx, icao):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        fp = p.get("flightPlan") or {}
        track = p.get("lastTrack") or {}

        if fp.get("arrivalId") == icao.upper():
            dep = fp.get("departureId", "----")
            state = track.get("state", "Unknown")
            result.append(f"{p['callsign']} from {dep} - {state}")

    if result:
        await ctx.send(f"✈️ Inbound {icao.upper()}:\n" + "\n".join(result[:15]))
    else:
        await ctx.send(f"No inbound traffic to {icao.upper()}")

    await delete_command(ctx)


@bot.command()
async def outbound(ctx, icao):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        fp = p.get("flightPlan") or {}
        track = p.get("lastTrack") or {}

        if fp.get("departureId") == icao.upper():
            arr = fp.get("arrivalId", "----")
            state = track.get("state", "Unknown")
            result.append(f"{p['callsign']} to {arr} - {state}")

    if result:
        await ctx.send(f"🛫 Outbound {icao.upper()}:\n" + "\n".join(result[:15]))
    else:
        await ctx.send(f"No outbound traffic from {icao.upper()}")

    await delete_command(ctx)


@bot.command()
async def route(ctx, dep, arr):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        fp = p.get("flightPlan") or {}
        track = p.get("lastTrack") or {}

        if fp.get("departureId") == dep.upper() and fp.get("arrivalId") == arr.upper():
            result.append(f"{p['callsign']} - {track.get('state', 'Unknown')}")

    if result:
        await ctx.send(f"✈️ {dep.upper()} → {arr.upper()}:\n" + "\n".join(result))
    else:
        await ctx.send(f"No flights from {dep.upper()} to {arr.upper()}")

    await delete_command(ctx)


# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not auto_collect.is_running():
        auto_collect.start()


# ---------------- START ----------------
init_db()
bot.run(TOKEN)