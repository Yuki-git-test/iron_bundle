from utils.logs.pretty_log import pretty_log
processing_box_item = set()

webhook_url_cache: dict[tuple[int, int], dict[str, str]] = {}
#     ...
#
# }
# key = (bot_id, channel_id)
# Structure:
# webhook_url_cache = {
# (bot_id, channel_id): {
#     "url": "https://discord.com/api/webhooks/..."
#     "channel_name": "alerts-channel",
# },
#


vna_members_cache: dict[int, dict] = {}
# Structure
# user_id: {
# "user_name": str,
# "pokemeow_name": str,
# "channel_id": int,
# "perks": str,
# "faction": str,
# }

market_value_cache: dict[str, dict] = {}

# 💜────────────────────────────────────────────
#       🟣 Server Shop Cache 🌸
# 💜────────────────────────────────────────────
server_shop_cache: dict[int, dict] = {}
# Structure:
# {
#   item_id: {
#       "item_name": str,
#       "price": int,
#       "stock": int,
#       "image_link": str,
#       "description": str,
#       "dex": str,
#   },
#   ...
# }
