import discord
from discord import app_commands
from discord.ext import commands

from group_commands.server_shop import *
from utils.db.server_shop import shop_item_autocomplete
from utils.essentials.command_safe import run_command_safe
from utils.essentials.pokemon_autocomplete import *
from utils.essentials.role_checks import *
from utils.logs.pretty_log import pretty_log
from constants.vn_allstars_constants import VNA_SERVER_ID


# 🪻────────────────────────────────────────────
#           ✨ ServerShop Cog Setup ✨
# ─────────────────────────────────────────────
class ServerShop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🪻────────────────────────────────────────────
    #           ✨ Slash Command Group ✨
    # 🪻────────────────────────────────────────────
    shop_group = app_commands.Group(
        name="shop",
        description="Commands related to the server shop",
        guild_ids=[VNA_SERVER_ID],
    )

    # 🪻────────────────────────────────────────────
    #           ✨ /shop view✨
    # 🪻────────────────────────────────────────────
    @shop_group.command(
        name="view", description="View an item or all items in the server shop"
    )
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="Name of the item to view (leave empty to view all items)",
    )
    async def view_shop(
        self,
        interaction: discord.Interaction,
        item_name: str = None,
    ):
        slash_cmd_name = "shop view"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=shop_view_func,
                item_name=item_name,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Error in /shop view command: {e}",
            )
    view_shop.extras = {"category": "Public"}

    # 🪻────────────────────────────────────────────
    #           ✨ /shop add✨
    # 🪻────────────────────────────────────────────
    @shop_group.command(name="add", description="Add an item in the server shop")
    @app_commands.autocomplete(item_name=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="Name of the item to add",
        price="Price of the item in Cherry Pins",
        stock="Stock of the item (-1 for unlimited)",
        description="Description of the item",
    )
    @admin_only()
    async def add_shop_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
        price: int,
        stock: int,
        description: str = None,
    ):
        slash_cmd_name = "shop add-item"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=add_item_func,
            item_name=item_name,
            price=price,
            stock=stock,
            description=description,
        )

    add_shop_item.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /shop edit✨
    # 🪻────────────────────────────────────────────
    @shop_group.command(name="edit", description="Edit an item in the server shop")
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="Name of the item to edit",
        new_price="New price for the item in Cherry Pins",
        new_stock="New stock for the item (-1 for unlimited)",
    )
    @admin_only()
    async def edit_shop_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
        new_price: int = None,
        new_stock: int = None,
    ):
        slash_cmd_name = "shop edit-item"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=edit_item_func,
            item_name=item_name,
            new_price=new_price,
            new_stock=new_stock,
        )

    edit_shop_item.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /shop buy✨
    # 🪻────────────────────────────────────────────
    @shop_group.command(name="buy", description="Buy an item from the server shop")
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="Name of the item to buy",
        amount="Amount of the item to buy",
    )
    async def buy_shop_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
        amount: int,
    ):
        slash_cmd_name = "shop buy-item"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=buy_item_func,
            item_name=item_name,
            amount=amount,
        )

    buy_shop_item.extras = {"category": "Public"}

    # 🪻────────────────────────────────────────────
    #          ✨ /shop remove ✨
    # 🪻────────────────────────────────────────────
    @shop_group.command(
        name="remove", description="Remove an item from the server shop"
    )
    @app_commands.autocomplete(
        item_name=shop_item_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        item_name="Name of the item to remove",
    )
    @admin_only()
    async def remove_shop_item(
        self,
        interaction: discord.Interaction,
        item_name: str,
    ):
        slash_cmd_name = "shop remove-item"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=remove_item_func,
            item_name=item_name,
        )

    remove_shop_item.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #          ✨ /shop clear ✨
    # 🪻────────────────────────────────────────────
    @shop_group.command(
        name="clear", description="Clear all items from the server shop"
    )
    @admin_only()
    async def clear_shop(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "shop clear"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=shop_clear_func,
        )

    clear_shop.extras = {"category": "Staff"}


# 🪻────────────────────────────────────────────
#           ✨ Cog Setup Function ✨
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ServerShop(bot))


