import discord
import asyncio
from discord.ext import commands
from discord import utils
import traceback
import sqlite3
import validators
from discord_slash import ComponentContext

import Utils
import Config
import UserCommands
from datetime import datetime, timedelta
import os
import re
from random import randint

from ModerCommands import ModerCommands
import DataBase
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate

last_Messages = []


async def updateUsersData(guild: discord.Guild):
    for member in guild.members:
        row = DataBase.getDataFromDB('users', 'id', f'id={member.id} AND guild={guild.id}')
        if row is None:
            await Utils.add_New_User(member, guild.id)
        DataBase.updateDataInDB('users', f'enterTime="{datetime.today()}", msgXpTime="{datetime.today()}"', f'id={member.id} AND guild={guild.id}')



async def deleteExtraUsersFromBD(guild: discord.Guild):
    users = DataBase.getDataFromDB('users', 'id', f'guild={guild.id}', 'all')
    for row in users:
        if not row[0] in [y.id for y in guild.members]:
            DataBase.deleteDataFromDB('users', f'id={row[0]} AND guild={guild.id}')


async def checkAndDeleteExtraPrivateChannelFromBD(guild: discord.Guild):
    data = DataBase.getDataFromDB('settings', 'privateChannelId', f'guild={guild.id}')
    if data is not None:
        channelID = data[0]
        privateChannel = guild.get_channel(int(channelID))
        if privateChannel is None:
            DataBase.updateDataInDB('settings', f'privateChannelId=0', f'guild={guild.id}')


async def deleteExtraVoiceChannelsFromBD(guild: discord.Guild):
    row = DataBase.getDataFromDB('voice', 'id', f'guild={guild.id}', 'all')
    for id in row:
        channel = guild.get_channel(int(id[0]))
        if channel is None:
            DataBase.deleteDataFromDB('voice', f'id={id[0]} AND guild={guild.id}')


async def deleteExtraMessagesFromBD(guild: discord.Guild):
    row = DataBase.getDataFromDB('customMessages', 'messageId, channelId', f'guild={guild.id}', 'all')
    for id in row:
        try:
            channel = guild.get_channel(int(id[1]))
            if channel is None:
                DataBase.deleteDataFromDB('customMessages', f'messageId={id[0]} AND guild={guild.id}')
            else:
                message = await channel.fetch_message(int(id[0]))
                if message is None:
                    DataBase.deleteDataFromDB('customMessages', f'messageId={id[0]} AND guild={guild.id}')
        except Exception:
            DataBase.deleteDataFromDB('customMessages', f'messageId={id[0]} AND guild={guild.id}')


async def dataUpdaterCycle(bot):
    stage = 0
    while True:
        for guild in bot.guilds:
            await checkAndDeletePunishments(guild)
            await checkAndDeleteOutOfTimeMessages(guild)
            if stage >= 60:
                await updateStatChannelsName(guild)

        await asyncio.sleep(1)
        stage += 1
        if stage > 60:
            stage = 0


async def checkAndDeletePunishments(guild: discord.Guild):
    for row in DataBase.getDataFromDB('punishments', 'id, timeOut', f'guild={guild.id}', 'all'):
        unmute_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
        c = unmute_time - datetime.today()
        r = divmod(c.days * 86400 + c.seconds, 60)
        if r[0] < 0 or r[1] < 0:
            DataBase.deleteDataFromDB('punishments', f'id={row[0]} AND guild={guild.id} AND timeOut="{row[1]}"')
            member = guild.get_member(row[0])

            row = DataBase.getDataFromDB('settings', 'muteRole', f'guild={guild.id}')
            role = utils.get(guild.roles, id=int(row[0]))
            if role is not None and member is not None:
                await member.remove_roles(role)


async def checkAndDeleteOutOfTimeMessages(guild: discord.Guild):
    for row in DataBase.getDataFromDB('messages', 'id, type, sendTime, channelId', f'guild={guild.id}', 'all'):
        delete_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S.%f')
        c = delete_time - datetime.today()
        r = divmod(c.days * 86400 + c.seconds, 60)
        if r[0] < 0 or r[1] < 0:
            if row[1] == "top" or row[1] == "embedlist" or row[1] == "shop" or row[1] == "help":
                DataBase.deleteDataFromDB('messages', f'id={row[0]} AND guild={guild.id}')
                try:
                    msg = await guild.get_channel(int(row[3])).fetch_message(int(row[0]))
                    if msg is not None:
                        await msg.delete()
                except Exception:
                    pass

