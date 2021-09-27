import re

import discord
import sqlite3
from datetime import datetime, timedelta
import os

from discord import utils
from pip._vendor import requests

import Config
import math
from PIL import Image, ImageFilter
from PIL import ImageFont
from PIL import ImageDraw

from io import BytesIO

import DataBase


async def add_New_User(user: discord.User, guild_id: int):
    DataBase.insertDataInDB('users', f'{user.id}, 0, 0, {guild_id}, 0, 0, 0, "{datetime.today()}", "", {Config.startReputation}')


async def add_New_Guild(guild_id: int):
    DataBase.insertDataInDB('settings', f'{guild_id}, 0, 0, "", "", 0, 1, 0, "", "", "", "", "", ""')


async def member_voice_xp_add(member: discord.Member, multiplier_members: int):
    row = DataBase.getDataFromDB('users', 'enterTime', f'id={member.id} AND guild={member.guild.id}')
    duration = timedelta(seconds=0)
    if row != None:
        duration = datetime.today() - datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')

    row = DataBase.getDataFromDB('settings', 'xpMultiplier, maxMembers', f'guild={member.guild.id}')
    multiplier = row[0]
    maxMembers = row[1]

    # money = DataBase.getDataFromDB('users', 'money', f'id={member.id} AND guild={member.guild.id}', 'all')[0]
    # money += int((duration.seconds/60)*6)
    # DataBase.updateDataInDB('users', f'money={money}', f'id={member.id} AND guild={member.guild.id}')
    # Удалить, если все работает!
    await addMoneyToUser(member, member.guild.id, int((duration.seconds / 60 * 6)))

    multiplier_members = min(multiplier, maxMembers)
    if multiplier_members == 1:
        multiplier_members = 0

    await xpadd(int(6 * (duration.seconds / 60) * multiplier * multiplier_members), member)

    voiceSeconds = 0
    row = DataBase.getDataFromDB('users', 'voice', f'id={member.id} AND guild={member.guild.id}')
    if row is not None:
        voiceSeconds = row[0]

    DataBase.updateDataInDB('users', f'voice="{voiceSeconds + duration.seconds}"', f'id={member.id} AND guild={member.guild.id}')
    DataBase.updateDataInDB('users', f'enterTime="{datetime.today()}"', f'id={member.id} AND guild={member.guild.id}')


async def shop_get(page: int, guild_id: int):
    desc = ''
    roles = [row[0] for row in DataBase.getDataFromDB('settings', 'shopRoles', f'guild={guild_id}', 'all')]
    rolesArray = roles[0].split(" ")
    del rolesArray[-1]
    costs = [row[0] for row in DataBase.getDataFromDB('settings', 'shopRolesCost', f'guild={guild_id}', 'all')]
    costsArray = costs[0].split(" ")
    del costsArray[-1]

    maxPage = math.floor(len(rolesArray) / 10)
    if len(rolesArray) % 10 > 0:
        maxPage += 1

    page = max(1, min(page, maxPage))

    num = 10 * page
    i = num - 10
    embed_obj = discord.Embed(title="**Магазин Ролей**", color=Config.embedCol)
    while i < num:
        if i < len(rolesArray):
            desc += f'**#{i + 1}.** <@&{rolesArray[i]}> **- {makePointedNumber(costsArray[i])}** {Config.money_reaction}\n'

        i += 1

    embed_obj.set_footer(text=f"!buy <номер>")
    embed_obj.description = desc
    embed_obj.set_author(name=f'Страница {page} из {maxPage}')
    return embed_obj


def makePointedNumber(arg: str):
    charsList = list(f'{arg}')
    i = len(charsList)-1
    numbersCounter = 0
    pointedNumber = ''
    while i >= 0:
        pointedNumber = charsList[i] + pointedNumber
        numbersCounter += 1
        if i != 0 and numbersCounter % 3 == 0:
            pointedNumber = f'.{pointedNumber}'
        i -= 1
    return pointedNumber


