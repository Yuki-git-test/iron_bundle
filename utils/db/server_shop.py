# Async function to fetch all unique box names from box_prizes table
import random
import string
from typing import List

import asyncpg
import discord

from constants.paldea_galar_dict import rarity_meta
from utils.logs.pretty_log import pretty_log


def generate_item_id(length=8):
    """Generate a random alphanumeric item_id of given length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


async def box_item_autocomplete(
    interaction: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    """
    Autocomplete for box items from the database.
    Choice.name = "Item Name"
    Choice.value = "item_name"
    Matches both names and item IDs.
    """
    from utils.cache.cache_list import box_names_cache

    current = (current or "").lower().strip()
    results: List[discord.app_commands.Choice[str]] = []
    for box_name in box_names_cache:
        if not current or current in box_name.lower():
            results.append(
                discord.app_commands.Choice(name=box_name.title(), value=box_name)
            )
        if len(results) >= 25:
            break
    if not results:
        results.append(discord.app_commands.Choice(name="No matches found", value=""))
    return results


async def fetch_all_box_names(bot) -> list:
    """Fetch all unique box names from the box_prizes table."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT box_name FROM box_prizes;")
            return [row["box_name"] for row in rows]
    except Exception as e:
        from utils.logs.pretty_log import pretty_log

        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch box names: {e}",
            label="🎁 BOX PRIZE DB",
        )
        return []


async def fetch_total_shop_items(bot) -> int:
    """Fetch the total number of items in the server shop."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT SUM(stock) AS total_stock FROM server_shop;"
            )
            total = row["total_stock"] if row and row["total_stock"] is not None else 0
            pretty_log(
                tag="db",
                message=f"Total stock in server shop: {total}",
                label="🛒 SERVER SHOP",
            )
            return total
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch total shop items: {e}",
            label="🛒 SERVER SHOP",
        )
        return 0


async def shop_item_autocomplete(
    interaction: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    """
    Autocomplete for server shop items from cache.
    Choice.name = "Item Name"
    Choice.value = "item_name"
    Matches both names and item IDs.
    """
    from utils.cache.server_shop_cache import fetch_all_shop_items

    try:
        items = fetch_all_shop_items()
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch shop items from cache: {e}",
            label="🛒 SERVER SHOP",
        )
        items = {}

    current = (current or "").lower().strip()
    results: List[discord.app_commands.Choice[str]] = []

    for item_id, item in items.items():
        item_name = str(item.get("item_name", "Unnamed Item"))
        if (
            not current
            or current in item_name.lower()
            or current in str(item_id).lower()
        ):
            results.append(discord.app_commands.Choice(name=item_name, value=item_name))
        if len(results) >= 25:
            break

    if not results:
        results.append(discord.app_commands.Choice(name="No matches found", value=""))

    return results


# -------------------- Server Shop Database Functions --------------------


async def upsert_item(
    bot: discord.Client,
    item_name: str,
    price: int,
    stock: int,
    image_link: str,
    description: str = None,
    dex: str = None,
) -> str:
    """
    Insert or update an item by name in the server_shop table.
    If the item already exists (by name), update its price and stock.
    If not, insert a new item with a generated item_id.
    Returns the item_id used.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            # Try to fetch existing item_id by name
            row = await conn.fetchrow(
                "SELECT item_id FROM server_shop WHERE item_name = $1;", item_name
            )
            if row:
                item_id = row["item_id"]
            else:
                item_id = generate_item_id()

            await conn.execute(
                """
                INSERT INTO server_shop (item_name, price, stock, item_id, image_link, description, dex)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (item_id)
                DO UPDATE SET item_name = EXCLUDED.item_name, price = EXCLUDED.price, stock = EXCLUDED.stock, image_link = EXCLUDED.image_link, description = EXCLUDED.description, dex = EXCLUDED.dex;
                """,
                item_name,
                price,
                stock,
                item_id,
                image_link,
                description,
                dex,
            )
            pretty_log(
                tag="db",
                message=f"Upserted item '{item_name}' (item_id: {item_id}, price: {price}, stock: {stock}, dex: {dex})",
                label="🛒 SERVER SHOP",
            )
            # Upsert in cache as well
            from utils.cache.server_shop_cache import upsert_shop_item

            upsert_shop_item(
                item_id, item_name, price, stock, image_link, description, dex
            )

        return item_id
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to upsert item '{item_name}': {e}",
            label="🛒 SERVER SHOP",
        )
        return None


async def remove_item_by_name(bot: discord.Client, item_name: str) -> None:
    """
    Remove an item by name from the server_shop table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM server_shop WHERE item_name = $1;", item_name
            )
            pretty_log(
                tag="db",
                message=f"Removed item '{item_name}' from shop.",
                label="🛒 SERVER SHOP",
            )

            # Remove from cache as well
            from utils.cache.server_shop_cache import remove_shop_item_by_name

            remove_shop_item_by_name(item_name)

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to remove item '{item_name}': {e}",
            label="🛒 SERVER SHOP",
        )


async def remove_item(bot: discord.Client, item_id: str) -> None:
    """
    Remove an item by item_id from the server_shop table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM server_shop WHERE item_id = $1;", item_id)
            pretty_log(
                tag="db",
                message=f"Removed item with item_id '{item_id}' from shop.",
                label="🛒 SERVER SHOP",
            )

            # Remove from cache as well
            from utils.cache.server_shop_cache import remove_shop_item

            remove_shop_item(item_id)

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to remove item with item_id '{item_id}': {e}",
            label="🛒 SERVER SHOP",
        )


