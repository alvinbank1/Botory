import discord, uuid, re
from discord.ext import commands
from pkgs.DBCog import DBCog

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Moderator'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB = dict()

    @commands.command(name = 'ban')
    async def ModBan(self, ctx, who, reason = None):
        who = self.mention2member(who, ctx.guild)
        await ctx.guild.ban(who, reason = reason, delete_message_days = 7)
        embed = discord.Embed(title = 'RIP :zany_face:', description = f'**{who.name}#{who.discriminator}**')
        await ctx.send(embed = embed)
