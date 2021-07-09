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
        channel = await member.create_dm()
        embed = discord.Embed(title = '밴 안내', description = '당신은 The Stories 서버에서 밴되셨습니다.:zany_face:')
        if reason: embed.add_field(name = '사유', value = reason)
        await channel.send(embed = embed)
        await ctx.guild.ban(who, reason = reason, delete_message_days = 7)
        await ctx.send(embed = discord.Embed(title = 'RIP :zany_face:', description = f'**{who.name}#{who.discriminator}**'))
