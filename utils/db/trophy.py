import discord

from constants.vn_allstars_constants import VN_ALLSTARS_TEXT_CHANNELS
from utils.logs.pretty_log import pretty_log

# SQL to create the trophies table
"""CREATE TABLE trophies (
    user_id   BIGINT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    amount    INT NOT NULL
);"""

LEADERBOARD_CHANNEL_ID = VN_ALLSTARS_TEXT_CHANNELS.clan_leaderboard


async def fetch_current_leaderboard_info(bot):
    """
    Fetch the trophy leaderboard info.
    Returns None if not found.
    """

    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM current_trophy_leaderboard
            WHERE channel_id = $1
            LIMIT 1;
            """,
            LEADERBOARD_CHANNEL_ID,
        )


async def remove_leaderboard_info(bot):
    """
    Remove the trophy leaderboard info for a specific channel.
    """

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM current_trophy_leaderboard
            WHERE channel_id = $1;
            """,
            LEADERBOARD_CHANNEL_ID,
        )


# Update leaderboard message ID
async def update_first_place_in_db(
    bot,
    message_id: int,
    first_place_id: int,
    first_place_name: str,
    first_place_trophy: int,
):
    """
    Update the trophy leaderboard message ID and first place info.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                    INSERT INTO current_trophy_leaderboard (
                        message_id, channel_id, first_place_id, first_place_name, first_place_trophy
                    ) VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (message_id) DO UPDATE SET
                        channel_id = EXCLUDED.channel_id,
                        first_place_id = EXCLUDED.first_place_id,
                        first_place_name = EXCLUDED.first_place_name,
                        first_place_trophy = EXCLUDED.first_place_trophy;
                    """,
                message_id,
                LEADERBOARD_CHANNEL_ID,
                first_place_id,
                first_place_name,
                first_place_trophy,
            )
            pretty_log(
                "info",
                f"Upserted current_trophy_leaderboard with message_id {message_id}, first place name {first_place_name} with {first_place_trophy} trophies.",
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Error updating current_trophy_leaderboard: {e}",
        )


# 🟣────────────────────────────────────────────
#          ⚡ trophy DB Functions ⚡
# 🟣────────────────────────────────────────────
# Fetch one trophy entry for a user
async def fetch_user_trophies(bot, user: discord.Member):
    """
    Fetch a single trophy row for a user.
    Returns None if not found.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM trophies
            WHERE user_id = $1;
            """,
            user_id,
        )


async def fetch_user_place_and_trophies(bot, user: discord.Member):
    """
    Fetch the rank (place) and trophy amount for a user.
    Returns None if not found or if user has no trophies.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                user_id,
                user_name,
                amount,
                RANK() OVER (ORDER BY amount DESC, updated_at ASC) AS place
            FROM trophies
            WHERE amount > 0
            ORDER BY amount DESC, updated_at ASC;
            """
        )
        for row in rows:
            if row["user_id"] == user_id:
                return row
        return None


async def remove_trophy_info_user(bot, user_id: int):
    """
    Remove the trophy entry for a specific user.
    """

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM trophies
            WHERE user_id = $1;
            """,
            user_id,
        )
        pretty_log(
            "info",
            f"Removed trophy entry for user ID {user_id}.",
            label="Trophy DB",
        )


# Fetch all trophies
async def fetch_all_trophies(bot):
    """
    Fetch all trophy rows.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT * FROM trophies;
            """
        )


async def update_trophies(bot, user: discord.Member, amount: int):
    user_id = user.id
    user_name = user.name
    first_place_info = await fetch_current_leaderboard_info(bot)
    current_msg_id = first_place_info["message_id"] if first_place_info else None
    first_place_user_id = (
        first_place_info["first_place_id"] if first_place_info else None
    )

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO trophies (user_id, user_name, amount, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET user_name = $2, amount = $3, updated_at = NOW();
            """,
            user_id,
            user_name,
            amount,
        )
        """if user_id == first_place_user_id:
            await update_first_place_in_db(
                bot=bot,
                message_id=current_msg_id,
                first_place_id=user.id,
                first_place_name=user.name,
                first_place_trophy=amount,
            )
            pretty_log(
                "info",
                f"Updated trophies for first place {user.name} to {amount}.",
            )
"""

