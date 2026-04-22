import discord
import requests
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

CHANNEL_ID = 1496389619523129494  # ใส่ channel id ของนาย

async def send_ivao_data():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while True:
        try:
            url = "https://api.ivao.aero/v2/tracker/whazzup"
            data = requests.get(url).json()

            count = 0
            for p in data["clients"]["pilots"]:
                if p.get("arrival") == "VTBD":
                    count += 1

            await channel.send(f"VTBD inbound now: {count}")

        except Exception as e:
            print(e)

        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(send_ivao_data())

client.run(TOKEN)