import asyncio
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks

from constants.vn_allstars_constants import VNA_SERVER_ID
from utils.cache.central_cache_loader import load_all_cache
from utils.db.get_pg_pool import get_pg_pool
from utils.logs.pretty_log import pretty_log, set_iron_bundle_bot
from dotenv import load_dotenv

# ---- Intents / Bot ----
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
set_iron_bundle_bot(bot)


# ❀───────────────────────────────❀
#   💖  App Command Error Handler 💖
# ❀───────────────────────────────❀
@bot.tree.error
async def on_app_command_error(interaction, error):
    from utils.essentials.role_checks import (
        AdminCheckFailure,
        VNAStaffCheckFailure,
    )


    if isinstance(error, VNAStaffCheckFailure):
        await interaction.response.send_message(str(error), ephemeral=True)

    elif isinstance(error, AdminCheckFailure):
        await interaction.response.send_message(str(error), ephemeral=True)

    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
    else:
        await interaction.response.send_message("An error occurred.", ephemeral=True)
    pretty_log(
        tag="info",
        message=f"App command error: {error}",
        include_trace=True,
    )


# ❀───────────────────────────────❀
#   💖  Prefix Command Error Handler 💖
# ❀───────────────────────────────❀
@bot.event
async def on_command_error(ctx, error):
    # Ignore prefix command not found
    if isinstance(error, commands.CommandNotFound):
        return

    # Handle other prefix errors
    await ctx.send("❌ Something went wrong.")
    pretty_log(
        tag="error",
        message=f"Prefix command error: {error}",
        include_trace=True,
    )


# 🟣────────────────────────────────────────────
#         ⚡ Hourly Cache Refresh Task ⚡
# 🟣────────────────────────────────────────────
@tasks.loop(hours=1)
async def refresh_all_caches():

    # Removed first-run skip logic so cache loads immediately
    await load_all_cache(bot)


# 🟣────────────────────────────────────────────
#         ⚡ Startup Checklist ⚡
# 🟣────────────────────────────────────────────
async def startup_checklist(bot: commands.Bot):
    from utils.cache.cache_list import (
        market_value_cache,
        vna_members_cache,
        webhook_url_cache,
    )

    total_market_values = len(market_value_cache)
    # ❀ This divider stays untouched ❀
    print("\n────────────────────────⋆⋅☆⋅⋆ ────────────────────────")
    print(f"✅ {len(bot.cogs)} ❄️ Cogs Loaded")
    print(f"✅ {len(vna_members_cache)} 🐧  VNA Members")
    print(f"✅ {total_market_values:,} 💵  Market Values")
    print(f"✅ {len(webhook_url_cache)} 🌨️  Webhook Urls")
    pg_status = "Ready" if hasattr(bot, "pg_pool") else "Not Ready"
    print(f"✅ {pg_status} 🧊  PostgreSQL Pool")
    total_slash_commands = sum(1 for _ in bot.tree.walk_commands())
    print(f"✅ {total_slash_commands} ⛄ Slash Commands Synced")
    print("────────────────────────⋆⋅☆⋅⋆ ────────────────────────\n")


# 🟣────────────────────────────────────────────
#         ⚡ Load Cogs ⚡
# 🟣────────────────────────────────────────────
async def load_extensions():
    """
    Dynamically load all Python files in the 'cogs' folder (ignores __pycache__).
    Logs loaded cogs with pretty_log and errors if loading fails.
    """
    loaded_cogs = []
    for root, dirs, files in os.walk("cogs"):
        # Skip __pycache__ folders
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Skip pokemons.py specifically in the cogs folder
                if root == "cogs" and file == "pokemons.py":
                    continue
                module_path = (
                    os.path.join(root, file).replace(os.sep, ".").replace(".py", "")
                )
                try:
                    await bot.load_extension(module_path)
                    loaded_cogs.append(module_path)
                except Exception as e:
                    pretty_log(
                        message=f"❌ Failed to load cog: {module_path}\n{e}",
                        tag="error",
                    )
    _loaded_count = len(loaded_cogs)
    pretty_log("ready", f"✅ Loaded { _loaded_count} cogs")  #


# 🟣────────────────────────────────────────────
#         ⚡ On Ready ⚡
# 🟣────────────────────────────────────────────
@bot.event
async def on_ready():
    # Guard for type checker: bot.user may be Optional
    user = bot.user
    if user is None:
        pretty_log("info", "Bot is online (user not yet cached).")
    else:
        pretty_log("info", f"Bot online as {user} (ID: {user.id})")

    # Sync commands to VNA server
    try:
        await bot.tree.sync(guild=discord.Object(id=VNA_SERVER_ID))
        pretty_log("info", f"Slash commands synced to guild {VNA_SERVER_ID}")
    except Exception as e:
        pretty_log("error", f"Slash sync to VNA server failed: {e}")

    # Start the hourly cache refresh task
    if not refresh_all_caches.is_running():
        refresh_all_caches.start()
        pretty_log(message="✅ Started hourly cache refresh task", tag="ready")

    # Load caches immediately before checklist
    from utils.cache.central_cache_loader import load_all_cache

    await load_all_cache(bot)

    # ❀ Run startup checklist ❀
    await startup_checklist(bot)

    try:
        await bot.change_presence(activity=discord.Game(name="🐧 /commands"))
    except Exception:
        pass


# 🟣────────────────────────────────────────────
#         ⚡ Main ⚡
# 🟣────────────────────────────────────────────
async def main():
    # Load extensions
    await load_extensions()

    # Intialize the database pool
    try:
        bot.pg_pool = await get_pg_pool()
        pretty_log(message="✅ PostgreSQL connection pool established", tag="ready")
    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Failed to initialize database pool: {e}",
            include_trace=True,
        )
        return  # Exit if DB connection fails

    load_dotenv()
    pretty_log("ready", "Iron Bundle Bot is starting...")

    retry_delay = 5
    while True:
        try:
            await bot.start(os.getenv("DISCORD_TOKEN"))
        except KeyboardInterrupt:
            pretty_log("ready", "Shutting down Iron Bundle Bot...")
            break
        except Exception as e:
            pretty_log("error", f"Bot crashed: {e}", include_trace=True)
            pretty_log("ready", f"Restarting Iron Bundle Bot in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)

# ❀───────────────────────────────❀
#       💖  Entry Point 💖
# ❀───────────────────────────────❀
if __name__ == "__main__":
    asyncio.run(main())
