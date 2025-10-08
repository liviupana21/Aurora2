import json
import os
import discord
from discord.ext import commands
from discord.ui import View, Select
from datetime import datetime
import asyncio

# ===== CONFIG =====
TOKEN = "MTQyNTU2MjM1NDA2MTU0NTU5Mw.GP2FAc.0kcpizBULRt3JcTuyqCCLXc0YzsNlsWb_k_LNE"
GUILD_ID = 1423063052420513825
TICKET_PANEL_CHANNEL = "ticket-system"
TICKET_LOG_CHANNEL = "ticket-logs"
TICKET_CATEGORY = "SUPORT"
COUNTER_FILE = "ticket_counter.json"
JSON_TEMPLATE_FILE = "Aurora2_Discord_Template.json"

# Roluri predefinite
ROLE_DEFS = [
    {"name": "Owner", "permissions": discord.Permissions.all()},
    {"name": "Developer", "permissions": discord.Permissions(kick_members=True, ban_members=True, mute_members=True, deafen_members=True, move_members=True)},
    {"name": "Tehnician", "permissions": discord.Permissions(kick_members=True, ban_members=True, mute_members=True, deafen_members=True, move_members=True)},
    {"name": "Moderator discord", "permissions": discord.Permissions.administrator()},
    {"name": "Membru Aurora2", "permissions": discord.Permissions(read_messages=True, send_messages=True, connect=True, create_instant_invite=True)},
    {"name": "Lider Breasla", "permissions": discord.Permissions(read_messages=True, send_messages=True, connect=True)},
    {"name": "Membru Breasla", "permissions": discord.Permissions(read_messages=True, send_messages=True, connect=True)}
]

# ===== INTENTS =====
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Load JSON Template =====
if os.path.exists(JSON_TEMPLATE_FILE):
    with open(JSON_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = json.load(f)
else:
    template = {"categories": []}

# ===== Ticket counter =====
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"counter": 0}, f)

def get_ticket_number():
    with open(COUNTER_FILE, "r") as f:
        data = json.load(f)
    data["counter"] += 1
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)
    return data["counter"]

# ====== Ticket Dropdown/View ======
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Probleme ItemShop", description="Raportează o problemă cu ItemShop-ul", emoji="🛒"),
            discord.SelectOption(label="Raporteaza o problema", description="Raportează o problemă generală", emoji="⚠️"),
            discord.SelectOption(label="Cerere asistență", description="Solicită ajutor de la staff", emoji="🧰"),
        ]
        super().__init__(placeholder="Selectează tipul de ticket 🎫", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY)

        ticket_number = get_ticket_number()
        channel_name = f"ticket-{ticket_number}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await ticket_channel.send(f"🎫 Ticket creat de {interaction.user.mention}\nTip: **{self.values[0]}**")
        await interaction.response.send_message(f"✅ Ticket creat: {ticket_channel.mention}", ephemeral=True)

        log_channel = discord.utils.get(guild.text_channels, name=TICKET_LOG_CHANNEL)
        if log_channel:
            embed = discord.Embed(
                title="🗂️ Ticket deschis",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Tip ticket", value=self.values[0], inline=False)
            embed.add_field(name="Deschis de", value=interaction.user.mention, inline=False)
            embed.add_field(name="Canal", value=ticket_channel.mention, inline=False)
            await log_channel.send(embed=embed)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ====== ON READY ======
@bot.event
async def on_ready():
    print(f"✅ Bot conectat ca {bot.user}")
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Serverul nu a fost găsit!")
        return

    # Creare roluri
    for role_def in ROLE_DEFS:
        role = discord.utils.get(guild.roles, name=role_def["name"])
        if not role:
            await guild.create_role(name=role_def["name"], permissions=role_def["permissions"])
            print(f"✅ Role creat: {role_def['name']}")
        else:
            print(f"⚠️ Role existent: {role_def['name']}")

    # Creare categorii + canale din JSON
    for category in template.get("categories", []):
        cat = discord.utils.get(guild.categories, name=category["name"])
        if not cat:
            cat = await guild.create_category(category["name"])
            print(f"✅ Categorie creată: {category['name']}")
        else:
            print(f"⚠️ Categorie existentă: {category['name']}")

        for ch in category.get("text_channels", []):
            existing = discord.utils.get(guild.text_channels, name=ch)
            if not existing:
                await guild.create_text_channel(ch, category=cat)
                print(f"✅ Text channel creat: {ch}")
        for ch in category.get("voice_channels", []):
            existing = discord.utils.get(guild.voice_channels, name=ch)
            if not existing:
                await guild.create_voice_channel(ch, category=cat)
                print(f"✅ Voice channel creat: {ch}")

    # Creare mesaj permanent cu dropdown în ticket-system
    panel_channel = discord.utils.get(guild.text_channels, name=TICKET_PANEL_CHANNEL)
    if not panel_channel:
        panel_channel = await guild.create_text_channel(TICKET_PANEL_CHANNEL)

    view = TicketView()
    await panel_channel.send("🎫 **Selectează tipul de ticket din meniul de mai jos:**", view=view)
    print("✅ Ticket panel creat!")

# ====== AUTO ROLE ======
@bot.event
async def on_member_join(member):
    guild = member.guild
    role = discord.utils.get(guild.roles, name="Membru Aurora2")
    if role:
        try:
            await member.add_roles(role)
            print(f"✅ Rol „Membru Aurora2” adăugat pentru {member.name}")
        except discord.Forbidden:
            print(f"❌ Nu am permisiunea de a adăuga rolul pentru {member.name}")

# ====== CLOSE TICKET ======
@bot.tree.command(name="close_ticket", description="Închide ticketul curent")
async def close_ticket(interaction: discord.Interaction):
    channel = interaction.channel
    if not channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Aceasta nu este o cameră de ticket.", ephemeral=True)
        return

    log_channel = discord.utils.get(interaction.guild.text_channels, name=TICKET_LOG_CHANNEL)
    if log_channel:
        embed = discord.Embed(
            title="🗂️ Ticket închis",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Canal", value=channel.name, inline=False)
        embed.add_field(name="Închis de", value=interaction.user.mention, inline=False)
        await log_channel.send(embed=embed)

    await interaction.response.send_message("🔒 Ticketul va fi închis în 5 secunde...", ephemeral=True)
    await asyncio.sleep(5)
    await channel.delete()

# ===== RUN BOT =====
bot.run(TOKEN)