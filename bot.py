import discord
from discord.ext import commands
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
IVAO_API_KEY = os.getenv("IVAO_API_KEY")

intents = discord.Intents.default()
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
        if p.get("arrival") == icao.upper():
            status = "🟢 Enroute" if p.get("groundspeed", 0) > 50 else "🟡 Ground"
            result.append(f"{p['callsign']} from {p.get('departure')} - {status}")

    if not result:
        await ctx.send(f"No inbound traffic to {icao}")
    else:
        await ctx.send(f"✈️ Inbound {icao}:\n" + "\n".join(result[:10]))

# ✈️ outbound
@bot.command()
async def outbound(ctx, icao):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        if p.get("departure") == icao.upper():
            status = "🟢 Airborne" if p.get("groundspeed", 0) > 50 else "🟡 On ground"
            result.append(f"{p['callsign']} to {p.get('arrival')} - {status}")

    if not result:
        await ctx.send(f"No outbound traffic from {icao}")
    else:
        await ctx.send(f"🛫 Outbound {icao}:\n" + "\n".join(result[:10]))

# ✈️ route
@bot.command()
async def route(ctx, dep, arr):
    data = get_ivao_data()
    pilots = data["clients"]["pilots"]

    result = []

    for p in pilots:
        if p.get("departure") == dep.upper() and p.get("arrival") == arr.upper():
            status = "🟢 Flying" if p.get("groundspeed", 0) > 50 else "🟡 Ground"
            result.append(f"{p['callsign']} - {status}")

    if not result:
        await ctx.send(f"No flights from {dep} to {arr}")
    else:
        await ctx.send(f"✈️ {dep} → {arr}:\n" + "\n".join(result))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)