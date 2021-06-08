import discord, uuid, re
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Moderator'
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.command(name = 'ban')
    @commands.has_guild_permissions(administrator = True)
    async def ModBan(self, ctx, who: discord.User, reason = None):
        await ctx.guild.ban(who, reason = reason, delete_message_days = 7)
        await ctx.send(embed = discord.Embed(title = 'RIP :zany_face:', description = f'**{who.name}#{who.discriminator}**'))

    @commands.command(name = 'countban')
    @commands.has_guild_permissions(administrator = True)
    async def ModBan(self, ctx, count: int):
        await ctx.message.delete()
        msgs = await ctx.channel.history(limit = count).flatten()
        for msg in msgs:
            who = msg.author
            if ctx.guild.get_member(who.id): continue
            await ctx.guild.ban(who, delete_message_days = 7)
