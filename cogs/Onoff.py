import discord, asyncio
from StudioBot.pkgs.DBCog import DBCog
from discord.ext import commands
import sys

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'OnOff'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['StopChannel'] = None

    @commands.Cog.listener()
    async def on_ready(self):
        version = '2.8.4'
        await self.app.change_presence(activity = discord.Game(f'Botory {version} by Undec'))
        guild = self.app.get_guild(self.GetGlobalDB()['StoryGuildID'])
        if self.DB['StopChannel']:
            StopChannel = guild.get_channel(self.DB['StopChannel'])
            await StopChannel.send(f'보토리 {version} is back.')
        self.MemberRole = discord.utils.get(guild.roles, name = '멤버')
        perms = self.MemberRole.permissions
        perms.update(add_reactions = True, attach_files = True)
        await self.MemberRole.edit(permissions = perms)

    @commands.command(name = 'stop')
    @commands.has_guild_permissions(administrator = True)
    async def StopApp(self, ctx):
        await ctx.message.delete()
        self.DB['StopChannel'] = ctx.channel.id;
        perms = self.MemberRole.permissions
        perms.update(add_reactions = False, attach_files = False)
        await self.MemberRole.edit(permissions = perms)
        await ctx.channel.send('장비를 정지합니다.')
        await self.app.change_presence(status = discord.Status.offline)
        await asyncio.sleep(1)
        await self.app.close()
