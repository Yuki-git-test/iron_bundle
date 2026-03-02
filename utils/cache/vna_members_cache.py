import discord

from utils.cache.cache_list import vna_members_cache
from utils.db.vna_members_db_func import fetch_all_members
from utils.logs.pretty_log import pretty_log


# Load all vna_members into cache
async def load_vna_members_cache(bot):
    """
    Load all vna_members from the database into the cache.
    """
    vna_members_cache.clear()
    try:
        members = await fetch_all_members(bot)
        if members:
            for member in members:
                user_id = member["user_id"]
                vna_members_cache[user_id] = {
                    "user_name": member["user_name"],
                    "pokemeow_name": member["pokemeow_name"],
                    "channel_id": member["channel_id"],
                    "perks": member["perks"],
                    "faction": member["faction"],
                    "clan_joined_date": member.get("clan_joined_date"),
                }
            pretty_log(
                "cache", f"Loaded {len(vna_members_cache)} vna_members into cache."
            )
        elif not members:
            pretty_log("cache", "No vna_members found to load into cache.")

    except Exception as e:
        pretty_log("error", f"Error loading vna_members cache: {e}")

    return vna_members_cache


def upsert_vna_member_cache(
    user_id: int,
    user_name: str,
    pokemeow_name: str,
    channel_id: int,
    perks: str,
    faction: str,
    clan_joined_date: int = None,
):
    """
    Upsert a vna_member into the cache.
    """
    vna_members_cache[user_id] = {
        "user_name": user_name,
        "pokemeow_name": pokemeow_name,
        "channel_id": channel_id,
        "perks": perks,
        "faction": faction,
        "clan_joined_date": clan_joined_date,
    }
    pretty_log("cache", f"Upserted vna_member {user_name} ({user_id}) into cache.")


def update_vna_member_multiple_fields_cache(
    user_id: int,
    user_name: str = None,
    pokemeow_name: str = None,
    channel_id: int = None,
    perks: str = None,
    faction: str = None,
    clan_joined_date: int = None,
):
    """
    Update multiple fields for a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        if user_name is not None:
            vna_members_cache[user_id]["user_name"] = user_name
        if pokemeow_name is not None:
            vna_members_cache[user_id]["pokemeow_name"] = pokemeow_name
        if channel_id is not None:
            vna_members_cache[user_id]["channel_id"] = channel_id
        if perks is not None:
            vna_members_cache[user_id]["perks"] = perks
        if faction is not None:
            vna_members_cache[user_id]["faction"] = faction
        if clan_joined_date is not None:
            vna_members_cache[user_id]["clan_joined_date"] = clan_joined_date
        pretty_log(
            "cache",
            f"Updated multiple fields for vna_member ({user_id}) in cache.",
        )


def update_vna_member_clan_joined_date_cache(user_id: int, clan_joined_date: int):
    """
    Update the clan_joined_date of a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        vna_members_cache[user_id]["clan_joined_date"] = clan_joined_date
        pretty_log(
            "cache",
            f"Updated clan_joined_date for vna_member ({user_id}) to {clan_joined_date} in cache.",
        )


def update_vna_member_channel_cache(user_id: int, channel_id: int):
    """
    Update the channel_id of a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        vna_members_cache[user_id]["channel_id"] = channel_id
        pretty_log(
            "cache",
            f"Updated channel_id for vna_member ({user_id}) to {channel_id} in cache.",
        )


def update_vna_member_faction_cache(user_id: int, faction: str):
    """
    Update the faction of a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        vna_members_cache[user_id]["faction"] = faction
        pretty_log(
            "cache",
            f"Updated faction for vna_member ({user_id}) to {faction} in cache.",
        )


def update_vna_member_perks_cache(user_id: int, perks: str):
    """
    Update the perks of a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        vna_members_cache[user_id]["perks"] = perks
        pretty_log(
            "cache",
            f"Updated perks for vna_member ({user_id}) to {perks} in cache.",
        )


def update_vna_member_pokemeow_name_cache(user_id: int, pokemeow_name: str):
    """
    Update the pokemeow_name of a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        vna_members_cache[user_id]["pokemeow_name"] = pokemeow_name
        pretty_log(
            "cache",
            f"Updated pokemeow_name for vna_member ({user_id}) to {pokemeow_name} in cache.",
        )


def update_vna_member_user_name_cache(user_id: int, user_name: str):
    """
    Update the user_name of a vna_member in the cache.
    """
    if user_id in vna_members_cache:
        vna_members_cache[user_id]["user_name"] = user_name
        pretty_log(
            "cache",
            f"Updated user_name for vna_member ({user_id}) to {user_name} in cache.",
        )


def fetch_vna_member_id_by_username(user_name: str) -> int | None:
    """
    Fetch a vna_member's user_id by their user_name from the cache.
    """
    for user_id, data in vna_members_cache.items():
        if data["user_name"] == user_name:
            return user_id
    return None


def fetch_vna_member_id_by_pokemeow_name(pokemeow_name: str) -> int | None:
    """
    Fetch a vna_member's user_id by their pokemeow_name from the cache.
    """
    for user_id, data in vna_members_cache.items():
        if data["pokemeow_name"] == pokemeow_name:
            return user_id
    return None


def fetch_vna_member_id_by_username_or_pokemeow_name(name: str) -> int | None:
    """
    Fetch a vna_member's user_id by their user_name or pokemeow_name from the cache.
    """
    for user_id, data in vna_members_cache.items():
        if data["user_name"] == name or data["pokemeow_name"] == name:
            return user_id
    return None


def remove_vna_member_from_cache(user_id: int):
    """
    Remove a vna_member from the cache by user_id.
    """
    if user_id in vna_members_cache:
        del vna_members_cache[user_id]
        pretty_log("cache", f"Removed vna_member ({user_id}) from cache.")


def fetch_all_user_ids_from_cache() -> list[int]:
    """
    Fetch all user_ids of vna_members from the cache.
    """
    members = list(vna_members_cache.keys())
    return members
