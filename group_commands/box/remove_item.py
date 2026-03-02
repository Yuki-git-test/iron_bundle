import re
from datetime import datetime

import discord
from discord.ext import commands

from constants.server_shop import COLOR
from constants.vn_allstars_constants import VN_ALLSTARS_TEXT_CHANNELS
from utils.db.box_prize_db import fetch_box_prize_with_box, remove_box_prize
from utils.functions.pokemon_func import get_display_name
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer

from .add_item import log_event


async def remove_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    box_name: str,
    item_name: str,
):
    """Remove an item from a box in the database."""
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Removing {item_name} from {box_name}...",
        ephemeral=False,
    )

    #  Check if the item exists in the box
    existing_prize = await fetch_box_prize_with_box(
        bot, box_name=box_name, prize=item_name
    )

    if not existing_prize:
        await loader.error(content=f"{item_name} is not in {box_name}.")
        return

    # Get data for the item to be removed (for logging purposes)
    dex = existing_prize.get("dex")
    image_link = existing_prize.get("image_link")
    stock = existing_prize.get("stock")

    # Remove the item from the box in the database
    try:
        await remove_box_prize(bot=bot, box_name=box_name, prize=item_name)
        pretty_log(
            tag="info",
            message=f"✅ Successfully removed item '{item_name}' from box '{box_name}'.",
            label="🎁 BOX PRIZE",
        )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to remove item '{item_name}' from box '{box_name}': {e}",
            label="🎁 BOX PRIZE",
        )
        await loader.error(content=f"Failed to remove {item_name} from {box_name}.")
        return

    # Build success embed
    display_name = get_display_name(item_name, dex=True)
    embed = discord.Embed(
        title=f"Removed {display_name} from {box_name}",
        description=(
            f"Successfully removed **{display_name}** from **{box_name}**.\n"
            f"**Dex Number:** {dex}\n"
            f"**Stock:** {stock}\n"
        ),
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed = design_embed(embed=embed, user=interaction.user, thumbnail_url=image_link)
    await loader.success(content="", embed=embed)

    # Send webhook notification
    log_channel = interaction.guild.get_channel(VN_ALLSTARS_TEXT_CHANNELS.server_log)
    await log_event(bot=bot, embed=embed, channel=log_channel)
