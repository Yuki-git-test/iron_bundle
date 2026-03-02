import discord
from discord import app_commands
from discord.ext import commands

from constants.aesthetic import *
from constants.vn_allstars_constants import (
    VNA_SERVER_ID,
    DEFAULT_EMBED_COLOR
)
from utils.logs.pretty_log import pretty_log
from utils.essentials.role_checks import is_staff_member


STAFF_THUMBNAIL = Thumbnails.penguin
START_THUMBNAIL = Thumbnails.blue_gift
PUBLIC_THUMBNAIL = Thumbnails.snowglobe
PUBLIC_EMOJI = "❄️"
STAFF_EMOJI = "☃️"
MAIN_DIVIDER = Dividers.snowflake
TITLE_EMOJI = "🐧"
FOOTER_EMOJI = "🍧"
# 🍭──────────────────────────────
#   🎀 Category Settings
# 🍭──────────────────────────────
CATEGORY_CONFIG = {
    "Public": {
        "emoji": PUBLIC_EMOJI,
        "label": "Public",
        "color": DEFAULT_EMBED_COLOR,
        "thumbnail": PUBLIC_THUMBNAIL,
    },
    "Staff": {
        "emoji": STAFF_EMOJI,
        "label": "Staff",
        "color": DEFAULT_EMBED_COLOR,
        "thumbnail": STAFF_THUMBNAIL,
    },
}


# 💠───────────────────────────────────────────────────────────────
# [🧩 HELPER] Flatten commands and include group prefixes
# ────────────────────────────────────────────────────────────────
def flatten_commands(commands_list, parent_name="") -> list[app_commands.Command]:
    flattened = []
    for cmd in commands_list:
        if isinstance(cmd, app_commands.Group):
            new_parent = f"{parent_name} {cmd.name}".strip()
            flattened.extend(flatten_commands(cmd.commands, new_parent))
        else:
            cmd.full_name = (
                f"/{parent_name} {cmd.name}".strip() if parent_name else f"/{cmd.name}"
            )
            flattened.append(cmd)
    return flattened


# 💠───────────────────────────────────────────────────────────────
# [📄 VIEW] Paginated View
# ────────────────────────────────────────────────────────────────
class PaginatedCategoryView(discord.ui.View):
    def __init__(self, user, category, commands_list, command_map):
        super().__init__(timeout=120)
        self.user = user
        self.category = category
        self.commands = commands_list
        self.page = 0
        self.per_page = 6
        self.max_page = (len(self.commands) - 1) // self.per_page
        self.command_map = command_map
        self.message: discord.Message = None
        self.add_navigation_buttons()

    def add_navigation_buttons(self):
        self.clear_items()
        if self.page > 0:
            self.add_item(PageNavButton("⬅️", self, -1))
        if self.page < self.max_page:
            self.add_item(PageNavButton("➡️", self, 1))
        # ✅ Always show home button
        self.add_item(BackHomeButton(self.user, self.command_map))

    async def send_page(self):
        try:
            cfg = CATEGORY_CONFIG[self.category]
            start = self.page * self.per_page
            end = start + self.per_page
            cmds = self.commands[start:end]

            embed = discord.Embed(
                title=f"{cfg['emoji']} {cfg['label']} Commands",
                color=cfg["color"],
            )
            embed.set_author(
                name=self.user.display_name, icon_url=self.user.display_avatar.url
            )
            if cfg.get("thumbnail"):
                embed.set_thumbnail(url=cfg["thumbnail"])

            for cmd in cmds:
                command_name = getattr(cmd, "full_name", "/" + cmd.name)
                embed.add_field(
                    name=command_name,
                    value=cmd.description or "No description",
                    inline=False,
                )
            embed.set_image(url=MAIN_DIVIDER)
            embed.set_footer(
                text=f"📄 Page {self.page + 1} of {self.max_page + 1} • {FOOTER_EMOJI} {len(self.commands)} commands"
            )


            self.add_navigation_buttons()
            await self.message.edit(embed=embed, view=self)
        except Exception as e:
            pretty_log("error", f"[PaginatedCategoryView] send_page failed: {e}")
