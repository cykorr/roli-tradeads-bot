#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 21:03:49 2026

@author: korr
"""

#Hello someone /e wave
#https://github.com/K0LP7/K0LPRoliTradeAd
#Started working on this discord bot on 2025/09/17
#Made this bc bot from Arachnid didnt have an option to add robux :C (and few other features)
import discord
from discord.ext import commands
import json
import requests
from datetime import datetime, timedelta
import random
import asyncio
import time
from collections import Counter

CONFIG_FILE = "config.json"

def load_config_file():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config_file(config_file):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_file, f, indent=4)

async def check_inventory_updates():
    await bot.wait_until_ready()

    while not bot.is_closed():
        config = load_config_file()
        player_id = config.get("PlayerID")
        channel_id = config.get("DiscordChannel")

        if not player_id or not channel_id:
            await asyncio.sleep(300)
            continue

        channel = bot.get_channel(channel_id)
        if not channel:
            await asyncio.sleep(300)
            continue

        try:
            inventory = fetch_inventory(player_id)
            current_ids = [i["userAssetId"] for i in inventory]
            stored_ids = config.get("LastInventory")

            # FIRST RUN: dump inventory
            if stored_ids is None:
                msg = "**Current Inventory:**\n"
                for item in inventory:
                    roli = f"https://www.rolimons.com/item/{item['assetId']}"
                    msg += f"• **{item['name']}** — {roli}\n"

                await channel.send(msg)

                config["LastInventory"] = current_ids
                save_config_file(config)
                await asyncio.sleep(300)
                continue

            # NORMAL RUN: detect new items
            new_items = [
                item for item in inventory
                if item["userAssetId"] not in stored_ids
            ]

            if new_items:
                msg = "**New inventory items detected:**\n"
                for item in new_items:
                    roli = f"https://www.rolimons.com/item/{item['assetId']}"
                    msg += f"• **{item['name']}** — {roli}\n"

                await channel.send(msg)

                config["LastInventory"] = current_ids
                save_config_file(config)

        except Exception as e:
            print(f"Inventory check error: {e}")

        await asyncio.sleep(300)


def fetch_inventory(player_id):
    """
    Returns a list of dicts:
    {
        "userAssetId": int,
        "assetId": int,
        "name": str
    }
    """
    inventory = []
    cursor = ""

    while True:
        url = (
            f"https://inventory.roblox.com/v1/users/{player_id}/assets/collectibles"
            f"?limit=100&sortOrder=Asc&cursor={cursor}"
        )
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        for item in data.get("data", []):
            inventory.append({
                "userAssetId": item["userAssetId"],
                "assetId": item["assetId"],
                "name": item["name"]
            })

        cursor = data.get("nextPageCursor")
        if not cursor:
            break

    return inventory

config_file = load_config_file()

urlTA = 'https://api.rolimons.com/tradeads/v1/createad'
urlIL = 'https://api.rolimons.com/items/v2/itemdetails'
urlPI = f'https://inventory.roblox.com/v1/users/{config_file["PlayerID"]}/assets/collectibles?limit=100&sortOrder=Asc'

responseIL = requests.get(urlIL)
resIL = responseIL.json()

Tag_Icons = {"upgrade": "📈 Upgrade","downgrade": "📉 Downgrade","adds": "➕ Adds","any": "📊 Any","wishlist": "🗄️ Wishlist","demand": "📊 Demand","rares": "💎 Rares","rap": "📊 Rap","robux": "💲 Robux","projecteds": "⚠️ Projecteds"}
AllTags = ["adds", "upgrade", "downgrade", "any", "wishlist", "demand", "rares", "rap", "robux", "projecteds"]

#Bot settings 
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# inv
import requests
from collections import Counter
import time  # for response time

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

@bot.command(name="inv")
async def inventory_command(ctx):
    start_time = time.perf_counter()
    command_sent_time = ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")

    config = load_config_file()
    player_id = config.get("PlayerID")
    if not player_id:
        await ctx.send("Player ID is not configured.")
        return

    try:
        inventory = fetch_inventory(player_id)
    except Exception as e:
        await ctx.send("Failed to fetch inventory.")
        print(e)
        return

    if not inventory:
        await ctx.send("Inventory is empty.")
        return

    counts = Counter([item["assetId"] for item in inventory])
    unique_items = {item["assetId"]: item for item in inventory}

    annotated_inventory = []

    for asset_id, item in unique_items.items():
        try:
            resp = requests.get(f"https://rolimons.reklaw.dev/api/item?id={asset_id}").json()
            data = resp.get("data", {})
            rap = safe_int(data.get("rap"))
            value = safe_int(data.get("value") or rap)
            acronym = data.get("acronym", "N/A")
            name = item["name"] or "Unknown Item"
            name = name[:40]  # truncate for table
            link = f"https://www.rolimons.com/item/{asset_id}"
            count = counts[asset_id]
            total_value = value * count
            total_rap = rap * count

            annotated_inventory.append({
                "name": name,
                "link": link,
                "rap": rap,
                "value": value,
                "acronym": acronym,
                "count": count,
                "total_value": total_value,
                "total_rap": total_rap
            })
        except Exception as e:
            print(f"Error fetching data for {item['name']}: {e}")
            continue

    annotated_inventory.sort(key=lambda x: x["total_value"], reverse=True)

    # Spreadsheet-style text
    header = f"{'Name':40} {'Count':>5} {'RAP':>10} {'Value':>10} {'Acronym':>8} {'Link'}"
    lines = [f"Command sent: {command_sent_time}", header]
    lines.append("-" * (len(header) + 20))

    total_combined_rap = 0
    total_combined_value = 0

    for item in annotated_inventory:
        lines.append(f"{item['name']:40} {item['count']:>5} {item['rap']:>10} {item['value']:>10} {item['acronym']:>8} {item['link']}")
        total_combined_rap += item["total_rap"]
        total_combined_value += item["total_value"]

    lines.append("-" * (len(header) + 20))
    lines.append(f"{'TOTAL':40} {'':>5} {total_combined_rap:>10} {total_combined_value:>10}")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    lines.append(f"\nResponse generated in {elapsed_time:.2f} seconds.")

    # Send in chunks if necessary
    message = ""
    for line in lines:
        if len(message) + len(line) + 1 > 1990:
            await ctx.send(f"```\n{message}```")
            message = ""
        message += line + "\n"

    if message:
        await ctx.send(f"```\n{message}```")


#NFT command
@bot.group(name="nft", invoke_without_command=True)
async def nft(ctx):
    await ctx.send("⚠️ Use `add`, `remove`, `list` or `clear`!")

@nft.command(name="list") #NFT Embed List
async def nft_list(ctx):
    config_file = load_config_file()
    NFT_Items=[]
    NonRolimonsApiItems=0

    for NFT_List in config_file["NotForTrade"]:
        item_data = resIL["items"].get(str(NFT_List))
        if item_data:
            if item_data[1] != "": #Checks if theres an acronym and if there is it picks it
                Item_Name = item_data[1]
            else:
                Item_Name=item_data[0]# If there isnt sets item name
            Item_Value=item_data[4]
            NFT_Items.append((Item_Name, NFT_List, Item_Value))
        else:
            NonRolimonsApiItems = NonRolimonsApiItems +1
    if NonRolimonsApiItems >0:
        await ctx.send(f"❌ Rolimons API doesnt recognize {NonRolimonsApiItems} IDs in the config!")
        
    NFT_Items = sorted(NFT_Items, key=lambda x: x[2], reverse=True) #Sorts Items by value   
    NFT_Item_List = ""
    for Item_Name, NFT_List, _ in NFT_Items:
        NFT_Item_List += f"● {Item_Name} ({NFT_List})\n"
            
    nftembed = discord.Embed(
        title="🚫 Not For Trade List",
        color=0x33cc66
    )
    nftembed.add_field(name="", value=NFT_Item_List, inline=False)

    await ctx.send(embed=nftembed) #Sends embed

@nft.command(name="add", aliases=["a"]) #NFT add
async def NFTAdd(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send("❌ Please provide an item ID or name to add!")
        return
       
    config_file = load_config_file()
    if arg.isnumeric():
        if int(arg) in config_file["NotForTrade"]:
            config_file["NotForTrade"].append(int(arg))
            save_config_file(config_file)  
            await ctx.send(f'✅ {arg} has been added to NFT List!')
        else:
            await ctx.send('❌ Item ID is already in NFT List.')
            return
    else:
        for itemid, itemname in resIL["items"].items():
            if (arg.casefold().strip() == itemname[1].casefold().strip() or  arg.casefold().strip() == itemname[0].casefold().strip()):
                if int(itemid) not in config_file["NotForTrade"]:
                    config_file["NotForTrade"].append(int(itemid))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {itemname[0]} has been added to NFT List!')
                    return
                else:
                    await ctx.send('❌ Item is already in your NFT List')

                    return
        else:
            await ctx.send('❌ Couldnt find this item in Rolimons API')
            return
       
@nft.command(name="remove", aliases=["r"]) #NFT remove
async def NFTRemove(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send('❌ Please provide an item ID or name to remove!')
        return
    
    config_file = load_config_file()
    if arg.isnumeric():
        if int(arg) in config_file["NotForTrade"]:
            config_file["NotForTrade"].remove(int(arg))
            save_config_file(config_file)  
            await ctx.send(f'✅ {arg} has been removed from NFT List!')
        else:
            await ctx.send('❌ Couldnt find this ID in your NFT List')
            return
    else:
        for itemid, itemname in resIL["items"].items():
            if (arg.casefold().strip() == itemname[1].casefold().strip() or  arg.casefold().strip() == itemname[0].casefold().strip()):
                if int(itemid) in config_file["NotForTrade"]:
                    config_file["NotForTrade"].remove(int(itemid))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {itemname[0]} has been removed from NFT List!')
                else:
                    await ctx.send('❌ Couldnt find this item in your NFT List')
                return
        else:
            await ctx.send('❌ Couldnt find this item in Rolimons API')
            return

@nft.command(name="clear") #NFT clear
async def NFTClear(ctx, *, arg: str = None):
    config_file = load_config_file()
    
    config_file["NotForTrade"].clear()
    save_config_file(config_file)
    await ctx.send("✅ Nft list has been cleared!")


#Tags command
@bot.group(name="tags", aliases=["tag"], invoke_without_command=True)
async def tags(ctx):
    await ctx.send('❌ Use `add`, `remove`, `list`, `clear` or `set`!')

@tags.command(name="list") #Tags Embed List
async def TagsList(ctx):

    tagsembed = discord.Embed(
        title="🏷️ Tags ",
        color=0x33cc66,
        description="- upgrade\n- downgrade\n- demand\n- rares\n- rap\n- robux\n- adds\n- projecteds\n- any\n- wishlist\n",
    )

    await ctx.send(embed=tagsembed) #Sends embed

@tags.command(name="add", aliases=["a"]) #Tags add
async def TagsAdd(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send("❌ Forgot the tag! Use `tags list` to see list of tags.")
        return
    
    All_Of_Tags =["adds", "upgrade", "downgrade", "any", "wishlist", "demand", "rares", "rap", "robux", "projecteds"]
    if arg not in All_Of_Tags:
        await ctx.send(f"❌ Tag doesnt exist! Use `tags list` to see list of tags.")
        return

    config_file = load_config_file()

    if arg in config_file["Tags"]:
        await ctx.send(f"❌ Tag already in Tags.")
        return
    
    #Adds ID to the config
    if len(config_file["Tags"]) < 4:
        config_file["Tags"].append(arg)
        save_config_file(config_file)
        await ctx.send(f"✅ {arg} has been added to Tags")
    else:
        await ctx.send("❌ Theres 4 tags already!")

@tags.command(name="remove", aliases=["r"]) #Tags remove
async def TagsRemove(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send("❌ Forgot the tag! Use `tags list` to see list of tags.")
        return
    
    config_file = load_config_file()
    
    if arg not in config_file["Tags"]:
        await ctx.send(f"❌ Tag not found in Tags.")
        return
    
    config_file["Tags"].remove(arg)
    save_config_file(config_file)
    await ctx.send(f"✅ {arg} has been removed from Tags!")

@tags.command(name="clear") #Tags clear
async def TagsClear(ctx, *, arg: str = None):
    config_file = load_config_file()
    
    config_file["Tags"].clear()
    save_config_file(config_file)
    await ctx.send("✅ Tags have been cleared!")

@tags.command(name="set")
async def Tagsset(ctx, *, arg: str = None):
    config_file=load_config_file()
    if arg in config_file["Presets"]:
        config_file["Tags"] = config_file["Presets"][f"{arg.lower()}"]
        save_config_file(config_file)
        await ctx.send(f"✅ Tags changed to {arg.lower()} preset!")
        return
    
    elif arg not in config_file["Presets"]:
        await ctx.send(f"❌ Preset doesnt exist!")
        return
    

#Config command        
@bot.command(name="config") 
async def config_command(ctx):
    config_file = load_config_file()

    responseIL = requests.get(urlIL)
    resIL = responseIL.json()

    responsePI = requests.get(urlPI)
    resPI = responsePI.json()

    configembed = discord.Embed(
        title="📋 Your Config",
        color=0x33cc66
    )

    if config_file["AutoPick"] == "false" and config_file["Top4"] == "false":
        Manual_Pick = "true"
    else:
        Manual_Pick = "false"

    #Fields
    configembed.add_field(name="Top 4", value=f"`{config_file['Top4'] }`", inline=True)  
    configembed.add_field(name="Auto Pick", value=f"`{config_file['AutoPick'] }`", inline=True)
    configembed.add_field(name="Manual Pick", value=f"`{Manual_Pick}`", inline=True)
    configembed.add_field(name="Min Value (autopick)", value=f"`{config_file['MinValue'] }`", inline=True)
    configembed.add_field(name="Demand Only", value=f"`{config_file['DemandOnly'] }`", inline=False)
    configembed.add_field(name="Time", value=f"`{int(config_file['Time']/60)} minutes`", inline=False)
    configembed.add_field(name="Robux", value=f"`{config_file['Robux'] }`", inline=False) #In life we have robux

    if config_file["AutoPick"] == "true": #Items offered Autopick
        configembed.add_field(name="✉️ Offered Items:", value="AutoPick chosen! Bot will randomly pick items", inline=False)

    Top4Items=[]
    #Items offered Top4
    if config_file['Top4'] == "true":
        for ItemsHold in resPI.get("data"):
            ItemID = ItemsHold.get("assetId")
            if ItemsHold.get("isOnHold") is True:
                continue
            if ItemID in config_file['NotForTrade']:
                continue
            item_data = resIL["items"].get(str(ItemID))
            if item_data:
                if item_data[1] != "": #Checks if theres an acronym and if there is it picks it
                    ItemName = item_data[1]
                else:
                    ItemName=item_data[0]# If there isnt sets item name
                value=item_data[4]
                rap=item_data[2]
                if config_file['DemandOnly'] == "true" and item_data[5] <= 0:#item_data[5] is demand in roli api
                    continue
                Top4Items.append((ItemID, value, ItemName))
        Top4List = [(ItemName, value) for _, value, ItemName in sorted(Top4Items, key=lambda x: x[1], reverse=True)[:4]]
        Top4FinalList = ""
        for Item_Name, value in Top4List:
            Top4FinalList += f"● {Item_Name} {value}\n"
        configembed.add_field(name="✉️ Offered Items", value=Top4FinalList, inline=False)


    if Manual_Pick == "true": #Manual pick
        Manual_Offered =[]
        if config_file["OfferedItems"]:
            for item in config_file["OfferedItems"]:
                item_data = resIL["items"].get(str(item))
                if item_data:
                    if item_data[1] != "": #Checks if theres an acronym and if there is it picks it
                        ItemName = item_data[1]
                    else:
                        ItemName=item_data[0]# If there isnt sets item name
                    value=item_data[4]
                    Manual_Offered.append((item, value, ItemName))

                ManualList = [(ItemName, value) for _, value, ItemName in sorted(Manual_Offered, key=lambda x: x[1], reverse=True)[:4]]
                ManualListFinal = ""
                for ItemName, value in ManualList:
                    ManualListFinal += f"● {ItemName} {value}\n"
        else:
            ManualListFinal="`None`"

        configembed.add_field(name="✉️ Offered Items:", value=ManualListFinal, inline=False)

    #Tags
    Tags = ""
    for item in config_file["Tags"]:
        if item in Tag_Icons:
            Tags += f"- {Tag_Icons[item]}\n"
        else:
            Tags += f"- {item}\n"

    configembed.add_field(name="🏷️ Tags", value=Tags, inline=False) #Tags
    
    #Requested Items
    Fancy_Requested = ""  
    if config_file["RequestedItems"]:
        for item in config_file["RequestedItems"]: #changed item_id to item
            item_data = resIL["items"].get(str(item))
            if item_data:
                if item_data[1] != "": #Checks if theres an acronym and if there is it picks it
                    Item_Name = item_data[1]
                else:
                    Item_Name=item_data[0]# If there isnt sets item name
                value=item_data[4]
                Fancy_Requested += f"● {Item_Name} {value}\n"
    else:
        Fancy_Requested = "`None`"

    configembed.add_field(name="🔍 Requested Items", value=Fancy_Requested, inline=False)

    await ctx.send(embed=configembed) #sends embed



#Set command
@bot.group(name="set", invoke_without_command=True)
async def set(ctx):
    await ctx.send('❌ Wrong option!')

@set.command(name="autopick") #Set Autopick
async def SetAutopick(ctx):
    config_file = load_config_file()
    config_file["AutoPick"] = "true"
    config_file["Top4"] = "false"
    save_config_file(config_file)
    await ctx.send('✅ AutoPick has been picked!')

@set.command(name="demandonly") #Set DemandOnly
async def SetDemandOnly(ctx, *, arg: str = None):
    if arg == "true":
        config_file = load_config_file()
        config_file["DemandOnly"] = "true"
        await ctx.send('✅ DemandOnly has been set to: True')

        save_config_file(config_file)
        return

    if arg == "false":
        config_file = load_config_file()
        config_file["DemandOnly"] = "false"
        save_config_file(config_file)
        await ctx.send('✅ DemandOnly has been set to: False')
        return

    await ctx.send('❌ DemandOnly can be only set as: `false/true`')

@set.command(name="manualpick", aliases=["manual"]) #Set Manualpick
async def SetManualPick(ctx):
    config_file = load_config_file()
    config_file["AutoPick"] = "false"
    config_file["Top4"] = "false"
    save_config_file(config_file)
    await ctx.send('✅ ManualPick has been picked!')

@set.command(name="minvalue", aliases=["minval", "minimumvalue"]) #Set MinValue
async def SetMinValue(ctx, *, arg: str = None):
    config_file = load_config_file()
    if arg != None:
        if arg.isnumeric():
            config_file["MinValue"] = int(arg)
            save_config_file(config_file)
            await ctx.send(f'✅ Minvalue has been set to: `{arg}`')
        else:
            await ctx.send('❌ This isnt a number')
            return 
    else:
        await ctx.send('❌ You need to type a number')

@set.command(name="playerid") #Set PlayerID
async def SetPlayerID(ctx, *, arg: str = None):
    config_file = load_config_file()
    if arg != None:
        if arg.isnumeric():
            config_file["PlayerID"] = int(arg)
            save_config_file(config_file)
            await ctx.send(f'✅ PlayerID has been set to: `{arg}`')
            await ctx.send('✅ Use `!rolisetup phrase` to add your Rolimons cookie') 
            print("PlayerID has been set! Use !rolisetup phrase to add your Rolimons cookie")
        else:
            await ctx.send('❌ This isnt a number')
    else:
        await ctx.send('❌ You need to type a number')

@set.command(name="robux") #Set Robux
async def SetRobux(ctx, *, arg: str = None):
    config_file = load_config_file()
    if arg != None:
        if arg.isnumeric():
            config_file["Robux"] = int(arg)
            save_config_file(config_file)
            await ctx.send(f'✅ Robux has been set to: `{arg}`')
        else:
            await ctx.send('❌ This isnt a number')
            return
    else:
        await ctx.send('❌ You need to type a number')

@set.command(name="time") #Set Time
async def SetTime(ctx, *, arg: str = None):
    config_file = load_config_file()
    if arg != None:
        if arg.isnumeric():
            config_file["Time"] = int(arg)
            save_config_file(config_file)
            await ctx.send(f'✅ Time has been set to: `{arg}` seconds')
        else:
            await ctx.send('❌ This isnt a number')
    else:
        await ctx.send('❌ You need to type a number')

@set.command(name="top4") #Set Top4
async def SetAutopick(ctx):
    config_file = load_config_file()
    config_file["Top4"] = "true"
    config_file["AutoPick"] = "false"
    save_config_file(config_file)
    await ctx.send('✅ Top4 has been picked!')

@set.command(name="channel") #Set Discord Channel
async def SetChannel(ctx, *, arg: str = None):
        config_file = load_config_file()
        config_file["DiscordChannel"] = int(arg)
        save_config_file(config_file)
        await ctx.send('✅ Discord Channel has been set')



#Items Command
@bot.group(name="items", aliases=["item"], invoke_without_command=True)
async def items(ctx):
    await ctx.send('❌ Use `offered <option>` or `requested <option>`.')


#Items Offered
@items.group(name="offered", aliases=["o"], invoke_without_command=True) #Items offered
async def itemsoffered(ctx):
    await ctx.send('❌ Use `add`, `clear` or `remove`.')

@itemsoffered.command(name="add", aliases=["a"]) #Items offered add
async def itemsofferedadd(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send('❌ Please provide an item ID or name to add')
        return
    
    config_file = load_config_file()
    if len(config_file["OfferedItems"]) < 4:
        if arg.isnumeric():
                item_data = resIL["items"].get(str(int(arg)))
                if item_data:
                    config_file["OfferedItems"].append(int(arg))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {arg} has been added to Offered Items!')
                else:
                    await ctx.send('❌ Couldnt find this ID in Rolimons API')
        else:
            for key, value in resIL["items"].items():
                if value[1].casefold() == arg.casefold() or value[0].casefold() == arg.casefold():
                    config_file["OfferedItems"].append(int(key))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {value[1]} has been added to Offered Items!')
                    return
            else:
                await ctx.send('❌ Couldnt find this name in Rolimons API')
    else:
        await ctx.send('❌ Theres 4 IDs in Offered Items!')            

@itemsoffered.command(name="remove", aliases=["r"]) #Items offered remove
async def itemsofferedremove(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send('❌ Please provide an item ID or name to remove')
        return
    config_file = load_config_file()

    if arg.isnumeric():
        if int(arg) in config_file["OfferedItems"]:
            config_file["OfferedItems"].remove(int(arg))
            save_config_file(config_file)  
            await ctx.send(f'✅ {arg} has been removed from Offered Items!')
        else:
            await ctx.send('❌ Couldnt find this ID in your config')
    else:
        for key, value in resIL["items"].items():
            if value[1].casefold() == arg.casefold() or value[0].casefold() == arg.casefold():
                if int(key) in config_file["OfferedItems"]:
                    config_file["OfferedItems"].remove(int(key))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {value[1]} has been removed from Offered Items!')
                else:
                    await ctx.send('❌ Couldnt find this acronym in your config')
                return
        else:
            await ctx.send('❌ Couldnt find this name in Rolimons API')
            
@itemsoffered.command(name="clear") #Items offered clear
async def itemsofferedclear(ctx, *, arg: str = None):
    config_file = load_config_file()
    
    config_file["OfferedItems"].clear()
    save_config_file(config_file)
    await ctx.send("✅ OfferedItems items have been cleared!")


#Items Requested
@items.group(name="requested", aliases=["r"], invoke_without_command=True) #Items offered
async def itemsrequested(ctx):
    await ctx.send('❌ Use `add`, `clear` or `remove`.')

@itemsrequested.command(name="add", aliases=["a"]) #Items offered add
async def itemsrequestedadd(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send('❌ Please provide an item ID to remove')
        return
    
    config_file = load_config_file()
    if len(config_file["RequestedItems"]) < 4:
        if arg.isnumeric():
                item_data = resIL["items"].get(str(int(arg)))
                if item_data:
                    config_file["RequestedItems"].append(int(arg))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {arg} has been added to Requested Items!')
                else:
                    await ctx.send('❌ Couldnt find this ID in Rolimons API')
        else:
            for key, value in resIL["items"].items():
                if value[1].casefold() == arg.casefold() or value[0].casefold() == arg.casefold():
                    config_file["RequestedItems"].append(int(key))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {value[1]} has been added to Requested Items!')
                    return
            else:
                await ctx.send('❌ Couldnt find this name in Rolimons API')
    else:
        await ctx.send('❌ Theres 4 IDs in Requested Items!') 

@itemsrequested.command(name="remove", aliases=["r"]) #Items offered remove
async def itemsrequestedremove(ctx, *, arg: str = None):
    if arg is None:
        await ctx.send('❌ Please provide an item ID or name to remove')
        return
    config_file = load_config_file()

    if arg.isnumeric():
        if int(arg) in config_file["RequestedItems"]:
            config_file["RequestedItems"].remove(int(arg))
            save_config_file(config_file)  
            await ctx.send(f'✅ {arg} has been removed from Requested Items!')
        else:
            await ctx.send('❌ Couldnt find this ID in your config')
    else:
        for key, value in resIL["items"].items():
            if value[1].casefold() == arg.casefold() or value[0].casefold() == arg.casefold():
                if int(key) in config_file["RequestedItems"]:
                    config_file["RequestedItems"].remove(int(key))
                    save_config_file(config_file)  
                    await ctx.send(f'✅ {value[1]} has been removed from Requested Items!')
                else:
                    await ctx.send('❌ Couldnt find this acronym in your config')
                return
        else:
            await ctx.send('❌ Couldnt find this name in Rolimons API')

@itemsrequested.command(name="clear") #NFT clear
async def itemsrequestedclear(ctx, *, arg: str = None):
    config_file = load_config_file()
    
    config_file["RequestedItems"].clear()
    save_config_file(config_file)
    await ctx.send("✅ Requested Items have been cleared!")


@bot.command(name="rolisetup", invoke_without_command=True)
async def set(ctx, *, arg: str = None):
    config_file = load_config_file()
    if arg == "phrase":
        if config_file["PlayerID"] != 0:
            responseRV = requests.get(f'https://api.rolimons.com/auth/v1/getphrase/{config_file["PlayerID"]}')
            resRV = responseRV.json()
            await ctx.send(f'Heres your phrase:\n`{resRV["phrase"]}`')
            await ctx.send(f'Paste it on your profile or [Rolimons game](https://www.roblox.com/games/10299209169/)')
            await ctx.send(f'Use `!rolisetup game/profile` after pasting ur phase')
        else:
            await ctx.send('❌ You need to add your Playerid! `!set playerid <number>`')
    
    elif arg == "profile":
        if config_file["PlayerID"] != 0:
            responseRPV = requests.post(f"https://api.rolimons.com/auth/v1/verifyphrase/{config_file['PlayerID']}")
            resRPV = responseRPV.json()
            if resRPV.get("success"):
                config_file["RolimonsToken"] = ""
                config_file["RolimonsToken"] = (f'{responseRPV.cookies.get("_RoliVerification")}')
                save_config_file(config_file)
                await ctx.send("✅ Your Rolimons account has been added!")
                await ctx.send("✅ Reopen python file to start making trade ads!")
                print("Reopen python file to start making trade ads!")
            if resRPV.get("code") == 7114:
                await ctx.send("❌ Rolimons doesnt see your phrase! If its on your Roblox profile then try entering this command again soon!")
            else: 
                await ctx.send("❌", resRPV)  
                print(resRPV)
      
        else:
            await ctx.send('❌ You need to add your Playerid! `!set playerid <number>`')

    elif arg == "game":
        if config_file["PlayerID"] != 0:
            responseRGV = requests.post(f"https://api.rolimons.com/auth/v1/confirmgamephraseverification/{config_file['PlayerID']}")
            resRGV = responseRGV.json()
            if resRGV.get("success"):
                config_file["RolimonsToken"] = ""  
                config_file["RolimonsToken"] = (f'{responseRGV.cookies.get("_RoliVerification")}')
                save_config_file(config_file)
                await ctx.send("✅ Your Rolimons account has been added!")
                await ctx.send("✅ Reopen python file to start making trade ads!")
                print("Reopen python file to start making trade ads!")
            if resRGV.get("code") == 7117:
                await ctx.send("❌ Rolimons didnt get your phrase! Try entering this command again soon!")
            else: 
                await ctx.send("❌", resRGV)
                print(resRGV)
        else:
            await ctx.send('❌ You need to add your Playerid! `!set playerid <number>`')
    else:
        await ctx.send("❌ To get your phrase type `!rolisetup phrase`")

        
#Help command
bot.remove_command('help')
@bot.group(name="help", invoke_without_command=True)
async def help(ctx):
    nftembed = discord.Embed(
        title="📝 Help",
        description='List of all commands with options avaible in this discord bot.\n',
        color=0x33cc66
    )
    nftembed.add_field(name="config", value="", inline=False)
    nftembed.add_field(name="rolisetup", value="phrase/profile/game", inline=False)
    nftembed.add_field(name="items/item:", value="offered/o or requested/r \n- `add/a <id/name>`\n- `remove/r <id/name>`\n- `clear`\n", inline=False)
    nftembed.add_field(name="nft", value='`add/a <id/name>`\n`remove/r <id/name>`\n`clear`\n`list`', inline=False)
    nftembed.add_field(name="tags/tag", value="`add/a <tag>`\n`remove/r <tag>`\n`set <preset>`\n`clear`\n`list`\n", inline=False)
    nftembed.add_field(name="set", value="`autopick`\n`top4`\n`channel`\n`demandonly <true/false>`\n`manualpick/manual`\n`minvalue/minimumvalue/minval <number>`\n`playerid <id>`\n`robux <number>`\n`time <number> (in seconds)`\n`rolitoken <token>`", inline=False)
    await ctx.send(embed=nftembed)

#Hello again someone
#Last change of discord bot was on 2025/12/15 :P

#Start of Trade Ad maker
#Started working on this on 2025/09/21 :D
async def trade_ad_loop():
    bot.loop.create_task(check_inventory_updates())
    config_file = load_config_file()
    
    #Bot sending Errors/Trade ads to discord channel
    channel_id = config_file.get("DiscordChannel")
    channel = None
    if channel_id != 0:
        channel = bot.get_channel(channel_id)
    else:
        print("Discord Channel not found!\nCheck if you typed correct id or use !set channel <id> to set it!")
    while True:
        config_file = load_config_file()
        Logs =""
        data = {
            "offer_item_ids": config_file["OfferedItems"],
            "offer_robux": config_file["Robux"],
            "player_id": config_file["PlayerID"],
            "request_item_ids": config_file["RequestedItems"],
            "request_tags": config_file["Tags"]
        }

        headers = {
            "content-type": "application/json",
            "cookie": "_RoliVerification=" + config_file["RolimonsToken"]
        }

        responsePI = requests.get(urlPI)
        res_PI = responsePI.json()
        responseIL = requests.get(urlIL)
        res_IL = responseIL.json()

        ItemValues=[]
        if config_file["Top4"] == "true" or config_file["AutoPick"] == "true":
            dataIH = res_PI.get("data")
            for ItemsHold in dataIH:
                ItemID = ItemsHold.get("assetId")
                if ItemsHold.get("isOnHold") is True:
                    continue
                if ItemID in config_file["NotForTrade"]:
                    continue
                item_data = res_IL["items"].get(str(ItemID))
                if item_data:
                    value=item_data[4]
                    rap=item_data[2]
                    if config_file["DemandOnly"] == "true" and item_data[5] <= 0:#item_data[5] is demand in roli api
                        continue
                    if config_file["AutoPick"] == "true" and value < config_file["MinValue"]:
                        continue
                    ItemValues.append((ItemID, value, rap))
            if config_file["Top4"] == "true":
                Top4List = [ItemID for ItemID, _, _ in sorted(ItemValues, key=lambda x: x[1], reverse=True)[:4]]
                data["offer_item_ids"] = Top4List           
            elif config_file["AutoPick"] == "true":
                if len(ItemValues) >= 4:
                    AutoPickList = [ItemID for ItemID, _, _ in sorted(random.sample(ItemValues, 4), key=lambda x: x[1], reverse=True)]
                else:
                    AutoPickList = [ItemID for ItemID, _, _ in sorted(ItemValues, key=lambda x: x[1], reverse=True)]
                data["offer_item_ids"] = AutoPickList
        
        if config_file["Robux"] <= 0: #u cant make a trade ad when robux are set to 0
            del data["offer_robux"]

        #Foolproofing Requesteds👀
        if config_file["Tags"] == [] and config_file["RequestedItems"] ==[]:
            config_file["Tags"] = config_file["Presets"]["default"]
            data["request_tags"] = config_file["Presets"]["default"]
            save_config_file(config_file)
            if channel != 0:
                await channel.send('❌ There are no tags or items set 🤬 Changed tags to default tho 🤤 @everyone')
        if len(config_file["Tags"]) + len(config_file["RequestedItems"]) >4:
            if len(config_file["RequestedItems"]) >1:
                config_file["Tags"] = []
                data["request_tags"] = []
                save_config_file(config_file)
                if channel != 0:
                    await channel.send('❌ Tags have been removed, Dont make trade ads when tags + items requested > 4 @everyone')
            else:
                config_file["RequestedItems"] = []
                config_file["Tags"] = config_file["default"]
                data["request_tags"] = config_file["default"]
                save_config_file(config_file)
                if channel != 0:
                    await channel.send('❌ Items requested have been removed and tags set to default. Dont make trade ads when tags + items requested > 4 @everyone')

        #Sends trade ad 
        responseTA = requests.post(urlTA, json=data, headers=headers)
            
        res_TA = responseTA.json()
        if res_TA.get("success") == True:
            TradeMode=""
            TotalValue = 0
            TotalRap = 0
            OffItemslist =[]

            if config_file["Top4"] == "true":
                TradeMode = "Top4"
            elif config_file["AutoPick"] ==   "true":
                TradeMode = "Autopick"
            else:
                TradeMode = "Manualpick"
            if config_file["DemandOnly"] =="true" and TradeMode != "Manualpick":
                TradeMode += " with DemandOnly"

            Logs += (f"✅ Trade ad Posted! ({TradeMode})\n\n")

            for item in data["offer_item_ids"]:
                item_data = res_IL["items"].get(str(item))
                if item_data:
                    TotalValue += item_data[4]
                    TotalRap += item_data[2]
                    if item_data[1] == "":
                        OffItemslist.append(f"- {item_data[0]} | Value: {item_data[4]}")
                    else:
                        OffItemslist.append(f"- {item_data[1]} | Value: {item_data[4]}")

            Logs += (f"📊 Total Value: {TotalValue}\n")
            Logs += (f"📊 Total RAP: {TotalRap}\n\n")
            Logs += ("📜 Offered Items:\n")
            OffItemsPrint=""
            for line in OffItemslist:
                OffItemsPrint += f"{line}\n"
            Logs += (f"{OffItemsPrint}\n")

            if config_file["RequestedItems"]:
                ReqItems = []
                for line in config_file["RequestedItems"]:
                    item_data = res_IL["items"].get(str(line))
                    if item_data[1] == "":
                        ReqItems.append(f"- {item_data[0]} | Value: {item_data[4]}")
                    else:
                        ReqItems.append(f"- {item_data[1]} | Value: {item_data[4]}")

                ReqItemslist =""
                for line in ReqItems:
                    ReqItemslist += f"{line}\n"
                
                Logs += (f"🔍 Requested Items:\n{ReqItemslist}\n\n")

            #Tags
            TagsText = ""
            for item_str in config_file["Tags"]:
                TagsText += f"- {Tag_Icons.get(item_str)}\n"
            if TagsText:
                Logs += (f"🔍 Tags:\n{TagsText}\n")

            if config_file["Robux"] > 0:
                Logs += (f'💲 Robux: {config_file["Robux"]}\n\n')

            future_time = datetime.now() + timedelta(seconds=config_file["Time"])   
            Logs +=(f'🕒 Next Trade Ad will be posted in: {config_file["Time"] / 60} minutes, Aka: {future_time.strftime("%H:%M")}\n')

            #Sends Trade ad into discord channel and terminal
            print(Logs)
            if channel:
                await channel.send(Logs)

        ErrorLogs =""     
        if res_TA.get("success") == False:
            future_time = datetime.now() + timedelta(seconds=config_file["Time"])
            if res_TA.get("code") == 7105:
                ErrorLogs +=(f"⏳ Ad creation cooldown has not elapsed ⏳\n🕒 Next try will be at: {future_time.strftime('%H:%M')} 🕒")
    
            elif res_TA.get("code") == 7110:
                ErrorLogs+=(f"❌ Change your Robux! Robux number can't exceed 50% RAP. ❌\n🕒 Next try will be at: {future_time.strftime('%H:%M')} @everyone 🕒")            
            
            elif res_TA.get("code") == 5:
                ErrorLogs +=(f"❌ Invalid Rolimons Token! ❌\n🕒 Next try will be at: {future_time.strftime('%H:%M')} @everyone 🕒")
    
            elif res_TA.get("code") == 14:
                ErrorLogs +=(f"❌ 24-hour ad creation limit has been hit! ❌\n🕒 Next try will be at: {future_time.strftime('%H:%M')} @everyone 🕒")
    
            elif res_TA.get("code") == 7104:
                ErrorLogs+=(f"❌ Player does not own all offered items! ❌\n🕒 Next try will be at: {future_time.strftime('%H:%M')} @everyone 🕒")
    
            elif res_TA.get("code") == 7111:
                ErrorLogs+=(f"❌ Requested value exceeds limit based on offered value (More than 5x) ❌\n🕒 Next try will be at: {future_time.strftime('%H:%M')} @everyone 🕒")
                        
            elif res_TA.get("code") != None:
                ErrorLogs += (f"❌ Something is not working!\n❌ Error message: {res_TA.get('message')}\n❌ Error code: {res_TA.get('code')}\n🕒 Next try will be at: {future_time.strftime('%H:%M')} @everyone 🕒")
            
            print(ErrorLogs)
            if channel:
                await channel.send(ErrorLogs)

        await asyncio.sleep(int(config_file["Time"]))

#Hello hello again
#Last change of Trade Ad Thingy was on 2025/12/15 :P 

#Token
config_file = load_config_file()

TOKEN = config_file["TOKEN"]

#Errors
@bot.event
async def on_command_error(ctx, error):
    print("Command error:", error)


#Starts Trade Ad Thingy when discord bot loads
@bot.event
async def on_ready():
    if config_file["PlayerID"] != 0:
        bot.loop.create_task(trade_ad_loop())
        bot.loop.create_task(check_inventory_updates())
    else:
        print('YOU NEED TO ADD YOUR PLAYER ID\nUse `!set playerid <id>`')


if __name__ == "__main__":
    if not TOKEN:
        print("No discord token detected. Please add it into your config file.")
        input("")
    else:
        bot.run(TOKEN)



