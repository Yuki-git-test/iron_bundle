import discord

from utils.logs.pretty_log import pretty_log

# SQL Script to create the vna_members table
"""CREATE TABLE vna_members (
    user_id           BIGINT PRIMARY KEY,
    user_name         VARCHAR(100) NOT NULL,
    channel_id        BIGINT NOT NULL,
    pokemeow_name     VARCHAR(100),
    perks             TEXT,
    faction           VARCHAR(100),
    clan_joined_date  BIGINT
);"""


# Fetch one member entry for a user
async def fetch_user_member(bot, user: discord.Member):
    """
    Fetch a single vna_members row for a user.
    Returns None if not found.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM vna_members
            WHERE user_id = $1;
            """,
            user_id,
        )


# Fetch all members
async def fetch_all_members(bot):
    """
    Fetch all vna_members rows.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT * FROM vna_members;
            """
        )


# Upsert member (insert or update)
async def upsert_member(
    bot,
    user: discord.Member,
    channel_id: int = None,
    pokemeow_name: str = None,
    perks: str = None,
    faction: str = None,
    clan_joined_date: int = None,
):
    """
    Insert or update a vna_members row for a user.
    """
    user_id = user.id
    user_name = user.name

    if not pokemeow_name:
        pokemeow_name = user.name
    else:
        pokemeow_name = pokemeow_name

    import time

    clan_joined_date = None
    if clan_joined_date is None:
        clan_joined_date = int(time.time())

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO vna_members (user_id, user_name, pokemeow_name, channel_id, perks, faction, clan_joined_date)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id)
                DO UPDATE SET user_name = $2, pokemeow_name = $3, channel_id = $4, perks = $5, faction = $6, clan_joined_date = $7;
                """,
                user_id,
                user_name,
                pokemeow_name,
                channel_id,
                perks,
                faction,
                clan_joined_date,
            )
            pretty_log(
                "info",
                f"Upserted vna_members for {user.name} with channel_id {channel_id}.",
            )
            # Update cache as well
            from utils.cache.vna_members_cache import upsert_vna_member_cache

            upsert_vna_member_cache(
                user_id=user_id,
                user_name=user_name,
                pokemeow_name=pokemeow_name,
                channel_id=channel_id,
                perks=perks,
                faction=faction,
                clan_joined_date=clan_joined_date,
            )
            return True
    except Exception as e:
        pretty_log("error", f"Failed to upsert vna_members for {user.name}: {e}")
        return False


# Add member (insert new row)
async def add_member(bot, user: discord.Member, channel_id: int):
    """
    Add a new vna_members row for a user.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO vna_members (user_id, user_name, channel_id, clan_joined_date)
            VALUES ($1, $2, $3, $4);
            """,
            user_id,
            user_name,
            channel_id,
            getattr(user, "clan_joined_date", None),
        )
        pretty_log(
            "info",
            f"Added {user.name} to vna_members with channel_id {channel_id}.",
        )


# Update member multiple fields for a user
async def update_member_fields(
    bot,
    user: discord.Member,
    user_name: str = None,
    pokemeow_name: str = None,
    channel_id: int = None,
    perks: str = None,
    faction: str = None,
    clan_joined_date: int = None,
):
    """
    Update multiple fields for a user in vna_members.
    """
    try:
        user_id = user.id
        fields = []
        values = []
        if user_name is not None:
            fields.append(f"user_name = ${len(values)+2}")
            values.append(user_name)
        if pokemeow_name is not None:
            fields.append(f"pokemeow_name = ${len(values)+2}")
            values.append(pokemeow_name)
        if channel_id is not None:
            fields.append(f"channel_id = ${len(values)+2}")
            values.append(channel_id)
        if perks is not None:
            fields.append(f"perks = ${len(values)+2}")
            values.append(perks)
        if faction is not None:
            fields.append(f"faction = ${len(values)+2}")
            values.append(faction)
        if clan_joined_date is not None:
            fields.append(f"clan_joined_date = ${len(values)+2}")
            values.append(clan_joined_date)
        if fields:
            sql = f"UPDATE vna_members SET {', '.join(fields)} WHERE user_id = $1;"
            async with bot.pg_pool.acquire() as conn:
                await conn.execute(sql, user_id, *values)
            pretty_log(
                "info", f"Updated fields for {user.name} in vna_members: {fields}"
            )

            # Update cache as well
            from utils.cache.vna_members_cache import (
                update_vna_member_multiple_fields_cache,
            )

            update_vna_member_multiple_fields_cache(
                user_id=user_id,
                user_name=user_name,
                pokemeow_name=pokemeow_name,
                channel_id=channel_id,
                perks=perks,
                faction=faction,
                clan_joined_date=clan_joined_date,
            )
            return True
        else:
            pretty_log("info", f"No fields to update for {user.name}.")
            return False
    except Exception as e:
        pretty_log("error", f"Failed to update fields for {user.name}: {e}")
        return False


# Update member faction for a user
async def update_member_faction(bot, user: discord.Member, faction: str):
    """
    Update the faction for a user in vna_members.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE vna_members
            SET faction = $1
            WHERE user_id = $2;
            """,
            faction,
            user_id,
        )
        pretty_log(
            "info",
            f"Updated faction for {user.name} to {faction} in vna_members.",
        )
        # Update cache as well
        from utils.cache.vna_members_cache import update_vna_member_faction_cache

        update_vna_member_faction_cache(user_id, faction)


# Update member channel_id for a user
async def update_member_channel(bot, user: discord.Member, channel_id: int):
    """
    Update the channel_id for a user in vna_members.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE vna_members
            SET channel_id = $1
            WHERE user_id = $2;
            """,
            channel_id,
            user_id,
        )
        pretty_log(
            "info",
            f"Updated channel_id for {user.name} to {channel_id} in vna_members.",
        )
        # Update cache as well
        from utils.cache.vna_members_cache import update_vna_member_channel_cache

        update_vna_member_channel_cache(user_id, channel_id)


# Update member perks for a user
async def update_member_perks(bot, user: discord.Member, perks: str):
    """
    Update the perks for a user in vna_members.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE vna_members
            SET perks = $1
            WHERE user_id = $2;
            """,
            perks,
            user_id,
        )
        pretty_log(
            "info",
            f"Updated perks for {user.name} to {perks} in vna_members.",
        )
        # Update cache as well
        from utils.cache.vna_members_cache import update_vna_member_perks_cache

        update_vna_member_perks_cache(user_id, perks)


# Update member pokemeow_name for a user
async def update_member_pokemeow_name(bot, user: discord.Member, pokemeow_name: str):
    """
    Update the pokemeow_name for a user in vna_members.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE vna_members
            SET pokemeow_name = $1
            WHERE user_id = $2;
            """,
            pokemeow_name,
            user_id,
        )
        pretty_log(
            "info",
            f"Updated pokemeow_name for {user.name} to {pokemeow_name} in vna_members.",
        )
        # Update cache as well
        from utils.cache.vna_members_cache import update_vna_member_pokemeow_name_cache

        update_vna_member_pokemeow_name_cache(user_id, pokemeow_name)


# Update member user_name for a user
async def update_member_user_name(bot, user: discord.Member, user_name: str):
    """
    Update the user_name for a user in vna_members.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE vna_members
            SET user_name = $1
            WHERE user_id = $2;
            """,
            user_name,
            user_id,
        )
        pretty_log(
            "info",
            f"Updated user_name for {user.name} to {user_name} in vna_members.",
        )
        # Update cache as well
        from utils.cache.vna_members_cache import update_vna_member_user_name_cache

        update_vna_member_user_name_cache(user_id, user_name)


# Update joined date for a user
async def update_member_joined_date(bot, user: discord.Member, joined_date: int):
    """
    Update the clan_joined_date for a user in vna_members.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE vna_members
            SET clan_joined_date = $1
            WHERE user_id = $2;
            """,
            joined_date,
            user_id,
        )
        pretty_log(
            "info",
            f"Updated clan_joined_date for {user.name} to {joined_date} in vna_members.",
        )
        # Update cache as well
        from utils.cache.vna_members_cache import (
            update_vna_member_clan_joined_date_cache,
        )

        update_vna_member_clan_joined_date_cache(user_id, joined_date)


# Remove member (delete row)
async def remove_member(bot, user: discord.Member):
    """
    Remove a vna_members row for a user.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM vna_members
            WHERE user_id = $1;
            """,
            user_id,
        )
        pretty_log(
            "info",
            f"Removed {user.name} from vna_members.",
        )
        # Remove from cache as well
        from utils.cache.vna_members_cache import remove_vna_member_from_cache

        remove_vna_member_from_cache(user_id)


# Reset members (clear table)
async def reset_members(bot):
    """
    Delete all rows from vna_members table.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            TRUNCATE TABLE vna_members;
            """
        )


# Get member by channel_id
async def get_member_by_channel(bot, channel_id: int):
    """
    Get the member with the given channel_id.
    Returns None if not found.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM vna_members
            WHERE channel_id = $1;
            """,
            channel_id,
        )
