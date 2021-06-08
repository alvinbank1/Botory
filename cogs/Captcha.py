import discord, uuid
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog
from captcha.image import ImageCaptcha

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Captcha'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['VerifiedIDs'] = set()

    @commands.Cog.listener('on_member_join')
    async def MemberJoin(self, member):
        if member.guild.id != self.GetGlobalDB()['StoryGuildID']: return


    @commands.Cog.listener('on_member_remove')
    async def MemberRemove(self, member):
        if member.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        try: del self.DB['VerifiedIDs'].remove(member.id)
        except: pass
