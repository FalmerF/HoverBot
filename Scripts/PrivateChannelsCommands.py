import sqlite3
from datetime import datetime, timedelta

import discord
from discord import utils
from discord.ext import commands

import Config
import Utils
import DataBase
from Utils import EmbedCreate, ArgumentsEmbedCreate


last_Messages = []


class PrivateChannelsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def c(self, ctx: discord.ext.commands.context, action: str, *args):
        row = DataBase.getDataFromDB('voice', 'id', f'guild={ctx.guild.id} AND user={ctx.author.id}')
        channel = None
        if row is not None and row[0] is not None:
            channel = ctx.guild.get_channel(row[0])
        if channel is None:
            embed_obj = await EmbedCreate(description=f'У вас нет приватного канала.',
                                          color=Config.yellowCol,
                                          footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
            return

        if action == 'ban' and len(args) >= 1:
            user = ctx.guild.get_member(int(args[0].replace('<@!', '').replace('>', '')))
            await channel.set_permissions(user, connect=False)
            for m in channel.members:
                if m == user:
                    await m.move_to(None)

            embed_obj = await EmbedCreate(description=f'Пользователь <@{user.id}> заблокирован в канале <#{channel.id}>.',
                                          color=Config.redCol,
                                          footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        elif action == 'unban' and len(args) >= 1:
            user = ctx.guild.get_member(int(args[0].replace('<@!', '').replace('>', '')))
            await channel.set_permissions(user, connect=True)

            embed_obj = await EmbedCreate(
                description=f'Пользователь <@{user.id}> разблокирован в канале <#{channel.id}>.',
                color=Config.greenCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        elif action == 'kick' and len(args) >= 1:
            user = ctx.guild.get_member(int(args[0].replace('<@!', '').replace('>', '')))
            for m in channel.members:
                if m == user:
                    await m.move_to(None)

            embed_obj = await EmbedCreate(
                description=f'Пользователь кикнут с канала <#{channel.id}>.',
                color=Config.yellowCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        elif action == 'rename' and len(args) >= 1:
            name = ''
            for word in args:
                name += f'{word} '
            await channel.edit(name=name)

            embed_obj = await EmbedCreate(
                description=f'Канал переименован: <#{channel.id}>.',
                color=Config.greenCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        elif action == 'limit' and len(args) >= 1:
            limit = max(min(int(args[0]), 99), 0)
            await channel.edit(user_limit=limit)

            embed_obj = await EmbedCreate(
                description=f'Установлен лимит пользователей `{limit}` для канала <#{channel.id}>.',
                color=Config.greenCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        elif action == 'delete':
            DataBase.deleteDataFromDB('voice', f'id={channel.id} AND guild={channel.guild.id}')
            if len(channel.members) >= 1:
                newChannel = await ctx.guild.create_voice_channel("Temp Channel", category=channel.category)

                DataBase.insertDataInDB('voice', f'{ctx.guild.id}, {newChannel.id}, "private", {self.bot.user.id}')

                for m in channel.members:
                    await m.move_to(newChannel)

            await channel.delete()

            embed_obj = await EmbedCreate(
                description=f'Канал удален.',
                color=Config.redCol,
                footerText=Utils.RequestedText(ctx))
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()
        else:
            embed_obj = await ArgumentsEmbedCreate(ctx, f'**Управление приватными каналами:**\n'
                                                        f'`!c ban <@участник>` - забрать доступ к вашему каналу для определенного участника.\n'
                                                        f'`!c unban <@участник>` - вернуть доступ к вашему каналу для определенного участника.\n'
                                                        f'`!c kick <@участник>` - кикнуть участника с вашего канала.\n'
                                                        f'`!c rename <имя>` - переименовать ваш канал.\n'
                                                        f'`!c limit <количество [0-99]>` - ограничить количество участников для вашего канала.\n'
                                                        f'`!c delete` - удалить ваш канал.')
            await ctx.send(embed=embed_obj)
            await ctx.message.delete()


    @c.error
    async def c_error(self, ctx, error):
        embed_obj = await ArgumentsEmbedCreate(ctx, f'**Управление приватными каналами:**\n'
                                                    f'`!c ban <@участник>` - забрать доступ к вашему каналу для определенного участника.\n'
                                                    f'`!c unban <@участник>` - вернуть доступ к вашему каналу для определенного участника.\n'
                                                    f'`!c kick <@участник>` - кикнуть участника с вашего канала.\n'
                                                    f'`!c rename <имя>` - переименовать ваш канал.\n'
                                                    f'`!c limit <количество [0-99]>` - ограничить количество участников для вашего канала.\n'
                                                    f'`!c delete` - удалить ваш канал.')
        await ctx.send(embed=embed_obj)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(PrivateChannelsCommands(bot))