async def xpadd(xp: int, member: discord.Member, useMultiplier=True):
    if member.bot:
        return

    id = member.id
    playerXp = 0
    level = 0
    multiplier = 1.0

    if useMultiplier:
        multiplier = await getMultiplierFromMemberRoles(member, False)
    row = DataBase.getDataFromDB('users', 'xp', f'id={id} AND guild={member.guild.id}')
    if row is not None:
        playerXp = row[0]
    playerXp += xp*multiplier
    playerXp = round(playerXp)

    row = DataBase.getDataFromDB('users', 'level', f'id={id} AND guild={member.guild.id}')
    if row is not None:
        level = row[0]
    oldLevel = level
    giveNextRole = False

    while True:
        xpToLevel = Config.RANKS[f'{min(level + 1, 1000)}']
        if level == 1000:
            playerXp = 0
            break

        if xpToLevel <= playerXp:
            playerXp -= xpToLevel
            level += 1
            levelChanged = True
            DataBase.updateDataInDB('users', f'level={level}', f'id={id} AND guild={member.guild.id}')
        else:
            break

    for roleLevel in Config.levelDict:
        if oldLevel < roleLevel <= level:
            giveNextRole = True
            break

    if giveNextRole:
        i = len(Config.levelDict)-1
        while i >= 0:
            if level >= Config.levelDict[i]:
                await removeAllLevelRolesFromMember(member)
                role = utils.get(member.guild.roles, id=Config.rolesPerLevel[Config.levelDict[i]])
                await member.add_roles(role)
                break
            i -= 1

    DataBase.updateDataInDB('users', f'xp={playerXp}', f'id={id} AND guild={member.guild.id}')


async def getMultiplierFromMemberRoles(member: discord.Member, moneyMultiplier: bool):
    row = None
    if moneyMultiplier:
        row = DataBase.getDataFromDB('settings', f'moneyBoostRoles', f'guild={member.guild.id}')
    else:
        row = DataBase.getDataFromDB('settings', f'xpBoostRoles', f'guild={member.guild.id}')

    multiplier = 1.0
    for roleData in row[0].split(' '):
        if roleData != '':
            data = roleData.split('=')
            for role in member.roles:
                if f'{role.id}' == data[0] and float(data[1]) > multiplier:
                    multiplier = float(data[1])
    return multiplier


async def removeAllLevelRolesFromMember(member):
    for key in Config.rolesPerLevel:
        try:
            role = utils.get(member.guild.roles, id=Config.rolesPerLevel[key])
            member.roles.index(role)
            await member.remove_roles(role)
        except Exception:
            pass


async def EmbedCreate(description='', title='', color='', author='', authorAvatar='', thumbnailUrl='', imageUrl='', footerText='', footerUrl='', fields=[['', '', False]]):
    embed_obj = discord.Embed(title=title, color=color)
    embed_obj.set_author(name=author, icon_url=authorAvatar)
    embed_obj.set_thumbnail(url=thumbnailUrl)
    embed_obj.set_image(url=imageUrl)
    embed_obj.set_footer(text=footerText, icon_url=footerUrl)
    embed_obj.description = description
    for field in fields:
        if field[0] != '' and field[1] != '':
            embed_obj.add_field(name=field[0], value=field[1], inline=field[2])

    return embed_obj


async def ArgumentsEmbedCreate(ctx, description=''):
    embed_obj = discord.Embed(title='Неверно указаны аргументы', color=Config.yellowCol)
    embed_obj.set_footer(text=f'Запросил {ctx.author.name}#{ctx.author.discriminator}')
    embed_obj.description = description
    return embed_obj


async def AccessEmbedCreate(ctx):
    embed_obj = discord.Embed(color=Config.redCol)
    embed_obj.set_author(name=f'{ctx.author.name} | Не достаточно прав', icon_url=ctx.author.avatar_url)
    return embed_obj


def keyFunc(item):
   return item[1]

def keyFunc2(item):
   return item[2]

