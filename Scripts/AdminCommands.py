import discord
import asyncio
from discord.ext import commands
import sqlite3

from discord_slash import ButtonStyle
from discord_slash.utils import manage_components

import Config
from datetime import datetime, timedelta
import os
import Utils
import DataBase
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate, check_admin_roles

last_Messages = []

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(check_admin_roles)
    async def helpadmin(self, ctx, *args):
        embed_obj = discord.Embed(title="**Команды для Администраторов**", color=Config.embedCol)
        embed_obj.add_field(name="`!setxp`", value=f"Изменить уровень/опыт участника.")
        embed_obj.add_field(name="`!setvoice`", value=f"Изменить статистику голосового чата участника.")
        embed_obj.add_field(name="`!setmoney`", value=f"Изменить баланс участника.")
        embed_obj.add_field(name="`!addmoney`", value=f"Добавить сумму к балансу участника.")
        embed_obj.add_field(name="`!setr`", value=f"Изменить репутацию участника.")
        embed_obj.add_field(name="`!addr`", value=f"Добавить репутацию участнику.")
        embed_obj.add_field(name="`!embed`", value=f"Создание embed сообщений.")
        embed_obj.add_field(name="`!pembed` | `!pe`", value=f"Конструктор embed сообщений.")
        embed_obj.add_field(name="`!setb`", value=f"Установить список значков.")
        embed_obj.add_field(name="`!colors`", value=f"Что?")
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

    @helpadmin.error
    async def helpadmin_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole) or isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def totalhelp(self, ctx, *args):
        embed_obj = discord.Embed(title="**Команды для управления БД сервера**", color=Config.embedCol)
        embed_obj.add_field(name="`!totalcls`", value=f"Полностью очистить данные участников сервера.")
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

    @totalhelp.error
    async def totalhelp_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole) or isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def totalcls(self, ctx, *args):
        return

    @totalcls.error
    async def totalcls_error(self, ctx, *args):
        return

    @commands.command()
    @commands.check(check_admin_roles)
    async def helpembed(self, ctx, *args):
        embed_obj = discord.Embed(title="**Параметры Embed сообщений**", color=Config.embedCol)
        embed_obj.add_field(name="Параметры", value=f'''・**title**=Title_Text
                ・**color**=blue
                ・**authorname**=Author_Name
                ・**authorurl**=some_url
                ・**authoriconurl**=some_url
                ・**footertext**=Footer_Text
                ・**footerurl**=some_url
                ・**reactions**=:cookie:|:tada:|:heart:
                ・**imageurl**=some_url
                ・**addfield**=Field_Name,Field_Value,False
                ・**thumbnailurl**=some_url
                ''')
        embed_obj.add_field(name="Переменные", value='''・**{author.name}**
        ・**{author.display_name}**
        ・**{author.discriminator}**
        ・**{author.color}**
        ・**{author.avatar_url}**
        ・**{author.id}**
        ・**{author.mention}**
        ・**{guild.name}**
        ・**{guild.members}**
        ・**{guild.channels}**
        ・**{guild.created_at}**
        ・**{guild.owner}**
        ・**{author.owner.discriminator}**
        ''')

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

    @helpadmin.error
    async def helpembed_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole) or isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def embed(self, ctx, *text):
        title = ''
        colorName = ''
        thumbnailUrl = ''
        content = ''
        imageUrl = ''
        emojisName = []
        roles = ''
        emojis = ''
        authorName = ''
        authorUrl = ''
        authorIconUrl = ''
        footerText = ''
        footerUrl = ''

        fullText = ''

        embed_obj = discord.Embed()
        for word in text:
            if word.startswith('title='):
                title = word.replace('title=', '')
                title = Utils.EmbedParseVars(ctx, title)
            elif word.startswith('color='):
                colorName = word.replace('color=', '')
                colorName = Utils.EmbedParseVars(ctx, colorName, False)

            elif word.startswith('authorname='):
                authorName = word.replace('authorname=', '')
                authorName = Utils.EmbedParseVars(ctx, authorName)
            elif word.startswith('authorurl='):
                authorUrl = word.replace('authorurl=', '')
                authorUrl = Utils.EmbedParseVars(ctx, authorUrl, False)
            elif word.startswith('authoriconurl='):
                authorIconUrl = word.replace('authoriconurl=', '')
                authorIconUrl = Utils.EmbedParseVars(ctx, authorIconUrl, False)

            elif word.startswith('footertext='):
                footerText = word.replace('footertext=', '')
                footerText = Utils.EmbedParseVars(ctx, footerText)
            elif word.startswith('footerurl='):
                footerUrl = word.replace('footerurl=', '')
                footerUrl = Utils.EmbedParseVars(ctx, footerUrl, False)

            elif word.startswith('reactions='):
                word = word.replace('reactions=', '')
                emojisName = word.split('|')
                emojis = word.replace('|', ' ')
            elif word.startswith('roles='):
                word = word.replace('roles=', '')
                roles = word.replace('<@&', '').replace('>', '').replace('|', ' ')

            elif word.startswith('imageurl='):
                imageUrl = word.replace('imageurl=', '')
                imageUrl = Utils.EmbedParseVars(ctx, imageUrl, False)
            elif word.startswith('thumbnailurl='):
                thumbnailUrl = word.replace('thumbnailurl=', '')
                thumbnailUrl = Utils.EmbedParseVars(ctx, thumbnailUrl, False)

            elif word.startswith('addfield='):
                field = word.replace('addfield=', '').split(',')
                embed_obj.add_field(name=Utils.EmbedParseVars(ctx, field[0]), value=Utils.EmbedParseVars(ctx, field[1]),
                                    inline=field[2])

            elif word.startswith('content='):
                content = word.replace('content=', '')
                content = Utils.EmbedParseVars(ctx, content, True)

            else:
                word = word.replace('\\n', '\n')
                fullText += word + ' '

        color = 0x2F3136

        if colorName.lower() == 'green':
            color = Config.greenCol
        elif colorName.lower() == 'yellow':
            color = Config.yellowCol
        elif colorName.lower() == 'red':
            color = Config.redCol
        elif colorName.lower() == 'blue':
            color = Config.blueCol
        elif colorName != '':
            colorInt = int(colorName.replace('#', ''), 16)
            color = int(hex(colorInt), 0)

        if fullText == '':
            fullText = '-'

        embed_obj.description = Utils.EmbedParseVars(ctx, fullText, False)
        embed_obj.title = title
        embed_obj.colour = color
        embed_obj.set_thumbnail(url=thumbnailUrl)
        embed_obj.set_image(url=imageUrl)
        embed_obj.set_author(name=authorName, url=authorUrl, icon_url=authorIconUrl)
        embed_obj.set_footer(text=footerText, icon_url=footerUrl)

        message = await ctx.send(content=content, embed=embed_obj)

        DataBase.insertDataInDB('customMessages', f'{message.guild.id}, {message.id}, {message.channel.id}, "{emojis}", "{roles}"')

        await ctx.message.delete()
        for name in emojisName:
            await message.add_reaction(name)

    @embed.error
    async def embed_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!embed <текст>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def pembed(self, ctx, action: str, *text):
        name = ''
        fullText = ''
        listx = list(text)
        if len(text) > 0:
            name = text[0]
            listx[0] = ''

        for w in listx:
            fullText += w + ' '

        if action == 'set':
            embed_obj = discord.Embed(color=Config.blueCol)
            embed_obj.set_footer(text=Utils.RequestedText(ctx))

            table_result = DataBase.getDataFromDB('embed', f'text', f'nameembed="{name}" AND guild={ctx.guild.id}')
            if table_result is not None:
                oldText = table_result[0]
            else:
                oldText = ''

            if oldText == '':
                DataBase.insertDataInDB('embed', f'{ctx.guild.id}, "{name}", "{fullText}"')
                embed_obj.description = f'Сообщение `{name}` успешно добавлено.'
            else:
                DataBase.updateDataInDB('embed', f'text="{fullText}"', f'nameembed="{name}" AND guild={ctx.guild.id}')
                embed_obj.description = f'Сообщение `{name}` успешно изменено.'

            await AdminCommands.pembed(self, ctx, 'send', name)
            await ctx.send(embed=embed_obj)

        elif action == 'del':
            embed_obj = discord.Embed(color=Config.blueCol)
            embed_obj.set_footer(text=Utils.RequestedText(ctx))
            oldText = DataBase.getDataFromDB('embed', 'text', f'nameembed="{name}" AND guild={ctx.guild.id}')

            if oldText == '':
                embed_obj.description = f'Сообщение `{name}` не найдено.'
            else:
                DataBase.deleteDataFromDB('embed',f'nameembed="{name}" AND guild={ctx.guild.id}')
                embed_obj.description = f'Сообщение `{name}` успешно удалено.'

            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

        elif action == 'get':
            embed_obj = discord.Embed(color=Config.blueCol)
            embed_obj.set_footer(text=Utils.RequestedText(ctx))

            oldText = DataBase.getDataFromDB('embed', 'text', f'nameembed="{name}" AND guild={ctx.guild.id}')[0]

            oldText = oldText.replace('\\n', '\\n\n')
            if oldText == '':
                embed_obj.description = f'Сообщение `{name}` не найдено.'
            else:
                embed_obj.description = f'Сообщение `{name}`: ```{oldText}```'

            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

        elif action == 'send':
            table_result = DataBase.getDataFromDB('embed', 'text', f'nameembed="{name}" AND guild={ctx.guild.id}')
            if table_result is not None:
                oldText = table_result[0]
            else:
                oldText = ''

            if oldText == '':
                embed_obj = discord.Embed(color=Config.blueCol)
                embed_obj.set_footer(text=Utils.RequestedText(ctx))
                embed_obj.description = f'Сообщение `{name}` не найдено.'
                await ctx.send(embed=embed_obj)
                await ctx.message.delete()
                return

            textList = oldText.split(' ')

            await AdminCommands.embed(self, ctx, *textList)

        elif action == 'list':
            embed_obj = await Utils.pembed_list_get(1, ctx.guild.id)
            embed_obj.set_footer(text=Utils.RequestedText(ctx))

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
            Utils.AddEventedMessage(ctx, message, 'embedlist')
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'''`!pembed set <имя> <текст>`
                        `!pembed del <имя>`
                        `!pembed get <имя>`
                        `!pembed send <имя>`
                        `!pembed list`
                        ''')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @pembed.error
    async def pembed_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'''`!pembed set <имя> <текст>`
            `!pembed del <имя>`
            `!pembed get <имя>`
            `!pembed send <имя>`
            `!pembed list`
            ''')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def pe(self, ctx, action: str, *text):
        await AdminCommands.pembed(self, ctx, action, *text)

    @pe.error
    async def pe_error(self, ctx, error):
        await AdminCommands.pembed_error(self, ctx, error)

    @commands.command()
    @commands.check(check_admin_roles)
    async def setxp(self, ctx, user: discord.Member, lvl: int, xp: int, *args):
        uid = user.id
        embed_obj = await EmbedCreate(description=f'Ранг изменен.', color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        lvl = max(min(lvl, 1000), 0)

        DataBase.updateDataInDB('users', f'level={lvl}', f'id={uid} AND guild={ctx.guild.id}')
        DataBase.updateDataInDB('users', f'xp=0', f'id={uid} AND guild={ctx.guild.id}')
        await Utils.xpadd(xp, user, False)

        await ctx.message.delete()

    @setxp.error
    async def setxp_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setxp @user <уровень> <опыт>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def setvoice(self, ctx, user: discord.User, h: int, m: int, *args):
        uid = user.id

        embed_obj = await EmbedCreate(description=f'Голосовая активность изменена.', color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        time = (h * 3600) + (m * 60)

        DataBase.updateDataInDB('users', f'voice={time}', f'id={uid} AND guild={ctx.guild.id}')

        await ctx.message.delete()

    @setvoice.error
    async def setvoice_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setvoice @user <часы> <минуты>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def setr(self, ctx, user: discord.User, rep: int, *args):
        uid = user.id
        embed_obj = await EmbedCreate(
            description=f'Репутация участника **<@{user.id}>** изменена на **{rep}** {Config.reputation_reaction}',
            color=Config.blueCol,
            footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        DataBase.updateDataInDB('users', f'reputation={rep}', f'id={uid} AND guild={ctx.guild.id}')

        await ctx.message.delete()

    @setr.error
    async def setr_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setr @user <репутация>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def addr(self, ctx, user: discord.User, rep: int, *args):
        uid = user.id
        reputation = DataBase.getDataFromDB('users', 'reputation', f'id={uid} AND guild={ctx.guild.id}')[0]
        reputation += rep
        DataBase.updateDataInDB('users', f'reputation={reputation}', f'id={uid} AND guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(
            description=f'Репутация участника **<@{user.id}>** {("повышена" if (rep>0) else "понижена")} на **{abs(rep)}** {Config.reputation_reaction}',
            color=Config.blueCol,
            footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @addr.error
    async def addr_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!addr @user <репутация>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def setmoney(self, ctx, user: discord.User, sum: int, *args):
        uid = user.id
        embed_obj = await EmbedCreate(
            description=f'Счет участника **<@{user.id}>** изменен на **{sum}** {Config.money_reaction}',
            color=Config.blueCol,
            footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        DataBase.updateDataInDB('users', f'money={sum}', f'id={uid} AND guild={ctx.guild.id}')

        await ctx.message.delete()

    @setmoney.error
    async def setmoney_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setmoney @user <сумма>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def addmoney(self, ctx, user: discord.User, sum: int, *args):
        uid = user.id
        money = DataBase.getDataFromDB('users', 'money', f'id={uid} AND guild={ctx.guild.id}')[0]
        money += sum
        DataBase.updateDataInDB('users', f'money={money}', f'id={uid} AND guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(
            description=f'Cчет участника **<@{user.id}>** {("увеличен" if (sum>0) else "уменьшен")} на **{abs(sum)}** {Config.money_reaction}',
            color=Config.blueCol,
            footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @addmoney.error
    async def addmoney_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!addmoney @user <сумма>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def colors(self, ctx, *args):
        embed_obj = discord.Embed(title="**Зеленый**", color=Config.greenCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        embed_obj = discord.Embed(title="**Жёлтый**", color=Config.yellowCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        embed_obj = discord.Embed(title="**Красный**", color=Config.redCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        embed_obj = discord.Embed(title="**Синий**", color=Config.blueCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        await ctx.message.delete()

    @colors.error
    async def colors_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def autoroles(self, ctx, role: discord.Role, *args):
        guild = ctx.guild
        embed_obj = await EmbedCreate(description=f'Начата выдача роли <@&{role.id}> всем участникам сервера.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        for member in guild.members:
            await member.add_roles(role)
            await asyncio.sleep(0.5)

        embed_obj = await EmbedCreate(description=f'Выдача роли <@&{role.id}> всем участникам сервера завершена.',
                                      color=Config.greenCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

    @autoroles.error
    async def autoroles_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!autoroles @role`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def setb(self, ctx, user: discord.Member, *badges):
        embed_obj = await EmbedCreate(description=f'Список значков изменен.', color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)

        fullBadges = ''
        for b in badges:
            fullBadges += f'{b} '

        DataBase.updateDataInDB('users', f'badges="{fullBadges}"', f'id={user.id} AND guild={ctx.guild.id}')
        await ctx.message.delete()

    @setb.error
    async def setb_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setb @user <значки>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(AdminCommands(bot))
