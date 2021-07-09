import discord, uuid
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog
from functools import wraps
from pkgs.ReportPayload import ReportPayload

def SkipCheck(func):
    @wraps(func)
    async def wrapper(self, message):
        if message.guild == None: return
        if message.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        if message.author.bot or message.author.guild_permissions.administrator: return
        return await func(self, message)
    return wrapper

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Filter'
        self.mfEmoji = '🖕'
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.Cog.listener('on_message')
    @SkipCheck
    async def ModShouldBeOnline(self, message):
        if message.author.status != discord.Status.offline: return
        if message.author.permissions_in(message.channel).manage_messages and not message.author.guild_permissions.administrator:
            await message.channel.send(f'<@{message.author.id}> 관리자께서는 되도록이면 오프라인 상태를 해제하여 관리활동 중임을 표시해주세요.', delete_after = 10.0)

    @commands.Cog.listener('on_message')
    @SkipCheck
    async def NoMiddleFinger(self, message):
        if self.mfEmoji in message.content:
            await message.delete()
            payload = ReportPayload.fromMessage(self.app.user, message, caption = '중지 이모지 사용')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.guild == None: return
        if reaction.message.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        if user.bot or user.guild_permissions.administrator: return
        if self.mfEmoji in str(reaction.emoji):
            await reaction.clear()
            payload = ReportPayload.fromReaction(self.app.user, reaction, user, caption = '중지 이모지 사용'):
