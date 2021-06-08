import discord
from discord.ext import commands, tasks
from StudioBot.pkgs.DBCog import DBCog
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random, asyncio

class Toto:
    def __init__(self, title, desc, team0, team1, guild, cog):
        self.title = title
        self.desc = desc
        self.name = [team0, team1]
        self.bet = [dict(), dict()]
        self.on_bet = False
        self.guild = guild
        self.cog = cog

    def getprop(self, index):
        tot = [self.gettot(0), self.gettot(1)]
        if index == 1: tot = tot[::-1]
        if tot[0] == 0: return -1
        return tot[1] / tot[0]

    def gettot(self, index):
        tot = 0
        for key in self.bet[index]: tot += self.bet[index][key]
        return tot

    def getmax(self, index):
        mxbet = mxcnt = mxid = 0
        for key in self.bet[index]: mxbet = max([mxbet, self.bet[index][key]])
        for key in self.bet[index]:
            if mxbet == self.bet[index][key]:
                mxid = key
                mxcnt += 1
        return self.cog.GetDisplayName(self.guild.get_member(mxid)), mxbet

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Toto'
        self.TopRankMessage = None
        self.LastRaid = None
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['TotoChannel'] = None
        self.DB['RaidChannel'] = None

    @commands.command(name = 'totosetup')
    @commands.has_guild_permissions(administrator = True)
    async def Setup(self, ctx, category: discord.CategoryChannel):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        TotoChannel = await category.create_text_channel('토토')
        self.DB['TotoChannel'] = TotoChannel.id
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await TotoChannel.edit(sync_permissions = True)
        await TotoChannel.set_permissions(MemberRole, send_messages = False)

    @commands.command(name = 'setraidhere')
    @commands.has_guild_permissions(administrator = True)
    async def SetRaidHere(self, ctx, category: discord.CategoryChannel):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        self.DB['RaidChannel'] = ctx.channel.id

    @commands.group(name = 'toto')
    @commands.has_guild_permissions(administrator = True)
    async def TotoGroup(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()

    @TotoGroup.command(name = 'new')
    async def NewToto(self, ctx, title, desc, team0, team1):
        desc = desc.replace('\\n', '\n')
        self.toto = Toto(title, desc, team0, team1, ctx.guild, self)
        TotoChannel = ctx.guild.get_channel(self.DB['TotoChannel'])
        TotoMessage = await TotoChannel.send('temp')
        await self.updateembed(TotoMessage)
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await TotoChannel.set_permissions(MemberRole, read_messages = True, send_messages = True)
        self.toto.on_bet = True
        await ctx.send(f'새로운 토토가 <#{self.DB["TotoChannel"]}>에서 시작되었습니다!')
        self.updateembed.start(TotoMessage)
        def check(message):
            return message.channel == TotoChannel and message.author.guild_permissions.administrator and message.content == 'stopbet'
        msg = await self.app.wait_for('message', check = check)
        await TotoChannel.set_permissions(MemberRole, read_messages = True, send_messages = False)
        self.toto.on_bet = False
        self.updateembed.cancel()
        await self.updateembed(TotoMessage)

    @commands.Cog.listener('on_message')
    async def getbet(self, message):
        if message.channel.id != self.DB['TotoChannel']: return
        try:
            if not self.toto.on_bet: return
        except: return
        if message.author.id == self.app.user.id: return
        await message.delete()
        TotoChannel, msg = message.channel, message
        try: val = int(msg.content)
        except: return
        if val == 0:
            for i in range(2):
                if msg.author.id in self.toto.bet[i]: del(self.toto.bet[i][msg.author.id])
            await TotoChannel.send(f'<@{msg.author.id}>님 베팅 취소되었습니다.', delete_after = 3.0)
            return
        if msg.author.id not in self.GetGlobalDB('Money')['mns'] or abs(val) > self.GetGlobalDB('Money')['mns'][msg.author.id]:
            await TotoChannel.send(f'<@{msg.author.id}>님 도토리가 부족하여 베팅 취소되었습니다.', delete_after = 3.0)
            return
        val, index = abs(val), int(val < 0)
        if msg.author.id in self.toto.bet[1 - index]: del(self.toto.bet[1 - index][msg.author.id])
        self.toto.bet[index][msg.author.id] = val
        await TotoChannel.send(f'<@{msg.author.id}>님 {self.toto.name[index]}에 {val}개 베팅되었습니다.', delete_after = 3.0)

    @tasks.loop(seconds = 5.0)
    async def updateembed(self, TotoMessage):
        embed = discord.Embed.from_dict({
            'title' : self.toto.title,
            'color' : 10690248,
            'description' : self.toto.desc,
            'author' : {'name' : "도토리 토토"},
            'fields' : [
                {
                    'name' : f':regional_indicator_a: {self.toto.name[0]}',
                    'value' : self.get_field_text(0, TotoMessage.guild)
                },
                {
                    'name' : f':regional_indicator_b: {self.toto.name[1]}',
                    'value' : self.get_field_text(1, TotoMessage.guild)
                },
                {
                    'name' : '베팅 방법',
                    'value' : '+숫자 혹은 -숫자 치시면 됩니다. 가장 마지막으로 베팅한 것만 적용되며 0을 입력하면 베팅이 취소됩니다.\n' +
                        '예시)\n' +
                        '`+1000` -> :regional_indicator_a:에 1000개 베팅\n' + 
                        '`-2000` -> :regional_indicator_b:에 2000개 베팅\n' + 
                        '`0` -> 베팅취소'
                },
                {
                    'name' : '진행현황',
                    'value' : '베팅중' if self.toto.on_bet else '베팅종료'
                }
            ]
        })
        await TotoMessage.edit(content = None, embed = embed)

    def get_field_text(self, index, guild):
        cnt = len(self.toto.bet[index])
        res = f'총 베팅 : {cnt}명 - {self.toto.gettot(index)}개'
        if cnt > 0:
            maxwho, maxbet = self.toto.getmax(index)
            res += f'\n최대 베팅 : {maxwho} - {maxbet}개'
        prop = self.toto.getprop(index)
        if prop >= 0: res += '\n배당률 : %.2f'%(prop + 1)
        return res

    @TotoGroup.command(name = 'end')
    async def EndToto(self, ctx, result):
        winindex = int(result in ('b', 'B'))
        winners, losers = self.toto.bet[::[1, -1][winindex]]
        for loser in losers: self.GetGlobalDB('Money')['mns'][loser] -= losers[loser]
        prop = self.toto.getprop(winindex)
        if prop < 0:
            embed = discord.Embed(title = self.toto.title, description = '토토가 종료되었습니다!')
            embed.add_field(name = '토토 결과', value = f'{result} 승리!\n아무도 돈을 얻지 못했습니다!')
        else:
            for winner in winners: self.GetGlobalDB('Money')['mns'][winner] += int(winners[winner] * prop)
            embed = discord.Embed(title = self.toto.title, description = '토토가 종료되었습니다!')
            embed.add_field(name = '토토 결과', value = f'{result} 승리!\n{len(winners)}명의 참가자가 건 도토리의 %.2f배 이득을 보았습니다!'%(prop + 1))
            maxwho, maxbet = self.toto.getmax(winindex)
            embed.add_field(name = '최대 수익', value = f'{maxwho} - 도토리 {int(maxbet * prop)}개를 얻었습니다!')
        await ctx.send(embed = embed)
        del(self.toto)

    @TotoGroup.command(name = 'cancel')
    async def CancelToto(self, ctx):
        embed = discord.Embed(title = self.toto.title, description = '토토가 취소되었습니다!')
        await ctx.send(embed = embed)
        del(self.toto)

    @commands.Cog.listener()
    async def on_ready(self): self.FeverRaid.start()

    @tasks.loop(minutes = 3)
    async def FeverRaid(self):
        guild = self.app.get_guild(self.GetGlobalDB()['StoryGuildID'])        
        RaidChannel = guild.get_channel(self.DB['RaidChannel'])
        if RaidChannel == None: return
        try:
            if (await RaidChannel.fetch_message(RaidChannel.last_message_id)).author.bot: return
        except: pass
        if random.random() >= 1 / 10: return
        aww = discord.utils.get(guild.emojis, name = 'rage_aww')
        prize = 2000
        if self.LastRaid:
            hdelta = (datetime.now() - self.LastRaid).total_seconds() / 3600
            prize = max([int(hdelta * 4000), prize])
        self.RaidMessage = await RaidChannel.send(embed = discord.Embed(
            title = '도토리 레이드 도착!',
            description = f'15초 안에 아래 이모지를 눌러서 도토리 {prize}개를 받으세요!'))
        self.raiders = set()
        self.on_raid = True
        await self.RaidMessage.add_reaction(aww)
        await asyncio.sleep(15)
        self.LastRaid = datetime.now()
        self.on_raid = False
        desc = ''
        if len(self.raiders) == 0:
            if prize < 4000: desc = f'아무도 도토리 {prize}개를 획득하지 못하셨습니다!'
            else: desc = f'아무도 레이드를 성공하지 못했습니다!\n무려 {prize}개짜리였는데!'
        else:
            for raider in self.raiders:
                dispname = self.GetDisplayName(raider)
                desc += dispname + ', '
            desc = f'{desc[:-2]}\n\n도토리 {prize}개를 획득하셨습니다!'
        await self.RaidMessage.edit(embed = discord.Embed(title = '도토리 레이드 마감~~!', description = desc))
        for user in self.raiders:
            if user.id not in self.GetGlobalDB('Money')['mns']: self.GetGlobalDB('Money')['mns'][user.id] = 0
            self.GetGlobalDB('Money')['mns'][user.id] += prize

    @commands.Cog.listener('on_reaction_add')
    async def onRaidReaction(self, reaction, user):
        try:
            if not self.on_raid: return
        except: return
        if reaction.message != self.RaidMessage: return
        if user.bot: return
        if reaction.emoji.name != 'rage_aww': return
        self.raiders.add(user)
