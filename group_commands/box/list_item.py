import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.server_shop import COLOR
from constants.vn_allstars_constants import VN_ALLSTARS_EMOJIS
from utils.db.box_prize_db import (add_box_prize, fetch_all_box_prizes,
                                   fetch_box_prize)
from utils.functions.pokemon_func import (get_dex_number_by_name,
                                          get_display_name)
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.get_pokemon_gif import get_pokemon_gif
from utils.visuals.pretty_defer import pretty_defer


def strip_emoji(item_name):
    # Remove Discord custom emoji (e.g., <...>) and leading emoji/spaces
    item_name = re.sub(r"^<[^>]+>\s*", "", item_name)
    item_name = re.sub(r"^[^a-zA-Z0-9#]+\s*", "", item_name)
    return item_name


async def list_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """List all items in a box."""
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Fetching box items...",
        ephemeral=False,
    )

    # Fetch all box prizes from the database
    box_prizes = await fetch_all_box_prizes(bot)
    if not box_prizes:
        await loader.error(content="No items found in any box.")
        return

    # Create dict for each box with list of items categorized by type (golden, shiny, legendary)
    categorized_boxes = {}
    from collections import Counter
    def format_counted_list(item_list):
        counts = Counter(item_list)
        return [f"{count} {name}" if count > 1 else name for name, count in counts.items()]

    for box_name, prizes in box_prizes.items():
        golden_list = []
        shiny_list = []
        gigantamax_list = []
        shiny_gigantamax_list = []
        legendary_list = []
        for prize_name, prize_info in prizes.items():
            item_name = get_display_name(prize_name)
            item_name_no_emoji = strip_emoji(item_name)
            if "golden" in item_name.lower():
                golden_list.append(item_name_no_emoji)
            if "shiny gigantamax" in item_name.lower():
                shiny_gigantamax_list.append(item_name_no_emoji)
            elif "gigantamax" in item_name.lower():
                gigantamax_list.append(item_name_no_emoji)
            elif "shiny" in item_name.lower():
                shiny_list.append(item_name_no_emoji)
            elif "legendary" in item_name.lower():
                legendary_list.append(item_name_no_emoji)
        categorized_boxes[box_name] = {
            "golden": format_counted_list(golden_list),
            "shiny gigantamax": format_counted_list(shiny_gigantamax_list),
            "shiny": format_counted_list(shiny_list),
            "gigantamax": format_counted_list(gigantamax_list),
            "legendary": format_counted_list(legendary_list),
        }
    # Now categorized_boxes is in the format:
    # {
    #   'box_1': {'golden': [...], 'shiny': [...], 'legendary': [...]},
    #   ...
    # }

    # Create embed
    embed = discord.Embed(
        title="Box Items",
        description="Here are the items currently in the boxes:",
        color=COLOR,
    )
    for box_name, categories in categorized_boxes.items():
        field_name = f"**{box_name}**"
        legendary_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_legendary}" + (", ".join(categories["legendary"]))
            if categories["legendary"]
            else ""
        )
        gigantamax_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_gmax}"
            + (", ".join(categories["gigantamax"]))
            if categories["gigantamax"]
            else ""
        )
        shiny_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_shiny}" + (", ".join(categories["shiny"]))
            if categories["shiny"]
            else ""
        )
        shiny_gigantamax_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_shiny_gmax}"
            + (", ".join(categories["shiny gigantamax"]))
            if categories["shiny gigantamax"]
            else ""
        )
        golden_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_golden}" + (", ".join(categories["golden"]))
            if categories["golden"]
            else ""
        )
        field_value = "\n".join(
            filter(
                None,
                [
                    golden_mons_str,
                    shiny_gigantamax_mons_str,
                    shiny_mons_str,
                    gigantamax_mons_str,
                    legendary_mons_str,
                ],
            )
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    await loader.success(content="", embed=embed)
