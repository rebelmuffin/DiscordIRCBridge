#!/usr/bin/python3

import sys
import json
import threading

import discord
from discord.ext import commands

from classes import IRCBot


# Setup discord bot
discord_bot = commands.Bot("**__", None)

# Load config
try:
    with open("config.json", "r") as f:
        config = json.loads(f.read())
except FileNotFoundError:
    print("Bot config file not found!")
    sys.exit(-1)


# Retrieve config data from dict
TOKEN = config.get("TOKEN")
IRC_HOST = config.get("IRC_HOST")
IRC_PORT = config.get("IRC_PORT", 6667)
IRC_PASS = config.get("IRC_PASS")
IRC_NICK = config.get("IRC_NICK")
IRC_REAL = config.get("IRC_REAL")


# Setup IRC bot
irc_bot = IRCBot(IRC_NICK, IRC_REAL, IRC_HOST, IRC_PORT)
irc_bot.discord_bot = discord_bot
irc_thread = threading.Thread(target=irc_bot.start)
irc_thread.start()


@discord_bot.event
async def on_ready():
    print(f"Discord bot ready on {discord_bot.user}")
    sys.stdout.flush()
    with open("channels.json", "r") as file:
        binds = json.loads(file.read())
    for irc, dc in binds.items():
        try:
            await discord_bot.fetch_channel(int(dc))
        except discord.NotFound:
            try:
                user_profile = await discord_bot.fetch_user_profile(int(dc))
            except discord.HTTPException:
                print(f"User or Channel `{dc}` is inaccessible")
                continue
            user = user_profile.user
            await user.create_dm()


@discord_bot.listen()
async def on_message(msg: discord.Message):
    await discord_bot.wait_until_ready()
    if msg.author != discord_bot.user:
        user_profile = await discord_bot.fetch_user_profile(msg.author.id)
        msg.author = user_profile.user
        print(f"[DISCORD] <{msg.author} ({msg.author.id})> \"{msg.content}\"")
        irc_bot.process_message(msg.channel, msg)


@discord_bot.listen()
async def on_message_edit(_, after: discord.Message):
    await discord_bot.wait_until_ready()
    if after.author != discord_bot.user:
        user_profile = await discord_bot.fetch_user_profile(after.author.id)
        after.author = user_profile.user
        print(f"[DISCORD] <{after.author} ({after.author.id})> \"{after.content}\"")
        irc_bot.process_message(after.channel, after, content_prefix="*")

discord_bot.run(TOKEN)