def keyFunc3(item):
   return item[3]

def keyFunc4(item):
   return item[4]


async def topget(page: int, type: str, guild: discord.Guild):
    Ids = []

    guild_id = guild.id

    users = DataBase.getDataFromDB('users', 'id, level, voice, money, reputation', f'guild={guild_id}', 'all')
    for row in users:
        member = guild.get_member(int(row[0]))
        if member is not None and not member.bot and not check_admin_roles_from_user(member):
            Ids.append((row[0], row[1], row[2], row[3], row[4]))

    if type == "level":
        Ids.sort(key=keyFunc, reverse=True)
    elif type == "voice":
        Ids.sort(key=keyFunc2, reverse=True)
    elif type == "money":
        Ids.sort(key=keyFunc3, reverse=True)
    elif type == "rep":
        Ids.sort(key=keyFunc4, reverse=True)

    maxPage = math.floor(len(Ids)/10)
    if len(Ids)%10 > 0:
        maxPage += 1

    page = max(1, min(page, maxPage))

    num = 10 * page
    i = num-10
    embed_obj = discord.Embed()
    embed_obj.set_thumbnail(url=guild.icon_url)

    while i < num:
        if i < len(Ids):
            id = Ids[i][0]
            level = Ids[i][1]
            voice = Ids[i][2]
            money = Ids[i][3]
            reputation = Ids[i][4]
            if id != 0:
                member = guild.get_member(int(id))
                if member is None:
                    i += 1
                    continue

                h = math.floor(int(voice) / 3600)
                m = math.floor((int(voice) % 3600) / 60)
                s = int(voice) % 60

                hTxt = f'{h}'
                mTxt = f'{m}'
                sTxt = f'{s}'

                if h < 10:
                    hTxt = f'0{h}'
                if m < 10:
                    mTxt = f'0{m}'
                if s < 10:
                    sTxt = f'0{s}'
                embed_obj.add_field(
                    name=f'**#{i + 1}.** {member.display_name}',
                    value=f'Уровень: `{level}`  |  {Config.reputation_reaction} `{reputation}`  |  {Config.money_reaction} `{money}`  |  :microphone: `{hTxt}:{mTxt}:{sTxt}`',
                    inline=False)

        i += 1

    embed_obj.set_author(name=f'Страница {page} из {maxPage} — Всего участников: {len(Ids)}')
    return embed_obj


def check_admin_roles(ctx):
    if ctx.author.guild_permissions.administrator:
        return True

    return False


def check_moder_roles(ctx):
    roles = [row[0] for row in DataBase.getDataFromDB('settings', 'ModerRoles', f'guild={ctx.guild.id}')]
    rolesArray = roles[0].split(" ")
    del rolesArray[-1]
    for role in rolesArray:
        if int(role) in [y.id for y in ctx.author.roles]:
            return True

    return check_admin_roles(ctx)


def check_admin_roles_from_user(member: discord.member):
    if member.guild_permissions.administrator:
        return True

    return False


def check_moder_roles_from_user(member: discord.member):
    roles = [row[0] for row in DataBase.getDataFromDB('settings', 'ModerRoles', f'guild={member.guild.id}')]
    rolesArray = roles[0].split(" ")
    del rolesArray[-1]
    for role in rolesArray:
        if int(role) in [y.id for y in member.roles]:
            return True

    return check_admin_roles_from_user(member)


async def pembed_list_get(page: int, guild_id: int):
    embed_obj = discord.Embed(color=Config.blueCol)
    embed_obj.title = 'Список сообщений'
    embedNames = ''
    names = []
    for row in DataBase.getDataFromDB('embed', 'nameembed', f'guild={guild_id}', 'all'):
        names.append(row[0])

    maxPage = math.floor(len(names) / 10)
    if len(names) % 10 > 0:
        maxPage += 1

    page = max(1, min(page, maxPage))
    embed_obj.set_author(name=f'Страница {page} из {maxPage}')
    num = page*10
    i = num-10
    while i < num:
        if i < len(names):
            embedNames += f'**#{i+1}.** `' + names[i] + '`\n'

        i += 1

    embed_obj.description = embedNames
    return embed_obj

