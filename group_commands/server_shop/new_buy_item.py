import random
import re
from datetime import datetime

import discord

from constants.vn_allstars_constants import VN_ALLSTARS_ROLES, KHY_USER_ID, VN_ALLSTARS_TEXT_CHANNELS
from discord import app_commands
from discord.ext import commands
from utils.db.box_prize_db import (
    add_box_prize,
    fetch_box_prizes,
    remove_box_prize,
)
from utils.db.trophy import (
    fetch_user_trophies,
    update_trophies
)
from utils.visuals.design_embed import design_embed
from utils.functions.webhook_func import send_webhook
from constants.server_shop import (
    COLOR,
    DIVIDER,
    SERVER_CURRENCY_EMOJI,
    SERVER_CURRENCY_NAME,
)
from group_commands.box.add_item import log_event
from utils.cache.cache_list import processing_box_item, server_shop_cache
from utils.db.server_shop import remove_item, update_stock
from utils.functions.pokemon_func import get_dex_number_by_name, get_display_name
from utils.logs.pretty_log import pretty_log
from utils.visuals.get_pokemon_gif import get_pokemon_gif
from utils.visuals.pretty_defer import pretty_defer
from constants.vn_allstars_constants import DEVS
from utils.cache.global_variables import Testing

async def open_box_func(
    bot: discord.Client,
    box_name: str,
    testing: bool = False,
):
    """Open a box and get a random item from it.
    Retruns a tuple of (True, prize_name, image_link, msg) or (False, None, None, msg) if there was an error.
    """
    if box_name in processing_box_item:
        error_message = f"⚠️ The box '{box_name}' is currently being opened by another user. Please wait a moment and try again."
        return False, None, None, error_message
    processing_box_item.add(box_name)

    # Get all prizes in the box
    prizes = await fetch_box_prizes(bot=bot, box_name=box_name)
    if not prizes:
        processing_box_item.remove(box_name)
        error_message = f"⚠️ The box '{box_name}' is currently empty. Please contact an admin to add prizes to the box."
        return False, None, None, error_message

    # Get a random prize from the box
    prize_name = random.choice(list(prizes.keys()))
    prize_info = prizes[prize_name]
    image_link = prize_info.get("image_link")

    # Remove the prize from the box in the database
    if not testing:
        try:
            await remove_box_prize(bot=bot, box_name=box_name, prize=prize_name)
            pretty_log(
                tag="info",
                message=f"✅ Successfully removed prize '{prize_name}' from box '{box_name}' after opening.",
                label="🎁 BOX PRIZE",
            )
        except Exception as e:
            pretty_log(
                tag="error",
                message=f"❌ Failed to remove prize '{prize_name}' from box '{box_name}' after opening. Error: {e}",
                label="🎁 BOX PRIZE",
            )
            processing_box_item.remove(box_name)
            error_message = (
                f"⚠️ An error occurred while opening the box. Please try again later."
            )
            return False, None, None, error_message

    # Prepare description for the prize
    prize_name_formatted = get_display_name(prize_name, dex=True)
    return True, prize_name_formatted, image_link, None


