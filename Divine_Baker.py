import discord
import logging
from discord.ext import commands
from openpyxl import load_workbook
import random

# -----------------------------
# Load Excel bread names
# -----------------------------
workbook = load_workbook('Bread List.xlsx')
sheet = workbook.active
breadTypes = []

# -----------------------------
# Logging
# -----------------------------
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# -----------------------------
# Intents
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# -----------------------------
# Bot Client (ONLY ONE)
# -----------------------------
bot = commands.Bot(command_prefix='!', intents=intents)

# Track used names per guild
inUseNames = {}

# -----------------------------
# Helper Functions
# -----------------------------
def get_rand_breadname(availableNames):
    return random.choice(availableNames)

async def change_nick(member, new_nickname):
    """Actual nickname changing logic."""
    try:
        await member.edit(nick=new_nickname)
    except Exception as e:
        print(f"Error changing nickname: {e}")

# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
    # Load bread names from column A
    for col_cells in sheet.iter_cols(min_col=1, max_col=1, values_only=True):
        for cell_value in col_cells:
            if cell_value:
                breadTypes.append(cell_value)

    print(f'Logged in as {bot.user}')

    # Process each guild
    for guild in bot.guilds:
        print(f"Guild: {guild.name} (ID: {guild.id})")

        guildInUseNames = []
        availableNames = []

        # Collect nicknames already in use
        for member in guild.members:
            if member.nick:
                guildInUseNames.append(member.nick)

        inUseNames[guild.name] = guildInUseNames

        # Build list of available bread names
        for breadName in breadTypes:
            if breadName not in guildInUseNames:
                availableNames.append(breadName)

        # Assign bread names to members without nicknames
        for member in guild.members:
            if member.nick is None:
                if not availableNames:
                    print("No bread names left!")
                    continue

                randomName = get_rand_breadname(availableNames)
                print(f"Assigning nickname to {member.name}: {randomName}")

                availableNames.remove(randomName)
                inUseNames[guild.name].append(randomName)

                await change_nick(member, randomName)

@bot.event
async def on_member_join(member):
    guild = member.guild

    # Ensure the guild exists in your tracking dictionary
    if guild.name not in inUseNames:
        inUseNames[guild.name] = []

    usedNames = inUseNames[guild.name]

    # Build list of available bread names
    available = [b for b in breadTypes if b not in usedNames]

    if not available:
        print("No bread names left!")
        return

    newBreadName = random.choice(available)
    usedNames.append(newBreadName)

    print(f"Assigning nickname to new member {member.name}: {newBreadName}")

    await change_nick(member, newBreadName)

# -----------------------------
# Commands
# -----------------------------
@bot.command()
async def setnick(ctx, member: discord.Member, new_nickname: str):
    """Command wrapper for nickname changes."""
    try:
        await change_nick(member, new_nickname)
        await ctx.send(f"Changed {member.display_name}'s nickname to {new_nickname}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to change that user's nickname.")
    except discord.HTTPException as e:
        await ctx.send(f"HTTP error: {e}")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
async def joined(ctx, member: discord.Member = None):
    """Shows when a member joined the server and assigns a bread name."""
    print(member.name)
    if member is None:
        member = ctx.author

    guild = member.guild
    usedNames = inUseNames[guild.name]

    # Find a bread name not in use
    available = [b for b in breadTypes if b not in usedNames]

    if not available:
        await ctx.send("No bread names left!")
        return

    newBreadName = get_rand_breadname(available)
    usedNames.append(newBreadName)

    await change_nick(member, newBreadName)

    joined_date = member.joined_at.strftime("%b %d, %Y at %I:%M %p UTC")
    await ctx.send(f"{member.mention} joined on {joined_date} and is now **{newBreadName}**.")

# -----------------------------
# Run Bot
# -----------------------------
bot.run('tokenHere', log_handler=handler)
