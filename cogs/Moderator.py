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
    @commands.has_guild_permissions(administrator = True)
    async def ModBan(self, ctx, who, reason = None):
        who = self.mention2member(who, ctx.guild)
        await ctx.guild.ban(who, reason = reason, delete_message_days = 7)
        embed = discord.Embed(title = 'RIP :zany_face:', description = f'**{who.name}#{who.discriminator}**')
        await ctx.send(embed = embed)

    @commands.command(name = 'countban')
    @commands.has_guild_permissions(administrator = True)
    async def ModBan(self, ctx, count: int):
        await ctx.message.delete()
        msgs = await ctx.channel.history(limit = count).flatten()
        for msg in msgs:
            who = msg.author
            if ctx.guild.get_member(who.id): continue
            print(who.name)
            #await ctx.guild.ban(who, delete_message_days = 7)