async def rankMet(ctx, user: discord.member):
    row = DataBase.getDataFromDB('users', 'xp, level, voice, money', f'id={user.id} AND guild={ctx.guild.id}')
    xp = row[0]
    level = row[1]
    voice = row[2]
    money = row[3]

    if level == 1000:
        xpNeed = 1
    else:
        xpNeed = Config.RANKS[f'{min(level + 1, 1000)}']

    length = xp / (xpNeed / 100)
    length *= 8
    length = round(length)

    h = math.floor(voice / 3600)
    m = math.floor((voice % 3600) / 60)
    s = voice % 60

    hTxt = f'{h}'
    mTxt = f'{m}'
    sTxt = f'{s}'

    if h < 10:
        hTxt = f'0{h}'
    if m < 10:
        mTxt = f'0{m}'
    if s < 10:
        sTxt = f'0{s}'

    if length < 35:
        length = 35

    # Дирректория изображений
    ImgDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Images'))
    FontDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Импорт изображений
    img = Image.open(f'{ImgDir}\\RankCard.png')
    img = img.convert('RGBA')
    mic = Image.open(f'{ImgDir}\\microphone.png')
    userIcon = Image.open(f'{ImgDir}\\userIcon.png')
    diamond = Image.open(f'{ImgDir}\\diamond.png')
    response = requests.get(user.avatar_url)
    watermark = Image.open(BytesIO(response.content))


    watermark.thumbnail((200, 200), Image.ANTIALIAS)
    watermark = watermark.resize((200, 200), Image.ANTIALIAS)
    mic.thumbnail((35, 35), Image.ANTIALIAS)
    userIcon.thumbnail((35, 35), Image.ANTIALIAS)
    diamond.thumbnail((32, 32), Image.ANTIALIAS)

    draw = ImageDraw.Draw(img)

    draw.ellipse(((397, 27), (603, 233)), fill=(0, 0, 0))

    shadow = Image.new("RGBA", img.size, 0)

    draw = ImageDraw.Draw(shadow)
    draw.ellipse(((390, 20), (610, 240)), fill=(0, 0, 0, 100))

    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    img.paste(shadow, (0, 0), shadow)

    mask_im = Image.new("L", watermark.size, 0)
    draw = ImageDraw.Draw(mask_im)
    draw.ellipse(((0, 0), watermark.size), fill=255)

    img.paste(watermark, (400, 30), mask_im)
    img.paste(userIcon, (15, 25), userIcon)
    img.paste(mic, (15, 72), mic)
    img.paste(diamond, (17, 122), diamond)

    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(f'{FontDir}\\font.ttf', 30)
    draw_text_with_outline(draw, (130, 218), "ур", (255, 255, 255), font, 2)
    draw_text_with_outline(draw, (55, 27), f"{user.display_name}#{user.discriminator}", (255, 255, 255), font, 2)
    draw_text_with_outline(draw, (800 - (15 * (len(f"{xp}/{xpNeed}"))), 220), f"{xp}/{xpNeed} EXP", (255, 255, 255), font, 2)
    draw_text_with_outline(draw, (55, 75), f'{hTxt}:{mTxt}:{sTxt}', (255, 255, 255), font, 2)
    draw_text_with_outline(draw, (55, 123), f'{money}', (255, 255, 255), font, 2)
    font = ImageFont.truetype(f'{FontDir}\\font.ttf', 40)
    draw_text_with_outline(draw, (170, 213), f"{level}", (255, 255, 255), font, 2)


    barHeight = 30
    progressBackGround = round_rectangle((800, barHeight), 12, (40, 40, 40))
    mark = Image.new("RGB", (800, barHeight), (40, 40, 40))
    img.paste(mark, (100, 255), progressBackGround)

    progress = round_rectangle((length, barHeight), 12, (130, 130, 249))
    mark = Image.new("RGB", (length, barHeight), (130, 130, 249))
    img.paste(mark, (100, 255), progress)

    img.save(f'{ImgDir}\\img.png', dpi=(300, 300))
    await ctx.send(file=discord.File(f'{ImgDir}\\img.png'))
    await ctx.message.delete()


