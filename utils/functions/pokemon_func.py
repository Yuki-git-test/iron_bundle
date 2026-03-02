from constants.paldea_galar_dict import get_dex_number_by_name, rarity_meta
from constants.pokemon_dex import *
from constants.vn_allstars_constants import (
    KHY_USER_ID,
    VN_ALLSTARS_EMOJIS,
    VN_ALLSTARS_ROLES,
    YUKI_USER_ID,
)
from utils.db.market_value_db import (
    fetch_market_value_cache,
    is_pokemon_exclusive_cache,
)
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

IN_GAME_MONS_LIST = (
    list(common_mons.keys())
    + list(uncommon_mons.keys())
    + list(rare_mons.keys())
    + list(superrare_mons.keys())
    + list(legendary_mons.keys())
    + list(mega_mons.keys())
    + list(gigantamax_mons.keys())
    + list(shiny_mons.keys())
    + list(shiny_mega_mons.keys())
    + list(shiny_gigantamax_mons.keys())
    + list(golden_mons.keys())
    + list(exclusive_mons.keys())
)

exclusive_mons_list = list(exclusive_mons.keys())


def get_embed_color_by_rarity(pokemon_name: str) -> int:
    rarity = get_rarity(pokemon_name)
    if rarity:
        meta = rarity_meta.get(rarity, {})
        color = meta.get("color")
        # If color is missing for shiny mega or shiny gigantamax, use shiny color
        if color is not None:
            return color
        elif rarity in ["shiny mega", "shiny gigantamax"]:
            shiny_color = rarity_meta.get("shiny", {}).get("color", 0xFFFFFF)
            return shiny_color
    return 0xFFFFFF  # Default to white if rarity is unknown


def format_price_w_coin(n: int) -> str:
    """Format PokeCoin price with commas (no K/M shorthand)."""
    pokecoin = VN_ALLSTARS_EMOJIS.vna_pokecoin
    n = int(n)  # Ensure n is an integer
    return f"{pokecoin} {n:,}"


def strip_prefixes(pokemon_name: str):
    """
    Strip form prefixes from a Pokémon name to get the base name for market value lookup.
    Handles prefixes like "Shiny", "Mega", "Gigantamax", "Shiny Mega", etc.
    """
    prefixes = [
        "shiny mega",
        "shiny gigantamax",
        "golden mega",
        "gigantamax",
        "mega",
        "shiny",
        "golden",
    ]
    pokemon_name_lower = pokemon_name.lower()
    for prefix in prefixes:
        for sep in [" ", "-"]:
            if pokemon_name_lower.startswith(prefix + sep):
                return pokemon_name[len(prefix) + 1 :].strip()
    return pokemon_name.strip().title()


RARITY_W_LONG_NAME = ["shiny gigantamax", "gigantamax"]


def get_display_name(
    pokemon_name: str, dex: bool = False, is_long_name: bool = False
) -> str:
    """Returns the display name of a Pokémon, optionally including the dex number."""

    rarity = get_rarity(pokemon_name)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "") if rarity else ""

    # Strip prefixes for display name to avoid clutter (e.g., "Shiny", "Mega", etc.)
    stripped_name = strip_prefixes(pokemon_name)

    if rarity in RARITY_W_LONG_NAME or is_long_name:
        is_long_name = True
    else:
        is_long_name = False

    if is_long_name:
        formatted_name = pokemon_name.title()
    else:
        formatted_name = stripped_name.title()

    display_name = f"{rarity_emoji} {formatted_name}".strip()

    if dex:
        dex_number = get_dex_number_by_name(pokemon_name)
        if dex_number:
            display_name = f"{display_name} #{dex_number}"
    return display_name.strip()


# enable_debug(f"{__name__}.is_mon_exclusive")
def is_mon_exclusive(pokemon: str) -> bool:
    """
    Checks if a given Pokémon is exclusive based on the exclusive_mons list or the market value cache.
    """
    debug_log(f"Checking exclusivity for: {pokemon}")
    name = pokemon.lower()
    if any(name == mon.lower() for mon in exclusive_mons_list):
        debug_log(f"{pokemon} is exclusive based on the exclusive_mons list.")
        return True
    # Check cache for exclusivity, if it's exclusive then it's not auctionable
    pokemon = format_names_for_market_value_lookup(pokemon)
    if is_pokemon_exclusive_cache(pokemon):
        debug_log(f"{pokemon} is exclusive based on the market value cache.")
        return True
    else:
        debug_log(f"{pokemon} is not exclusive based on the market value cache.")
        return False