async def updateStatChannelsName(guild: discord.Guild):
    for row in DataBase.getDataFromDB('voice', 'id, type', f'guild={guild.id}', 'all'):
        statType = row[1]
        id = row[0]
        stat = await Utils.GetGuildStat(guild, statType)
        if stat != 'private':
            channel = guild.get_channel(int(id))
            await channel.edit(name=stat)


async def checkAndCreatePrivateChannel(member: discord.Member):
    if member.voice is not None:
        channelID = DataBase.getDataFromDB('settings', 'privateChannelId', f'guild={member.guild.id}')[0]
        privateChannel = member.guild.get_channel(int(channelID))
        if privateChannel is not None and member.voice.channel.id == channelID:
            row = DataBase.getDataFromDB('voice', 'id', f'guild={member.guild.id} AND user={member.id}')
            channel = None
            if row is not None and row[0] is not None:
                channel = member.guild.get_channel(row[0])
            if channel is not None:
                await member.move_to(channel)
            else:
                category = privateChannel.category
                name = member.display_name
                name += "'s Channel"
                channel = await member.guild.create_voice_channel(name, category=category)

                DataBase.insertDataInDB('voice', f'{member.guild.id}, {channel.id}, "private", {member.id}')

                await member.move_to(channel)


async def checkAndApplyVoiceStateUpdate(member: discord.Member, before, after, afterChannelXpGet):
    if afterChannelXpGet and (before.self_mute != after.self_mute or before.self_deaf != after.self_deaf):
        membersMultiplayer = 0  # Количество активных участников

        for voiceMember in after.channel.members:
            # Если участник не бот, не в муте и включен звук
            if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf and \
                    voiceMember is not member:
                membersMultiplayer += 1

        # Был ли активным до изменения
        if not before.self_mute and not before.self_deaf:
            membersMultiplayer += 1
            await Utils.member_voice_xp_add(member, membersMultiplayer)
        else:
            await Utils.member_voice_xp_add(member, 0)

        for voiceMember in after.channel.members:
            if not voiceMember.bot and not voiceMember.voice.self_mute and not voiceMember.voice.self_deaf and \
                    voiceMember is not member:
                await Utils.member_voice_xp_add(voiceMember, membersMultiplayer)


