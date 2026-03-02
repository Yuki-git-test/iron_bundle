import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.server_shop import COLOR
from constants.vn_allstars_constants import VN_ALLSTARS_EMOJIS
from utils.db.box_prize_db import (
    add_box_prize,
    fetch_all_box_prizes,
    fetch_box_prize,
    fetch_total_stock_for_box,
)
from utils.functions.pokemon_func import get_dex_number_by_name, get_display_name
from utils.functions.webhook_func import send_webhook
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.get_pokemon_gif import get_pokemon_gif
from utils.visuals.pretty_defer import pretty_defer

# enable_debug(f"{__name__}.list_item_func")


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
    debug_log(f"Fetching all box prizes from the database...")
    box_prizes = await fetch_all_box_prizes(bot)
    if not box_prizes:
        await loader.error(content="No items found in any box.")
        return

    # Create dict for each box with list of items categorized by type (golden, shiny, legendary)
    categorized_boxes = {}

    def format_stocked_list(prizes_dict, filter_func):
        result = []
        for prize_name, prize_info in prizes_dict.items():
            item_name = get_display_name(prize_name, is_long_name=False)
            item_name_no_emoji = strip_emoji(item_name)
            # Use the raw prize_name for filtering, not the formatted name
            if filter_func(prize_name):
                stock = prize_info.get("stock", 1)
                if stock and stock > 1:
                    result.append(f"{stock} {item_name_no_emoji}")
                else:
                    result.append(item_name_no_emoji)
        return result

    box_item_counts = {}
    from utils.db.box_prize_db import fetch_total_stock_for_box

    for box_name, prizes in box_prizes.items():
        debug_log(f"Box: {box_name} | prizes: {prizes}")
        # Fetch DB total for this box for debugging
        db_total = await fetch_total_stock_for_box(bot, box_name)
        debug_log(f"Box: {box_name} | DB total stock: {db_total}")
        already_categorized = set()

        def format_stocked_list_unique(prizes_dict, filter_func):
            result = []
            for prize_name, prize_info in prizes_dict.items():
                if prize_name in already_categorized:
                    continue
                item_name = get_display_name(prize_name, is_long_name=False)
                item_name_no_emoji = strip_emoji(item_name)
                if filter_func(prize_name):
                    stock = prize_info.get("stock", 1)
                    if stock and stock > 1:
                        result.append(f"{stock} {item_name_no_emoji}")
                    else:
                        result.append(item_name_no_emoji)
                    already_categorized.add(prize_name)
            return result

        categorized_boxes[box_name] = {
            "golden": format_stocked_list_unique(
                prizes, lambda n: "golden" in n.lower()
            ),
            "shiny gigantamax": format_stocked_list_unique(
                prizes, lambda n: "shiny gigantamax" in n.lower()
            ),
            "shiny mega": format_stocked_list_unique(
                prizes, lambda n: "shiny mega" in n.lower()
            ),
            "shiny": format_stocked_list_unique(
                prizes,
                lambda n: "shiny" in n.lower()
                and "gigantamax" not in n.lower()
                and "mega" not in n.lower(),
            ),
            "gigantamax": format_stocked_list_unique(
                prizes,
                lambda n: "gigantamax" in n.lower() and "shiny" not in n.lower(),
            ),
            "mega": format_stocked_list_unique(
                prizes,
                lambda n: "mega" in n.lower() and "shiny" not in n.lower(),
            ),
            # Fallback: anything not already categorized
            "legendary": format_stocked_list_unique(
                prizes,
                lambda n: n not in already_categorized,
            ),
        }
        # Always count the total number of items in the box (sum of all stocks, including multiples)
        total_stock = sum(prize_info.get("stock", 1) for prize_info in prizes.values())
        debug_log(f"Box: {box_name} | Computed total stock: {total_stock}")
        for pname, pinfo in prizes.items():
            debug_log(f"  {pname}: stock={pinfo.get('stock', 1)}")
        box_item_counts[box_name] = total_stock
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
    total_all = sum(box_item_counts.values())
    for box_name, categories in categorized_boxes.items():
        count = box_item_counts.get(box_name, 0)
        field_name = f"**{box_name} ({count})**"
        legendary_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_legendary}" + (", ".join(categories["legendary"]))
            if categories["legendary"]
            else ""
        )
        mega_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.mega}" + (", ".join(categories["mega"]))
            if categories["mega"]
            else ""
        )
        gigantamax_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_gmax}" + (", ".join(categories["gigantamax"]))
            if categories["gigantamax"]
            else ""
        )
        shiny_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_shiny}" + (", ".join(categories["shiny"]))
            if categories["shiny"]
            else ""
        )
        shiny_mega_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_smega}" + (", ".join(categories["shiny mega"]))
            if categories["shiny mega"]
            else ""
        )
        shiny_gigantamax_mons_str = (
            f"{VN_ALLSTARS_EMOJIS.vna_shinygmax}"
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
                    shiny_mega_mons_str,
                    shiny_mons_str,
                    gigantamax_mons_str,
                    mega_mons_str,
                    legendary_mons_str,
                ],
            )
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    embed.set_footer(text=f"Total number of all items: {total_all}")
    await loader.success(content="", embed=embed)
