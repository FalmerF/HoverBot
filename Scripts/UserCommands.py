import sqlite3
from datetime import datetime, timedelta
# import keep_alive

import discord
from discord import utils
from discord.ext import commands

import Config
import Utils
import DataBase
from Utils import EmbedCreate, ArgumentsEmbedCreate

from discord_slash.model import ButtonStyle
from discord_slash.utils import manage_components


last_Messages = []


class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *args):
        embed_obj = discord.Embed(title="**Общие команды**", color=Config.embedCol)
        # embed_obj.add_field(name="`!rank`", value=f"Показывает информацию о ранге участника.")
        embed_obj.add_field(name="`!balance` | `!b`", value=f"Показывает информацию о балансе.")
        embed_obj.add_field(name="`!reputation` | `!r`", value=f"Посмотреть репутацию участника.")
        embed_obj.add_field(name="`!pr`", value=f"Повысить репутацию участника.")
        embed_obj.add_field(name="`!shop`", value=f"Магазин в котором можно купить роли.")
        embed_obj.add_field(name="`!everyday`", value=f"Получить ежедневную награду.")
        embed_obj.add_field(name="`!transfer` | `!t`", value=f"Передать {Config.money_reaction} другому участнику.")
        embed_obj.add_field(name="`!minfo`", value=f"Информация о мьюте участника.")
        embed_obj.add_field(name="`!profile` | `!p`", value=f"Посмотреть профиль участника.")
        embed_obj.add_field(name="`!c`", value=f"Управление приватными каналами.")
        embed_obj.add_field(name="`!warns`", value=f"Посмотреть список предупреждений участника.")
        embed_obj.add_field(name="`!top [voice, money, rep]`", value=f"Показывает топ участников.")
        embed_obj.add_field(name="`!av`", value=f"Показывает аватар участника.")
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

    # @commands.command()
    # async def rank(self, ctx, user: discord.Member, *args):
    #     await Utils.rankMet(ctx, user)
    #
    # @rank.error
    # async def rank_error(self, ctx, error):
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         await Utils.rankMet(ctx, ctx.author)

    @commands.command()
    async def profile(self, ctx, user: discord.Member, *args):
        embed_obj = await Utils.ProfileCreate(ctx, user)
        await ctx.send(embed=embed_obj)
        # buttons = [
        #     manage_components.create_button(
        #         style=ButtonStyle.red,
        #         emoji=self.bot.get_emoji(id=Config.cancel_emoji),
        #         custom_id='1000'
        #     ),
        #     # manage_components.create_button(
        #     #     style=ButtonStyle.grey,
        #     #     emoji=Config.reputation_emoji,
        #     #     custom_id='1003'
        #     # ),
        # ]
        # action_row = manage_components.create_actionrow(*buttons)
        #
        # prf = await ctx.send(embed=embed_obj, components=[action_row])
        await ctx.message.delete()
        # Utils.AddEventedMessage(ctx, prf, 'help')

    @profile.error
    async def profile_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.profile(self, ctx, ctx.author)
        elif isinstance(error, commands.errors.CheckFailure):
            embed_obj = await Utils.AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!profile @user`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    async def p(self, ctx, user: discord.Member, *args):
        await UserCommands.profile(self, ctx, user, *args)

    @p.error
    async def p_error(self, ctx, error):
        await UserCommands.profile_error(self, ctx, error)

    @commands.command()
    async def balance(self, ctx, user: discord.User, *args):
        row = DataBase.getDataFromDB('users', 'money', f'id={user.id} AND guild={ctx.guild.id}')
        embed_obj = await EmbedCreate(description=f'・**{Utils.makePointedNumber(row[0])}** {Config.money_reaction}', color=Config.greenCol,
                                      title=f'Баланс {user.name}#{user.discriminator}',
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @balance.error
    async def balance_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.balance(self, ctx, ctx.author)
        elif isinstance(error, commands.errors.CheckFailure):
            embed_obj = await Utils.AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!b @user`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    async def b(self, ctx, user: discord.User, *args):
        await UserCommands.balance(self, ctx, user)

    @b.error
    async def b_error(self, ctx, error):
        await UserCommands.balance_error(self, ctx, error)

    @commands.command()
    async def reputation(self, ctx, user: discord.User, *args):
        row = DataBase.getDataFromDB('users', 'reputation', f'id={user.id} AND guild={ctx.guild.id}')
        embed_obj = await EmbedCreate(description=f'・**{row[0]}** {Config.reputation_reaction}', color=Config.greenCol,
                                      title=f'Репутация {user.name}#{user.discriminator}',
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @reputation.error
    async def reputation_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.reputation(self, ctx, ctx.author)
        elif isinstance(error, commands.errors.CheckFailure):
            embed_obj = await Utils.AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!reputation @user`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    async def r(self, ctx, user: discord.User, *args):
        await UserCommands.reputation(self, ctx, user)

    @r.error
    async def b_error(self, ctx, error):
        await UserCommands.reputation_error(self, ctx, error)

    @commands.command()
    async def shop(self, ctx, *args):
        embed_obj = await Utils.shop_get(1, ctx.guild.id)
        embed_obj.set_footer(text=f'!buy <номер> ・ {Utils.RequestedText(ctx)}')

        buttons = [
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.previous_emoji),
                custom_id='1001'
            ),
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.next_emoji),
                custom_id='1002'
            ),
            manage_components.create_button(
                style=ButtonStyle.red,
                emoji=self.bot.get_emoji(id=Config.cancel_emoji),
                custom_id='1000'
            ),
        ]
        action_row = manage_components.create_actionrow(*buttons)
        message = await ctx.send(embed=embed_obj, components=[action_row])
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'shop')

    @commands.command()
    async def buy(self, ctx, id: int, *args):
        rolesArray = DataBase.getDataFromDB('settings', 'shopRoles', f'guild={ctx.guild.id}')[0].split(" ")
        del rolesArray[-1]
        costsArray = DataBase.getDataFromDB('settings', 'shopRolesCost', f'guild={ctx.guild.id}')[0].split(" ")
        del costsArray[-1]

        id -= 1

        if 0 <= id < len(rolesArray):
            for y in ctx.author.roles:
                if int(rolesArray[id]) == int(y.id):
                    embed_obj = await EmbedCreate(description=f'У тебя уже есть роль <@&{rolesArray[id]}>',
                                                  footerText=Utils.RequestedText(ctx),
                                                  color=Config.yellowCol)
                    await ctx.send(embed=embed_obj)
                    break
            else:
                money = DataBase.getDataFromDB('users', 'money', f'id={ctx.author.id} AND guild={ctx.guild.id}')[0]
                if money >= int(costsArray[id]):
                    money -= int(costsArray[id])
                    DataBase.updateDataInDB('users', f'money={money}', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                    role = utils.get(ctx.guild.roles, id=int(rolesArray[id]))
                    await ctx.author.add_roles(role)
                    embed_obj = await EmbedCreate(
                        description=f'Роль <@&{rolesArray[id]}> куплена за **{costsArray[id]}** {Config.money_reaction}',
                        footerText=Utils.RequestedText(ctx), color=Config.greenCol)
                    await ctx.send(embed=embed_obj)

                else:
                    embed_obj = await EmbedCreate(
                        description=f'Не достаточно {Config.money_reaction} для покупки роли <@&{rolesArray[id]}>',
                        footerText=Utils.RequestedText(ctx), color=Config.redCol)
                    await ctx.send(embed=embed_obj)
        else:
            embed_obj = await EmbedCreate(description=f'Неверно указан номер', color=Config.yellowCol,
                                          footerText=Utils.RequestedText(ctx))
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
        elif isinstance(error, commands.errors.CheckFailure):
            embed_obj = await Utils.AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'``!transfer @участник <сумма>``')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    async def transfer(self, ctx, user: discord.User, sum: int, *args):
        if ctx.author.id != user.id:
            money = 0
            if sum < 0:
                sum *= -1

            money = DataBase.getDataFromDB('users', 'money', f'id={ctx.author.id} AND guild={ctx.guild.id}')[0]

            if money >= sum:
                money2 = DataBase.getDataFromDB('users', 'money', f'id={user.id} AND guild={ctx.guild.id}')[0]

                money -= sum
                money2 += sum

                DataBase.updateDataInDB('users', f'money={money}', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                DataBase.updateDataInDB('users', f'money={money2}', f'id={user.id} AND guild={ctx.guild.id}')

                embed_obj = await EmbedCreate(description=f'**{sum}** {Config.money_reaction} переведено участнику <@{user.id}>.',
                                              color=Config.greenCol,
                                              author=f'{ctx.author.name}#{ctx.author.discriminator} > {user.name}#{user.discriminator}',)
                await ctx.send(embed=embed_obj)

            else:
                embed_obj = await EmbedCreate(description=f'Не достаточно {Config.money_reaction}',
                                              color=Config.redCol,
                                              footerText=Utils.RequestedText(ctx))
                await ctx.send(embed=embed_obj)

        else:
            embed_obj = await EmbedCreate(description=f'Вы не можете перевести {Config.money_reaction} себе :D',
                                          color=Config.redCol,
                                          footerText=Utils.RequestedText(ctx))
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
            embed_obj.title = f"**:trophy: Рейтинг по балансу {Config.money_reaction}**"
            embed_obj.color = Config.embedCol

        if id == 'voice':
            embed_obj = await Utils.topget(1, "voice", ctx.guild)
            embed_obj.title = f"**:trophy: Рейтинг по голосовой активности**"
            embed_obj.color = Config.embedCol

        if id == 'rep' or id == 'reputation':
            embed_obj = await Utils.topget(1, "rep", ctx.guild)
            embed_obj.title = f"**:trophy: Рейтинг по репутации {Config.reputation_reaction}**"
            embed_obj.color = Config.embedCol

        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx)}')

        buttons = [
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.previous_emoji),
                custom_id='1001'
            ),
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.next_emoji),
                custom_id='1002'
            ),
            manage_components.create_button(
                style=ButtonStyle.red,
                emoji=self.bot.get_emoji(id=Config.cancel_emoji),
                custom_id='1000'
            ),
        ]
        action_row = manage_components.create_actionrow(*buttons)
        message = await ctx.send(embed=embed_obj, components=[action_row])
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'top')

    @top.error
    async def top_error(self, ctx, error):
        embed_obj = await Utils.topget(1, "level", ctx.guild)
        embed_obj.title = "**:trophy: Рейтинг по уровню**"
        embed_obj.color = Config.embedCol
        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx)}')

        buttons = [
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.previous_emoji),
                custom_id='1001'
            ),
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.next_emoji),
                custom_id='1002'
            ),
            manage_components.create_button(
                style=ButtonStyle.red,
                emoji=self.bot.get_emoji(id=Config.cancel_emoji),
                custom_id='1000'
            ),
        ]
        action_row = manage_components.create_actionrow(*buttons)
        message = await ctx.send(embed=embed_obj, components=[action_row])
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'top')

    @commands.command()
    async def minfo(self, ctx, user: discord.User, *args):
        row = DataBase.getDataFromDB('punishments', 'timeOut, reason, moder', f'id={user.id} AND guild={ctx.guild.id} AND type="mute"')
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
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

        else:
            embed_obj = await EmbedCreate(
                description=f'<@{user.id}> не имеет мьют',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @minfo.error
    async def minfo_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.minfo(self, ctx, ctx.author)

    @commands.command()
    async def warns(self, ctx, user: discord.User, *args):
        embed_obj = await Utils.WarnsListGet(1, user, ctx.guild.id)
        embed_obj.set_footer(text=f'{Utils.RequestedText(ctx)}')

        buttons = [
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.previous_emoji),
                custom_id='1001'
            ),
            manage_components.create_button(
                style=ButtonStyle.green,
                emoji=self.bot.get_emoji(id=Config.next_emoji),
                custom_id='1002'
            ),
            manage_components.create_button(
                style=ButtonStyle.red,
                emoji=self.bot.get_emoji(id=Config.cancel_emoji),
                custom_id='1000'
            ),
        ]
        action_row = manage_components.create_actionrow(*buttons)
        message = await ctx.send(embed=embed_obj, components=[action_row])
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'warns')

    @warns.error
    async def warns_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await UserCommands.warns(self, ctx, ctx.author)

    @commands.command()
    async def pr(self, ctx, user: discord.User, *args):
        access_pr = False
        if ((ctx.author.name == user.name) and (ctx.author.discriminator == user.discriminator)):
            embed_obj = await EmbedCreate(
                description=f'Нельзя повысить свою репутацию!',
                color=Config.yellowCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            row = DataBase.getDataFromDB('reputation', 'previous', f'id={ctx.author.id} AND guild={ctx.guild.id}')
            if (row == None):
                row = DataBase.getDataFromDB('reputation', 'last', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                if (row == None):
                    DataBase.insertDataInDB('reputation', f'{ctx.author.id}, {ctx.guild.id}, "{datetime.today()}", "{datetime.today()}"')
                DataBase.updateDataInDB('reputation', f'last="{datetime.today() + timedelta(days=1)}"', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                access_pr = True
            else:
                row = DataBase.getDataFromDB('reputation', 'previous', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                previous_reputation = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                c = previous_reputation - datetime.today()
                r = divmod(c.days * 86400 + c.seconds, 60)
                if r[0] < 0 or r[1] < 0:
                    access_pr = True
                    row = DataBase.getDataFromDB('reputation', 'last', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                    DataBase.updateDataInDB('reputation', f'previous="{row[0]}"', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                    DataBase.updateDataInDB('reputation', f'last="{datetime.today() + timedelta(days=1)}"', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                else:
                    embed_obj = await EmbedCreate(
                        description=f'Вы можете повысить чью-то репутацию только **2 раза в день**!',
                        color=Config.yellowCol,
                        footerText=Utils.RequestedText(ctx))
                    await ctx.send(embed=embed_obj)
                    await ctx.message.delete()
        if (access_pr):
            uid = user.id
            row = DataBase.getDataFromDB('users', 'reputation', f'id={uid} AND guild={ctx.guild.id}')
            reputation = row[0] + Config.reputationPr
            DataBase.updateDataInDB('users', f'reputation={reputation}', f'id={uid} AND guild={ctx.guild.id}')

            embed_obj = await EmbedCreate(
                description=f'Репутация участника **<@{user.id}>** был повышена на **{Config.reputationPr}** {Config.reputation_reaction}!',
                color=Config.blueCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @pr.error
    async def pr_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await Utils.AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!pr @user`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    # @commands.command()
    # async def invite(self, ctx, *args):
    #     embed_obj = await EmbedCreate(
    #         title='Приглашение бота',
    #         description='**- - - - -> [\\*тык\\*](https://discord.com/oauth2/authorize?client_id=701115392801767434&permissions=0&scope=bot) <- - - - -**',
    #         color=Config.greenCol,
    #         footerText=Utils.RequestedText(ctx))
    #     await ctx.send(embed=embed_obj)
    #     await ctx.message.delete()

    @commands.command()
    async def symbols(self, ctx, *args):
        embed_obj = await EmbedCreate(
            title='Спец. символы',
            description='```・ ⟨⟩ ⊱⊰ ⌜⌟ ◜◞ ┊︱ ⌠⌡ ━```',
            color=Config.greenCol,
            footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @commands.command()
    async def everyday(self, ctx, *args):
        row = DataBase.getDataFromDB('everyday', 'date', f'id={ctx.author.id} AND guild={ctx.guild.id}')
        if row is None:
            DataBase.insertDataInDB('everyday', f'{ctx.author.id}, {ctx.guild.id}, "{datetime.today()  + timedelta(days=1)}"')
            embed_obj = await EmbedCreate(
                title=f'Ежедневные награды!',
                description=f'**<@{ctx.author.id}>**, вы получили **{await Utils.addMoneyToUser(ctx.author, ctx.guild.id, Config.moneyEveryday)}** {Config.money_reaction}!\nВозвращайтесь через 24 часа за новой.',
                color=Config.greenCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            row = DataBase.getDataFromDB('everyday', 'date', f'id={ctx.author.id} AND guild={ctx.guild.id}')
            lastGetEveryday = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
            c = lastGetEveryday - datetime.today()
            r = divmod(c.days * 86400 + c.seconds, 60)
            if r[0] < 0 or r[1] < 0:
                DataBase.updateDataInDB('everyday', f'date="{datetime.today() + timedelta(days=1)}"', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                embed_obj = await EmbedCreate(
                    title=f'Ежедневные награды!',
                    description=f'**<@{ctx.author.id}>**, вы получили **{await Utils.addMoneyToUser(ctx.author, ctx.guild.id, Config.moneyEveryday)}** {Config.money_reaction}!\nВозвращайтесь через 24 часа за новой.',
                    color=Config.greenCol,
                    footerText=Utils.RequestedText(ctx))
                await ctx.send(embed=embed_obj)
                await ctx.message.delete()
            else:
                row = DataBase.getDataFromDB('everyday', 'date', f'id={ctx.author.id} AND guild={ctx.guild.id}')
                lastGetEveryday = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                dateDifference = (lastGetEveryday - datetime.today()).seconds
                hours, remainder = divmod(dateDifference, 3600)
                minutes, seconds = divmod(remainder, 60)
                moneyLeft = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
                embed_obj = await EmbedCreate(
                    description=f'''Вы можете получить награду только **1 раз в 24 часа**!
                                    Следующую награду можно будет получить через **{moneyLeft}**''',
                    color=Config.yellowCol,
                    footerText=Utils.RequestedText(ctx))
                await ctx.send(embed=embed_obj)
                await ctx.message.delete()

    # @everyday.error
    # async def everyday_error(self, ctx, error):
    #     if isinstance(error, commands.errors.CheckFailure):
    #         embed_obj = await Utils.AccessEmbedCreate(ctx)
    #         await ctx.send(embed=embed_obj)
    #         await ctx.message.delete()
    #     else:
    #         embed_obj = await ArgumentsEmbedCreate(ctx, f'`!everyday`')
    #         await ctx.send(embed=embed_obj)
    #         await ctx.message.delete()



def setup(bot):
    bot.add_cog(UserCommands(bot))
