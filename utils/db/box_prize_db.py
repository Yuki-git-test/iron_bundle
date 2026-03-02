from typing import Any

import discord

from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE box_prizes (
    prize TEXT,
    box_name TEXT,
    stock INTEGER,
    dex TEXT,
    image_link TEXT,
    PRIMARY KEY (prize, box_name)
);"""


async def fetch_all_box_names(bot: discord.Client) -> list[str]:
    """Fetch all distinct box names from the database."""
    box_names = []
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT box_name FROM box_prizes;")
            box_names = [row["box_name"] for row in rows]
            pretty_log(
                tag="db",
                message=f"Fetched {len(box_names)} distinct box names.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch distinct box names: {e}",
            label="🎁 BOX PRIZE DB",
        )
    return box_names


async def fetch_all_box_prizes(
    bot: discord.Client,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Fetch all box prizes from the database, including dex and image_link."""
    box_prizes = {}
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT box_name, prize, stock, dex, image_link FROM box_prizes;"
            )
            for row in rows:
                box_name = row["box_name"]
                prize = row["prize"]
                stock = row["stock"]
                dex = row["dex"]
                image_link = row["image_link"]
                if box_name not in box_prizes:
                    box_prizes[box_name] = {}
                box_prizes[box_name][prize] = {
                    "stock": stock,
                    "dex": dex,
                    "image_link": image_link,
                }
            pretty_log(
                tag="db",
                message=f"Fetched prizes for {len(box_prizes)} boxes.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch box prizes: {e}",
            label="🎁 BOX PRIZE DB",
        )
    return box_prizes


async def add_box_prize(
    bot: discord.Client,
    prize: str,
    box_name: str,
    stock: int,
    dex: str = None,
    image_link: str = None,
):
    """Add a prize to a box in the database, including dex and image_link."""
    dex = str(dex) if dex is not None else None
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO box_prizes (prize, box_name, stock, dex, image_link)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (prize, box_name) DO UPDATE
                SET stock = EXCLUDED.stock, dex = EXCLUDED.dex, image_link = EXCLUDED.image_link;
                """,
                prize,
                box_name,
                stock,
                dex,
                image_link,
            )
            pretty_log(
                tag="db",
                message=f"Added/Updated prize '{prize}' in box '{box_name}' with stock {stock}, dex '{dex}', and image_link '{image_link}'.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to add/update prize '{prize}' in box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )


async def update_box_prize_stock(
    bot: discord.Client, prize: str, box_name: str, stock: int, image_link: str = None
):
    """Update the stock (and optionally image_link) of a prize in a box."""
    try:
        async with bot.pg_pool.acquire() as conn:
            if image_link is not None:
                await conn.execute(
                    """
                    UPDATE box_prizes
                    SET stock = $3, image_link = $4
                    WHERE prize = $1 AND box_name = $2;
                    """,
                    prize,
                    box_name,
                    stock,
                    image_link,
                )
            else:
                await conn.execute(
                    """
                    UPDATE box_prizes
                    SET stock = $3
                    WHERE prize = $1 AND box_name = $2;
                    """,
                    prize,
                    box_name,
                    stock,
                )
            pretty_log(
                tag="db",
                message=f"Updated stock of prize '{prize}' in box '{box_name}' to {stock}{' and image_link ' + image_link if image_link else ''}.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to update stock of prize '{prize}' in box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )


async def fetch_box_prize_with_box(bot: discord.Client, prize: str, box_name: str):
    """Fetch a specific prize from a specific box in the database, including dex and image_link."""
    prize_data = None
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT prize, box_name, stock, dex, image_link FROM box_prizes WHERE prize = $1 AND box_name = $2;",
                prize,
                box_name,
            )
            if row:
                prize_data = {
                    "prize": row["prize"],
                    "box_name": row["box_name"],
                    "stock": row["stock"],
                    "dex": row["dex"],
                    "image_link": row["image_link"],
                }
            pretty_log(
                tag="db",
                message=f"Fetched prize '{prize}' from box '{box_name}' in the database.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch prize '{prize}' from box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )
    return prize_data


async def fetch_box_prize(bot: discord.Client, prize: str):
    """Fetch a specific prize from the database, including image_link."""
    prize_data = None
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT prize, box_name, stock, dex, image_link FROM box_prizes WHERE prize = $1;",
                prize,
            )
            if row:
                prize_data = {
                    "prize": row["prize"],
                    "box_name": row["box_name"],
                    "stock": row["stock"],
                    "dex": row["dex"],
                    "image_link": row["image_link"],
                }
            pretty_log(
                tag="db",
                message=f"Fetched prize '{prize}' from the database.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch prize '{prize}': {e}",
            label="🎁 BOX PRIZE DB",
        )


async def fetch_box_prizes(bot: discord.Client, box_name: str) -> dict[str, int]:
    """Fetch all prizes and their stock and image_link for a given box."""
    prizes = {}
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT prize, stock, image_link FROM box_prizes WHERE box_name = $1;",
                box_name,
            )
            for row in rows:
                prizes[row["prize"]] = {
                    "stock": row["stock"],
                    "image_link": row["image_link"],
                }
            pretty_log(
                tag="db",
                message=f"Fetched {len(prizes)} prizes for box '{box_name}'.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to fetch prizes for box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )
    return prizes


async def remove_box_prize(bot: discord.Client, prize: str, box_name: str):
    """Remove a prize from a box in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM box_prizes WHERE prize = $1 AND box_name = $2;",
                prize,
                box_name,
            )
            pretty_log(
                tag="db",
                message=f"Removed prize '{prize}' from box '{box_name}'.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to remove prize '{prize}' from box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )


async def clear_box_prizes(bot: discord.Client, box_name: str):
    """Clear all prizes from a box in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM box_prizes WHERE box_name = $1;",
                box_name,
            )
            pretty_log(
                tag="db",
                message=f"Cleared all prizes from box '{box_name}'.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to clear prizes from box '{box_name}': {e}",
            label="🎁 BOX PRIZE DB",
        )


async def clear_all_box_prizes(bot: discord.Client):
    """Clear all prizes from all boxes in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM box_prizes;")
            pretty_log(
                tag="db",
                message="Cleared all prizes from all boxes.",
                label="🎁 BOX PRIZE DB",
            )
    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"⚠️ Failed to clear all prizes from all boxes: {e}",
            label="🎁 BOX PRIZE DB",
        )
