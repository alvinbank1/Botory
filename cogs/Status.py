import discord, asyncio
from discord.ext import commands
from pkgs.DBCog import DBCog

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Status'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB = dict()

    @commands.group(name = 'status')
    @commands.has_guild_permissions(administrator = True)
    async def StatusGroup(self, ctx):
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Status Manager\nSubcommands : update')

    @StatusGroup.command(name = 'update')
    async def StatusUpdate(self, ctx, ChannelID, value):
        channel = discord.utils.get(ctx.guild.channels, id = int(ChannelID))
        ChannelName = channel.name
        fr = to = 0
        for i in range(len(ChannelName) - 1, -1, -1):
            if ChannelName[i].isdigit():
                to = i + 1
                break
        for i in range(to - 1, -1, -1):
            if not ChannelName[i].isdigit():
                fr = i + 1
                break
        NewName = ChannelName[:fr] + value + ChannelName[to:]
        await channel.edit(name = NewName)
