from datetime import datetime

import discord

from constants.vn_allstars_constants import DEFAULT_EMBED_COLOR

from .get_pokemon_gif import get_pokemon_gif


def format_bulletin_desc(*args, key_style_override: str = None) -> str:
    """
    Flexible bulletin formatter.
    - By default, keys are bold.
    - If key_style_override is provided, all keys use that style.
    - Skips any key/value pair where the value is None or empty string.
    """

    def apply_style(text: str, style: str) -> str:
        style = style.lower()
        if style == "bold":
            return f"**{text}**"
        elif style == "italic":
            return f"*{text}*"
        elif style == "underline":
            return f"__{text}__"
        elif style == "strikethrough":
            return f"~~{text}~~"
        elif style == "spoiler":
            return f"||{text}||"
        elif style == "inline_code":
            return f"`{text}`"
        elif style == "code":
            return f"```\n{text}\n```"
        elif style == "bold_upper":
            return f"**{text.upper()}**"
        else:
            return f"**{text}**"  # default bold

    key_style = key_style_override if key_style_override else "bold"

    lines = []
    i = 0
    while i < len(args):
        key = args[i]
        value = args[i + 1] if i + 1 < len(args) else None

        # 🔹 Skip if value is None or empty string
        if value is None or (isinstance(value, str) and value.strip() == ""):
            i += 2
            continue

        formatted_key = apply_style(f"{key}:", key_style)
        lines.append(f"- {formatted_key} {value}")

        i += 2

    return "\n".join(lines)


def design_embed(
    embed: discord.Embed,
    user: discord.User | discord.Member,
    thumbnail_url: str = None,
    image_url: str = None,
    footer_text: str = None,
    pokemon_name: str = None,
    color: discord.Colour | str = None,
) -> discord.Embed:
    """
    Sets the embed's author, thumbnail, image, footer, and optional color.
    - Author text = user's display name
    - Author icon = user's avatar
    - Thumbnail = thumbnail_url or user's avatar
    - Image = image_url if provided
    - Footer = footer_text or user ID
    - Color = Discord Color or Espeon shade string
    """
    avatar_url = user.display_avatar.url
    embed.set_author(name=user.display_name, icon_url=avatar_url)
    embed.timestamp = datetime.now()

    if pokemon_name:
        pokemon_gif = get_pokemon_gif(pokemon_name)
        if pokemon_gif:
            thumbnail_url = pokemon_gif

    # Set thumbnail
    embed.set_thumbnail(url=thumbnail_url or avatar_url)

    # Set image if provided
    if image_url:
        embed.set_image(url=image_url)

    # Set footer
    embed.set_footer(
        text=footer_text or f"💫 User ID: {user.id}",
        icon_url=(
            getattr(user.guild.icon, "url", None) if hasattr(user, "guild") else None
        ),
    )

    # Set color
    if isinstance(color, str):
        embed.color = DEFAULT_EMBED_COLOR
    elif isinstance(color, discord.Colour):
        embed.color = color
    else:
        embed.color = DEFAULT_EMBED_COLOR

    return embed
