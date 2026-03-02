from utils.cache.cache_list import server_shop_cache, box_names_cache
from utils.db.server_shop import fetch_all_items, fetch_all_box_names
from utils.logs.pretty_log import pretty_log


# 🟣────────────────────────────────────────────
#       💜 Server Shop Cache Loader 💜
# ─────────────────────────────────────────────
async def load_server_shop_cache(bot):
    """
    Load all server shop items into memory cache.
    Uses the fetch_all_items DB function.
    """
    server_shop_cache.clear()

    rows = await fetch_all_items(bot)
    for row in rows:
        server_shop_cache[row["item_id"]] = {
            "item_name": row.get("item_name"),
            "price": row.get("price"),
            "stock": row.get("stock"),
            "image_link": row.get("image_link"),
            "description": row.get("description"),
            "dex": row.get("dex"),
        }
    # Load box names into separate cache for quick access
    box_names_cache.clear()
    box_names = await fetch_all_box_names(bot)
    for box_name in box_names:
        box_names_cache.add(box_name)
        
    pretty_log(
        tag="",
        label="🛒 SERVER SHOP CACHE",
        message=f"Loaded {len(server_shop_cache)} server shop items into cache",
    )

    return server_shop_cache


# 🟣────────────────────────────────────────────
#       💜 Server Shop Cache Helpers 💜
# ─────────────────────────────────────────────
def upsert_shop_item(
    item_id: str,
    item_name: str,
    price: int,
    stock: int,
    image_link: str,
    description: str = None,
    dex: str = None,
):
    """Insert or update a server shop item in cache."""
    server_shop_cache[item_id] = {
        "item_name": item_name,
        "price": price,
        "stock": stock,
        "image_link": image_link,
        "description": description,
        "dex": dex,
    }
    pretty_log(
        tag="",
        label="🛒 SERVER SHOP CACHE",
        message=f"Inserted/Updated item '{item_id}' in cache (cache now {len(server_shop_cache)} items)",
    )


def remove_shop_item(item_id: str):
    """Remove a server shop item from cache."""
    if item_id in server_shop_cache:
        server_shop_cache.pop(item_id)
        pretty_log(
            tag="",
            label="🛒 SERVER SHOP CACHE",
            message=f"Removed item '{item_id}' from cache (cache now {len(server_shop_cache)} items)",
        )


def update_price_in_cache(item_id: str, price: int):
    """Update the price of a server shop item in cache."""
    if item_id in server_shop_cache:
        server_shop_cache[item_id]["price"] = price
        pretty_log(
            tag="success",
            label="🛒 SERVER SHOP CACHE",
            message=f"Updated price for item '{item_id}' in cache to {price}",
        )


def update_stock_in_cache(item_id: str, stock: int):
    """Update the stock of a server shop item in cache."""
    if item_id in server_shop_cache:
        server_shop_cache[item_id]["stock"] = stock
        pretty_log(
            tag="success",
            label="🛒 SERVER SHOP CACHE",
            message=f"Updated stock for item '{item_id}' in cache to {stock}",
        )


def update_shop_item_in_cache(
    item_id: str,
    item_name: str = None,
    price: int = None,
    stock: int = None,
    image_link: str = None,
):
    """Update multiple fields of a server shop item in cache."""
    if item_id in server_shop_cache:
        if item_name is not None:
            server_shop_cache[item_id]["item_name"] = item_name
        if price is not None:
            server_shop_cache[item_id]["price"] = price
        if stock is not None:
            server_shop_cache[item_id]["stock"] = stock
        if image_link is not None:
            server_shop_cache[item_id]["image_link"] = image_link
        pretty_log(
            tag="success",
            label="🛒 SERVER SHOP CACHE",
            message=f"Updated item '{item_id}' in cache | Updated fields: {', '.join(k for k, v in [('item_name', item_name), ('price', price), ('stock', stock), ('image_link', image_link)] if v is not None)}",
        )


def fetch_shop_item_id_by_name(item_name: str) -> str | None:
    """Fetch a server shop item ID by its name from cache."""
    for item_id, item in server_shop_cache.items():
        if item.get("item_name") == item_name:
            return item_id
    return None


def fetch_shop_item(item_id: str) -> dict | None:
    """Fetch a server shop item from cache."""
    return server_shop_cache.get(item_id)


def fetch_all_shop_items() -> dict[str, dict]:
    """Fetch all server shop items from cache."""
    return server_shop_cache


def fetch_all_box_items() -> dict[str, dict]:
    """Fetch all server shop items then filters only box items (those with 'box' in their name) and returns them."""
    box_items = {}
    for item_id, item in server_shop_cache.items():
        if "box" in item.get("item_name", "").lower():
            box_items[item_id] = item
    return box_items

