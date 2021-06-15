import asyncio
import json
from typing import Union, Optional

import discord
from discord.ext import commands
import irc.bot
import irc.strings


MAX_NOTICE_LENGTH = 512


class IRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, realname, server, port=6667):
        super().__init__([(server, port)], nickname, realname)
        self.loop = asyncio.new_event_loop()
        self.discord_bot: Optional[commands.Bot] = None
        self.discord_channels = irc.bot.IRCDict()

    def on_nicknameinuse(self, c, _):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, _):
        print(f"IRC {self.connection.get_nickname()} ready")
        # Join general
        c.join("#general")
        # Load channel binds
        with open("channels.json", "r") as file:
            channels = json.loads(file.read())
        for channel in channels:
            self.bind_channel(channel, channels[channel])

    def on_privmsg(self, _, e):
        self.process_command(e, e.arguments[0])

    def process_message(self, channel: Union[discord.GroupChannel, discord.DMChannel, discord.TextChannel],
                        message: discord.Message, content_prefix: str = "", content_suffix: str = ""):
        """Processes a message that came to discord bot"""
        c = self.connection

        # Get bound IRC channel
        channel_id = channel.id
        irc_channel = self.get_channel_from_discord(channel_id)
        if not irc_channel:
            return

        # Send message into the bound IRC channel
        attachments = ' '.join([a.url for a in message.attachments])

        # Clean the content and wrap it correctly for IRC notice compatibility
        content_lines = (content_prefix + str(message.clean_content) + content_suffix).split("\n")
        content_lines_paginated = []
        for line in content_lines:
            pages = [line[i:i + MAX_NOTICE_LENGTH] for i in range(0, len(line), MAX_NOTICE_LENGTH)]
            if len(pages) > 1:
                content_lines_paginated = content_lines_paginated + pages
            else:
                content_lines_paginated.append(line)

        if isinstance(channel, discord.DMChannel):
            for line in content_lines_paginated:
                c.notice(irc_channel, line)
            if attachments:
                c.notice(irc_channel, attachments)
        else:
            for line in content_lines_paginated:
                c.notice(irc_channel, f"<{message.author}> {line}")
            if attachments:
                c.notice(irc_channel, f"<{message.author}> {attachments}")

    def on_pubmsg(self, _, e):
        if self.discord_bot is None:
            return
        discord_channel = self.get_discord_channel(self.discord_channels.get(e.target))
        self.discord_bot.loop.create_task(discord_channel.send(" ".join(e.arguments)))

    def get_channel_from_discord(self, channel_id: int):
        """Gets IRC channel name from discord channel ID"""
        inverted = {v: k for k, v in self.discord_channels.items()}
        return inverted.get(channel_id)

    def get_channel_from_irc(self, channel_name: str):
        """Gets discord channel id from IRC channel name"""
        return self.discord_channels.get(channel_name)

    def get_discord_channel(self, channel_id: int) -> Union[discord.DMChannel,
                                                            discord.TextChannel,
                                                            discord.GroupChannel]:
        """Gets discord channel object from the id"""
        channel = self.discord_bot.get_channel(channel_id)
        if not channel:
            channel = self.discord_bot.get_user(channel_id)
        return channel

    def bind_channel(self, irc_channel: str, discord_channel_id: int):
        """Binds IRC channel to discord channel"""
        self.discord_channels[irc_channel] = discord_channel_id
        self.connection.join(irc_channel)

    def perm_bind(self, irc_channel: str, discord_channel_id: int):
        """Permanently binds an IRC channel to discord channel"""
        # Bind in memory
        self.bind_channel(irc_channel, discord_channel_id)

        # Write to channels.json
        with open("channels.json", "r") as f:
            binds = json.loads(f.read())
        binds[irc_channel] = int(discord_channel_id)
        with open("channels.json", "w") as f:
            f.write(json.dumps(binds))

    def process_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        args = cmd.split()[1:]
        cmd = cmd.split()[0]

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel Stats ---")
                c.notice(nick, f"Channel: {chname}")
                users = sorted(chobj.users())
                c.notice(nick, f"Users: {', '.join(users)}")
                opers = sorted(chobj.opers())
                c.notice(nick, f"Opers: {', '.join(opers)}")
                voiced = sorted(chobj.voiced())
                c.notice(nick, f"Voiced: {', '.join(voiced)}")
        elif cmd == "channels":
            c.notice(nick, f"Channels: {', '.join([str(ch) for ch in self.channels])}")
            c.notice(nick, f"Channel Objs: {', '.join([str(ch) for ch in self.channels.items()])}")
        elif cmd == "test":
            c.notice(nick, f"Target: {e.target}")
            c.notice(nick, f"Source: {e.source}")
            c.notice(nick, f"Args: {str(args)}")
        elif cmd == "bind":
            irc_channel = args[0]
            discord_channel = args[1]
            try:
                if not self.get_discord_channel(int(discord_channel)):
                    return c.notice(nick, "Discord channel not found!")
                c.join(irc_channel)
                self.bind_channel(irc_channel, discord_channel)
                c.notice(nick, "Bind successful")
            except Exception as e:
                c.notice(nick, f"Exception: {e}")
        elif cmd in ["pbind", "permbind", "permabind"]:
            irc_channel = args[0]
            discord_channel = args[1]
            try:
                irc_channel = "#" + irc_channel if not irc_channel.startswith("#") else irc_channel
                if not self.get_discord_channel(int(discord_channel)):
                    return c.notice(nick, "Discord channel not found!")
                c.join(irc_channel)
                self.perm_bind(irc_channel, discord_channel)
                c.notice(nick, "Bind successful")
            except Exception as e:
                c.notice(nick, f"Exception: {e}")
        else:
            c.notice(nick, f"Unknown Command: {cmd}")
