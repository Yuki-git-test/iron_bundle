import discord

from utils.logs.pretty_log import pretty_log


from .vna_members_cache import load_vna_members_cache
from .webhook_url_cache import load_webhook_url_cache
from utils.db.market_value_db import load_market_cache_from_db
from .server_shop_cache import load_server_shop_cache

async def load_all_cache(bot: discord.Client):
    """
    Loads all caches used by the bot.
    """
    try:

        # Load VNA Members Cache
        await load_vna_members_cache(bot)

        # Load Webhook URL Cache
        await load_webhook_url_cache(bot)

        # Load Market Value Cache from database
        await load_market_cache_from_db(bot)

        # Load Server Shop Cache
        await load_server_shop_cache(bot)


    except Exception as e:
        pretty_log(
            message=f"❌ Error loading caches: {e}",
            tag="cache",
        )
        return
    pretty_log(
        message="✅ All caches loaded successfully.",
        tag="cache",
    )
