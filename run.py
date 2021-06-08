import discord, sys, os, pickle
from discord.ext import commands
from StudioBot.pkgs.DBCog import GDB
import cogs

app = commands.Bot(command_prefix = '&', intents = discord.Intents.all(), help_command = None)

def main():
    global GDB
    GDB.requestDB('__global__')['StoryGuildID'] = 775210688183664640
    InitCogs()
    app.run(GetToken())
    GDB.saveall()

def InitCogs():
    for CogName in cogs.__all__:
        __import__(f'cogs.{CogName}')
        sys.modules[f'cogs.{CogName}'].Core(app)

def GetToken():
    if os.path.isfile('token.db'):
        with open('token.db', 'rb') as f: return pickle.load(f)
    token = input('Enter token : ')
    with open('token.db', 'wb') as f: pickle.dump(token, f)
    return token

if __name__ == "__main__": main()
