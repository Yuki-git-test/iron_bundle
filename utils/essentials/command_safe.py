import inspect
import traceback

import discord
from discord.ext import commands

from constants.vn_allstars_constants import YUKI_USER_ID
from utils.logs.pretty_log import pretty_log


# 🟣────────────────────────────────────────────
#          ⚡ Safe Run Command ⚡
# 🟣────────────────────────────────────────────
async def run_command_safe(
    bot,
    interaction: discord.Interaction,
    slash_cmd_name: str,
    command_func,  # the actual command function to call
    *args,
    **kwargs,
):
    """
    Generic wrapper for slash commands with logging and safe follow-up.

    ✅ Works with any combination of parameters (member, role, etc.).
    ✅ Logs trigger, success, and error messages with pretty_log.
    ✅ Sends ephemeral error message if something goes wrong (skips message for Yuki).
    """

    target = ""
    if "member" in kwargs:
        target = f" for {kwargs['member']}"
    elif args:
        first_arg = args[0]
        if isinstance(first_arg, discord.Member):
            target = f" for {first_arg}"

    try:
        pretty_log(
            "info",
            f"🌸 {slash_cmd_name} triggered by {interaction.user}{target}",
        )

        # 🔹 Call the actual command function
        await command_func(bot=bot, interaction=interaction, *args, **kwargs)

        pretty_log(
            "success",
            f"✅ /{slash_cmd_name} completed{target}",
        )
    #
    except Exception as e:
        # Include who triggered the command in the traceback log
        tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        user_info = (
            f"Command invoked by {interaction.user} (ID: {interaction.user.id})\n"
        )
        full_tb = user_info + tb_str

        pretty_log(
            "error",
            f"❌ Error in /{slash_cmd_name}{target}:\n{full_tb}",
            include_trace=False,
        )

        # Only notify if user is NOT YUKI
        if interaction.user.id != YUKI_USER_ID:
            try:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please contact Khy.",
                    ephemeral=True,
                )
            except Exception:
                pretty_log(
                    "warn",
                    f"⚠️ Failed to notify {interaction.user}",
                )