def draw_text_with_outline(draw, pos, text, color, font, outline=1):
    draw.text(pos, text, (0, 0, 0), font=font, stroke_width=outline)
    draw.text(pos, text, color, font=font)


def round_corner(radius):
    """Draw a round corner"""
    corner = Image.new('L', (radius, radius), 0)  # (25, 27, 28, 0)
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
    return corner


def round_rectangle(size, radius, fill):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = Image.new('L', size, 255)
    corner = round_corner(radius)
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, height - radius))  # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle


async def get_mentions(ids: str, separator: str, mention: str):
    ids_array = ids.split(separator)
    mention_text = ''
    if len(ids_array) > 0:
        for id in ids_array:
            if id != '' and id != '0':
                if mention_text != '':
                    mention_text += ' - '

                mention_text += f'{mention.replace("id", id)}'

    if mention_text == '':
        mention_text = '-'
    return mention_text


def RequestedText(ctx):
    return f'Запросил {ctx.author.name}#{ctx.author.discriminator} | {ctx.bot.command_prefix}{ctx.command}'

def RequestedTextCustom(member, command, bot):
    return f'Запросил {member.name}#{member.discriminator} | {bot.command_prefix}{command}'


def AddEventedMessage(ctx, message: discord.Message, type: str, time: int = Config.time_delete_msg):
    DataBase.insertDataInDB('messages', f'{message.guild.id}, {message.id}, {message.channel.id}, "{type}", "{datetime.today() + timedelta(seconds=time)}", {ctx.author.id}')


def EmbedParseVars(ctx, message: str, space: bool = True):
    message = message.replace('{author.name}', f'{ctx.author.name}')
    message = message.replace('{author.display_name}', f'{ctx.author.display_name}')
    message = message.replace('{author.discriminator}', f'{ctx.author.discriminator}')
    message = message.replace('{author.color}', f'{ctx.author.color}')
    message = message.replace('{author.avatar_url}', f'{ctx.author.avatar_url}')
    message = message.replace('{author.id}', f'{ctx.author.id}')
    message = message.replace('{author.mention}', f'{ctx.author.mention}')
    message = message.replace('{guild.name}', f'{ctx.guild.name}')
    message = message.replace('{guild.members}', f'{len(ctx.guild.members)}')
    message = message.replace('{guild.channels}', f'{len(ctx.guild.channels)}')
    message = message.replace('{guild.created_at}', f'{ctx.guild.created_at}')
    message = message.replace('{guild.owner}', f'{ctx.guild.owner.mention}')
    message = message.replace('{guild.owner.discriminator}', f'{ctx.guild.owner.discriminator}')
    if space:
        message = message.replace('_', f' ')
    return message


