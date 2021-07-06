import discord
import asyncio
from discord.ext import commands
from discord import utils
import traceback
import sqlite3
import validators
import Utils
import Config
from datetime import datetime, timedelta
import os
import re
from random import randint
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

last_Messages = []


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged in as')
        print(self.bot.user.name)
        print(self.bot.user.id)
        print('------')
        print('Guilds:')

        game = discord.Activity(name='!help <\> !invite')
        game.type = discord.ActivityType.playing
        await self.bot.change_presence(activity=game)

        for guild in self.bot.guilds:  # Проверяет все сервера
            print(guild.name)
            for member in guild.members:  # Проверяет всех участников на серверах
                cursor.execute(f"SELECT id FROM users where id={member.id} AND guild={guild.id}")
                if cursor.fetchone() is None:  # Если нет участника в БД, то добавляет его
                    await Utils.add_New_User(member, guild.id)

                cursor.execute(f'UPDATE users SET enterTime=? where id=? AND guild=?',
                               (datetime.today(), member.id, guild.id))
                cursor.execute(f'UPDATE users SET msgXpTime=? where id=? AND guild=?',
                               (datetime.today(), member.id, guild.id))
                conn.commit()

            cursor.execute(f"SELECT privateChannelId FROM settings where guild={guild.id}")
            if cursor.fetchone() is None:
                await Utils.add_New_Guild(guild.id)
            else:
                cursor.execute(f"SELECT privateChannelId FROM settings where guild={guild.id}")
                channelID = cursor.fetchone()[0]
                privateChannel = guild.get_channel(int(channelID))
                if privateChannel is None:
                    cursor.execute(f'UPDATE settings SET privateChannelId=? where guild=?', (0, guild.id))
            conn.commit()

            cursor.execute(f"SELECT id FROM users where guild={guild.id}")
            users = cursor.fetchall()
            for row in users:
                if not row[0] in [y.id for y in guild.members]:
                    print(f'Deleted user: {row[0]}')
                    cursor.execute(f'DELETE FROM users WHERE id={row[0]} AND guild={guild.id}')
                    conn.commit()

            cursor.execute(f"SELECT id FROM voice where guild={guild.id}")
            row = cursor.fetchall()
            for id in row:
                channel = guild.get_channel(int(id[0]))
                if channel is None:
                    cursor.execute(f'DELETE FROM voice WHERE id={id[0]} AND guild={guild.id}')

            conn.commit()

        print('------')

        cursor.execute(f"SELECT guild FROM settings")
        guilds = cursor.fetchall()
        for row in guilds:
            if not int(row[0]) in [g.id for g in self.bot.guilds]:
                cursor.execute(f'DELETE FROM settings WHERE guild={row[0]}')
                cursor.execute(f'DELETE FROM embed WHERE guild={row[0]}')
                cursor.execute(f'DELETE FROM messages WHERE guild={row[0]}')
                cursor.execute(f'DELETE FROM users WHERE guild={row[0]}')
                conn.commit()

        time = 0
        while True:
            for guild in self.bot.guilds:
                for row in cursor.execute(f"SELECT id, timeOut FROM punishments where guild={guild.id}"):
                    unmute_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
                    c = unmute_time - datetime.today()
                    r = divmod(c.days * 86400 + c.seconds, 60)
                    if r[0] < 0 or r[1] < 0:
                        cursor.execute(f'DELETE FROM punishments WHERE id={row[0]} AND guild={guild.id} AND timeOut="{row[1]}"')
                        conn.commit()
                        member = guild.get_member(row[0])
                        role = utils.get(guild.roles, id=832078085540151357)
                        if role is not None:
                            await member.remove_roles(role)
                        print(f'[{datetime.today()}] {member.name} Un muted')

                for row in cursor.execute(f"SELECT id, type, sendTime, channelId FROM messages where guild={guild.id}"):
                    delete_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S.%f')
                    c = delete_time - datetime.today()
                    r = divmod(c.days * 86400 + c.seconds, 60)
                    if r[0] < 0 or r[1] < 0:
                        if row[1] == "top" or row[1] == "embedlist" or row[1] == "shop" or row[1] == "help":
                            cursor.execute(f'DELETE FROM messages WHERE id={row[0]} AND guild={guild.id}')
                            conn.commit()
                            try:
                                msg = await guild.get_channel(int(row[3])).fetch_message(int(row[0]))
                                await msg.delete()
                            finally:
                                pass

                if time >= 60:
                    time = 0
                    for row in cursor.execute(f"SELECT id, type FROM voice where guild={guild.id}"):
                        statType = row[1]
                        if statType == 'members' or statType == 'online' or statType == 'voice' or statType == 'bots':
                            id = row[0]
                            stat = await Utils.GetGuildStat(guild, statType)
                            channel = guild.get_channel(int(id))
                            await channel.edit(name=stat)

            await asyncio.sleep(1)
            time += 1

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        cursor.execute(f"SELECT guild FROM settings where guild={guild.id}")
        if cursor.fetchone() is None:
            await Utils.add_New_Guild(guild.id)
        else:
            pass

        for member in guild.members:
            cursor.execute(f"SELECT id FROM users where id={member.id} AND guild={guild.id}")
            if cursor.fetchone() is None:
                await Utils.add_New_User(member, guild.id)

            cursor.execute(f'UPDATE users SET enterTime=? where id=? AND guild=?',
                           (datetime.today(), member.id, guild.id))
            conn.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cursor.execute(f"SELECT id FROM users where id={member.id} AND guild={member.guild.id}")
        if cursor.fetchone() is None:
            await Utils.add_New_User(member, member.guild.id)  # Добавление новго участника в БД

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        cursor.execute(f"SELECT id FROM users where id={member.id} AND guild={member.guild.id}")
        if cursor.fetchone() is not None:
            cursor.execute(f'DELETE FROM users WHERE id={member.id} AND guild={member.guild.id}')
            conn.commit()  # Удаление участника с БД

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        # Создание приватного канала
        if member.voice is not None:
            cursor.execute(f"SELECT privateChannelId FROM settings where guild={member.guild.id}")
            channelID = cursor.fetchone()[0]
            privateChannel = member.guild.get_channel(int(channelID))
            if privateChannel is not None and member.voice.channel.id == channelID:
                category = privateChannel.category
                name = member.display_name
                name += "'s Channel"
                channel = await member.guild.create_voice_channel(name, category=category)

                cursor.execute(f'INSERT INTO voice VALUES ({member.guild.id}, {channel.id}, "private")')
                conn.commit()

                await channel.set_permissions(member, manage_channels=True)
                await member.move_to(channel)

        channels = [row[0] for row in cursor.execute(f"SELECT noXpChanels FROM settings where guild={member.guild.id}")]
        channelsArray = channels[0].split(" ")
        del channelsArray[-1]
        beforeChannelXpGet = True
        afterChannelXpGet = True

        # Проверка на No Xp канал
        for channelSearchID in channelsArray:
            if before.channel is not None and channelSearchID == before.channel.id:
                beforeChannelXpGet = False

            if after.channel is not None and channelSearchID == after.channel.id:
                afterChannelXpGet = False

        # Если с канала можно получить XP и произошли изменения
        if afterChannelXpGet and (before.self_mute != after.self_mute or before.self_deaf != after.self_deaf):
            membersMultiplayer = 0  # Количество активных участников

            for voiceMember in after.channel.members:
                # Если участник не бот, не в муте и включен звук
                if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf and \
                        voiceMember is not member:
                    membersMultiplayer += 1

            # Был ли активным до изменение
            if not before.self_mute and not before.self_deaf:
                membersMultiplayer += 1
                await Utils.member_voice_xp_add(member, membersMultiplayer)
            else:
                await Utils.member_voice_xp_add(member, 0)

            for voiceMember in after.channel.members:
                if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf and \
                        voiceMember is not member:
                    await Utils.member_voice_xp_add(voiceMember, membersMultiplayer)

        # Если канал был изменен
        if before.channel is not after.channel:
            if beforeChannelXpGet and before.channel is not None:
                membersMultiplayer = 0
                for voiceMember in before.channel.members:
                    # Если участник не бот, не в муте и включен звук
                    if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf:
                        membersMultiplayer += 1

                if not before.self_mute and not before.self_deaf:
                    membersMultiplayer += 1
                    await Utils.member_voice_xp_add(member, membersMultiplayer)
                else:
                    await Utils.member_voice_xp_add(member, 0)

                for voiceMember in before.channel.members:
                    if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf:
                        await Utils.member_voice_xp_add(voiceMember, membersMultiplayer)

            if afterChannelXpGet and after.channel is not None:
                membersMultiplayer = 0
                # Если участник не бот, не в муте и включен звук
                for voiceMember in after.channel.members:
                    # Если участник не бот, не в муте и включен звук
                    if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf and \
                            voiceMember is not member:
                        membersMultiplayer += 1

                for voiceMember in after.channel.members:
                    if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf and \
                            voiceMember is not member:
                        await Utils.member_voice_xp_add(voiceMember, membersMultiplayer)

        # Удаление приватного канала
        if before.channel is not None and len(before.channel.members) == 0:
            cursor.execute(f"SELECT type FROM voice where guild={member.guild.id} AND id={before.channel.id}")
            row = cursor.fetchone()
            if row is not None and row[0] == 'private':
                cursor.execute(f'DELETE FROM voice WHERE guild={member.guild.id} AND id={before.channel.id}')
                conn.commit()
                await before.channel.delete()

        elif before.channel is None:
            cursor.execute(f'UPDATE users SET enterTime=? where id=? AND guild=?',
                           (datetime.today(), member.id, member.guild.id))
            conn.commit()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        cursor.execute(f"SELECT privateChannelId FROM settings where guild={channel.guild.id}")
        channelID = int(cursor.fetchone()[0])
        if channelID == channel.id:
            cursor.execute(f'UPDATE settings SET privateChannelId=? where guild=?', (0, channel.guild.id))
            conn.commit()

        cursor.execute(f"SELECT id FROM voice where guild={channel.guild.id} AND id={channel.id}")
        row = cursor.fetchone()
        if row is not None:
            cursor.execute(f'DELETE FROM voice WHERE id={channel.id} AND guild={channel.guild.id}')

        conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            i = 0
            msg_founded = False
            while i < len(last_Messages):
                if last_Messages[i][0] == message.author.id:
                    if last_Messages[i][1] == message.content:
                        if last_Messages[i][2] > 2:
                            embed_obj = await EmbedCreate(color=Config.redCol,
                                                          author=f'{message.author.name} | Флудить не хорошо',
                                                          authorAvatar=message.author.avatar_url)
                            await message.channel.send(embed=embed_obj)
                            await message.delete()
                        else:
                            last_Messages[i][2] += 1

                    else:
                        last_Messages[i][1] = message.content
                        last_Messages[i][2] = 1

                    msg_founded = True
                    break

                i += 1

            if not msg_founded:
                last_Messages.append([message.author.id, message.content, 1])

            hasLink = False
            match = re.findall(r'https?://[\w.-]+/?[\w.-]*', message.content)
            availableLinks = ['https://cdn.discordapp.com/attachments', 'https://cdn.discordapp.com/avatars',
                              'https://media.discordapp.net/attachments',
                              'https://tenor.com/view', 'https://tenor.com/view', 'https://www.youtube.com/watch']
            for invite in await message.guild.invites():
                availableLinks.append(f'https://discord.gg/{invite.code}')

            for link in match:
                if link != '' and availableLinks.count(link) == 0:
                    hasLink = True
                    break

            if hasLink:
                embed_obj = await EmbedCreate(color=Config.redCol,
                                              author=f'{message.author.name} | Ккидать ссылки запрещено',
                                              authorAvatar=message.author.avatar_url)
                await message.channel.send(embed=embed_obj)
                await message.delete()

            else:
                cursor.execute(f"SELECT msgXpTime FROM users where id={message.author.id} AND guild={message.guild.id}")
                timeOut = datetime.strptime(cursor.fetchone()[0], '%Y-%m-%d %H:%M:%S.%f')
                c = timeOut - datetime.today()
                r = divmod(c.days * 86400 + c.seconds, 60)
                if r[0] < 0 or r[1] < 0:
                    cursor.execute(f'UPDATE users SET msgXpTime=? where id=? AND guild=?',
                                   (datetime.today() + timedelta(minutes=1), message.author.id, message.guild.id))
                    conn.commit()

                    cursor.execute(f"SELECT xpMultiplier FROM settings where guild={message.guild.id}")
                    multiplier = cursor.fetchone()

                    await Utils.xpadd(randint(15, 25) * multiplier[0], message.author)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.id in [int(y[0]) for y in cursor.execute(f"SELECT id FROM messages WHERE guild={message.guild.id}")]:
            cursor.execute(f'DELETE FROM messages WHERE id={message.id} AND guild={message.guild.id}')
            conn.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await Events.raw_reaction_changed(self, payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await Events.raw_reaction_changed(self, payload)

    async def raw_reaction_changed(self, payload):
        if payload.user_id != 701115392801767434:
            if payload.message_id in [int(y[0]) for y in
                                      cursor.execute(f"SELECT id FROM messages WHERE guild={payload.guild_id}")]:
                guild = None
                for g in self.bot.guilds:
                    if g.id == payload.guild_id:
                        guild = g
                        break

                msg = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
                cursor.execute(
                    f"SELECT type, userId FROM messages WHERE id={payload.message_id} AND guild={payload.guild_id}")
                row = cursor.fetchone()
                type = row[0]
                userId = row[1]

                if userId != payload.user_id:
                    return

                if payload.emoji.id == 831732305667948594:
                    cursor.execute(f'DELETE FROM messages WHERE id={msg.id} AND guild={payload.guild_id}')
                    conn.commit()
                    await msg.delete()
                elif type == 'top':
                    words = msg.embeds[0].author.name.split(' ')
                    newPage = int(words[1])

                    print(payload.emoji.id)
                    if payload.emoji.id == 831761280607977493:  # left
                        newPage -= 1
                    elif payload.emoji.id == 831761280594608138:  # right
                        newPage += 1

                    embed_obj = msg.embeds[0]
                    if msg.embeds[0].title == "**:trophy: Рейтинг по :gem:**":
                        embed_obj = await Utils.topget(newPage, "money", guild)
                    elif msg.embeds[0].title == "**:trophy: Рейтинг по голосовой активности**":
                        embed_obj = await Utils.topget(newPage, "voice", guild)
                    elif msg.embeds[0].title == "**:trophy: Рейтинг по уровню**":
                        embed_obj = await Utils.topget(newPage, "level", guild)

                    embed_obj.title = msg.embeds[0].title
                    embed_obj.color = Config.embedCol
                    embed_obj.set_footer(
                        text=f'{Utils.RequestedText(self.bot.get_user(payload.user_id))}')
                    await msg.edit(embed=embed_obj)

                elif type == 'embedlist':
                    words = msg.embeds[0].author.name.split(' ')
                    newPage = int(words[1])

                    if payload.emoji.id == 831761280607977493:  # left
                        newPage -= 1
                    elif payload.emoji.id == 831761280594608138:  # right
                        newPage += 1

                    embed_obj = await Utils.pembed_list_get(newPage, payload.guild_id)
                    embed_obj.set_footer(text=Utils.RequestedText(self.bot.get_user(payload.user_id)))

                    await msg.edit(embed=embed_obj)

                elif type == 'shop':
                    words = msg.embeds[0].author.name.split(' ')
                    newPage = int(words[1])

                    if payload.emoji.id == 831761280607977493:  # left
                        newPage -= 1
                    elif payload.emoji.id == 831761280594608138:  # right
                        newPage += 1

                    embed_obj = await Utils.shop_get(newPage, payload.guild_id)
                    embed_obj.set_footer(
                        text=f'!buy <номер> ・ {Utils.RequestedText(self.bot.get_user(payload.user_id))}')

                    await msg.edit(embed=embed_obj)

                elif type == 'warns':
                    words = msg.embeds[0].author.name.split(' ')
                    newPage = int(words[1])
                    userId = re.findall(r'\d+', msg.embeds[0].description)[0]

                    if payload.emoji.id == 831761280607977493:  # left
                        newPage -= 1
                    elif payload.emoji.id == 831761280594608138:  # right
                        newPage += 1

                    embed_obj = await Utils.WarnsListGet(newPage, self.bot.get_user(int(userId)), payload.guild_id)
                    embed_obj.set_footer(
                        text=f'{Utils.RequestedText(self.bot.get_user(payload.user_id))}')

                    await msg.edit(embed=embed_obj)


def setup(bot):
    bot.add_cog(Events(bot))
