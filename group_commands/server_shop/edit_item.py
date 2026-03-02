from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.server_shop import COLOR, SERVER_CURRENCY_EMOJI
from constants.vn_allstars_constants import VN_ALLSTARS_TEXT_CHANNELS
from utils.cache.cache_list import server_shop_cache
from utils.db.server_shop import fetch_item_by_id, update_item
from utils.logs.pretty_log import pretty_log
from utils.visuals.pretty_defer import pretty_defer
from utils.functions.pokemon_func import get_dex_number_by_name, get_display_name

async def edit_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    new_price: int = None,
    new_stock: int = None,
    new_image_link: str = None,
):
    """
    Edit an existing item in the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Editing item in shop...", ephemeral=True
    )

    # Fetch existing item in cache to check if it exists
    from utils.cache.server_shop_cache import fetch_shop_item_id_by_name

    item_id = str(fetch_shop_item_id_by_name(item_name))
    if not item_id:
        await loader.error(content=f"Item '{item_name}' does not exist in the shop.")
        return

    existing_item = server_shop_cache.get(item_id)
    old_image_link = existing_item.get("image_link")
    old_price = existing_item.get("price")
    old_stock = existing_item.get("stock")
    dex = existing_item.get("dex")
    old_item_name = existing_item.get("item_name")
    old_item_name = get_display_name(old_item_name, dex=dex)

    # Check if user provided at least one field to update
    if new_price is None and new_stock is None and new_image_link is None:
        await loader.error(content="Please provide at least one field to update.")
        return

    # Update item in the database
    await update_item(
        bot=bot,
        item_id=item_id,
        price=new_price,
        stock=new_stock,
        image_link=new_image_link,
    )

    # Success embed
    desc = f"**Item Name:** {old_item_name} | **ID:** {item_id}\n"
    embed = discord.Embed(
        title="Item Edited in Shop",
        description=desc,
        color=COLOR,
        timestamp=datetime.now(),
    )

    if new_price is not None:
        value_str = f"> - **Old:** {old_price} {SERVER_CURRENCY_EMOJI}\n> - **New:** {new_price} {SERVER_CURRENCY_EMOJI}"
        embed.add_field(name="Price", value=value_str, inline=False)

    if new_stock is not None:
        value_str = f"> - **Old:** {old_stock}\n> - **New:** {new_stock}"
        embed.add_field(name="Stock", value=value_str, inline=False)

    if new_image_link is not None:
        value_str = f"> - **Old:** {old_image_link}\n> - **New:** {new_image_link}"
        embed.add_field(name="Image Link", value=value_str, inline=False)

    if new_image_link is not None:
        embed.set_thumbnail(url=new_image_link)
    elif old_image_link := existing_item.get("image_link"):
        embed.set_thumbnail(url=old_image_link)

    await loader.success(embed=embed, content="")
    pretty_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) edited item "
            f"'{item_id}' in the server shop."
        ),
        label="🛒 SERVER SHOP",
    )

    # Send log embed
    log_channel_id = VN_ALLSTARS_TEXT_CHANNELS.gift_box
    guild = interaction.guild
    log_channel = guild.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(embed=embed)

        await log_channel.send(embed=embed)
