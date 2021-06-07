import discord, uuid, re
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog
from typing import union

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Moderator'
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.command(name = 'ban')
    async def ModBan(self, ctx, who: discord.User, reason = None):
        await ctx.guild.ban(who, reason = reason, delete_message_days = 7)
        embed = discord.Embed(title = 'RIP :zany_face:', description = f'**{who.name}#{who.discriminator}**')
        await ctx.send(embed = embed)