async def ProfileCreate(ctx, user: discord.member):
    row = DataBase.getDataFromDB('users', 'xp, level, voice, money, badges, reputation', f'id={user.id} AND guild={ctx.guild.id}')
    xp = row[0]
    level = row[1]
    voice = row[2]
    money = row[3]
    badges = row[4]
    reputation = row[5]

    if level == 1000:
        xpNeed = 1
    else:
        xpNeed = Config.RANKS[f'{min(level + 1, 1000)}']

    length = xp / (xpNeed / 100)
    length *= 8
    length = round(length)

    h = math.floor(voice / 3600)
    m = math.floor((voice % 3600) / 60)
    s = voice % 60

    hTxt = f'{h}'
    mTxt = f'{m}'
    sTxt = f'{s}'

    if h < 10:
        hTxt = f'0{h}'
    if m < 10:
        mTxt = f'0{m}'
    if s < 10:
        sTxt = f'0{s}'

    if length < 35:
        length = 35

    embed_obj = discord.Embed()
    embed_obj.title = f'Профиль {user.name}#{user.discriminator}'
    embed_obj.set_footer(text=RequestedText(ctx))
    embed_obj.set_thumbnail(url=user.avatar_url)
    embed_obj.add_field(name=f'Упоминание', value=f'<@{user.id}>')
    embed_obj.add_field(name=f'Активность', value=f'''・Уровень: **{level}**
    ・Опыт: **{xp}/{xpNeed}**
    ・Голос: **{hTxt}:{mTxt}:{sTxt}**
    ''', inline=False)
    embed_obj.add_field(name=f'Баланс', value=f'''・**{makePointedNumber(money)}** {Config.money_reaction}
        ''', inline=True)
    embed_obj.add_field(name=f'Репутация', value=f'''・**{reputation}** {Config.reputation_reaction}
        ''', inline=True)
    if ((badges != '') and (badges != None)):
        embed_obj.add_field(name=f'Значки', value=f'''・{badges}
                ''', inline=True)

    return embed_obj


async def GetGuildStat(guild: discord.Guild, statType: str):
    members = 0
    bots = 0
    online = 0
    voice = 0
    for m in guild.members:
        if m.bot is True:
            bots += 1
        else:
            members += 1
            if m.status != discord.Status.offline:
                online += 1

    for v in guild.voice_channels:
        for user in v.members:
            if not user.bot:
                voice += 1

    return statType.replace('%members%', f'{members}').replace('%bots%', f'{bots}').replace('%online%', f'{online}').replace('%voice%', f'{voice}')


async def ParseStringToTime(*time):
    d = 0
    h = 0
    m = 0
    s = 0
    month = 0
    y = 0

    yText = ['years', 'year', 'y', 'года', 'год', 'г', 'лет']
    monthText = ['mo', 'mos', 'month', 'months', 'мес', 'месяц', 'месяца', 'месяцев']
    dText = ['d', 'day', 'days', 'д', 'день', 'дня', 'дней']
    hText = ['h', 'hour', 'hours', 'ч', 'час', 'часа', 'часов']
    mText = ['m', 'min', 'mins', 'minute', 'minutes', 'мин', 'минута', 'минуту', 'минуты', 'минут']
    sText = ['s', 'sec', 'secs', 'second', 'seconds', 'c', 'сек', 'секунда', 'секунду', 'секунды', 'секунд']

    for timeElement in time:
        if FindWithArray(timeElement, *sText):
            # print(f'Sec: {timeElement}')
            timeElement = re.findall(r'\d+', timeElement)[0]
            s = int(timeElement)

        elif FindWithArray(timeElement, *monthText):
            # print(f'Month: {timeElement}')
            timeElement = re.findall(r'\d+', timeElement)[0]
            month = int(timeElement)

        elif FindWithArray(timeElement, *mText):
            # print(f'Min: {timeElement}')
            timeElement = re.findall(r'\d+', timeElement)[0]
            m = int(timeElement)

        elif FindWithArray(timeElement, *hText):
            # print(f'Hours: {timeElement}')
            timeElement = re.findall(r'\d+', timeElement)[0]
            h = int(timeElement)

        elif FindWithArray(timeElement, *dText):
            # print(f'Days: {timeElement}')
            timeElement = re.findall(r'\d+', timeElement)[0]
            d = int(timeElement)

        elif FindWithArray(timeElement, *yText):
            # print(f'Years: {timeElement}')
            timeElement = re.findall(r'\d+', timeElement)[0]
            y = int(timeElement)

    d += y * 365
    d += month * 31

    return timedelta(days=d, seconds=s, minutes=m, hours=h)


def FindWithArray(text: str, *array):
    for a in array:
        if text.find(f'{a}') != -1:
            return True
    return False