async def update_price(bot: discord.Client, item_id: str, price: int) -> None:
    """
    Update the price of an item in the server_shop table by item_id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_shop SET price = $1 WHERE item_id = $2;",
                price,
                item_id,
            )
            pretty_log(
                tag="db",
                message=f"Updated price for item_id '{item_id}' to {price}.",
                label="🛒 SERVER SHOP",
            )
            # Update in cache as well
            from utils.cache.server_shop_cache import update_price_in_cache

            update_price_in_cache(item_id, price)

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update price for item_id '{item_id}': {e}",
            label="🛒 SERVER SHOP",
        )


async def update_stock(bot: discord.Client, item_id: str, stock: int) -> None:
    """
    Update the stock of an item in the server_shop table by item_id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_shop SET stock = $1 WHERE item_id = $2;",
                stock,
                item_id,
            )
            pretty_log(
                tag="db",
                message=f"Updated stock for item_id '{item_id}' to {stock}.",
                label="🛒 SERVER SHOP",
            )

            # Update in cache as well
            from utils.cache.server_shop_cache import update_stock_in_cache

            update_stock_in_cache(item_id, stock)

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update stock for item_id '{item_id}': {e}",
            label="🛒 SERVER SHOP",
        )


async def update_item(
    bot: discord.Client,
    item_id: str,
    item_name: str = None,
    price: int = None,
    stock: int = None,
    image_link: str = None,
):
    """
    Update multiple fields of an item in the server_shop table by item_id."""

    try:
        async with bot.pg_pool.acquire() as conn:
            fields = []
            values = []
            if item_name is not None:
                fields.append("item_name = $" + str(len(values) + 1))
                values.append(item_name)
            if price is not None:
                fields.append("price = $" + str(len(values) + 1))
                values.append(price)
            if stock is not None:
                fields.append("stock = $" + str(len(values) + 1))
                values.append(stock)
            if image_link is not None:
                fields.append("image_link = $" + str(len(values) + 1))
                values.append(image_link)
            if not fields:
                return  # Nothing to update
            values.append(item_id)
            query = f"UPDATE server_shop SET {', '.join(fields)} WHERE item_id = ${len(values)};"
            await conn.execute(query, *values)
            pretty_log(
                tag="db",
                message=f"Updated item with item_id '{item_id}': {fields}",
                label="🛒 SERVER SHOP",
            )

            # Update in cache as well
            from utils.cache.server_shop_cache import update_shop_item_in_cache

            update_shop_item_in_cache(item_id, item_name, price, stock, image_link)

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update item with item_id '{item_id}': {e}",
            label="🛒 SERVER SHOP",
        )


async def remove_all_items(bot: discord.Client) -> None:
    """
    Remove all items from the server_shop table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM server_shop;")
            pretty_log(
                tag="db",
                message="Removed all items from server_shop.",
                label="🛒 SERVER SHOP",
            )

            # Clear cache as well
            from utils.cache.cache_list import server_shop_cache

            server_shop_cache.clear()
            pretty_log(
                tag="cache",
                message="Cleared server shop cache after removing all items.",
                label="🛒 SERVER SHOP",
            )

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to remove all items: {e}",
            label="🛒 SERVER SHOP",
        )


async def fetch_all_items(bot: discord.Client):
    """
    Fetch all items from the server_shop table.
    Returns a list of records.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM server_shop;")
            pretty_log(
                tag="db",
                message=f"Fetched all items from server_shop ({len(rows)} items).",
                label="🛒 SERVER SHOP",
            )
            return rows
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch all items: {e}",
            label="🛒 SERVER SHOP",
        )
        return []


async def fetch_item_by_id(bot: discord.Client, item_id: str):
    """
    Fetch a single item by item_id from the server_shop table.
    Returns the record or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM server_shop WHERE item_id = $1;", item_id
            )
            pretty_log(
                tag="db",
                message=f"Fetched item with item_id '{item_id}' from server_shop: {row}",
                label="🛒 SERVER SHOP",
            )
            return row
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch item with item_id '{item_id}': {e}",
            label="🛒 SERVER SHOP",
        )
        return None


async def fetch_item_by_name(bot: discord.Client, item_name: str):
    """
    Fetch a single item by name from the server_shop table.
    Returns the record or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM server_shop WHERE item_name = $1;", item_name
            )
            pretty_log(
                tag="db",
                message=f"Fetched item '{item_name}' from server_shop: {row}",
                label="🛒 SERVER SHOP",
            )
            return row
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch item '{item_name}': {e}",
            label="🛒 SERVER SHOP",
        )
        return None
        return None
