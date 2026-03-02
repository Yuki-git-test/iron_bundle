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


async def log_event(
    bot, embed: discord.Embed, channel: discord.TextChannel, context: str = "log_event"
):
    """Log event changes to the designated log channel via webhook if logging is enabled."""
    if not Testing.box_prize:
        pretty_log(
            tag="debug",
            message="Event logging is currently disabled. Skipping log.",
            label="🎁 Event Log",
        )
        return
    if context == "add_item":
        pretty_log(
            tag="info",
            message="Not sending log to Discord channel because context is 'add_item' and we want to avoid spamming logs for every item added.",
            label="🎁 Event Log",
        )
        return  # Don't send logs

    if channel.id == VN_ALLSTARS_TEXT_CHANNELS.gift_box:
        guild = channel.guild
        clan_event_log_channel = guild.get_channel(VN_ALLSTARS_TEXT_CHANNELS.gift_box)
        log_channels = [channel, clan_event_log_channel]
        for log_channel in log_channels:
            await send_webhook(
                channel=log_channel,
                embed=embed,
                bot=bot,
            )
    else:
        await send_webhook(
            channel=channel,
            embed=embed,
            bot=bot,
        )


async def add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    box_name: str,
    item_name: str,
    amount: int = 1,
):
    """Add an item to a box in the database."""
    stock = amount  # Stock to add for this item
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Adding {item_name} to {box_name}...",
        ephemeral=False,
    )
    # Get image link for the item
    image_link = None
    gif_url = get_pokemon_gif(item_name)
    pretty_log(
        tag="debug",
        message=(f"Fetched GIF URL for item '{item_name}': {gif_url}"),
        label="🎁 BOX PRIZE",
    )
    image_link = gif_url if gif_url else None

    # Get dex number for the item
    dex = get_dex_number_by_name(item_name)

    # Add item to the box in the database
    try:
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
        else:
            # Update stock of the box if it already exists
            box_id = existing_box.get("item_id")
            old_stock = existing_box.get("stock", 0)
            new_stock = old_stock + amount
            await update_stock(bot=bot, item_id=box_id, stock=new_stock)

        # Fetch current stock for this item in the box
        existing_prize = await fetch_box_prize_with_box(
            bot, box_name=box_name, prize=item_name
        )
        if existing_prize:
            current_item_stock = existing_prize.get("stock", 0)
            new_item_stock = current_item_stock + amount
        else:
            new_item_stock = amount
        await add_box_prize(
            bot=bot,
            prize=item_name,
            box_name=box_name,
            stock=new_item_stock,
            dex=dex,
            image_link=image_link,
        )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to add item '{item_name}' to box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )
        await loader.error(content=f"⚠️ Failed to add {item_name} to {box_name}.")
        return

    # Build success embed
    display_name = get_display_name(item_name, dex=True)
    embed = discord.Embed(
        title=f"New Box Item Added!",
        description=(
            f"- **Item Name:** {display_name}\n"
            f"- **Box Name:** {box_name}\n"
            f"- **Stock:** {stock}\n"
        ),
        timestamp=datetime.now(),
        color=COLOR,
    )
    embed = design_embed(embed=embed, user=interaction.user, thumbnail_url=image_link)
    await loader.success(content="", embed=embed)
    # Send webhook notification
    log_channel = interaction.guild.get_channel(VN_ALLSTARS_TEXT_CHANNELS.server_log)
    await log_event(bot=bot, embed=embed, channel=log_channel, context="add_item")

