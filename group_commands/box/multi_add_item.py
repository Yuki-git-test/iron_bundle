import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.server_shop import COLOR, SERVER_CURRENCY_EMOJI
from constants.vn_allstars_constants import VN_ALLSTARS_TEXT_CHANNELS
from utils.cache.global_variables import Testing
from utils.db.box_prize_db import (
    add_box_prize,
    fetch_box_prize,
    fetch_box_prize_with_box,
)
from utils.db.server_shop import fetch_item_by_name, update_stock, upsert_item
from utils.functions.pokemon_func import get_dex_number_by_name, get_display_name
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.get_pokemon_gif import get_pokemon_gif
from utils.visuals.pretty_defer import pretty_defer

from .add_item import log_event


async def multi_add_item_func(
    bot: commands.Bot,
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
    stock = 1

    # Defer
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Adding items to {box_name}...",
        ephemeral=False,
    )

    # Check if box exists
    existing_box = await fetch_item_by_name(bot, item_name=box_name)
    if not existing_box:
        # Upsert box in the database if it doesn't exist
        try:
            box_id = await upsert_item(
                bot=bot,
                item_name=box_name,
                price=10000,
                stock=0,
                image_link=None,
                description=None,
                dex=None,
            )
            pretty_log(
                tag="info",
                message=f"Created new box '{box_name}' in server shop with ID {box_id}.",
                label="🎁 BOX PRIZE DB",
            )
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"⚠️ Failed to create box '{box_name}' in server shop: {e}",
                label="🎁 BOX PRIZE DB",
            )
            await loader.error(
                content=f"⚠️ Failed to create box '{box_name}' in server shop."
            )
            return

    # List of items to add
    items_to_add = [
        item_1,
        item_2,
        item_3,
        item_4,
        item_5,
        item_6,
        item_7,
        item_8,
        item_9,
        item_10,
    ]
    items_to_add = [item for item in items_to_add if item is not None]

    # Add each item to the box, incrementing stock if it already exists
    for item_name in items_to_add:
        dex = get_dex_number_by_name(item_name)
        image_link = get_pokemon_gif(item_name)
        try:
            # Check if the item already exists in the box
            existing_prize = await fetch_box_prize_with_box(
                bot, box_name=box_name, prize=item_name
            )
            if existing_prize:
                current_item_stock = existing_prize.get("stock", 0)
                new_item_stock = current_item_stock + 1
            else:
                new_item_stock = 1
            await add_box_prize(
                bot=bot,
                box_name=box_name,
                prize=item_name,
                stock=new_item_stock,
                image_link=image_link,
                dex=dex,
            )
            pretty_log(
                tag="info",
                message=f"Added item '{item_name}' to box '{box_name}' with stock {new_item_stock}.",
                label="🎁 BOX PRIZE DB",
            )
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"⚠️ Failed to add item '{item_name}' to box '{box_name}': {e}",
                label="🎁 BOX PRIZE DB",
            )
            await loader.error(
                content=f"⚠️ Failed to add item '{item_name}' to box '{box_name}'."
            )
            return
    # Update stock of the box itself to reflect the new items added
    try:
        existing_box = await fetch_item_by_name(bot, item_name=box_name)
        box_id = existing_box.get("item_id")
        old_stock = existing_box.get("stock", 0)
        new_stock = old_stock + len(items_to_add)
        await update_stock(bot=bot, item_id=box_id, stock=new_stock)

        # Success embed
        desc = (
            f"**Box Name:** {box_name}\n"
            f"**Items Added:** {', '.join(items_to_add)}\n"
            f"**Total Items in Box:** {new_stock}\n"
        )
        embed = discord.Embed(
            title=f"Items Added to {box_name}!",
            description=desc,
            color=COLOR,
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        await loader.success(embed=embed, content="")
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update stock for box '{box_name}' after adding items: {e}",
            label="🎁 BOX PRIZE DB",
        )
        await loader.error(
            content=f"⚠️ Failed to update stock for box '{box_name}' after adding items."
        )
        return
