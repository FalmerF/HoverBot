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
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate, check_moder_roles

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

last_Messages = []


class ModerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(check_moder_roles)
    async def helpmoder(self, ctx, *args):
        embed_obj = discord.Embed(title="**Команды для Модераторов**", color=Config.embedCol)
        embed_obj.add_field(name="`!mute`", value=f"Замьютить участника.")
        embed_obj.add_field(name="`!unmute`", value=f"Размьютить участника.")
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))

        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

        await message.add_reaction(Config.cancel_reaction)

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
        if Utils.check_moder_roles_from_user(member):
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> имеет иммунитет к мьюту.', color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        timeOut = await Utils.ParseStringToTime(*time)
        timeOut2 = datetime.today() + timeOut

        cursor.execute(f'SELECT timeOut FROM punishments where id={user.id} AND guild={ctx.guild.id} AND type="mute"')
        row = cursor.fetchone()
        if row:
            cursor.execute(f'UPDATE punishments SET timeOut=?, reason=?, moder=?, date=? where id=? AND guild=?',
                           (timeOut2, reason, ctx.author.id, datetime.today(), user.id, ctx.guild.id))
        else:
            cursor.execute(
                f'INSERT INTO punishments VALUES ({user.id}, "mute", "{timeOut2}", {ctx.guild.id}, "{reason}", {ctx.author.id}, "{datetime.today()}")')

        conn.commit()
        role = utils.get(ctx.guild.roles, id=832078085540151357)
        if role is None:
            embed_obj = await EmbedCreate(
                description=f'Роль мьюта отсутствует', color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        await member.add_roles(role)
        embed_obj = await EmbedCreate(
            description=f'''Пользователь <@{user.id}> был замьючен модератором <@{ctx.author.id}>
            ・Время: **{await Utils.ParseTimeToString(timeOut, True)}**
            ・Причина: **{reason}**''', color=Config.redCol)
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            print(error)
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!mute @user <причина> <время>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_moder_roles)
    async def unmute(self, ctx, user: discord.User, *args):
        cursor.execute(f"SELECT timeOut FROM punishments where id={user.id} AND guild={ctx.guild.id}")
        row = cursor.fetchone()
        if row:
            cursor.execute(f'DELETE FROM punishments WHERE id={user.id} AND guild={ctx.guild.id}')
            conn.commit()
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> был размьючен.',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
            member = ctx.guild.get_member(user.id)
            role = utils.get(ctx.guild.roles, id=832078085540151357)
            await member.remove_roles(role)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> не имеет мьют.',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
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
        if Utils.check_moder_roles_from_user(member):
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> имеет иммунитет к предупреждениям.', color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        timeOut = await Utils.ParseStringToTime(*time)
        if timeOut.total_seconds() == 0:
            timeOut = timedelta(days=1)
        timeOut2 = datetime.today() + timeOut

        cursor.execute(
            f'INSERT INTO punishments VALUES ({user.id}, "warn", "{timeOut2}", {ctx.guild.id}, "{reason}", {ctx.author.id}, "{datetime.today()}")')
        conn.commit()

        embed_obj = await EmbedCreate(
            description=f'''Пользователь <@{user.id}> получил предупреждение от модератора <@{ctx.author.id}>
            ・Время: **{await Utils.ParseTimeToString(timeOut, True)}**
            ・Причина: **{reason}**''', color=Config.yellowCol)
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            print(error)
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!warn @user <причина> [время]`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_moder_roles)
    async def warnclear(self, ctx, user: discord.User, num: str, *args):
        if num == 'all':
            cursor.execute(f'DELETE FROM punishments WHERE id={user.id} AND guild={ctx.guild.id} AND type="warn"')
            conn.commit()

            embed_obj = await EmbedCreate(color=Config.blueCol,
                                          description=f'''Все предупреждения пользователя <@{user.id}> очищены.''')
            embed_obj.set_footer(text=f'{Utils.RequestedText(ctx.author)}')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        warnNum = int(num)
        cursor.execute(f'SELECT date FROM punishments where guild={ctx.guild.id} AND id={user.id} AND type="warn"')
        row = cursor.fetchall()
        cursor.execute(
            f'DELETE FROM punishments WHERE id={user.id} AND guild={ctx.guild.id} AND type="warn" AND date="{row[warnNum - 1][0]}"')
        conn.commit()

        embed_obj = await EmbedCreate(color=Config.blueCol,
                                      description=f'''Предупреждение пользователя <@{user.id}> `#{warnNum}` очищено.''')
        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx.author)}')
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
