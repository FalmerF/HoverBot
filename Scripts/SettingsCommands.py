import discord
from discord.ext import commands
import sqlite3
import Config
from datetime import datetime, timedelta
import os
import Utils
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

last_Messages = []


class SettingsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def helpsettings(self, ctx, *args):
        embed_obj = discord.Embed(title="**Информация о доп. командах**", color=Config.embedCol)
        embed_obj.add_field(name="`!setmoderroles`", value=f"Устанавливает роли Модераторов.")
        embed_obj.add_field(name="`!pcreate`", value=f"Создает категорию приватных каналов.")
        embed_obj.add_field(name="`!setnoxp`",
                            value=f"Устанавливает каналы с которых пльзователь не будет получать опыт.")
        embed_obj.add_field(name="`!shopadd`", value=f"Добавляет новую роль в магазин.")
        embed_obj.add_field(name="`!shopdel`", value=f"Удаляет роль с магазина.")
        embed_obj.add_field(name="`!setxpm`", value=f"Устанавливает множитель опыта.")
        embed_obj.add_field(name="`!setm`", value=f"Устанавливает максимальный множитель опыта от количества участников в голосовом канале.")
        embed_obj.add_field(name="`!addchannelstat`", value=f"Создает канал со статистикой.")
        embed_obj.add_field(name="`Скоро...`", value=f"-")
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))
        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

        await message.add_reaction(Config.cancel_reaction)

    @helpsettings.error
    async def helpsettings_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole) or isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx, *args):
        cursor.execute(f"SELECT privateChannelId, noXpChanels, AdminRoles, ModerRoles, xpMultiplier FROM settings where guild={ctx.guild.id}")
        row = cursor.fetchone()
        embed_obj = discord.Embed(title="**Настройки бота**", color=Config.embedCol)

        mentions_text = await Utils.get_mentions(row[3], ' ', '<@&id>')
        embed_obj.add_field(name="Роли Модерации", value=mentions_text)

        mentions_text = await Utils.get_mentions(row[1], ' ', '<#id>')
        embed_obj.add_field(name="No XP каналы", value=mentions_text)

        if row[0] is not None and row[0] != 0:
            embed_obj.add_field(name="Приватный канал", value=f'<#{row[0]}>')

        embed_obj.add_field(name=f'Множитель опыта: `{row[4]}x`', value='-')
        embed_obj.set_footer(text=Utils.RequestedText(ctx.author))

        message = await ctx.send(embed=embed_obj)
        await ctx.message.delete()
        Utils.AddEventedMessage(ctx, message, 'help')

        await message.add_reaction(Config.cancel_reaction)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmoderroles(self, ctx, *roles: discord.Role):
        rolesId = ''
        for role in roles:
            rolesId += f'{role.id} '

        if len(roles) == 0:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setmoderroles @roles`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return 0

        cursor.execute(f'UPDATE settings SET ModerRoles=? where guild=?', (rolesId, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Список ролей модерации изменен.', color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)

        await ctx.message.delete()

    @setmoderroles.error
    async def setmoderroles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setmoderroles @roles`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pcreate(self, ctx, *args):
        cursor.execute(f"SELECT privateChannelId FROM settings where guild={ctx.guild.id}")
        channelId = cursor.fetchone()[0]
        if channelId != '' and channelId != 0:
            embed_obj = await EmbedCreate(description=f'Категория приватных каналов уже создана.',
                                          color=Config.yellowCol,
                                          footerText=Utils.RequestedText(ctx.author))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        categ = await ctx.guild.create_category("Приватные")
        channel = await ctx.guild.create_voice_channel("🔒｜Создать", category=categ)
        cursor.execute(f'UPDATE settings SET privateChannelId=? where guild=?', (channel.id, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Категория приватных каналов создана.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @pcreate.error
    async def pcreate_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setnoxp(self, ctx, *ids):
        no_xp_channels = ''
        for id in ids:
            no_xp_channels += f'{id} '

        cursor.execute(f'UPDATE settings SET noXpChanels=? where guild=?', (no_xp_channels, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Список каналов без получения опыта обновлен.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setnoxp.error
    async def setnoxp_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setxpm(self, ctx, multiplier: float, *args):
        multiplier = max(min(multiplier, 10), 0.25)
        cursor.execute(f'UPDATE settings SET xpMultiplier=? where guild=?', (multiplier, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Множитель опыта обновлен.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setxpm.error
    async def setxpm_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setxpm <множитель (0.25 - 10)>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def shopadd(self, ctx, role: discord.Role, sum: int, *args):
        if sum < 1:
            sum *= -1

        roles = [row[0] for row in cursor.execute(f"SELECT shopRoles FROM settings where guild={ctx.guild.id}")]
        roles[0] += f'{role.id} '
        costs = [row[0] for row in cursor.execute(f"SELECT shopRolesCost FROM settings where guild={ctx.guild.id}")]
        costs[0] += f'{sum} '

        cursor.execute(f'UPDATE settings SET shopRoles=? where guild=?',
                       (roles[0], ctx.guild.id))  # shopRoles shopRolesCost
        cursor.execute(f'UPDATE settings SET shopRolesCost=? where guild=?', (costs[0], ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Роль <@&{role.id}> добавлена в магазин со стоимостью {sum} :gem:',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @shopadd.error
    async def shopadd_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!shopadd @role <сумма>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def shopdel(self, ctx, num: int, *args):
        num -= 1
        roles = [row[0] for row in cursor.execute(f"SELECT shopRoles FROM settings where guild={ctx.guild.id}")]
        rolesArray = roles[0].split(" ")
        del rolesArray[-1]
        del rolesArray[num]
        newRoles = ''
        for r in rolesArray:
            newRoles += f'{r} '

        costs = [row[0] for row in cursor.execute(f"SELECT shopRolesCost FROM settings where guild={ctx.guild.id}")]
        costsArray = costs[0].split(" ")
        del costsArray[-1]
        del costsArray[num]
        newCosts = ''
        for c in costsArray:
            newCosts += f'{c} '

        cursor.execute(f'UPDATE settings SET shopRoles=? where guild=?',
                       (newRoles, ctx.guild.id))  # shopRoles shopRolesCost
        cursor.execute(f'UPDATE settings SET shopRolesCost=? where guild=?', (newCosts, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Роль под номером `{num + 1}` удалена из магазина.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @shopdel.error
    async def shopdel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!shopadd <номер>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setm(self, ctx, count: int, *args):
        count = max(count, 0)
        cursor.execute(f'UPDATE settings SET maxMembers=? where guild=?', (count, ctx.guild.id))
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Значение изменено.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setm.error
    async def setm_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setm <множитель (0 = без ограничения)>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addchannelstat(self, ctx, typeStat: str, *args):
        if typeStat != 'members' and typeStat != 'online' and typeStat != 'voice' and typeStat != 'bots':
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!addchannelstat <members/online/voice/bots>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        channel = await ctx.guild.create_voice_channel(await Utils.GetGuildStat(ctx.guild, typeStat))
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        cursor.execute(f'INSERT INTO voice VALUES ({ctx.guild.id}, {channel.id}, "{typeStat}")')
        conn.commit()

        embed_obj = await EmbedCreate(description=f'Канал статистики создан.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx.author))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @addchannelstat.error
    async def addchannelstat_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!addchannelstat <members/online/voice/bots>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(SettingsCommands(bot))
