import discord, uuid, re
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog
from datetime import datetime, timedelta

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Moderator'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['OfficeChannel'] = None
        self.DB['reports'] = []

    @commands.command(name = 'officehere')
    @commands.has_guild_permissions(administrator = True)
    async def SetOffice(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        self.DB['OfficeChannel'] = ctx.channel.id

    @commands.command(name = 'bustercall', aliases = ['buster', '버스터콜'])
    async def SetOffice(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        self.DB['OfficeChannel'] = ctx.channel.id

    @commands.command(name = 'ban')
    @commands.has_guild_permissions(administrator = True)
    async def ModBan(self, ctx, who: discord.User, reason = None):
        channel = await member.create_dm()
        embed = discord.Embed(title = '안내', description = '당신은 The Stories 서버에서 밴되셨습니다.:zany_face:')
        if reason: embed.add_field(name = '사유', value = reason)
        await channel.send(embed = embed)
        await ctx.guild.ban(who, reason = reason, delete_message_days = 7)
        await ctx.send(embed = discord.Embed(title = 'RIP :zany_face:', description = f'**{who.name}#{who.discriminator}**'))

    @commands.command(name = 'report', aliases = ['신고'])
    async def Report(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        channel = await ctx.author.create_dm()
        try:
            if ctx.message.reference:
                message = await self.MessageFromLink(ctx.message.reference.jump_url)
                if ReportPayload.fromMessage(ctx.author, message) in self.reports: raise Exception('exists')
                await channel.send('10분안에 신고 사유를 하나의 메시지에 말씀해주세요. 그 후 원하신다면 최대 3개까지 첨부할 사진을 보내주세요.')
                flag = datetime.now() + timedelta(minutes = 10)
                while True:
                    reply = await self.app.wait_for('message', check = lambda msg: msg.channel == channel, timeout = (flag - datetime.now()).total_seconds())
                    if datetime.now() < flag: raise asyncio.TimeoutError
                    if : raise asyncio.TimeoutError
                payload = ReportPayload.fromMessage(ctx.author, message, reply.content)
            else:
                if ReportPayload.fromMessage(ctx.author, message) in self.reports: raise Exception('exists')
                await channel.send('10분안에 신고 사유를 하나의 메시지에 말씀해주세요. 그 후 원하신다면 최대 3개까지 첨부할 사진을 보내주세요.')
                flag = datetime.now() + timedelta(minutes = 10)
                while True:
                    reply = await self.app.wait_for('message', check = lambda msg: msg.channel == channel, timeout = (flag - datetime.now()).total_seconds())
                    if datetime.now() < flag: raise asyncio.TimeoutError
                    if : raise asyncio.TimeoutError
                payload = ReportPayload.fromMessage(ctx.author, message, reply.content)
                self.DB['reports'].append(payload)
        except discord.HTTPException: await ctx.send('서버 dm을 허용해주세요.')
        except asyncio.TimeoutError: await channel.send('시간초과로 신고가 취소되었습니다.')
        except Exception as inst:
            if inst.args and inst.args[0] == 'exists':
                await channel.send('이미 신고된 내용입니다.')