async def ParseTimeToString(time: timedelta, full = False):
    totalSec = time.total_seconds()

    y = math.floor(totalSec / 31536000)
    totalSec -= y * 31536000

    d = math.floor(totalSec / 86400)
    totalSec -= d * 86400

    h = math.floor(totalSec / 3600)
    totalSec -= h * 3600

    m = math.floor(totalSec / 60)
    totalSec -= m * 60

    totalSec = math.floor(totalSec)

    timeStr = ''

    if full is False:
        if y > 0:
            if y == 1:
                timeStr += f'{y}год '
            elif 1 < y < 5:
                timeStr += f'{y}года '
            elif y >= 5:
                timeStr += f'{y}лет '
        if d > 0:
            timeStr += f'{d}д '
        if h > 0 and y == 0 and d < 7:
            timeStr += f'{h}ч '
        if m > 0 and y == 0 and d < 7:
            timeStr += f'{m}м '
        if totalSec > 0 and y == 0 and d == 0 and h == 0:
            timeStr += f'{totalSec}с '
    else:
        if y > 0:
            if y == 1:
                timeStr += f'{y}год '
            elif 1 < y < 5:
                timeStr += f'{y}года '
            elif y >= 5:
                timeStr += f'{y}лет '
        if d > 0:
            timeStr += f'{d}д '
        if h > 0:
            timeStr += f'{h}ч '
        if m > 0:
            timeStr += f'{m}м '
        if totalSec > 0:
            timeStr += f'{totalSec}с '
    return timeStr


async def WarnsListGet(page: int, user: discord.User, guild_id: int):
    embed_obj = discord.Embed(color=Config.blueCol)
    embed_obj.title = f'Список предупреждений' # {user.name}#{user.discriminator}
    embed_obj.description = f'<@{user.id}>'
    names = []
    for row in DataBase.getDataFromDB('punishments', 'timeOut, moder, reason, date', f'guild={guild_id} AND id={user.id} AND type="warn"', 'all'):
        names.append(row)

    maxInPage = 3
    maxPage = math.floor(len(names) / maxInPage)
    if len(names) % maxInPage > 0:
        maxPage += 1

    page = max(1, min(page, maxPage))
    embed_obj.set_author(name=f'Страница {page} из {maxPage}')
    num = page*maxInPage
    i = num-maxInPage
    while i < num:
        if i < len(names):
            unMuteTime = datetime.strptime(names[i][0], '%Y-%m-%d %H:%M:%S.%f')
            c = unMuteTime - datetime.today()
            r = divmod(c.days * 86400 + c.seconds, 60)
            timeOut = timedelta(days=0, seconds=r[1], microseconds=0, milliseconds=0, minutes=r[0], hours=0,
                                weeks=0)
            time2 = datetime.strptime(names[i][3], '%Y-%m-%d %H:%M:%S.%f')
            embed_obj.add_field(name=f'#{i+1}', value=f'''・Время: **{await ParseTimeToString(timeOut)}**
            ・Причина: **{names[i][2]}**
            ・Выдал: <@{names[i][1]}>
            ・**{time2.strftime("%d.%m.%Y %H:%M")}**
            ''', inline=True)

        i += 1

    return embed_obj


