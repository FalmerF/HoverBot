import discord
import asyncio
from discord.ext import commands
from discord import utils
import traceback
import sqlite3
import validators
from discord_slash import ButtonStyle
from discord_slash.utils import manage_components

import Utils
import Config
from datetime import datetime, timedelta
import os

import DataBase
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate, check_moder_roles


last_Messages = []


class ModerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_warn(self, bot, moder: discord.member, channel: discord.TextChannel, user: discord.member, reason: str, *time: str):
        if Utils.check_moder_roles_from_user(user):
            if not Utils.check_admin_roles_from_user(moder) or Utils.check_admin_roles_from_user(user):
                embed_obj = await EmbedCreate(
                    description=f'<@{user.id}> имеет иммунитет к предупреждениям.', color=Config.blueCol,
                    footerText=Utils.RequestedTextCustom(moder, 'warn', bot))
                await channel.send(embed=embed_obj)
                return

        timeOut = await Utils.ParseStringToTime(*time)
        if timeOut.total_seconds() == 0:
            timeOut = timedelta(days=1)
        timeOut2 = datetime.today() + timeOut

        DataBase.insertDataInDB('punishments', f'{user.id}, "warn", "{timeOut2}", {channel.guild.id}, "{reason}", {moder.id}, "{datetime.today()}"')

        row = DataBase.getDataFromDB('users', 'reputation', f'guild={channel.guild.id} AND id={user.id}')
        reputationCount = 100
        if row is not None:
            reputationCount = int(row[0]) + Config.reputationWarn
        DataBase.updateDataInDB('users', f'reputation={reputationCount}', f'guild={channel.guild.id} AND id={user.id}')

        embed_obj = await EmbedCreate(
            description=f'''Пользователь <@{user.id}> получил предупреждение от модератора <@{moder.id}>
                    ・Время: **{await Utils.ParseTimeToString(timeOut, True)}**
                    ・Причина: **{reason}**''', color=Config.yellowCol)
        await channel.send(embed=embed_obj)

        row = DataBase.getDataFromDB('punishments', 'moder', f'guild={channel.guild.id} AND id={user.id} AND type="warn"', 'all')
        warnsCount = len(row)
        if warnsCount >= 10:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '10 предупреждений', '24h')
        elif warnsCount >= 9:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '9 предупреждений', '16h')
        elif warnsCount >= 8:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '8 предупреждений', '12h')
        elif warnsCount >= 7:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '7 предупреждений', '8h')
        elif warnsCount >= 6:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '6 предупреждений', '6h')
        elif warnsCount >= 5:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '5 предупреждений', '4h')
        elif warnsCount >= 4:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '4 предупреждения', '2h')
        elif warnsCount >= 3:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '3 предупреждения', '30m')
        elif warnsCount >= 2:
            await ModerCommands.send_mute(self, bot, channel.guild.get_member(bot.user.id), channel, user, '2 предупреждения', '1m')

    async def send_mute(self, bot, moder: discord.member, channel: discord.TextChannel, user: discord.member, reason: str, *time: str):
        row = DataBase.getDataFromDB('settings', 'muteRole', f'guild={channel.guild.id}')

        role = utils.get(channel.guild.roles, id=int(row[0]))
        if role is None:
            embed_obj = await EmbedCreate(
                description=f'Роль мьюта отсутствует.', color=Config.blueCol,
                footerText=Utils.RequestedTextCustom(moder, 'mute', bot))
            await channel.send(embed=embed_obj)
            return

        member = channel.guild.get_member(user.id)
        if Utils.check_moder_roles_from_user(member):
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> имеет иммунитет к мьюту.', color=Config.blueCol,
                footerText=Utils.RequestedTextCustom(moder, 'mute', bot))
            await channel.send(embed=embed_obj)
            return

        timeOut = await Utils.ParseStringToTime(*time)
        timeOut2 = datetime.today() + timeOut

        row = DataBase.getDataFromDB('punishments', 'timeOut', f'id={user.id} AND guild={channel.guild.id} AND type="mute"')
        if row:
            DataBase.updateDataInDB('punishments', f'timeOut={timeOut2}, reason={reason}, moder={moder.id}, date={datetime.today()}', f'id={user.id} AND guild={channel.guild.id}')
        else:
            DataBase.insertDataInDB('punishments', f'{user.id}, "mute", "{timeOut2}", {channel.guild.id}, "{reason}", {moder.id}, "{datetime.today()}"')

        await member.add_roles(role)
        embed_obj = await EmbedCreate(
            description=f'''Пользователь <@{user.id}> был замьючен модератором <@{moder.id}>
            ・Время: **{await Utils.ParseTimeToString(timeOut, True)}**
            ・Причина: **{reason}**''', color=Config.redCol)
        await channel.send(embed=embed_obj)

    @commands.command()
    @commands.check(check_moder_roles)
    async def helpmoder(self, ctx, *args):
        embed_obj = discord.Embed(title="**Команды для Модераторов**", color=Config.embedCol)
        embed_obj.add_field(name="`!mute`", value=f"Замьютить участника.")
        embed_obj.add_field(name="`!unmute`", value=f"Размьютить участника.")
        embed_obj.add_field(name="`!warn`", value=f"Выдать предупреждение участнику.")
        embed_obj.add_field(name="`!warnclear`", value=f"Снять предупреждение участника.")
        embed_obj.set_footer(text=Utils.RequestedText(ctx))

        buttons = [
            manage_components.create_button(
                style=ButtonStyle.red,
                emoji=self.bot.get_emoji(id=Config.cancel_emoji),
                custom_id='1000'
            ),
        ]
        action_row = manage_components.create_actionrow(*buttons)
        message = await ctx.send(embed=embed_obj, components=[action_row])
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

    @helpmoder.error
    async def helpmoder_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_moder_roles)
    async def mute(self, ctx, user: discord.User, reason, *time: str):
        member = ctx.guild.get_member(user.id)
        await self.send_mute(self.bot, ctx.author, ctx.channel, member, reason, *time)
        await ctx.message.delete()

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!mute @user <причина> <время>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_moder_roles)
    async def unmute(self, ctx, user: discord.User, *args):
        row = DataBase.getDataFromDB('punishments', 'timeOut', f'id={user.id} AND guild={ctx.guild.id}')
        if row:
            DataBase.deleteDataFromDB('punishments', f'id={user.id} AND guild={ctx.guild.id}')
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> был размьючен.',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx))
            member = ctx.guild.get_member(user.id)
            row = DataBase.getDataFromDB('settings', 'muteRole', f'guild={ctx.guild.id}')
            role = utils.get(ctx.guild.roles, id=int(row[0]))

            await member.remove_roles(role)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> не имеет мьют.',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!unmute @user`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_moder_roles)
    async def warn(self, ctx, user: discord.User, reason, *time: str):
        member = ctx.guild.get_member(user.id)
        await self.send_warn(self.bot, ctx.author, ctx.channel, member, reason, *time)
        await ctx.message.delete()

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!warn @user <причина> [время]`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_moder_roles)
    async def warnclear(self, ctx, user: discord.User, num: str, *args):
        row = DataBase.getDataFromDB('punishments', '*', f'id={user.id} AND guild={ctx.guild.id} AND type="warn"', 'all')
        if len(row) == 0 and num != 'all':
            embed_obj = await EmbedCreate(color=Config.blueCol,
                                          description=f'''Предупреждение под номером `{num}` у пользователя <@{user.id}> не найдено!''')
            embed_obj.set_footer(text=f'{Utils.RequestedText(ctx)}')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        if num == 'all':
            DataBase.deleteDataFromDB('punishments', f'id={user.id} AND guild={ctx.guild.id} AND type="warn"')

            embed_obj = await EmbedCreate(color=Config.blueCol,
                                          description=f'''Все предупреждения пользователя <@{user.id}> очищены.''')
            embed_obj.set_footer(text=f'{Utils.RequestedText(ctx)}')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        warnNum = int(num)
        row = DataBase.getDataFromDB('punishments', 'date', f'guild={ctx.guild.id} AND id={user.id} AND type="warn"', 'all')
        DataBase.deleteDataFromDB('punishments', f'id={user.id} AND guild={ctx.guild.id} AND type="warn" AND date="{row[warnNum - 1][0]}"')

        embed_obj = await EmbedCreate(color=Config.blueCol,
                                      description=f'''Предупреждение пользователя <@{user.id}> `#{warnNum}` очищено.''')
        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx)}')
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @warnclear.error
    async def warnclear_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            print(error)
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!warnclear @user <номер/all>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(ModerCommands(bot))
