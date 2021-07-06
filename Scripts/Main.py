import discord
from discord.ext import commands
import traceback
import sys
import sqlite3
import os

intents = discord.Intents.all()
# intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

bot.remove_command("help")

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

# cursor.execute('ALTER TABLE messages ADD COLUMN "userId" INT')

# cursor.execute('ALTER TABLE users ADD COLUMN "badges" TEXT')

# cursor.execute('ALTER TABLE settings ADD COLUMN "maxMembers" INT')

# cursor.execute("""CREATE TABLE "voice"
#        ("guild" INT, "id" INT, "type" TEXT)""")

# cursor.execute("DROP TABLE punishments")
#
# cursor.execute("""CREATE TABLE "punishments"
#     ("id" INT, "type" TEXT, "timeOut" DATETIME, "guild" INT, "reason" TEXT, "moder" INT, "date" DATETIME)""")

DISCORD_TOKEN = 'TOKEN'

initial_extensions = ['Events', 'UserCommands', 'SettingsCommands', 'AdminCommands', 'ModerCommands']

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

bot.run(DISCORD_TOKEN)