# Upsert trophy (insert or update)
async def upsert_trophies(bot, user: discord.Member, amount: int):
    """
    Insert or update a trophy row for a user.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO trophies (user_id, user_name, amount)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET user_name = $2, amount = $3;
            """,
            user_id,
            user_name,
            amount,
        )


# Add trophy (insert new row)
async def add_trophies(bot, user: discord.Member, amount: int):
    """
    Add a new trophy row for a user.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO trophies (user_id, user_name, amount)
            VALUES ($1, $2, $3);
            """,
            user_id,
            user_name,
            amount,
        )


# Remove trophy (delete row)
async def remove_trophies(bot, user: discord.Member):
    """
    Remove a trophy row for a user.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM trophies
            WHERE user_id = $1;
            """,
            user_id,
        )


# Reset trophies (clear table)
async def reset_trophies(bot):
    """
    Delete all rows from trophies table.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            TRUNCATE TABLE trophies;
            """
        )


# Get first place (user with highest amount)
async def get_first_place(bot):
    """
    Get the user with the highest trophy amount.
    Returns None if table is empty.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM trophies
            ORDER BY amount DESC, updated_at ASC
            LIMIT 1;
            """
        )


## 🟣────────────────────────────────────────────
#   Current Trophy Leaderboard DB Functions
# 🟣────────────────────────────────────────────
# SQL SCRIPT
"""CREATE TABLE current_trophy_leaderboard (
    message_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    channel_name VARCHAR(100) NOT NULL,
    first_place_id BIGINT,
    first_place_name VARCHAR(100),
    first_place_trophy INTEGER
);"""


# Upsert row if table is empty
async def upsert_leaderboard_msg_id(bot, message_id: int, channel: discord.TextChannel):
    """
    Upsert the trophy leaderboard message ID.
    """
    channel_name = channel.name
    channel_id = channel.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO current_trophy_leaderboard (message_id, channel_id, channel_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (message_id) DO UPDATE
            SET channel_id = EXCLUDED.channel_id,
                channel_name = EXCLUDED.channel_name;
            """,
            message_id,
            channel_id,
            channel_name,
        )
        pretty_log(
            "info",
            f"Upserted leaderboard message ID: {message_id} in channel {channel_name} ({channel_id})",
            label="Trophy Leaderboard DB",
        )


async def fetch_leaderboard_message_id(bot):
    """
    Fetch the trophy leaderboard message ID.
    Returns None if not found.
    """
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM current_trophy_leaderboard
            LIMIT 1;
            """
        )
        if row:
            return row["message_id"]
        return None


async def update_leaderboard_first_place(bot):
    """
    Scan the trophies table and update the leaderboard with the user who has the highest trophy amount.
    If tied, pick the user with the oldest updated_at.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, user_name, amount, updated_at
                FROM trophies
                WHERE amount = (SELECT MAX(amount) FROM trophies)
                ORDER BY updated_at ASC
                LIMIT 1;
                """
            )
            if row:
                message_id_row = await conn.fetchrow(
                    """
                    SELECT message_id FROM current_trophy_leaderboard
                    WHERE channel_id = $1
                    LIMIT 1;
                    """,
                    LEADERBOARD_CHANNEL_ID,
                )
                message_id = message_id_row["message_id"] if message_id_row else None
                await conn.execute(
                    """
                    UPDATE current_trophy_leaderboard
                    SET message_id = $1,
                        first_place_id = $2,
                        first_place_name = $3,
                        first_place_trophy = $4
                    WHERE channel_id = $5;
                    """,
                    message_id,
                    row["user_id"],
                    row["user_name"],
                    row["amount"],
                    LEADERBOARD_CHANNEL_ID,
                )
                pretty_log(
                    "info",
                    f"Updated current_trophy_leaderboard with message_id {message_id} , first place name {row['user_name']} with {row['amount']} trophies.",
                )
            else:
                pretty_log(
                    "info",
                    "No trophies found to update leaderboard.",
                )
    except Exception as e:
        pretty_log(
            "error",
            f"Error updating current_trophy_leaderboard: {e}",
        )
