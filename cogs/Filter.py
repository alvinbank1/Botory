import discord, uuid
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog
from functools import wraps

def SkipCheck(func):
    @wraps(func)
    async def wrapper(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.author.bot or message.author.guild_permissions.administrator: return
        return await func(self, message)
    return wrapper

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Filter'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['ReportChannel'] = None

    @commands.command(name = 'reporthere')
    @commands.has_guild_permissions(administrator = True)
    async def SetChannels(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        self.DB['ReportChannel'] = ctx.channel.id

    @commands.Cog.listener('on_message')
    @SkipCheck
    async def ModShouldBeOnline(self, message):
        if message.author.permissions_in(message.channel).manage_messages and not message.author.administrator:
            await message.channel.send(f'<@{message.author.id}> 관리자께서는 되도록이면 오프라인 상태를 해제하여 관리활동 중임을 표시해주세요.', delete_after = 10.0)

    @commands.Cog.listener('on_message')
    @SkipCheck
    async def NoMiddleFinger(self, message):
        if '🖕' in message.content:
            await message.delete()
            await self.MiddleFingerReport(message.author.id, message.channel)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.guild.id != GlobalDB['StoryGuildID']: return
        if user.bot or user.guild_permissions.administrator: return
        if '🖕' in str(reaction.emoji):
            await reaction.clear()
            await self.MiddleFingerReport(user.id, reaction.message.channel)

    async def MiddleFingerReport(self, user: discord.User, channel):
        ReportChannel = channel.guild.get_channel(self.DB['ReportChannel'])
        await channel.send(f'<@{user.id}> 중지 절단 완료.')
        if ReportChannel:
            await ReportChannel.send(f'<@{user.id}> 이 사용자 중지 이모지 사용으로 경고바랍니다.', allowed_mentions = discord.AllowedMentions.none())
