import discord
from discord import app_commands
from discord.ext import commands

from group_commands.box import *
from utils.db.server_shop import box_item_autocomplete
from utils.essentials.command_safe import run_command_safe
from utils.essentials.pokemon_autocomplete import *
from utils.essentials.role_checks import *
from utils.logs.pretty_log import pretty_log
from constants.vn_allstars_constants import VNA_SERVER_ID


# 🪻────────────────────────────────────────────
#           ✨ Box Cog Setup ✨
# ─────────────────────────────────────────────
class Box_Group(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🪻────────────────────────────────────────────
    #           ✨ Box Command Group ✨
    # 🪻────────────────────────────────────────────
    box_group = app_commands.Group(
        name="box",
        description="Commands related to the box",
        guild_ids=[VNA_SERVER_ID],
    )

    # 🪻────────────────────────────────────────────
    #           ✨ /box list✨
    # 🪻────────────────────────────────────────────
    @box_group.command(name="list", description="List all items in the box")
    @admin_only()
    async def list_box_items(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "box list"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=list_item_func,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Error in /box list command: {e}",
            )

    list_box_items.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /box add-item✨
    # 🪻────────────────────────────────────────────
    @box_group.command(name="add-item", description="Add an item to the box")
    @app_commands.describe(
        box_name="Name of the box to add the item to",
        item_name="Name of the item to add (must be an existing server shop item)",
        amount="Amount of the item to add (default is 1)",
    )
    @app_commands.autocomplete(box_name=box_item_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_name=pokemon_autocomplete)  # 👈 attach autocomplete
    @admin_only()
    async def add_box_item(
        self,
        interaction: discord.Interaction,
        box_name: str,
        item_name: str,
        amount: int = 1,
    ):
        slash_cmd_name = "box add-item"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=add_item_func,
                box_name=box_name,
                item_name=item_name,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Error in /box add-item command: {e}",
            )

    add_box_item.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /box remove-item✨
    # 🪻────────────────────────────────────────────
    @box_group.command(name="remove-item", description="Remove an item from the box")
    @app_commands.describe(
        box_name="Name of the box to remove the item from",
        item_name="Name of the item to remove",
    )
    @app_commands.autocomplete(box_name=box_item_autocomplete)  # 👈 attach autocomplete
    @admin_only()
    async def remove_box_item(
        self,
        interaction: discord.Interaction,
        box_name: str,
        item_name: str,
    ):
        slash_cmd_name = "box remove-item"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=remove_item_func,
                box_name=box_name,
                item_name=item_name,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Error in /box remove-item command: {e}",
            )

    remove_box_item.extras = {"category": "Staff"}


# 🪻────────────────────────────────────────────
#           ✨ Setup Function ✨
# 🪻────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Box_Group(bot))