async def send_audit(audit_type: str, guild: discord.Guild, *args):
    row = DataBase.getDataFromDB('settings', 'audit', f'guild={guild.id}')
    if row[0] is None:
        return
    channel = guild.get_channel(row[0])
    if audit_type == 'voice_change':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) перешел в другой голосовой канал:'
        embed_obj.add_field(name="Предыдущий канал", value=f'{args[1].name} (<#{args[1].id}>)')
        embed_obj.add_field(name="Новый канал", value=f'{args[2].name} (<#{args[2].id}>)')

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'voice_leave':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) вышел с голосового канала:'
        embed_obj.add_field(name="Канал", value=f'{args[1].name} (<#{args[1].id}>)')

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'voice_join':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) зашел в голосовой канал:'
        embed_obj.add_field(name="Канал", value=f'{args[1].name} (<#{args[1].id}>)')

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'message_edit':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'[Сообщение]({args[2].jump_url}) было отредактировано:'
        embed_obj.add_field(name="Старое содержимое:", value=f'```{args[1].content}```', inline=False)
        embed_obj.add_field(name="Новое содержимое:", value=f'```{args[2].content}```', inline=False)

        embed_obj.add_field(name="Автор", value=f'**{args[0].display_name}** (<@{args[0].id}>)')
        embed_obj.add_field(name="Канал", value=f'**{args[2].channel.name}** (<#{args[2].channel.id}>)')

        embed_obj.set_footer(text=f'id сообщения: {args[2].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'message_delete':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Сообщение было удалено:'
        embed_obj.add_field(name="Содержимое:", value=f'```{args[1].content}```', inline=False)

        embed_obj.add_field(name="Автор", value=f'**{args[0].display_name}** (<@{args[0].id}>)')
        embed_obj.add_field(name="Канал", value=f'**{args[1].channel.name}** (<#{args[1].channel.id}>)')

        embed_obj.set_footer(text=f'id сообщения: {args[1].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'role_remove':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Роли участника **{args[0].display_name}** (<@{args[0].id}>) были изменены:'
        embed_obj.add_field(name="Удалена роль", value=f'**{args[1].name}** (<@&{args[1].id}>)')

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'role_add':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Роли участника **{args[0].display_name}** (<@{args[0].id}>) были изменены:'
        embed_obj.add_field(name="Добавлена роль", value=f'**{args[1].name}** (<@&{args[1].id}>)')

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'name_changed':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Ник участника **{args[0].display_name}** (<@{args[0].id}>) был изменен:'
        embed_obj.add_field(name="Старый ник", value=f'{args[1].display_name}')
        embed_obj.add_field(name="Новый ник", value=f'{args[2].display_name}')

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'voice_muted':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участнику **{args[0].display_name}** (<@{args[0].id}>) был отключен микрофон.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'voice_unmuted':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участнику **{args[0].display_name}** (<@{args[0].id}>) был включен микрофон.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'voice_deaf':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участнику **{args[0].display_name}** (<@{args[0].id}>) был отключен звук.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'voice_undeaf':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участнику **{args[0].display_name}** (<@{args[0].id}>) был включен звук.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'user_ban':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) был забанен.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'user_unban':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) был разбанен.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'member_join':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) присоеденился к серверу.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)
    elif audit_type == 'member_leave':
        embed_obj = discord.Embed(color=Config.embedCol)
        embed_obj.description = f'Участник **{args[0].display_name}** (<@{args[0].id}>) покинул сервер.'

        embed_obj.set_footer(text=f'id участника: {args[0].id}')
        await channel.send(embed=embed_obj)


async def addMoneyToUser(user: discord.Member, guildId: int, sum: int, useMultiplier=True):
    multiplier = 1.0
    if useMultiplier:
        multiplier = await getMultiplierFromMemberRoles(user, True)
    row = DataBase.getDataFromDB('users', 'money', f'id={user.id} AND guild={guildId}')
    money = 0
    if row is not None:
        money = row[0]
    money += sum*multiplier
    DataBase.updateDataInDB('users', f'money={int(money)}', f'id={user.id} AND guild={guildId}')
    return sum*multiplier


async def sendGuildBoostedMessage(user: discord.Member, guild: discord.guild, role: discord.Role):
    embed_obj = discord.Embed(color=role.color)
    embed_obj.description = f'<@{user.id}> спасибо за буст сервера! Мы ценим вашу поддержку.\nНа ваш счет добавлено **50.000** {Config.money_reaction}'

    await guild.system_channel.send(embed=embed_obj)

async def out_red(text):
    print("\033[31m {}" .format(text))
async def out_green(text):
    print("\033[32m {}" .format(text))
async def out_yellow(text):
    print("\033[33m {}" .format(text))
async def out_blue(text):
    print("\033[34m {}" .format(text))
async def out_white(text):
    print("\033[37m {}" .format(text))