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
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

last_Messages = []


class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *args):
        embed_obj = discord.Embed(title="**Общие команды**", color=Config.embedCol)
        embed_obj.add_field(name="`!rank`", value=f"Показывает информацию о ранге участника.")
        embed_obj.add_field(name="`!balance` | `!b`", value=f"Показывает информацию о балансе.")
        embed_obj.add_field(name="`!shop`", value=f"Магазин в котором можно купить роли.")
        embed_obj.add_field(name="`!top [voice, money]`", value=f"Показывает топ участников.")
        embed_obj.add_field(name="`!transfer` | `!t`", value=f"Передать :gem: другому участнику.")
        embed_obj.add_field(name="`!minfo`", value=f"Информация о мьюте участника.")
        embed_obj.add_field(name="`!profile`", value=f"Посмотреть профиль участника.")
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

        await message.add_reaction(Config.cancel_reaction)

    @commands.command()
    async def rank(self, ctx, user: discord.Member, *args):
        await Utils.rankMet(ctx, user)

    @rank.error
    async def rank_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await Utils.rankMet(ctx, ctx.author)

    @commands.command()
    async def profile(self, ctx, user: discord.Member, *args):
        embed_obj = await Utils.ProfileCreate(ctx, user)
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @profile.error
    async def profile_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.profile(self, ctx, ctx.author)

    @commands.command()
    async def p(self, ctx, user: discord.Member, *args):
        await UserCommands.profile(self, ctx, user, *args)

    @p.error
    async def p_error(self, ctx, error):
        await UserCommands.profile_error(self, ctx, error)

    @commands.command()
    async def balance(self, ctx, user: discord.User, *args):
        cursor.execute(f"SELECT money FROM users where id={user.id} AND guild={ctx.guild.id}")
        embed_obj = await EmbedCreate(description=f'・**{cursor.fetchone()[0]}** :gem:', color=Config.greenCol,
                                      title=f'Баланс {user.name}#{user.discriminator}',
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @balance.error
    async def balance_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.balance(self, ctx, ctx.author)

    @commands.command()
    async def b(self, ctx, user: discord.User, *args):
        await UserCommands.balance(self, ctx, user)

    @b.error
    async def b_error(self, ctx, error):
        await UserCommands.balance_error(self, ctx, error)

    @commands.command()
    async def shop(self, ctx, *args):
        embed_obj = await Utils.shop_get(1, ctx.guild.id)
        embed_obj.set_footer(text=f'!buy <номер> ・ {Utils.RequestedText(ctx.author)}')
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'shop')

        await message.add_reaction(Config.previous_reaction)
        await message.add_reaction(Config.next_reaction)
        await message.add_reaction(Config.cancel_reaction)

    @commands.command()
    async def buy(self, ctx, id: int, *args):
        cursor.execute(f"SELECT shopRoles FROM settings where guild={ctx.guild.id}")
        rolesArray = cursor.fetchone()[0].split(" ")
        del rolesArray[-1]
        cursor.execute(f"SELECT shopRolesCost FROM settings where guild={ctx.guild.id}")
        costsArray = cursor.fetchone()[0].split(" ")
        del costsArray[-1]

        id -= 1

        if 0 <= id < len(rolesArray):
            if rolesArray[id] == [y.id for y in ctx.author.roles]:
                embed_obj = await EmbedCreate(description=f'У тебя уже есть роль <@&{rolesArray[id]}>',
                                              footerText=Utils.RequestedText(ctx.author),
                                              color=Config.yellowCol)
                await ctx.send(embed=embed_obj)

            else:
                cursor.execute(f"SELECT money FROM users where id={ctx.author.id} AND guild={ctx.guild.id}")
                money = cursor.fetchone()[0]
                if money >= int(costsArray[id]):
                    money -= int(costsArray[id])
                    cursor.execute(f'UPDATE users SET money=? where id=? AND guild=?',
                                   (money, ctx.author.id, ctx.guild.id))
                    conn.commit()
                    role = utils.get(ctx.guild.roles, id=int(rolesArray[id]))
                    await ctx.author.add_roles(role)
                    embed_obj = await EmbedCreate(
                        description=f'Роль <@&{rolesArray[id]}> куплена за **{costsArray[id]}** :gem:',
                        footerText=Utils.RequestedText(ctx.author), color=Config.greenCol)
                    await ctx.send(embed=embed_obj)

                else:
                    embed_obj = await EmbedCreate(
                        description=f'Не достаточно :gem: для покупки роли <@&{rolesArray[id]}>',
                        footerText=Utils.RequestedText(ctx.author), color=Config.redCol)
                    await ctx.send(embed=embed_obj)
        else:
            embed_obj = await EmbedCreate(description=f'Неверно указан номер', color=Config.yellowCol,
                                          footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)

        await ctx.message.delete()

    @buy.error
    async def buy_error(self, ctx, error):
        embed_obj = await ArgumentsEmbedCreate(ctx, f'`!buy <номер>`')
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @commands.command()
    async def t(self, ctx, user: discord.User, sum: int, *args):
        await UserCommands.transfer(self, ctx, user, sum)

    @t.error
    async def t_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.transfer_error(self, ctx, error)

    @commands.command()
    async def transfer(self, ctx, user: discord.User, sum: int, *args):
        if ctx.author.id != user.id:
            money = 0
            if sum < 0:
                sum *= -1

            cursor.execute(f"SELECT money FROM users where id={ctx.author.id} AND guild={ctx.guild.id}")
            money = cursor.fetchone()[0]

            if money >= sum:
                cursor.execute(f"SELECT money FROM users where id={user.id} AND guild={ctx.guild.id}")
                money2 = cursor.fetchone()[0]

                money -= sum
                money2 += sum

                cursor.execute(f'UPDATE users SET money=? where id=? AND guild=?', (money, ctx.author.id, ctx.guild.id))
                cursor.execute(f'UPDATE users SET money=? where id=? AND guild=?', (money2, user.id, ctx.guild.id))
                conn.commit()

                embed_obj = await EmbedCreate(description=f'**{sum}** :gem: переведено участнику <@{user.id}>.',
                                              color=Config.greenCol,
                                              author=f'{ctx.author.name}#{ctx.author.discriminator} > {user.name}#{user.discriminator}',)
                await ctx.send(embed=embed_obj)

            else:
                embed_obj = await EmbedCreate(description=f'Не достаточно :gem:',
                                              color=Config.redCol,
                                              footerText=Utils.RequestedText(ctx.author))
                await ctx.send(embed=embed_obj)

        else:
            embed_obj = await EmbedCreate(description=f'Вы не можете перевести :gem: себе :D',
                                          color=Config.redCol,
                                          footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)

        await ctx.message.delete()

    @transfer.error
    async def transfer_error(self, ctx, error):
        embed_obj = await ArgumentsEmbedCreate(ctx, f'`!transfer @участник <сумма>`')
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @commands.command()
    async def top(self, ctx, id: str, *args):
        if id == 'money':
            embed_obj = await Utils.topget(1, "money", ctx.guild)
            embed_obj.title = "**:trophy: Рейтинг по :gem:**"
            embed_obj.color = Config.embedCol

        if id == 'voice':
            embed_obj = await Utils.topget(1, "voice", ctx.guild)
            embed_obj.title = "**:trophy: Рейтинг по голосовой активности**"
            embed_obj.color = Config.embedCol

        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx.author)}')
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'top')

        await message.add_reaction(Config.previous_reaction)
        await message.add_reaction(Config.next_reaction)
        await message.add_reaction(Config.cancel_reaction)

    @top.error
    async def top_error(self, ctx, error):
        embed_obj = await Utils.topget(1, "level", ctx.guild)
        embed_obj.title = "**:trophy: Рейтинг по уровню**"
        embed_obj.color = Config.embedCol
        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx.author)}')
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()

        Utils.AddEventedMessage(ctx, message, 'top')

        await message.add_reaction(Config.previous_reaction)
        await message.add_reaction(Config.next_reaction)
        await message.add_reaction(Config.cancel_reaction)

    @commands.command()
    async def minfo(self, ctx, user: discord.User, *args):
        cursor.execute(f'SELECT timeOut, reason, moder FROM punishments where id={user.id} AND guild={ctx.guild.id} AND type="mute"')
        row = cursor.fetchone()
        if row:
            unMuteTime = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
            c = unMuteTime - datetime.today()
            r = divmod(c.days * 86400 + c.seconds, 60)

            timeOut = timedelta(days=0, seconds=r[1], microseconds=0, milliseconds=0, minutes=r[0], hours=0,
                                weeks=0)

            embed_obj = await EmbedCreate(
                description=f'''У пользователя <@{user.id}> мьют на **{await Utils.ParseTimeToString(timeOut)}**
                ・Причина: **{row[1]}**
                ・Выдал: <@{row[2]}>''',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

        else:
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> не имеет мьют',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @minfo.error
    async def minfo_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.minfo(self, ctx, ctx.author)

    @commands.command()
    async def warns(self, ctx, user: discord.User, *args):
        embed_obj = await Utils.WarnsListGet(1, user, ctx.guild.id)
        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx.author)}')
        message = await ctx.send(embed=embed_obj)
        Utils.AddEventedMessage(ctx, message, 'warns')
        await ctx.message.delete()
        await message.add_reaction(Config.previous_reaction)
        await message.add_reaction(Config.next_reaction)
        await message.add_reaction(Config.cancel_reaction)

    @warns.error
    async def warns_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.warns(self, ctx, ctx.author)

    @commands.command()
    async def invite(self, ctx, *args):
        embed_obj = await EmbedCreate(
            title='Приглашение бота',
            description='**- - - - -> [\\*тык\\*](https://discord.com/oauth2/authorize?client_id=701115392801767434&permissions=0&scope=bot) <- - - - -**',
            color=Config.greenCol,
            footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @commands.command()
    async def symbols(self, ctx, *args):
        embed_obj = await EmbedCreate(
            title='Спец. символы',
            description='```・ ⟨⟩ ⊱⊰ ⌜⌟ ◜◞ ┊︱ ⌠⌡ ━```',
            color=Config.greenCol,
            footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(UserCommands(bot))