async def buy_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    amount: int,
):
    """
    Buy an item from the server shop.
    """
    # Check if event is active or khy is buying for testing
    if Testing.box_prize and interaction.user.id not in DEVS:
        content = "The server shop is currently unavailable. Please check back later."
        await interaction.response.send_message(content=content, ephemeral=True)
        pretty_log(
            "info",
            f"User {interaction.user} attempted to view the shop but the event is not active. Reason: {content}",
            source="Shop View Command",
        )
        return

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Processing your purchase...", ephemeral=False
    )

    # Fetch item from cache
    from utils.cache.server_shop_cache import fetch_shop_item_id_by_name

    item_id = fetch_shop_item_id_by_name(item_name)
    if not item_id:
        await loader.error(content=f"Item '{item_name}' does not exist in the shop.")
        return

    # Get item details
    item = server_shop_cache.get(item_id)
    item_name = item.get("item_name", "Unknown Item")
    price = item.get("price", 0)
    stock = item.get("stock", 0)
    dex = item.get("dex", "N/A")
    image_link = item.get("image_link")
    box_prize = None
    box_name = None

    # Fetch user balance
    user = interaction.user
    user_id = interaction.user.id
    user_name = interaction.user.name
    user_balance = await fetch_user_trophies(bot, user=interaction.user)
    if not user_balance:
        user_balance = 0
    guild = interaction.guild

    if amount <= 0:
        await loader.error(content="You must purchase at least 1 item.")
        return

    purchased_box = True if "box" in item_name.lower() else False
    if purchased_box and amount > 1:
        await loader.error(content="You can only purchase 1 box at a time.")
        return

    # Check stock
    if stock == 0:
        await loader.error(content=f"Sorry, the item '{item_name}' is out of stock.")
        return

    # Check if there are enough items in stock for the requested amount
    if stock > 0 and amount > stock:
        await loader.error(
            content=(
                f"Sorry, there are only {stock} '{item_name}' left in stock. "
                f"You requested {amount}."
            )
        )
        return

    # Calculate total price
    total = price * amount
    # Check if user has enough balance
    if (
        user_balance < total and interaction.user.id != KHY_USER_ID
    ):  # Allow Khy to buy items without balance check for testing
        await loader.error(
            content=(
                f"You do not have enough {SERVER_CURRENCY_NAME} to buy '{item_name}'.\n"
                f"You currently have {user_balance} {SERVER_CURRENCY_EMOJI}."
            )
        )
        return

    # Check if member has vna member role or is a dev
    vna_member_role = guild.get_role(VN_ALLSTARS_ROLES.vna_member)
    if vna_member_role not in interaction.user.roles and interaction.user.id not in DEVS:
        await loader.error(
            content=(
                f"You need to have the {vna_member_role.mention} role to purchase items from the server shop."
            )
        )
        return

    desc_lines = []
    if purchased_box:
        # Process box opening and get prize
        box_name = item_name
        success, box_prize, box_prize_image_url, error_message = await open_box_func(
            bot=bot,
            box_name=item_name,
        )
        if not success:
            await loader.error(content=error_message)
            return
        desc_lines.append(
            f"🎁 {user.mention} bought a **{box_name}** and got **{box_prize}** for {total} {SERVER_CURRENCY_EMOJI}"
        )
    else:
        desc_lines.append(
            f"🛒 {user.mention} bought **{amount}x {item_name}** for {total} {SERVER_CURRENCY_EMOJI}."
        )
    # Deduct price from user balance
    new_balance = user_balance - total
    await update_trophies(bot, user, new_balance)
    item_name = get_display_name(item_name, dex=True)

    title = f"{item_name} Purchased!"
    # Decrease stock if not unlimited
    if stock > 0:
        new_stock = stock - amount
        if not Testing.box_prize:
            await update_stock(bot, item_id, new_stock)
        if new_stock == 0:
            # Remove from database
            await remove_item(bot, item_id)
            pretty_log(
                tag="info",
                message=(
                    f"Item '{item_name}' (item_id: {item_id}) is out of stock and has been removed from the shop."
                ),
                label="🛒 SERVER SHOP",
            )
            title = f"{item_name} is now out of stock!"
            desc_lines.append(
                f"⚠️ The item **{item_name}** is now out of stock and has been removed from the shop."
            )
        else:

            desc_lines.append(f"**Remaining Stock:** {new_stock}.")
    elif stock == -1:
        desc_lines.append(f"**Stock:** Unlimited.")
    desc_lines.append(f"**New Balance:** {new_balance} {SERVER_CURRENCY_EMOJI}.")
    forward_line_str = f"\nPlease forward this message in <#1174386110089146430> and wait for staff to hand your prize."
    desc_lines.append(forward_line_str)

    # Success embed
    embed = discord.Embed(
        title=title,
        description="\n".join(desc_lines),
        color=COLOR,
        timestamp=datetime.now(),
    )
    image_url = (
        box_prize_image_url if purchased_box else image_link if image_link else None
    )
    embed = design_embed(embed=embed, user=interaction.user, thumbnail_url=image_url)

    await loader.success(content="", embed=embed)
    gift_log_channel = guild.get_channel(VN_ALLSTARS_TEXT_CHANNELS.gift_box)
    await log_event(bot=bot, embed=embed, channel=gift_log_channel)

    if purchased_box:
        processing_box_item.remove(box_name)
        pretty_log(
            tag="info",
            message=(
                f"Finished processing purchase of box '{box_name}' for user_id {user_id}. "
                f"Removed from processing list."
            ),
            label="🛒 SERVER SHOP",
        )
