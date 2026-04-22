import discord
from discord.ext import commands, tasks
import requests
import os
import sqlite3
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button

from db import init_db
from collector import process_data

TOKEN = os.getenv("DISCORD_TOKEN")
IVAO_API_KEY = os.getenv("IVAO_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def search_flights(dep=None, arr=None, page=1, per_page=10):
    conn = sqlite3.connect("/data/ivao.db")
    cur = conn.cursor()

    sql = """
    SELECT session_id, callsign, aircraft_id, departure, arrival,
           landed_at, status, last_state
    FROM pilot_sessions
    WHERE 1=1
    """

    count_sql = """
    SELECT COUNT(*)
    FROM pilot_sessions
    WHERE 1=1
    """

    params = []

    if dep:
        sql += " AND departure=?"
        count_sql += " AND departure=?"
        params.append(dep.upper())

    if arr:
        sql += " AND arrival=?"
        count_sql += " AND arrival=?"
        params.append(arr.upper())

    total = cur.execute(count_sql, params).fetchone()[0]

    offset = (page - 1) * per_page

    sql += " ORDER BY connected_at DESC LIMIT ? OFFSET ?"
    rows = cur.execute(sql, params + [per_page, offset]).fetchall()

    conn.close()
    return rows, total

def build_search_embed(rows, total, page, per_page):
    embed = discord.Embed(
        title="✈️ Traffic Search Result",
        color=0x2b6cff
    )

    start = (page - 1) * per_page + 1
    end = min(page * per_page, total)

    text = ""

    for row in rows:
        sid, callsign, acft, dep, arr = row[:5]
        status = format_status(row)
        link = f"https://tracker.ivao.aero/sessions/{sid}"

        text += (
            f"**{callsign}** {acft}\n"
            f"{dep} → {arr}\n"
            f"{status} | [Track #{sid}]({link})\n\n"
        )

    embed.description = text[:4000]
    embed.set_footer(text=f"Showing {start}-{end} of {total} | Page {page}")

    return embed

class SearchView(discord.ui.View):
    def __init__(self, dep, arr, page=1):
        super().__init__(timeout=300)

        self.dep = dep
        self.arr = arr
        self.page = page
        self.per_page = 10

        self.update_buttons(1)

    def update_buttons(self, total):
        max_page = max(1, (total + self.per_page - 1) // self.per_page)

        self.prev.disabled = self.page <= 1
        self.next.disabled = self.page >= max_page

    @discord.ui.button(label="⬅ Prev", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.page > 1:
            self.page -= 1

        rows, total = search_flights(
            self.dep, self.arr, self.page, self.per_page
        )

        self.update_buttons(total)

        embed = build_search_embed(
            rows, total, self.page, self.per_page
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(label="Next ➡", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):

        rows, total = search_flights(
            self.dep, self.arr, self.page, self.per_page
        )

        max_page = max(1, (total + self.per_page - 1) // self.per_page)

        if self.page < max_page:
            self.page += 1

        rows, total = search_flights(
            self.dep, self.arr, self.page, self.per_page
        )

        self.update_buttons(total)

        embed = build_search_embed(
            rows, total, self.page, self.per_page
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

def format_status(row):
    landed_at = row[5]
    status = row[6]
    last_state = row[7]

    if landed_at:
        return "🟢 Landed"

    if status == "offline":
        return "🔴 Missing"

    return f"🟡 {last_state or 'Online'}"

class SearchModal(Modal, title="Traffic Search"):

    dep = TextInput(label="Departure ICAO", required=False, max_length=4)
    arr = TextInput(label="Arrival ICAO", required=False, max_length=4)

    async def on_submit(self, interaction: discord.Interaction):

        dep = self.dep.value.strip().upper()
        arr = self.arr.value.strip().upper()

        # Validate English letters only
        if dep and not dep.isalpha():
            await interaction.response.send_message(
                "Please enter Departure ICAO in English letters only.",
                ephemeral=True
            )
            return

        if arr and not arr.isalpha():
            await interaction.response.send_message(
                "Please enter Arrival ICAO in English letters only.",
                ephemeral=True
            )
            return

        # โหลดหน้าแรก
        page = 1
        per_page = 10

        rows, total = search_flights(dep, arr, page, per_page)

        # ถ้าไม่เจอ
        if not rows:
            embed = discord.Embed(
                title="✈️ Traffic Search Result",
                description="No flights found.",
                color=0x2b6cff
            )

            await interaction.response.send_message(embed=embed)
            return

        # สร้าง embed + ปุ่มเปลี่ยนหน้า
        embed = build_search_embed(rows, total, page, per_page)
        view = SearchView(dep, arr, page)

        await interaction.response.send_message(
            embed=embed,
            view=view
        )


@bot.tree.command(
    name="search",
    description="Search traffic history"
)
async def search_command(interaction: discord.Interaction):
    await interaction.response.send_modal(SearchModal())




# ---------------- API ----------------
def get_ivao_data():
    url = "https://api.ivao.aero/v2/tracker/whazzup"

    headers = {
        "apiKey": IVAO_API_KEY
    }

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

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
    print(f"Logged in as {bot.user}", flush=True)

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands", flush=True)
    except Exception as e:
        print("Slash sync error:", e, flush=True)

    if not auto_collect.is_running():
        auto_collect.start()
        print("Collector loop started", flush=True)


# ---------------- AUTO COLLECT ----------------
@tasks.loop(seconds=15)
async def auto_collect():
    try:
        data = get_ivao_data()
        process_data(data)
        print("Collector updated", flush=True)

    except Exception as e:
        print("AUTO COLLECT ERROR:", e, flush=True)

# ---------------- START ----------------
init_db()
bot.run(TOKEN)