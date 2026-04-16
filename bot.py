import discord
from discord.ext import commands
import os
import datetime
from dotenv import load_dotenv

# Load environment variables (for token)
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Storage
message_counts = {}
case_number = 0

@bot.event
async def on_ready():
    print(f'✅ Bot is online as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!help | Moderation Bot"))

# Track messages
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in message_counts:
        message_counts[user_id] = 0
    message_counts[user_id] += 1

    await bot.process_commands(message)

# ====================== COMMANDS ======================

@bot.command()
async def messages(ctx, member: discord.Member = None):
    """Check how many messages a user has sent"""
    member = member or ctx.author
    count = message_counts.get(str(member.id), 0)
    embed = discord.Embed(
        title="📊 Message Statistics",
        description=f"{member.mention} has sent **{count:,}** messages.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def owner(ctx):
    """Show server owner"""
    owner = ctx.guild.owner
    embed = discord.Embed(title="👑 Server Owner", description=f"{owner.mention}", color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member with moderation embed"""
    global case_number
    case_number += 1

    # DM the banned user
    ban_embed = discord.Embed(
        title="⛔ You have been banned",
        description=f"You were banned from **{ctx.guild.name}**",
        color=discord.Color.red()
    )
    ban_embed.add_field(name="Banned by", value=ctx.author.mention, inline=False)
    ban_embed.add_field(name="Reason", value=reason, inline=False)
    ban_embed.add_field(name="Case Number", value=f"#{case_number}", inline=False)
    ban_embed.set_footer(text=f"Server: {ctx.guild.name}")
    ban_embed.timestamp = datetime.datetime.utcnow()

    try:
        await member.send(embed=ban_embed)
    except:
        pass  # User has DMs disabled

    # Ban the user
    await member.ban(reason=f"{reason} | Case #{case_number} | Banned by {ctx.author}")

    # Confirmation
    confirm = discord.Embed(
        title="✅ Member Banned Successfully",
        description=f"{member.mention} has been banned.",
        color=discord.Color.red()
    )
    confirm.add_field(name="Moderator", value=ctx.author.mention)
    confirm.add_field(name="Reason", value=reason)
    confirm.add_field(name="Case #", value=f"#{case_number}")
    await ctx.send(embed=confirm)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member"""
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Member Kicked", description=f"{member.mention} has been kicked.", color=discord.Color.orange())
    embed.add_field(name="Moderator", value=ctx.author.mention)
    embed.add_field(name="Reason", value=reason)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """Clear messages in the channel"""
    if amount < 1 or amount > 100:
        await ctx.send("Amount must be between 1 and 100.")
        return
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Cleared **{amount}** messages.", delete_after=5)

@bot.command()
async def announce(ctx, channel: discord.TextChannel, *, message=None):
    """Make an announcement in a specific channel"""
    if not message:
        await ctx.send("Usage: `!announce #channel Your message here`")
        return
    embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.purple())
    embed.set_footer(text=f"Announced by {ctx.author}")
    await channel.send(embed=embed)
    await ctx.send("✅ Announcement sent!", delete_after=3)

@bot.command()
async def echo(ctx, *, message):
    """Make the bot repeat your message"""
    await ctx.send(message)

@bot.command()
async def whois(ctx, member: discord.Member = None):
    """Show user information"""
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info - {member}", color=discord.Color.blurple())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%d %b %Y") if member.joined_at else "Unknown", inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%d %b %Y"), inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(title="🤖 Bot Commands", color=discord.Color.green())
    embed.add_field(name="Utility", value="`!messages [user]`\n`!whois [user]`\n`!owner`\n`!echo <text>`", inline=False)
    embed.add_field(name="Moderation", value="`!ban <user> [reason]`\n`!kick <user> [reason]`\n`!clear <amount>`", inline=False)
    embed.add_field(name="Fun/Utility", value="`!announce #channel <message>`", inline=False)
    embed.set_footer(text="Prefix: !")
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments. Use `!help` for usage.")
    else:
        print(f"Error: {error}")

# ====================== RUN BOT ======================
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN not found! Please set it in .env or environment variables.")
    else:
        bot.run(token)
