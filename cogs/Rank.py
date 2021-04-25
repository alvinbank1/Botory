import discord
from discord.ext import commands, tasks
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from pkgs.Scheduler import Schedule

class Toto:
    def __init__(self, title, desc, ateam, bteam):
        self.title = title
        self.desc = desc
        self.ateam = ateam
        self.bteam = bteam
        self.abet = dict()
        self.bbet = dict()
        self.on_bet = False

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Rank'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB = dict()
        self.DB['RankChannel'] = None
        self.DB['TotoChannel'] = None
        self.DB['xps'] = dict()
        self.DB['Cooldown'] = dict()

    def rank2xp(self, rank):
        return 5 / 3 * rank ** 3 + 45 / 2 * rank ** 2 + 455 / 6 * rank

    def xp2rank(self, xp):
        l, r = 0, 1001
        while r - l > 1:
            mid = (l + r) // 2
            if xp < self.rank2xp(mid): r = mid
            else: l = mid
        return l

    @commands.command(name = 'ranksetup')
    @commands.has_guild_permissions(administrator = True)
    async def Setup(self, ctx, CategoryID):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        Category = ctx.guild.get_channel(int(CategoryID))
        RankChannel = await Category.create_text_channel('랭크확인')
        TotoChannel = await Category.create_text_channel('토토')
        self.DB['RankChannel'] = RankChannel.id
        self.DB['TotoChannel'] = TotoChannel.id
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await RankChannel.set_permissions(MemberRole, read_messages = True, add_reactions = False)
        await TotoChannel.set_permissions(MemberRole, read_messages = True, send_messages = False, add_reactions = False)

    @commands.command(name = 'rank')
    async def GetRank(self, ctx):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        if ctx.channel.id != self.DB['RankChannel']: return
        await ctx.message.delete()
        if ctx.author.id in self.DB['xps']: xp = self.DB['xps'][ctx.author.id]
        else: xp = 0
        rank = self.xp2rank(xp)
        tonext = self.rank2xp(rank + 1) - xp
        if rank < 1000: await ctx.send(f'<@{ctx.author.id}>님은 {xp // 100 / 10}k 경험치로 {rank}레벨입니다! {rank + 1} 레벨까지 {tonext} 경험치 남았습니다!', delete_after = 10.0)
        else: await ctx.send(f'<@{ctx.author.id}>님은 {rank}레벨입니다! 만렙이네요!ㄷㄷ', delete_after = 10.0)

    @commands.command(name = 'givexp')
    @commands.has_guild_permissions(administrator = True)
    async def GiveXP(self, ctx, who, val):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['xps']: self.DB['xps'][who.id] = 0
        self.DB['xps'][who.id] += int(val)

    @commands.command(name = 'takexp')
    @commands.has_guild_permissions(administrator = True)
    async def TakeXP(self, ctx, who, val):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['xps']: self.DB['xps'][who.id] = 0
        self.DB['xps'][who.id] -= int(val)
        if self.DB['xps'][who.id] < 0: self.DB['xps'][who.id] = 0

    @commands.Cog.listener('on_message')
    async def messageXP(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.author.bot: return
        if message.channel.id == self.DB['RankChannel']: return
        whoid = message.author.id
        if whoid not in self.DB['Cooldown']: self.DB['Cooldown'][whoid] = Schedule('0s')
        if self.DB['Cooldown'][whoid].is_done():
            if whoid not in self.DB['xps']: self.DB['xps'][whoid] = 0
            self.DB['xps'][whoid] += 20
            self.DB['Cooldown'][whoid] = Schedule('1m')

    @commands.Cog.listener('on_message')
    async def nomsginrank(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.channel.id != self.DB['RankChannel']: return
        if message.author.id == self.app.user.id: return
        if message.content != '&rank': await message.delete()

    @commands.command(name = 'newtoto')
    @commands.has_guild_permissions(administrator = True)
    async def NewToto(self, ctx, title, desc, ateam, bteam):
        self.toto = Toto(title, desc, ateam, bteam)
        await ctx.message.delete()
        TotoChannel = ctx.guild.get_channel(self.DB['TotoChannel'])
        TotoMessage = await TotoChannel.send('temp')
        await self.updateembed(TotoMessage)
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await TotoChannel.set_permissions(MemberRole, read_messages = True, send_messages = True)
        self.toto.on_bet = True
        self.updateembed.start(TotoMessage)
        def check(message):
            return message.channel == TotoChannel and message.author.guild_permissions.administrator and message.content == 'stopbet'
        msg = await self.app.wait_for('message', check = check)
        await TotoChannel.set_permissions(MemberRole, read_messages = True, send_messages = False)
        self.toto.on_bet = False
        self.updateembed.cancel()
        await self.updateembed(TotoMessage)
        embed = TotoMessage.embeds[0]

    @commands.Cog.listener('on_message')
    async def getbet(self, message):
        if message.channel.id != self.DB['TotoChannel']: return
        if not self.toto.on_bet: return
        if message.author.id == self.app.user.id: return
        await message.delete()
        TotoChannel, msg = message.channel, message
        try: val = int(msg.content)
        except: return
        if msg.author.id not in self.DB['xps'] or abs(val) > self.DB['xps'][msg.author.id]:
            await TotoChannel.send(f'<@{msg.author.id}>님 xp가 부족하여 베팅 취소되었습니다.', delete_after = 3.0)
            return
        if val == 0:
            if msg.author.id in self.toto.abet: del(self.toto.abet[msg.author.id])
            if msg.author.id in self.toto.bbet: del(self.toto.bbet[msg.author.id])
            await TotoChannel.send(f'<@{msg.author.id}>님 베팅 취소되었습니다.', delete_after = 3.0)
        if val > 0:
            if msg.author.id in self.toto.bbet: del(self.toto.bbet[msg.author.id])
            self.toto.abet[msg.author.id] = val
            await TotoChannel.send(f'<@{msg.author.id}>님 {self.toto.ateam}에 {val}xp 베팅되었습니다.', delete_after = 3.0)
        if val < 0:
            if msg.author.id in self.toto.abet: del(self.toto.abet[msg.author.id])
            self.toto.bbet[msg.author.id] = -val
            await TotoChannel.send(f'<@{msg.author.id}>님 {self.toto.bteam}에 {-val}xp 베팅되었습니다.', delete_after = 3.0)

    @tasks.loop(seconds = 5.0)
    async def updateembed(self, TotoMessage):
        embed = discord.Embed.from_dict({
            'title' : self.toto.title,
            'color' : 10690248,
            'description' : self.toto.desc,
            'author' : {'name' : "경험치 토토"},
            'fields' : [
                {
                    'name' : f':regional_indicator_a: {self.toto.ateam}',
                    'value' : self.get_field_text(self.toto.abet, TotoMessage.guild)
                },
                {
                    'name' : f':regional_indicator_b: {self.toto.bteam}',
                    'value' : self.get_field_text(self.toto.bbet, TotoMessage.guild)
                },
                {
                    'name' : '베팅 방법',
                    'value' : '+숫자 혹은 -숫자 치시면 됩니다. 가장 마지막으로 베팅한 것만 적용되며 0을 입력하면 베팅이 취소됩니다.\n' +
                        '예시)\n' +
                        '`+1000` :regional_indicator_a:에 1000xp 베팅\n' + 
                        '`-2000` :regional_indicator_b:에 2000xp 베팅\n' + 
                        '`0` 베팅취소'
                },
                {
                    'name' : '진행현황',
                    'value' : '베팅중' if self.toto.on_bet else '베팅종료'
                }
            ]
        })
        await TotoMessage.edit(content = None, embed = embed)

    def get_field_text(self, _dict, guild):
        cnt = len(_dict)
        if cnt == 0: return '총 베팅 : 0명 - 0xp'
        net = mx = mxcnt = 0
        mxid = None
        for key in _dict:
            net += _dict[key]
            mx = max([_dict[key], mx])
        for key in _dict:
            if _dict[key] == mx:
                mxcnt += 1
                if mxid == None: mxid = key
        mxstr = f'{self.GetDisplayName(guild.get_member(mxid))}'
        if mxcnt > 1: mxstr += f' 외 {mxcnt - 1}명'
        return f'총 베팅 : {cnt}명 - {net}xp\n최대 베팅 : {mxstr} - {mx}xp'

    @commands.command(name = 'endtoto')
    @commands.has_guild_permissions(administrator = True)
    async def EndToto(self, ctx, result):
        await ctx.message.delete()
        windict, losedict = self.toto.abet, self.toto.bbet
        if result == 'B': windict, losedict = losedict, windict
        ltot = wtot = wmax = mxcnt = 0
        mxid = None
        for loser in losedict:
            self.DB['xps'][loser] -= losedict[loser]
            ltot += losedict[loser]
        for winner in windict:
            wtot += windict[winner]
            wmax = max([wmax, windict[winner]])
        for winner in windict:
            if windict[winner] == wmax:
                mxcnt += 1
                if mxid == None: mxid = winner
        mxstr = f'{self.GetDisplayName(ctx.guild.get_member(mxid))}'
        if mxcnt > 1: mxstr += f' 외 {mxcnt - 1}명'
        prop = ltot / wtot
        for winner in windict: self.DB['xps'][winner] += int(windict[winner] * prop)
        embed = discord.Embed(title = self.toto.title, description = '토토가 종료되었습니다!')
        embed.add_field(name = '토토 결과', value = f'{result} 승리!\n{len(windict)}명의 참가자가 {int(prop * 1000) / 10}% 이득을 보았습니다!')
        embed.add_field(name = '최대 수익', value = f'{mxstr} - {int(wmax * prop)}xp를 얻었습니다!')
        await ctx.send(embed = embed)
        del(self.toto)
