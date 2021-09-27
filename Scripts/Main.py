from datetime import datetime, timedelta
import re
from random import randint

import discord
from discord import utils
from discord.ext import commands
import traceback
import sys
import sqlite3
import os

import logging

from discord.ext.commands import CommandNotFound

import Utils, Config, DataBase
from ModerCommands import ModerCommands
from Utils import EmbedCreate

from discord_slash import SlashCommand

intents = discord.Intents.all()
# intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
slash = SlashCommand(bot)

bot.remove_command("help")

DISCORD_TOKEN = 'YOUR_TOKEN'

initial_extensions = ['Events', 'UserCommands', 'SettingsCommands', 'AdminCommands', 'ModerCommands', 'PrivateChannelsCommands']

StartUpTime = datetime.today()

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

last_Messages = []
serverMonitoringBotId = 315926021457051650
dsMonitoringBotId = 575776004233232386
sdcMonitoring = 464272403766444044
dBookBotId = 612285534458609718


@bot.event
async def on_message(message: discord.Message):
    if not message.author.bot:
        spamChannel = False
        row = DataBase.getDataFromDB('settings', 'spamChannels', f'guild={message.guild.id}')

        if row[0] is not None:
            spamChannels = row[0].split(' ')
            for channel in spamChannels:
                if channel == f'{message.channel.id}':
                    spamChannel = True

        if not spamChannel:
            i = 0
            msg_founded = False
            while i < len(last_Messages):
                if last_Messages[i][0] == message.author.id:
                    if last_Messages[i][1] == message.content:
                        last_Messages[i][2] += 1
                        if last_Messages[i][2] > 5:
                            await ModerCommands.send_warn(bot, bot, message.guild.get_member(bot.user.id), message.channel, message.author, 'спам')
                            await message.delete()
                            return
                        elif last_Messages[i][2] > 3:
                            embed_obj = await EmbedCreate(color=Config.redCol,
                                                          author=f'{message.author.name} | Флудить не хорошо',
                                                          authorAvatar=message.author.avatar_url)
                            await message.channel.send(embed=embed_obj)
                            await message.delete()
                            return

                    else:
                        last_Messages[i][1] = message.content
                        last_Messages[i][2] = 1

                    msg_founded = True
                    break

                i += 1

            if not msg_founded:
                last_Messages.append([message.author.id, message.content, 1])

            # Check Link
            if not Utils.check_admin_roles_from_user(message.author) or (message.content == '' and len(message.attachments) > 0):
                hasLink = False
                match = re.findall(r'https?://[\w.-]+/?[\w.-]*', message.content)
                availableLinks = ['https://cdn.discordapp.com/attachments', 'https://cdn.discordapp.com/avatars',
                                  'https://media.discordapp.net/attachments',
                                  'https://tenor.com/view', 'https://tenor.com/view', 'https://www.youtube.com/watch',
                                  'http://cdn.discordapp.com/attachments',
                                  'http://cdn.discordapp.com/avatars',
                                  'http://media.discordapp.net/attachments',
                                  'http://tenor.com/view', 'http://tenor.com/view', 'http://www.youtube.com/watch',
                                  'http://c.tenor.com/', 'https://c.tenor.com/'
                                  ]
                for invite in await message.guild.invites():
                    availableLinks.append(f'https://discord.gg/{invite.code}')

                for link in match:
                    for availableLink in availableLinks:
                        if link != '' and link.startswith(availableLink):
                            break
                    else:
                        hasLink = True
                        break

                if hasLink:
                    embed_obj = await EmbedCreate(color=Config.redCol,
                                                  author=f'{message.author.name} | Ккидать ссылки запрещено',
                                                  authorAvatar=message.author.avatar_url)
                    await message.channel.send(embed=embed_obj)
                    await message.delete()
                    return


        row = DataBase.getDataFromDB('settings', 'commandsChannel', f'guild={message.guild.id}')
        command = message.content.split(' ')[0]
        if row[0] is not None and not Utils.check_admin_roles_from_user(message.author):
            for c in row[0].split(','):
                arr = c.split('~')
                if len(arr) >= 2 and f'{bot.command_prefix}{arr[0]}' == command:
                    for channel in arr[1].split(' '):
                        if channel == f'{message.channel.id}':
                            break
                    else:
                        return
                    break

        time = DataBase.getDataFromDB('users', 'msgXpTime', f'id={message.author.id} AND guild={message.guild.id}')
        r = [0,0]
        if time is not None:
            timeOut = datetime.strptime(time[0], '%Y-%m-%d %H:%M:%S.%f')
            c = timeOut - datetime.today()
            r = divmod(c.days * 86400 + c.seconds, 60)
        if r[0] < 0 or r[1] < 0 or time is None:
            try:
                msgXpTime, id, guild = datetime.today() + timedelta(minutes=1), message.author.id, message.guild.id
                await DataBase.updateDataInDB('users', f'msgXpTime={msgXpTime}', f'id={id} AND guild={guild}')
            except Exception:
                pass

            multiplier = DataBase.getDataFromDB('settings', 'xpMultiplier', f'guild={message.guild.id}')

            await Utils.xpadd(randint(15, 25) * multiplier[0], message.author)

        await bot.process_commands(message)


    if message.author.id == serverMonitoringBotId and len(message.embeds) > 0:
        matches = re.search('Server bumped by (<@([0-9]*)>)', message.embeds[0].description)
        if matches is not None:
            member = message.guild.get_member(int(matches.group(2)))
            await Utils.addMoneyToUser(member, message.guild.id, 400)

    elif message.author.id == dsMonitoringBotId and len(message.embeds) > 0:
        if message.embeds[0].description.startswith('You successfully liked the server.'):
            author = message.embeds[0].author.name.split('#')
            member = utils.get(bot.get_all_members(), name=author[0], discriminator=author[1])
            await Utils.addMoneyToUser(member, message.guild.id, 400)

    elif message.author.id == sdcMonitoring and len(message.embeds) > 0:
        if message.embeds[0].title == 'Сервер Up':
            author = message.embeds[0].footer.text.split('#')
            member = utils.get(bot.get_all_members(), name=author[0], discriminator=author[1])
            await Utils.addMoneyToUser(member, message.guild.id, 400)

    elif message.author.id == dBookBotId and message.content.endswith('liked this server!'):
        matches = re.search('(<@([0-9]*)>)', message.content)
        if matches is not None:
            member = message.guild.get_member(int(matches.group(2)))
            await Utils.addMoneyToUser(member, message.guild.id, 800)

bot.run(DISCORD_TOKEN)
