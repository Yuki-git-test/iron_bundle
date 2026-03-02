import discord
from discord.ext import commands

from constants.vn_allstars_constants import (
    VN_ALLSTARS_EMOJIS,
    VN_ALLSTARS_ROLES,
    VN_ALLSTARS_TEXT_CHANNELS,
    VNA_SERVER_ID,
)
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


async def send_log_to_server_log(
    bot: discord.Client,
    guild: discord.Guild,
    embed: discord.Embed,
    content: str = None,
):
    """
    Sends a log message to the server log channel.
    """
    try:
        log_channel_id = VN_ALLSTARS_TEXT_CHANNELS.server_log
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            pretty_log(f"Server log channel with ID {log_channel_id} not found.")
            return

        await send_webhook(
            bot,
            log_channel,
            content=content,
            embed=embed,
        )
    except Exception as e:
        pretty_log(f"Failed to send log to server log channel: {e}")
