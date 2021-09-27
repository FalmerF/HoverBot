import discord
from discord.ext import commands
import sqlite3

from discord_slash import ButtonStyle
from discord_slash.utils import manage_components

import Config
from datetime import datetime, timedelta
import os
import Utils
import DataBase
import re
from Utils import EmbedCreate, ArgumentsEmbedCreate, AccessEmbedCreate

last_Messages = []


class SettingsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def helpsettings(self, ctx, *args):
        embed_obj = discord.Embed(title="**Информация о доп. командах**", color=Config.embedCol)
        embed_obj.add_field(name="`!setmoderroles`", value=f"Устанавливает роли Модераторов.")
        embed_obj.add_field(name="`!seteventsroles`", value=f"Устанавливает роли проводящих Ивенты.")
        embed_obj.add_field(name="`!pcreate`", value=f"Создает категорию приватных каналов.")
        embed_obj.add_field(name="`!setnoxp`",
                            value=f"Устанавливает каналы с которых пльзователь не будет получать опыт.")
        embed_obj.add_field(name="`!setspam`", value=f"Устанавливает каналы в которых не работает спам фильтр.")
        embed_obj.add_field(name="`!shopadd`", value=f"Добавляет новую роль в магазин.")
        embed_obj.add_field(name="`!shopdel`", value=f"Удаляет роль с магазина.")
        embed_obj.add_field(name="`!setxpm`", value=f"Устанавливает множитель опыта.")
        embed_obj.add_field(name="`!setm`", value=f"Устанавливает максимальный множитель опыта от количества участников в голосовом канале.")
        embed_obj.add_field(name="`!addchannelstat`", value=f"Создает канал со статистикой.")
        embed_obj.add_field(name="`!сс`", value=f"Ограничить команду для определенных каналов.")
        embed_obj.add_field(name="`!setaudit`", value=f"Установить канал аудита.")
        embed_obj.add_field(name="`!setXpBoostRole` | `!sxbr`", value=f"Установить множитель опыта для роли.")
        embed_obj.add_field(name="`!setMoneyBoostRole` | `!smbr`", value=f"Установить множитель денег для роли.")
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

    @helpsettings.error
    async def helpsettings_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole) or isinstance(error, commands.errors.CheckFailure):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx, *args):
        row = DataBase.getDataFromDB('settings', 'privateChannelId, noXpChanels, ModerRoles, xpMultiplier, commandsChannel, spamChannels, muteRole, audit, xpBoostRoles, moneyBoostRoles, eventsRoles', f'guild={ctx.guild.id}')
        embed_obj = discord.Embed(title="**Настройки бота**", color=Config.embedCol)

        mentions_text = await Utils.get_mentions(row[2], ' ', '<@&id>')
        embed_obj.add_field(name="Роли Модерации", value=mentions_text)

        mentions_text = await Utils.get_mentions(row[10], ' ', '<@&id>')
        embed_obj.add_field(name="Роли для Ивентов", value=mentions_text)

        mentions_text = await Utils.get_mentions(row[1], ' ', '<#id>')
        embed_obj.add_field(name="No XP каналы", value=mentions_text)

        mentions_text = await Utils.get_mentions(row[5], ' ', '<#id>')
        embed_obj.add_field(name="Spam каналы", value=mentions_text)

        if row[0] is not None and row[0] != 0:
            embed_obj.add_field(name="Приватный канал", value=f'<#{row[0]}>')

        embed_obj.add_field(name=f'Множитель опыта: `{row[3]}x`', value='-')

        if row[6] is not None:
            embed_obj.add_field(name=f'Мьют роль:', value=f'<@&{row[6]}>')

        if row[7] is not None:
            embed_obj.add_field(name=f'Канал аудита:', value=f'<#{row[7]}>')

        if row[8] is not None and row[8] != '':
            value = ''
            for roleData in row[8].split(' '):
                if roleData != '':
                    data = roleData.split('=')
                    value += f'<@&{data[0]}> `{data[1]}x` '
            embed_obj.add_field(name=f'Множители опыта ролей', value=value)

        if row[9] is not None and row[9] != '':
            value = ''
            for roleData in row[9].split(' '):
                if roleData != '':
                    data = roleData.split('=')
                    value += f'<@&{data[0]}> `{data[1]}x` '
            embed_obj.add_field(name=f'Множители денег ролей', value=value)

        if row[4] is not None:
            val = ''
            for c in row[4].split(','):
                arr = c.split('~')
                if len(arr) >= 2:
                    channels = ''
                    for channel in arr[1].split(' '):
                        if channel != '' and channel != ' ':
                            channels += f'<#{channel}>'
                    val += f'`{arr[0]}` - {channels}\n'

            embed_obj.add_field(name=f'Каналы для команд', value=val, inline=False)

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

        DataBase.updateDataInDB('settings', f'ModerRoles={rolesId}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Список ролей модерации изменен.', color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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
    async def seteventsroles(self, ctx, *roles: discord.Role):
        rolesId = ''
        for role in roles:
            rolesId += f'{role.id} '

        if len(roles) == 0:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!seteventsroles @roles`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return 0

        DataBase.updateDataInDB('settings', f'eventsRoles={rolesId}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Список ролей для ивентов изменен.', color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @seteventsroles.error
    async def seteventsroles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!seteventsroles @roles`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pcreate(self, ctx, *args):
        channelId = DataBase.getDataFromDB('settings', 'privateChannelId', f'guild={ctx.guild.id}')[0]
        if channelId != '' and channelId != 0:
            embed_obj = await EmbedCreate(description=f'Категория приватных каналов уже создана.',
                                          color=Config.yellowCol,
                                          footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        categ = await ctx.guild.create_category("Приватные")
        channel = await ctx.guild.create_voice_channel("🔒｜Создать", category=categ)
        DataBase.updateDataInDB('settings', f'privateChannelId={channel.id}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Категория приватных каналов создана.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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

        DataBase.updateDataInDB('settings', f'noXpChanels="{no_xp_channels}"', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Список каналов без получения опыта обновлен.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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
        DataBase.updateDataInDB('settings', f'xpMultiplier={multiplier}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Множитель опыта обновлен.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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

        roles = [row[0] for row in DataBase.getDataFromDB('settings', 'shopRoles', f'guild={ctx.guild.id}', 'all')]
        roles[0] = f'{roles[0]}{role.id} '
        costs = [row[0] for row in DataBase.getDataFromDB('settings', 'shopRolesCost', f'guild={ctx.guild.id}', 'all')]
        costs[0] = f'{costs[0]}{sum} '

        DataBase.updateDataInDB('settings', f'shopRoles="{roles[0]}"', f'guild={ctx.guild.id}')
        DataBase.updateDataInDB('settings', f'shopRolesCost="{costs[0]}"', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Роль <@&{role.id}> добавлена в магазин со стоимостью **{sum}** {Config.money_reaction}',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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
        roles = [row[0] for row in DataBase.getDataFromDB('settings', 'shopRoles', f'guild={ctx.guild.id}', 'all')]
        rolesArray = roles[0].split(" ")

        del rolesArray[-1]
        del rolesArray[num]
        newRoles = ''
        for r in rolesArray:
            newRoles += f'{r} '

        costs = [row[0] for row in DataBase.getDataFromDB('settings', 'shopRolesCost', f'guild={ctx.guild.id}', 'all')]
        costsArray = costs[0].split(" ")
        del costsArray[-1]
        del costsArray[num]
        newCosts = ''
        for c in costsArray:
            newCosts += f'{c} '

        DataBase.updateDataInDB('settings', f'shopRoles="{newRoles}"', f'guild={ctx.guild.id}')
        DataBase.updateDataInDB('settings', f'shopRolesCost="{newCosts}"', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Роль под номером `{num + 1}` удалена из магазина.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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
        DataBase.updateDataInDB('settings', f'maxMembers={count}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Значение изменено.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
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
    async def addchannelstat(self, ctx, *typeStat: str):
        pattern = ''
        for s in typeStat:
            pattern += f'{s} '

        channel = await ctx.guild.create_voice_channel(await Utils.GetGuildStat(ctx.guild, pattern))
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        DataBase.insertDataInDB('voice', f'{ctx.guild.id}, {channel.id}, "{pattern}", "0"')

        embed_obj = await EmbedCreate(description=f'Канал статистики создан.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @addchannelstat.error
    async def addchannelstat_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!addchannelstat <pattern>`\n\n'
                                                        f'**Переменные:**\n'
                                                        f'`%members%` - количество участников сервера.\n'
                                                        f'`%bots%` - количество ботов на сервере.\n'
                                                        f'`%online%` - количество онлайн пользователей.\n'
                                                        f'`%voice%` - количество пользователей в голосовых каналах.')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def cc(self, ctx, command, *channels: str):
        channelsId = ''
        channelsMention = ''
        clear = len(channels) >= 1 and channels[0] == 'clear'
        for channel in channels:
            channelsId += f'{channel} '
            channelsMention += f'<#{channel}>'

        if len(channels) == 0:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!cc <command> <channels>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return 0

        row = DataBase.getDataFromDB('settings', 'commandsChannel', f'guild={ctx.guild.id}')
        commands = ''
        if row[0] is not None:
            commands = row[0].split(',')

        newCommands = ''
        commandFind = False

        for c in commands:
            arr = c.split('~')
            if arr[0] == command:
                commandFind = True
                if channelsId != '' and not clear:
                    newCommands += f'{arr[0]}~{channelsId},'
            elif len(arr) >= 2:
                newCommands += f'{arr[0]}~{arr[1]},'

        if not commandFind:
            newCommands += f'{command}~{channelsId},'

        DataBase.updateDataInDB('settings', f'commandsChannel="{newCommands}"', f'guild={ctx.guild.id}')

        if not clear:
            embed_obj = await EmbedCreate(description=f'Установлены каналы доступные для комманды `{command}`: {channelsMention}', color=Config.blueCol,
                                          footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
        else:
            embed_obj = await EmbedCreate(description=f'Очищены каналы доступные для комманды `{command}`', color=Config.blueCol,
                                          footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)

        await ctx.message.delete()

    @cc.error
    async def cc_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!cc <command> <channels/clear>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setspam(self, ctx, *ids):
        spam_channels = ''
        for id in ids:
            spam_channels += f'{id} '

        DataBase.updateDataInDB('settings', f'spamChannels="{spam_channels}"', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Список каналов без спам фильтра изменен.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setspam.error
    async def setspam_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def muterole(self, ctx, role: discord.Role):
        DataBase.updateDataInDB('settings', f'muteRole={role.id}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Роль мьюта изменена на <@&{role.id}>.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @muterole.error
    async def muterole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!muterole <@role>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setaudit(self, ctx, id: int):
        DataBase.updateDataInDB('settings', f'audit={id}', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Канал аудита установлен <#{id}>.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setaudit.error
    async def setaudit_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setaudit <канал>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command(aliases=['setxpboostrole', 'sxbr'])
    @commands.has_permissions(administrator=True)
    async def setXpBoostRole(self, ctx, role: discord.Role, multiplier: float):
        row = DataBase.getDataFromDB('settings', f'xpBoostRoles', f'guild={ctx.guild.id}')
        rolesData = row[0]
        match = re.search(f'{role.id}=([0-9.]*)', rolesData)
        if match is not None:
            if multiplier != 1.0:
                rolesData = rolesData.replace(f'{role.id}={match.group(1)}', f'{role.id}={multiplier}')
            else:
                rolesData = rolesData.replace(f'{role.id}={match.group(1)} ', '')
        elif multiplier != 1.0:
            rolesData += f'{role.id}={multiplier} '
        DataBase.updateDataInDB('settings', f'xpBoostRoles="{rolesData}"', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Для роли <@&{role.id}> установлен множитель опыта `{multiplier}x`.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setXpBoostRole.error
    async def setXpBoostRole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setXpBoostRole <@роль> <множитель>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()

    @commands.command(aliases=['setmoneyboostrole', 'smbr'])
    @commands.has_permissions(administrator=True)
    async def setMoneyBoostRole(self, ctx, role: discord.Role, multiplier: float):
        row = DataBase.getDataFromDB('settings', f'moneyBoostRoles', f'guild={ctx.guild.id}')
        rolesData = row[0]
        match = re.search(f'{role.id}=([0-9.]*)', rolesData)
        if match is not None:
            if multiplier != 1.0:
                rolesData = rolesData.replace(f'{role.id}={match.group(1)}', f'{role.id}={multiplier}')
            else:
                rolesData = rolesData.replace(f'{role.id}={match.group(1)} ', '')
        elif multiplier != 1.0:
            rolesData += f'{role.id}={multiplier} '
        DataBase.updateDataInDB('settings', f'moneyBoostRoles="{rolesData}"', f'guild={ctx.guild.id}')

        embed_obj = await EmbedCreate(description=f'Для роли <@&{role.id}> установлен множитель денег `{multiplier}x`.',
                                      color=Config.blueCol,
                                      footerText=Utils.RequestedText(ctx))
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()

    @setMoneyBoostRole.error
    async def setMoneyBoostRole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_obj = await AccessEmbedCreate(ctx)
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'`!setMoneyBoostRole <@роль> <множитель>`')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(SettingsCommands(bot))
