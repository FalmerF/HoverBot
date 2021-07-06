import discord
import asyncio
from discord.ext import commands
import sqlite3
import Config
from datetime import datetime, timedelta
import os
import Utils
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate, check_admin_roles

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

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
        embed_obj.add_field(name="`!pembed`", value=f"Создание embed сообщений.")
        embed_obj.add_field(name="`!setb`", value=f"Установить список значков.")
        embed_obj.add_field(name="`!colors`", value=f"Что?")
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

        await message.add_reaction(Config.cancel_reaction)

    @helpadmin.error
    async def helpadmin_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole) or isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.check(check_admin_roles)
    async def helpembed(self, ctx, *args):
        embed_obj = discord.Embed(title="**Параметры Embed сообщений**", color=Config.embedCol)
        # embed_obj.add_field(name="・title", value=f"Пример: `title=Title_Text`")
        # embed_obj.add_field(name="・color", value=f"Пример: `color=blue`")
        # embed_obj.add_field(name="・authorname", value=f"Пример: `authorname=Author_Name`")
        # embed_obj.add_field(name="・authorurl", value=f"Пример: `authorurl=some_url`")
        # embed_obj.add_field(name="・authoriconurl", value=f"Пример: `authoriconurl=some_url`")
        # embed_obj.add_field(name="・footertext", value=f"Пример: `footertext=Footer_Text`")
        # embed_obj.add_field(name="・footerurl", value=f"Пример: `footerurl=some_url`")
        # embed_obj.add_field(name="・reactions", value=f"Пример: `reactions=:cookie:|:tada:|:heart:`")
        # embed_obj.add_field(name="・imageurl", value=f"Пример: `imageurl=some_url`")
        # embed_obj.add_field(name="・thumbnailurl", value=f"Пример: `thumbnailurl=some_url`")
        # embed_obj.add_field(name="・addfield", value=f"Пример: `addfield=Field_Name,Field_Value,False`")
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

        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

        await message.add_reaction(Config.cancel_reaction)

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
        imageUrl = ''
        emojisName = []
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

        message = await ctx.send(embed=embed_obj)

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
            embed_obj.set_footer(text=Utils.RequestedText(ctx.author))

            cursor.execute(f'SELECT text FROM embed where nameembed="{name}" AND guild={ctx.guild.id}')
            table_result = cursor.fetchone()
            if table_result is not None:
                oldText = table_result[0]
            else:
                oldText = ''

            if oldText == '':
                cursor.execute(f'INSERT INTO embed VALUES ({ctx.guild.id}, "{name}", "{fullText}")')
                embed_obj.description = f'Сообщение `{name}` успешно добавлено.'
            else:
                cursor.execute(f'UPDATE embed SET text=? where nameembed=? AND guild=?', (fullText, name, ctx.guild.id))
                embed_obj.description = f'Сообщение `{name}` успешно изменено.'

            conn.commit()
            await AdminCommands.pembed(self, ctx, 'send', name)
            await ctx.send(embed=embed_obj)

        elif action == 'del':
            embed_obj = discord.Embed(color=Config.blueCol)
            embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
            cursor.execute(f'SELECT text FROM embed where nameembed="{name}" AND guild={ctx.guild.id}')
            oldText = cursor.fetchone()[0]

            if oldText == '':
                embed_obj.description = f'Сообщение `{name}` не найдено.'
            else:
                cursor.execute(f'DELETE FROM embed where nameembed="{name}" AND guild={ctx.guild.id}')
                conn.commit()
                embed_obj.description = f'Сообщение `{name}` успешно удалено.'

            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

        elif action == 'get':
            embed_obj = discord.Embed(color=Config.blueCol)
            embed_obj.set_footer(text=Utils.RequestedText(ctx.author))

            cursor.execute(f'SELECT text FROM embed where nameembed="{name}" AND guild={ctx.guild.id}')
            oldText = cursor.fetchone()[0]

            oldText = oldText.replace('\\n', '\\n\n')
            if oldText == '':
                embed_obj.description = f'Сообщение `{name}` не найдено.'
            else:
                embed_obj.description = f'Сообщение `{name}`: ```{oldText}```'

            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

        elif action == 'send':
            cursor.execute(f'SELECT text FROM embed where nameembed="{name}" AND guild={ctx.guild.id}')
            table_result = cursor.fetchone()
            if table_result is not None:
                oldText = table_result[0]
            else:
                oldText = ''

            if oldText == '':
                embed_obj = discord.Embed(color=Config.blueCol)
                embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
                embed_obj.description = f'Сообщение `{name}` не найдено.'
                await ctx.send(embed=embed_obj)
                await ctx.message.delete()
                return

            textList = oldText.split(' ')

            await AdminCommands.embed(self, ctx, *textList)

        elif action == 'list':
            embed_obj = await Utils.pembed_list_get(1, ctx.guild.id)
            embed_obj.set_footer(text=Utils.RequestedText(ctx.author))

            message = await ctx.send(embed=embed_obj)
            await ctx.message.delete()

            Utils.AddEventedMessage(ctx, message, 'embedlist')

            await message.add_reaction(Config.previous_reaction)
            await message.add_reaction(Config.next_reaction)
            await message.add_reaction(Config.cancel_reaction)
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
            print(error)
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
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        lvl = max(min(lvl, 1000), 0)

        cursor.execute(f'UPDATE users SET level=? where id=? AND guild=?', (lvl, uid, ctx.guild.id))
        cursor.execute(f'UPDATE users SET xp=? where id=? AND guild=?', (0, uid, ctx.guild.id))
        conn.commit()
        await Utils.xpadd(xp, user)

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
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        time = (h * 3600) + (m * 60)

        cursor.execute(f'UPDATE users SET voice=? where id=? AND guild=?', (time, uid, ctx.guild.id))
        conn.commit()

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
    async def setmoney(self, ctx, user: discord.User, sum: int, *args):
        uid = user.id
        embed_obj = await EmbedCreate(
            description=f'Счет участника {user.name}#{user.discriminator} изменен на **{sum}** :gem:',
            color=Config.blueCol,
            footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        cursor.execute(f'UPDATE users SET money=? where id=? AND guild=?', (sum, uid, ctx.guild.id))
        conn.commit()

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
        cursor.execute(f"SELECT money FROM users where id={uid} AND guild={ctx.guild.id}")
        money = cursor.fetchone()[0]
        money += sum
        cursor.execute(f'UPDATE users SET money=? where id=? AND guild=?', (money, uid, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(
            description=f'На счет участника {user.name}#{user.discriminator} добавлено **{sum}** :gem:',
            color=Config.blueCol,
            footerText=Utils.RequestedText(ctx.author))
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
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        embed_obj = discord.Embed(title="**Жёлтый**", color=Config.yellowCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        embed_obj = discord.Embed(title="**Красный**", color=Config.redCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        embed_obj = discord.Embed(title="**Синий**", color=Config.blueCol)
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
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
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        for member in guild.members:
            await member.add_roles(role)
            await asyncio.sleep(0.5)

        embed_obj = await EmbedCreate(description=f'Выдача роли <@&{role.id}> всем участникам сервера завершена.',
                                      color=Config.greenCol,
                                      footerText=Utils.RequestedText(ctx.author))
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
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        fullBadges = ''
        for b in badges:
            fullBadges += f'{b} '

        cursor.execute(f'UPDATE users SET badges=? where id=? AND guild=?', (fullBadges, user.id, ctx.guild.id))
        conn.commit()
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
