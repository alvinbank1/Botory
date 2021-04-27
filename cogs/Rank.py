import discord
from discord.ext import commands, tasks
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from pkgs.Scheduler import Schedule
from PIL import Image, ImageDraw, ImageFont
import requests, os

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
        self.CogName = 'Rank'
        DBCog.__init__(self, app)
        self.TopRankMessage = None

    def initDB(self):
        self.DB = dict()
        self.DB['RankChannel'] = None
        self.DB['TotoChannel'] = None
        self.DB['xps'] = dict()
        self.DB['Cooldown'] = dict()

    def level2xp(self, rank):
        return (10 * rank ** 3 + 135 * rank ** 2 + 455 * rank) // 6

    def xp2level(self, xp):
        l, r = 0, 1001
        while r - l > 1:
            mid = (l + r) // 2
            if xp < self.level2xp(mid): r = mid
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
    async def GetRank(self, ctx, arg = None):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        if ctx.channel.id != self.DB['RankChannel']: return
        await ctx.message.delete()
        who = ctx.author
        if arg and ctx.author.guild_permissions.administrator: who = self.mention2member(arg, ctx.guild)
        if who.id in self.DB['xps']: xp = self.DB['xps'][who.id]
        else: xp = 0
        level = self.xp2level(xp)
        tonext = self.level2xp(level + 1) - xp
        rank = 1
        for key in self.DB['xps']:
            if self.DB['xps'][key] > xp: rank += 1
        if rank < 1000: await ctx.send(f'<@{who.id}>님은 {xp // 100 / 10}k 경험치로 {level}레벨 {rank}등입니다! {level + 1} 레벨까지 {tonext} 경험치 남았습니다!', delete_after = 10.0)
        else: await ctx.send(f'<@{who.id}>님은 {level}레벨 {rank}등입니다! 만렙이네요!ㄷㄷ', delete_after = 10.0)

    @commands.Cog.listener()
    async def on_ready(self):
        self.TopRankMsg.start()
        self.AutoRole.start()

    @tasks.loop(minutes = 5)
    async def TopRankMsg(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        RankChannel = guild.get_channel(self.DB['RankChannel'])
        img = self.makerankimg()
        img.save('tmp.png')
        with open('tmp.png', 'rb') as fp:
            if self.TopRankMessage: await self.TopRankMessage.delete()
            self.TopRankMessage = await RankChannel.send(file = discord.File(fp))
        os.remove('tmp.png')

    def makerankimg(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        lst = []
        for key in self.DB['xps']: lst.append([self.DB['xps'][key], key])
        lst.sort(reverse = True)
        res = Image.new("RGB", (1480 * 2 + 20, 280 * 10 + 20), (50, 50, 50))
        i = 0
        for elem in lst:
            if i > 19: break
            who = guild.get_member(elem[1])
            if who == None: continue
            level = self.xp2level(elem[0])
            if level == 1000: prop = 1
            else: prop = (elem[0] - self.level2xp(level)) / (self.level2xp(level + 1) - self.level2xp(level))
            one = self._makerankone(self.GetDisplayName(who), elem[0], i + 1, level, prop, who.avatar_url)
            res.paste(one, ((i // 10) * 1480, (i % 10) * 280))
            i += 1
        return res

    def _makerankone(self, who, exp, rank, level, prop, url):
        res = Image.new("RGB", (1500, 300), (50, 50, 50))
        canvas = ImageDraw.Draw(res)
        canvas.rectangle((0, 0, 1500, 300), outline = (70, 70, 70), width = 20)
        canvas.ellipse((1269, 69, 1431, 231), width = 6, outline = (80, 80, 80))
        canvas.text((1350, 120), 'LEVEL', font = ImageFont.truetype('NanumGothic.ttf', 30), fill = (140, 140, 140), align = 'center', anchor = 'mm')
        canvas.text((1110, 120), 'EXP', font = ImageFont.truetype('NanumGothic.ttf', 30), fill = (140, 140, 140), align = 'center', anchor = 'mm')

        if rank < 4: rankcolor = [(212, 175, 55), (208, 208, 208), (138, 84, 30)][rank - 1]
        else: rankcolor = (100, 100, 100)
        darkercolor = tuple(c - 20 for c in rankcolor)
        canvas.ellipse((75, 75, 225, 225), fill = rankcolor, width = 12, outline = darkercolor)
        if prop < 1:
            canvas.arc((1269, 69, 1431, 231), start = 270, end = int(270 + prop * 360) % 360, width = 6, fill = rankcolor if rank < 4 else (200, 200, 200))
        else: canvas.ellipse((1269, 69, 1431, 231), width = 6, outline = (255, 0, 0))
        canvas.text((150, 150), str(rank), font = ImageFont.truetype('NanumGothic.ttf', 90), fill = (255, 255, 255),
            anchor = 'mm', stroke_width = 4, stroke_fill = (0, 0, 0))
     
        if len(who) > 9: who = who[:8] + '...'
        if level == 1000: level = 'MAX'
        else: level = str(level)
        canvas.text((450, 150), who, font = ImageFont.truetype('NanumGothic.ttf', 60), fill = (255, 255, 255), anchor = 'lm')
        canvas.text((1350, 165), level, font = ImageFont.truetype('NanumGothic.ttf', 48), fill = (255, 255, 255), align = 'center', anchor = 'mm')
        canvas.text((1110, 165), '%.1fk'%(exp / 1000), font = ImageFont.truetype('NanumGothic.ttf', 48), fill = (255, 255, 255), anchor = 'mm')

        res.convert('RGBA')
        profile = Image.open(requests.get(url, stream=True).raw)
        profile = profile.resize((120, 120))
        mask = Image.new('L', (120, 120), 0)
        mcanvas = ImageDraw.Draw(mask)
        mcanvas.ellipse((0, 0, 120, 120), fill = 255)
        res.paste(profile, (300, 90), mask = mask)
        return res

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
        ctx = await self.app.get_context(message)
        if not ctx.valid: await message.delete()

    @commands.command(name = 'newtoto')
    @commands.has_guild_permissions(administrator = True)
    async def NewToto(self, ctx, title, desc, team0, team1):
        self.toto = Toto(title, desc, team0, team1, ctx.guild, self)
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
        if val == 0:
            for i in range(2):
                if msg.author.id in self.toto.bet[i]: del(self.toto.bet[i][msg.author.id])
            await TotoChannel.send(f'<@{msg.author.id}>님 베팅 취소되었습니다.', delete_after = 3.0)
            return
        if msg.author.id not in self.DB['xps'] or abs(val) > self.DB['xps'][msg.author.id]:
            await TotoChannel.send(f'<@{msg.author.id}>님 xp가 부족하여 베팅 취소되었습니다.', delete_after = 3.0)
            return
        val, index = abs(val), int(val < 0)
        if msg.author.id in self.toto.bet[1 - index]: del(self.toto.bet[1 - index][msg.author.id])
        self.toto.bet[index][msg.author.id] = val
        await TotoChannel.send(f'<@{msg.author.id}>님 {self.toto.name[index]}에 {val}xp 베팅되었습니다.', delete_after = 3.0)

    @tasks.loop(seconds = 5.0)
    async def updateembed(self, TotoMessage):
        embed = discord.Embed.from_dict({
            'title' : self.toto.title,
            'color' : 10690248,
            'description' : self.toto.desc,
            'author' : {'name' : "경험치 토토"},
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
                        '`+1000` -> :regional_indicator_a:에 1000xp 베팅\n' + 
                        '`-2000` -> :regional_indicator_b:에 2000xp 베팅\n' + 
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
        res = f'총 베팅 : {cnt}명 - {self.toto.gettot(index)}xp'
        if cnt > 0:
            maxwho, maxbet = self.toto.getmax(index)
            res += f'\n최대 베팅 : {maxwho} - {maxbet}xp'
        prop = self.toto.getprop(index)
        if prop >= 0: res += '\n배당률 : %.2f'%(prop + 1)
        return res

    @commands.command(name = 'endtoto')
    @commands.has_guild_permissions(administrator = True)
    async def EndToto(self, ctx, result):
        await ctx.message.delete()
        winindex = int(result in ('b', 'B'))
        winners, losers = self.toto.bet[::[1, -1][winindex]]
        for loser in losers: self.DB['xps'][loser] -= losers[loser]
        prop = self.toto.getprop(winindex)
        if prop < 0:
            embed = discord.Embed(title = self.toto.title, description = '토토가 종료되었습니다!')
            embed.add_field(name = '토토 결과', value = f'{result} 승리!\n아무도 돈을 얻지 못했습니다!')
        else:
            for winner in winners: self.DB['xps'][winner] += int(winners[winner] * prop)
            embed = discord.Embed(title = self.toto.title, description = '토토가 종료되었습니다!')
            embed.add_field(name = '토토 결과', value = f'{result} 승리!\n{len(winners)}명의 참가자가 건 돈의 %.2f배 이득을 보았습니다!'%(prop + 1))
            maxwho, maxbet = self.toto.getmax(winindex)
            embed.add_field(name = '최대 수익', value = f'{maxwho} - {int(maxbet * prop)}xp를 얻었습니다!')
        await ctx.send(embed = embed)
        del(self.toto)

    @commands.command(name = 'canceltoto')
    @commands.has_guild_permissions(administrator = True)
    async def CancelToto(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(title = self.toto.title, description = '토토가 취소되었습니다!')
        await ctx.send(embed = embed)
        del(self.toto)

    @tasks.loop(minutes = 5)
    async def AutoRole(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        dcRole = discord.utils.get(guild.roles, name = '디창')
        lst = []
        for key in self.DB['xps']: lst.append([self.DB['xps'][key], key])
        for elem in lst:
            who = guild.get_member(elem[1])
            if who == None: continue
            is_dc = self.xp2level(elem[0]) >= 40
            has_dc = dcRole in who.roles
            if is_dc and not has_dc: await who.add_roles(dcRole)
            if not is_dc and has_dc: await who.remove_roles(dcRole)
