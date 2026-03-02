from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.server_shop import COLOR, SERVER_CURRENCY_EMOJI
from constants.vn_allstars_constants import VN_ALLSTARS_TEXT_CHANNELS
from group_commands.box.add_item import log_event
from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop import fetch_item_by_id, remove_all_items, remove_item
from utils.functions.pokemon_func import get_dex_number_by_name, get_display_name
from utils.logs.pretty_log import pretty_log
from utils.visuals.pretty_defer import pretty_defer


async def remove_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
):
    """
    Remove an item from the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Removing item from shop...", ephemeral=True
    )

    # Fetch existing item in cache to check if it exists
    from utils.cache.server_shop_cache import fetch_shop_item_id_by_name

    item_id = fetch_shop_item_id_by_name(item_name)
    if not item_id:
        await loader.error(content=f"Item '{item_name}' does not exist in the shop.")
        return

    existing_item = server_shop_cache.get(item_id)
    price = existing_item.get("price", 0)
    stock = existing_item.get("stock", 0)
    image_link = existing_item.get("image_link")
    dex = existing_item.get("dex", "N/A")
    item_name = existing_item.get("item_name", "Unknown Item")
    item_name = get_display_name(item_name, dex=True)

    # Remove item from the database
    await remove_item(bot, item_id)

    # Success embed
    desc = (
        f"**Item Name:** {item_name}\n"
        f"**Item ID:** `{item_id}`\n"
        f"**Price:** {price} {SERVER_CURRENCY_EMOJI}\n"
        f"**Stock:** {stock}\n"
    )
    embed = discord.Embed(
        title="Item Removed from Shop",
        description=desc,
        color=COLOR,
        timestamp=datetime.now(),
    )
    if image_link:
        embed.set_thumbnail(url=image_link)

    await loader.success(embed=embed, content="")
    pretty_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) removed item "
            f"'{existing_item['item_name']}' (item_id: {item_id}) from the server shop."
        ),
        label="🛒 SERVER SHOP",
    )
    # Send log embed
    log_channel_id = VN_ALLSTARS_TEXT_CHANNELS.gift_box
    guild = interaction.guild
    log_channel = guild.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(embed=embed)


async def shop_clear_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    Clear all items from the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction,
        content="Clearing all items from shop...",
        ephemeral=True,
    )

    # Remove all items from the database
    await remove_all_items(bot)

    # Success embed
    embed = discord.Embed(
        title="Server Shop Cleared",
        description="All items have been removed from the server shop.",
        color=COLOR,
        timestamp=datetime.now(),
    )
    await loader.success(embed=embed, content="")
    pretty_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) cleared all items from the server shop."
        ),
        label="🛒 SERVER SHOP",
    )

    guild = interaction.guild
    gift_log_channel_id = VN_ALLSTARS_TEXT_CHANNELS.gift_box
    log_channel = guild.get_channel(gift_log_channel_id)
    await log_event(bot=bot, embed=embed, channel=log_channel)