async def checkAndApplyIfChannelChanged(member: discord.Member, before, after, afterChannelXpGet, beforeChannelXpGet):
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

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyUnreachableCode
    @commands.Cog.listener()
    async def on_ready(self):
        print(' ')
        # await Utils.out_white('------')
        # await Utils.out_green(f'Logged in as: {self.bot.user.name} id: {self.bot.user.id}')
        # await Utils.out_yellow(f'Start up time: {datetime.today()}')
        # await Utils.out_white('------')
        print('------')
        print(f'Logged in as: {self.bot.user.name} id: {self.bot.user.id}')
        print(f'Start up time: {datetime.today()}')
        print('------')
        game = discord.Activity(name='Кофейку?')
        game.type = discord.ActivityType.playing
        await self.bot.change_presence(activity=game)
        await Events.updateAndDeleteExtraDataFromBD(self)
        await Events.deleteExtraGuildsFromBD(self)
        print('------')
        print(' ')
        await dataUpdaterCycle(self.bot)

    async def updateAndDeleteExtraDataFromBD(self):
        for guild in self.bot.guilds:
            print(f'Guild: {guild.name}')
            await updateUsersData(guild)
            await checkAndDeleteExtraPrivateChannelFromBD(guild)
            await deleteExtraUsersFromBD(guild)
            await deleteExtraVoiceChannelsFromBD(guild)
            await deleteExtraMessagesFromBD(guild)

    async def deleteExtraGuildsFromBD(self):
        guilds = DataBase.getDataFromDB('settings', 'guild', '', 'all')
        sheets = DataBase.getTablesListFromDB()
        for row in guilds:
            for tables in sheets:
                if not int(row[0]) in [g.id for g in self.bot.guilds]:
                    DataBase.deleteDataFromDB(f'{tables[0]}' f'guild={row[0]}')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        row = DataBase.getDataFromDB('settings', 'guild', f'guild={guild.id}')
        if row is None:
            await Utils.add_New_Guild(guild.id)
        else:
            pass

        for member in guild.members:
            row = DataBase.getDataFromDB('users', 'id', f'id={member.id} AND guild={guild.id}')
            if row is None:
                await Utils.add_New_User(member, guild.id)

            DataBase.updateDataInDB('users', f'enterTime="{datetime.today()}"', f'id={member.id} AND guild={guild.id}')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        row = DataBase.getDataFromDB('users', 'id', f'id={member.id} AND guild={member.guild.id}')
        if row is None:
            await Utils.add_New_User(member, member.guild.id)  # Добавление новго участника в БД

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        row = DataBase.getDataFromDB('users', 'id', f'id={member.id} AND guild={member.guild.id}')
        if row is not None:
            DataBase.deleteDataFromDB('users', f'id={member.id} AND guild={member.guild.id}')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        await checkAndCreatePrivateChannel(member)

        channels = [row[0] for row in DataBase.getDataFromDB('settings', 'noXpChanels', f'guild={member.guild.id}', 'all')]
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

        await checkAndApplyVoiceStateUpdate(member, before, after, afterChannelXpGet)
        await checkAndApplyIfChannelChanged(member, before, after, afterChannelXpGet, beforeChannelXpGet)

        # Удаление приватного канала
        if before.channel is not None and len(before.channel.members) == 0:
            row = DataBase.getDataFromDB('voice', 'type', f'guild={member.guild.id} AND id={before.channel.id}')
            if row is not None and row[0] == 'private':
                DataBase.deleteDataFromDB('voice', f'guild={member.guild.id} AND id={before.channel.id}')
                await before.channel.delete()

        elif before.channel is None:
            DataBase.updateDataInDB('users', f'enterTime="{datetime.today()}"', f'guild={member.guild.id} AND id={member.id}')

        if before.channel is not after.channel:
            if before.channel is not None and after.channel is not None:
                await Utils.send_audit('voice_change', member.guild, member, before.channel, after.channel)
            elif before.channel is not None:
                await Utils.send_audit('voice_leave', member.guild, member, before.channel)
            elif after.channel is not None:
                await Utils.send_audit('voice_join', member.guild, member, after.channel)

        if before.mute is False and after.mute is True:
            await Utils.send_audit('voice_muted', member.guild, member)
        elif before.mute is True and after.mute is False:
            await Utils.send_audit('voice_unmuted', member.guild, member)

        if before.deaf is False and after.deaf is True:
            await Utils.send_audit('voice_deaf', member.guild, member)
        elif before.deaf is True and after.deaf is False:
            await Utils.send_audit('voice_undeaf', member.guild, member)


    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        channelID = DataBase.getDataFromDB('settings', 'privateChannelId', f'guild={channel.guild.id}')[0]
        if channelID == channel.id:
            DataBase.updateDataInDB('settings', 'privateChannelId=0', f'guild={channel.guild.id}')

        row = DataBase.getDataFromDB('voice', 'id', f'guild={channel.guild.id} AND id={channel.id}')
        if row is not None:
            DataBase.deleteDataFromDB('voice', f'id={channel.id} AND guild={channel.guild.id}')

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.id in [int(y[0]) for y in DataBase.getDataFromDB('messages', 'id', f'guild={message.guild.id}', 'all')]:
            DataBase.deleteDataFromDB('messages', f'id={message.id} AND guild={message.guild.id}')
        if message.id in [int(y[0]) for y in DataBase.getDataFromDB('customMessages', 'messageId', f'guild={message.guild.id}', 'all')]:
            DataBase.deleteDataFromDB('customMessages', f'messageId={message.id} AND guild={message.guild.id}')
        await Utils.send_audit('message_delete', message.guild, message.author, message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.author.bot:
            await Utils.send_audit('message_edit', after.guild, after.author, before, after)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        for role in before.roles:
            try:
                after.roles.index(role)
            except Exception:
                await Utils.send_audit('role_remove', after.guild, after, role)

        for role in after.roles:
            try:
                before.roles.index(role)
            except Exception:
                await Utils.send_audit('role_add', after.guild, after, role)
                try:
                    if role.is_premium_subscriber():
                        await Utils.sendGuildBoostedMessage(after, after.guild, role)
                        await Utils.addMoneyToUser(after, after.guild.id, 50000)
                except AttributeError:
                    pass

        if before.display_name != after.display_name:
            await Utils.send_audit('name_changed', after.guild, after, before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await Utils.send_audit('user_ban', guild, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await Utils.send_audit('user_unban', guild, user)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await Utils.send_audit('member_join', member.guild, member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await Utils.send_audit('member_leave', member.guild, member)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "⭐":
            await Events.reaction_add_reputation(self, payload)
        await Events.raw_reaction_changed(self, payload)

    @commands.Cog.listener()
    async def reaction_add_reputation(self, payload):
        message = await payload.member.guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
        access_pr = False
        if payload.user_id == message.author.id or payload.member.bot :
            return
        else:
            row = DataBase.getDataFromDB('reputation', 'previous', f'id={payload.user_id} AND guild={payload.guild_id}')
            if row == None:
                row = DataBase.getDataFromDB('reputation', 'last', f'id={payload.user_id} AND guild={payload.guild_id}')
                if row == None:
                    DataBase.insertDataInDB('reputation', f'{payload.user_id}, {payload.guild_id}, "{datetime.today()}", "{datetime.today()}"')
                DataBase.updateDataInDB('reputation', f'last="{datetime.today() + timedelta(days=1)}"', f'id={payload.user_id} AND guild={payload.guild_id}')
                access_pr = True
            else:
                row = DataBase.getDataFromDB('reputation', 'previous', f'id={payload.user_id} AND guild={payload.guild_id}')
                previous_reputation = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                c = previous_reputation - datetime.today()
                r = divmod(c.days * 86400 + c.seconds, 60)
                if r[0] < 0 or r[1] < 0:
                    row = DataBase.getDataFromDB('reputation', 'last', f'id={payload.user_id} AND guild={payload.guild_id}')
                    DataBase.updateDataInDB('reputation', f'previous="{row[0]}", last="{datetime.today() + timedelta(days=1)}"', f'id={payload.user_id} AND guild={payload.guild_id}')
                    access_pr = True
            if access_pr:
                reputation = Config.reputationPr + DataBase.getDataFromDB('users', 'reputation', f'id={message.author.id} AND guild={payload.guild_id}')[0]
                DataBase.updateDataInDB('users', f'reputation={reputation}', f'id={message.author.id} AND guild={payload.guild_id}')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await Events.raw_reaction_changed(self, payload)

    @commands.Cog.listener()
    async def raw_reaction_changed(self, payload):
        if payload.user_id != 701115392801767434:
            if payload.message_id in [int(y[0]) for y in DataBase.getDataFromDB('customMessages', 'messageId', f'guild={payload.guild_id}', 'all')]:
                row = DataBase.getDataFromDB('customMessages', 'reactions, roles', f'messageId={payload.message_id} AND guild={payload.guild_id}')
                reactions = row[0].split(' ')
                roles = row[1].split(' ')

                guild = None
                for g in self.bot.guilds:
                    if g.id == payload.guild_id:
                        guild = g
                        break

                member = guild.get_member(payload.user_id)
                i = 0
                while i < len(reactions):
                    if f'{reactions[i]}' == f'{payload.emoji}':
                        role = utils.get(guild.roles, id=int(roles[i]))
                        if payload.event_type == 'REACTION_ADD':
                            await member.add_roles(role)
                        else:
                            await member.remove_roles(role)
                        break
                    i += 1

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        if ctx.custom_id == '1000':
            userId = DataBase.getDataFromDB('messages', 'userId', f'id={ctx.origin_message_id} AND guild={ctx.guild_id}')[0]
            if userId != ctx.author_id:
                await ctx.send(
                    content=f"**<@{ctx.author_id}>, вы не можете управлять этим сообщением, т.к. не вы его запросили!**",
                    hidden=True)
                return
            else:
                await ctx.origin_message.delete()
        else:
            msg = await ctx.guild.get_channel(ctx.channel_id).fetch_message(ctx.origin_message_id)
            row = DataBase.getDataFromDB('messages', 'type, userId', f'id={ctx.origin_message_id} AND guild={ctx.guild_id}')
            type = row[0]
            userId = row[1]

            if userId != ctx.author_id:
                await ctx.send(
                    content=f"**<@{ctx.author_id}>, вы не можете управлять этим сообщением, т.к. не вы его запросили!**",
                    hidden=True)
                return

            if type == 'shop':
                words = msg.embeds[0].author.name.split(' ')
                newPage = int(words[1])

                if ctx.custom_id == '1001':  # left
                    newPage -= 1
                elif ctx.custom_id == '1002':  # right
                    newPage += 1

                embed_obj = await Utils.shop_get(newPage, ctx.guild_id)
                embed_obj.set_footer(
                    text=f'!buy <номер> ・ {Utils.RequestedTextCustom(self.bot.get_user(ctx.author_id), "shop", self.bot)}')

                await msg.edit(embed=embed_obj)
                await ctx.edit_origin()
            elif type == 'top':
                words = msg.embeds[0].author.name.split(' ')
                newPage = int(words[1])

                if ctx.custom_id == '1001':  # left
                    newPage -= 1
                elif ctx.custom_id == '1002':  # right
                    newPage += 1

                embed_obj = msg.embeds[0]
                if msg.embeds[0].title == f"**:trophy: Рейтинг по балансу {Config.money_reaction}**":
                    embed_obj = await Utils.topget(newPage, "money", ctx.guild)
                elif msg.embeds[0].title == "**:trophy: Рейтинг по голосовой активности**":
                    embed_obj = await Utils.topget(newPage, "voice", ctx.guild)
                elif msg.embeds[0].title == "**:trophy: Рейтинг по уровню**":
                    embed_obj = await Utils.topget(newPage, "level", ctx.guild)
                elif msg.embeds[0].title == f"**:trophy: Рейтинг по репутации {Config.reputation_reaction}**":
                    embed_obj = await Utils.topget(newPage, "rep", ctx.guild)

                embed_obj.title = msg.embeds[0].title
                embed_obj.color = Config.embedCol
                embed_obj.set_footer(
                    text=f'{Utils.RequestedTextCustom(self.bot.get_user(ctx.author_id), "top", self.bot)}')
                await msg.edit(embed=embed_obj)
                await ctx.edit_origin()
            elif type == 'warns':
                words = msg.embeds[0].author.name.split(' ')
                newPage = int(words[1])
                userId = re.findall(r'\d+', msg.embeds[0].description)[0]

                if ctx.custom_id == '1001':  # left
                    newPage -= 1
                elif ctx.custom_id == '1002':  # right
                    newPage += 1

                embed_obj = await Utils.WarnsListGet(newPage, self.bot.get_user(int(userId)), ctx.guild_id)
                embed_obj.set_footer(
                    text=f'{Utils.RequestedTextCustom(self.bot.get_user(ctx.author_id), "warns", self.bot)}')

                await msg.edit(embed=embed_obj)
                await ctx.edit_origin()
            elif type == 'embedlist':
                words = msg.embeds[0].author.name.split(' ')
                newPage = int(words[1])

                if ctx.custom_id == '1001':  # left
                    newPage -= 1
                elif ctx.custom_id == '1002':  # right
                    newPage += 1

                embed_obj = await Utils.pembed_list_get(newPage, ctx.guild_id)
                embed_obj.set_footer(
                    text=Utils.RequestedTextCustom(self.bot.get_user(ctx.author_id), "embed", self.bot))

                await msg.edit(embed=embed_obj)
                await ctx.edit_origin()


def setup(bot):
    bot.add_cog(Events(bot))
