import re

import discord
from discord import app_commands
from discord.ext import commands

from constants.server_shop import COLOR, SERVER_CURRENCY_EMOJI
from constants.vn_allstars_constants import VN_ALLSTARS_TEXT_CHANNELS
from group_commands.box.add_item import log_event
from utils.db.server_shop import upsert_item
from utils.functions.pokemon_func import get_dex_number_by_name, get_display_name
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.get_pokemon_gif import get_pokemon_gif
from utils.visuals.pretty_defer import pretty_defer


async def add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    price: int,
    stock: int,
    description: str = None,
):
    """
    Add or update an item in the server shop.
    """
    image_link = None
    if "coins" in item_name.lower() or "box" in item_name.lower():
        image_link = None

    else:
        # Clean item name and remove # and dex number if present
        item_name = re.sub(r"\s*#\d+$", "", item_name)
        pretty_log(
            tag="debug",
            message=(f"Cleaned item name: {item_name}"),
            label="🛒 SERVER SHOP",
        )
        gif_url = get_pokemon_gif(item_name)
        pretty_log(
            tag="debug",
            message=(f"Fetched GIF URL for item '{item_name}': {gif_url}"),
            label="🛒 SERVER SHOP",
        )
        image_link = gif_url if gif_url else None

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Adding item to shop...", ephemeral=True
    )
    dex = get_dex_number_by_name(item_name)
    # Upsert item in the database
    item_id = await upsert_item(
        bot=bot,
        item_name=item_name,
        price=price,
        stock=stock,
        image_link=image_link,
        description=description,
        dex=dex,
    )
    if not item_id:
        await loader.error("Failed to add item to the shop. Please try again later.")
        return

    # Success embed
    display_name = get_display_name(item_name, dex=True)
    description_line = f"**Description:** {description}\n" if description else ""
    embed = discord.Embed(
        title="Item Added to Shop",
        description=(
            f"**Item Name:** {display_name}\n"
            f"**Item ID:** `{item_id}`\n"
            f"**Price:** {price} {SERVER_CURRENCY_EMOJI}\n"
            f"**Stock:** {stock}\n"
            f"{description_line}"
        ),
        color=COLOR,
    )
    if image_link:
        embed.set_thumbnail(url=image_link)
    await loader.success(embed=embed, content="")
    pretty_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) added item "
            f"'{item_name}' (item_id: {item_id}, price: {price}, stock: {stock}) in the server shop."
        ),
        label="🛒 SERVER SHOP",
    )
    guild = interaction.guild
    gift_log_channel = guild.get_channel(VN_ALLSTARS_TEXT_CHANNELS.gift_box)
    await log_event(bot=bot, embed=embed, channel=gift_log_channel)
    await log_event(bot=bot, embed=embed, channel=gift_log_channel)
    await log_event(bot=bot, embed=embed, channel=gift_log_channel)