# 💠───────────────────────────────────────────────────────────────
# [🔘 BUTTONS] Navigation
# ────────────────────────────────────────────────────────────────
class PageNavButton(discord.ui.Button):
    def __init__(self, emoji, view, direction):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
        self.view_ref = view
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.user:
            return await interaction.response.send_message(
                "This menu isn't for you! ❌", ephemeral=True
            )
        await interaction.response.defer()
        self.view_ref.page += self.direction
        await self.view_ref.send_page()


class BackHomeButton(discord.ui.Button):
    def __init__(self, user, command_map):
        super().__init__(emoji="🏠", style=discord.ButtonStyle.primary)
        self.user = user
        self.command_map = command_map

    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user != self.user:
                return await interaction.response.send_message(
                    "This menu isn’t for you! ❌", ephemeral=True
                )

            view = CommandCategoryMenuView(self.user, self.command_map or {})
            description = (
                "Choose a command group by clicking the buttons below! ✨\n\n"
                + "\n".join(view.category_lines)
            )

            embed = discord.Embed(
                title=f"{TITLE_EMOJI} Command Categories",
                description=description,
                color=DEFAULT_EMBED_COLOR,
            )
            embed.set_image(url=MAIN_DIVIDER)
            embed.set_thumbnail(url=START_THUMBNAIL)
            embed.set_author(
                name=self.user.display_name, icon_url=self.user.display_avatar.url
            )

            view.message = interaction.message
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            pretty_log("error", f"[BackHomeButton] Callback failed: {e}")


# 💠───────────────────────────────────────────────────────────────
# [🌼 VIEW] Category Menu — Home
# ────────────────────────────────────────────────────────────────
class CommandCategoryMenuView(discord.ui.View):
    def __init__(self, user: discord.User, command_map: dict[str, list[str]]):
        super().__init__(timeout=120)
        self.user = user
        self.command_map = command_map
        self.message: discord.Message = None
        self.category_lines = []

        for category, data in CATEGORY_CONFIG.items():
            emoji = data["emoji"]
            if command_map.get(category):
                self.add_item(
                    CategoryButton(user, category, command_map[category], command_map)
                )
                self.category_lines.append(f"{emoji} — {data['label']} Commands")


class CategoryButton(discord.ui.Button):
    def __init__(self, user, category, commands_list, command_map):
        config = CATEGORY_CONFIG[category]
        super().__init__(emoji=config["emoji"], style=discord.ButtonStyle.secondary)
        self.user = user
        self.category = category
        self.commands = commands_list
        self.command_map = command_map

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This menu isn’t for you! ❌", ephemeral=True
            )
        await interaction.response.defer()

        view = PaginatedCategoryView(
            self.user, self.category, self.commands, self.command_map
        )
        view.message = interaction.message
        await view.send_page()


# 💠───────────────────────────────────────────────────────────────
# [📚 COG] CommandsView
# ────────────────────────────────────────────────────────────────
class CommandsView(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=VNA_SERVER_ID))
    @app_commands.command(name="commands", description="View Iron Bundle's commands!")

    async def commands(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)

            user = interaction.user

            # Staff check
            # Flatten commands
            all_commands = flatten_commands(self.bot.tree.get_commands())
            command_map = {"Public": [], "Staff": []}

            for cmd in all_commands:
                category = getattr(cmd, "extras", {}).get("category", "Public")

                # 👑 Staff Only
                if category == "Staff":
                    if is_staff_member(user):
                        command_map["Staff"].append(cmd)
                else:
                    command_map["Public"].append(cmd)

            view = CommandCategoryMenuView(user, command_map)
            description = (
                f"Choose a command group by clicking the buttons below! {FOOTER_EMOJI}\n\n"
                + "\n".join(view.category_lines)
            )

            embed = discord.Embed(
                title=f"{TITLE_EMOJI} Command Categories",
                description=description,
                color=DEFAULT_EMBED_COLOR,
            )
            embed.set_image(url=MAIN_DIVIDER)
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=START_THUMBNAIL)
            view.message = await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            pretty_log("error", f"[CommandsView] Command failed: {e}")

    commands.extras = {"category": "Public"}
# 💠───────────────────────────────────────────────────────────────
# [📦 SETUP]
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    try:
        await bot.add_cog(CommandsView(bot))
        # pretty_log("info", "🍧 CommandsView cog loaded successfully!")
    except Exception as e:
        pretty_log("critical", f"Failed to load CommandsView cog: {e}")
