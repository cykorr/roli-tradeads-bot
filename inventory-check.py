#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 17:27:47 2026

@author: korr
"""

import requests
import time
from datetime import datetime, timezone

# ================= CONFIG =================

USER_ID = 363042553
WEBHOOK_URL = secrets.INVENTORY_WEBHOOK
CHECK_INTERVAL = 61

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

PLAYER_ASSETS_URL = f"https://api.rolimons.com/players/v1/playerassets/{USER_ID}"
ITEM_CACHE_URL = "https://www.rolimons.com/itemapi/itemdetails"

# ================= GLOBAL ITEM CACHE =================

ITEM_CACHE = {}

def load_item_cache():
    global ITEM_CACHE
    print("Loading Rolimons item cache...")

    r = requests.get(ITEM_CACHE_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()

    data = r.json().get("items", {})

    cache = {}
    for item_id_str, entry in data.items():
        item_id = int(item_id_str)

        name = entry[0]
        rap = entry[2] if entry[2] >= 0 else None
        value = entry[3] if entry[3] >= 0 else None

        cache[item_id] = {
            "name": name,
            "rap": rap,
            "value": value
        }

    ITEM_CACHE = cache
    print(f"Cached {len(ITEM_CACHE)} items.")

# ================= FETCHERS =================

def fetch_player_assets():
    r = requests.get(PLAYER_ASSETS_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()

    assets = r.json()["playerAssets"]

    uaid_map = {}
    for item_id, uaids in assets.items():
        for uaid in uaids:
            uaid_map[uaid] = int(item_id)

    return uaid_map

def get_item_details(item_id):
    return ITEM_CACHE.get(item_id, {
        "name": f"Item {item_id}",
        "rap": None,
        "value": None
    })

# ================= DISCORD =================

def send_discord(title, uaid_map):
    if not uaid_map:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [f"**[{timestamp}]**\n", f"**{title}**"]

    for uaid, item_id in uaid_map.items():
        item = get_item_details(item_id)

        rap = item["rap"]
        value = item["value"]

        rap_str = f"{rap:,}" if rap is not None else "N/A"
        value_str = f"{value:,}" if value is not None else "N/A"

        item_link = f"https://www.rolimons.com/item/{item_id}"
        uaid_link = f"https://www.rolimons.com/uaid/{uaid}"

        lines.append(
            f"- [{item['name']}]({item_link})\n"
            f"  RAP: {rap_str} | Value: {value_str}\n"
            f"  UAID: {uaid_link}"
        )

    requests.post(WEBHOOK_URL, json={"content": "\n".join(lines)})

# ================= MAIN =================

print("Rolimons inventory watcher started.")

# Load item cache ONCE
load_item_cache()

# Initial snapshot
previous = fetch_player_assets()

# 🔹 Send full inventory on startup
send_discord("Initial inventory :", previous)

# Watch loop
while True:
    try:
        current = fetch_player_assets()

        added = {u: i for u, i in current.items() if u not in previous}
        removed = {u: i for u, i in previous.items() if u not in current}

        send_discord("Items removed :", removed)
        send_discord("Items added :", added)

        previous = current

    except Exception as e:
        print("Error:", e)

    time.sleep(CHECK_INTERVAL)
