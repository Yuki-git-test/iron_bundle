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
    #           ✨ /box multi-add-item✨
    # 🪻────────────────────────────────────────────
    @box_group.command(name="multi-add-item", description="Add multiple items to the box at once")
    @app_commands.describe(
        box_name="Name of the box to add the items to",
        item_1="Name of the first item to add",
        item_2="Name of the second item to add (optional)",
        item_3="Name of the third item to add (optional)",
        item_4="Name of the fourth item to add (optional)",
        item_5="Name of the fifth item to add (optional)",
        item_6="Name of the sixth item to add (optional)",
        item_7="Name of the seventh item to add (optional)",
        item_8="Name of the eighth item to add (optional)",
        item_9="Name of the ninth item to add (optional)",
        item_10="Name of the tenth item to add (optional)",
    )
    @app_commands.autocomplete(box_name=box_item_autocomplete)  # 👈 attach
    @app_commands.autocomplete(item_1=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_2=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_3=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_4=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_5=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_6=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_7=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_8=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_9=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.autocomplete(item_10=pokemon_autocomplete)  # 👈 attach autocomplete
    @admin_only()
    async def multi_add_box_items(
        self,
        interaction: discord.Interaction,
        box_name: str,
        item_1: str,
        item_2: str = None,
        item_3: str = None,
        item_4: str = None,
        item_5: str = None,
        item_6: str = None,
        item_7: str = None,
        item_8: str = None,
        item_9: str = None,
        item_10: str = None,
    ):
        slash_cmd_name = "box multi-add-item"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=multi_add_item_func,
                box_name=box_name,
                item_1=item_1,
                item_2=item_2,
                item_3=item_3,
                item_4=item_4,
                item_5=item_5,
                item_6=item_6,
                item_7=item_7,
                item_8=item_8,
                item_9=item_9,
                item_10=item_10,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Error in /box multi-add-item command: {e}",
            )
    multi_add_box_items.extras = {"category": "Staff"}
    
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
