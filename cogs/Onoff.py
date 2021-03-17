import discord, asyncio
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from discord.ext import commands

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'OnOff'
        DBCog.__init__(self, app)

    def initDB(self): self.DB = dict()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.app.change_presence(activity = discord.Game('Botory 2.3.0 by Undec'))
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])
        self.MemberRole = discord.utils.get(guild.roles, name = '멤버')
        perms = self.MemberRole.permissions
        perms.update(add_reactions = True, attach_files = True)
        await self.MemberRole.edit(permissions = perms)

    @commands.command(name = 'stop')
    @commands.has_guild_permissions(administrator = True)
    async def StopApp(self, ctx):
        await ctx.message.delete()
        perms = self.MemberRole.permissions
        perms.update(add_reactions = False, attach_files = False)
        await self.MemberRole.edit(permissions = perms)
        await ctx.channel.send('장비를 정지합니다.')
        await self.app.change_presence(status = discord.Status.offline)
        await asyncio.sleep(1)
        await self.app.close()