enable_debug(f"{__name__}.get_rarity")


def get_rarity(pokemon: str):
    """Determines the rarity of a given Pokemon based on the name"""

    name = pokemon.lower()
    pretty_log("info", f"Determining rarity for: {pokemon}")
    debug_log(f"Checking rarity for: {name}")
    if "golden" in name:
        debug_log(f"Matched 'golden' in name: {name}")
        return "golden"
    elif "shiny" in name and "gigantamax" in name:
        debug_log(f"Matched 'shiny' and 'gigantamax' in name: {name}")
        return "shiny gigantamax"
    elif "shiny" in name and "mega" in name:
        debug_log(f"Matched 'shiny' and 'mega' in name: {name}")
        return "shiny mega"
    elif "shiny" in name:
        debug_log(f"Matched 'shiny' in name: {name}")
        return "shiny"
    elif "gigantamax" in name:
        debug_log(f"Matched 'gigantamax' in name: {name}")
        return "gigantamax"
    elif "mega" in name and not "yanmega" in name and not "meganium" in name:
        debug_log(f"Matched 'mega' in name (not yanmega/meganium): {name}")
        return "mega"

    # Fallback to the list (case-insensitive)
    debug_log(f"Checking fallback rarity lists for: {name}")
    if name in (mon.lower() for mon in legendary_mons):
        debug_log(f"Matched legendary_mons: {name}")
        return "legendary"
    elif name in (mon.lower() for mon in superrare_mons):
        debug_log(f"Matched superrare_mons: {name}")
        return "superrare"
    elif name in (mon.lower() for mon in rare_mons):
        debug_log(f"Matched rare_mons: {name}")
        return "rare"
    elif name in (mon.lower() for mon in uncommon_mons):
        debug_log(f"Matched uncommon_mons: {name}")
        return "uncommon"
    elif name in (mon.lower() for mon in common_mons):
        debug_log(f"Matched common_mons: {name}")
        return "common"
    else:
        debug_log(f"No rarity matched for: {name}")
        return None


def format_names_for_market_value_lookup(pokemon_name: str):
    """
    Format Pokémon name for market value lookup"""
    # Special log for names containing '-o'
    if "-o" in pokemon_name:
        debug_log(f"SPECIAL: '-o' detected in name: {pokemon_name!r}")
    # Special log for 'type null'
    if pokemon_name.lower().strip() == "type null":
        debug_log(f"SPECIAL: 'type null' detected: {pokemon_name!r}")
    pokemon_name = pokemon_name.lower().strip()
    if pokemon_name.startswith("sgmax "):
        # shiny gigantamax-<name>
        base = pokemon_name[6:].strip()
        result = f"shiny gigantamax-{base}"
        # debug_log(f"sgmax result: {result}")
        return result
    elif pokemon_name.startswith("gmax "):
        # gigantamax-<name>
        base = pokemon_name[5:].strip()
        result = f"gigantamax-{base}"
        # debug_log(f"gmax result: {result}")
        return result
    elif "smega" in pokemon_name:
        result = pokemon_name.replace("smega", "shiny mega").replace("-", " ")
        # debug_log(f"smega result: {result}")
        return result
    elif "mega" in pokemon_name:
        result = pokemon_name.replace("-", " ")
        # debug_log(f"mega result: {result}")
        return result
    else:
        # debug_log(f"default result: {pokemon_name}")
        return pokemon_name


def is_mon_in_game(pokemon_name: str) -> bool:
    """Check if a Pokémon is in the game."""
    name_lower = pokemon_name.lower()
    if name_lower in IN_GAME_MONS_LIST:
        return True
    # Fallback to check if the formatted name is in the market value cache
    pokemon_name_formatted = format_names_for_market_value_lookup(pokemon_name)
    market_value = fetch_market_value_cache(pokemon_name_formatted)
    if market_value is not None:
        return True
    return False
