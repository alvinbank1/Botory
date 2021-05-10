import discord
from discord.ext import commands, tasks
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from pkgs.Scheduler import Schedule
from PIL import Image, ImageDraw, ImageFont
import random, uuid, os, asyncio, requests
from datetime import datetime, timedelta

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
        DBCog.__init__(self, app)
        self.TopRankMessage = None
        self.LastRaid = None

    def initDB(self):
        self.DB = dict()
        self.DB['BankChannel'] = None
        self.DB['TotoChannel'] = None
        self.DB['RaidChannel'] = None
        self.DB['mns'] = dict()
        self.DB['RichRole'] = None
        self.DB['RichPivot'] = None
        self.DB['flag'] = dict()

    @commands.group(name = 'toto')
    @commands.has_guild_permissions(administrator = True)
    async def TotoGroup(self, ctx):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return

    @TotoGroup.command(name = 'setup')
    async def Setup(self, ctx, CategoryID):
        Category = ctx.guild.get_channel(int(CategoryID))
        BankChannel = await Category.create_text_channel('계좌확인')
        TotoChannel = await Category.create_text_channel('토토')
        self.DB['BankChannel'] = BankChannel.id
        self.DB['TotoChannel'] = TotoChannel.id
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await BankChannel.edit(sync_permissions = True, topic = '&money 를 쳐서 잔액을 확인하세요! 채팅을 치다보면 1분마다 도토리를 50개씩 얻을 수 있습니다.')
        await TotoChannel.edit(sync_permissions = True)
        await TotoChannel.set_permissions(MemberRole, send_messages = False)

    @TotoGroup.command(name = 'new')
    async def NewToto(self, ctx, title, desc, team0, team1):
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
        if msg.author.id not in self.DB['mns'] or abs(val) > self.DB['mns'][msg.author.id]:
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
        for loser in losers: self.DB['mns'][loser] -= losers[loser]
        prop = self.toto.getprop(winindex)
        if prop < 0:
            embed = discord.Embed(title = self.toto.title, description = '토토가 종료되었습니다!')
            embed.add_field(name = '토토 결과', value = f'{result} 승리!\n아무도 돈을 얻지 못했습니다!')
        else:
            for winner in winners: self.DB['mns'][winner] += int(winners[winner] * prop)
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

    @commands.command(name = 'money')
    async def GetRank(self, ctx, arg = None):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        if ctx.channel.id != self.DB['BankChannel']: return
        who = ctx.author
        if arg and ctx.author.guild_permissions.administrator: who = self.mention2member(arg, ctx.guild)
        img = self._makerankone(who)
        imgname = uuid.uuid4().hex + '.png'
        img.save(imgname)
        with open(imgname, 'rb') as fp:
            await ctx.send(file = discord.File(fp), delete_after = 10.0)
        os.remove(imgname)

    @commands.Cog.listener()
    async def on_ready(self):
        self.TopRankMsg.start()
        self.AutoRole.start()
        self.FeverRaid.start()

    @tasks.loop(minutes = 10)
    async def TopRankMsg(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        RankChannel = guild.get_channel(self.DB['BankChannel'])
        if RankChannel == None: return
        img = self.makerankimg()
        imgname = uuid.uuid4().hex + '.png'
        img.save(imgname)
        with open(imgname, 'rb') as fp:
            try: await self.TopRankMessage.delete()
            except: pass
            self.TopRankMessage = await RankChannel.send(file = discord.File(fp))
        os.remove(imgname)

    def makerankimg(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        lst = []
        for key in self.DB['mns']: lst.append([self.DB['mns'][key], key])
        lst.sort(reverse = True)
        res = Image.new("RGB", (1480 * 2 + 20, 280 * 10 + 20), (50, 50, 50))
        i = 0
        for elem in lst:
            if i > 19: break
            who = guild.get_member(elem[1])
            if who == None: continue
            one = self._makerankone(who, i + 1) 
            res.paste(one, ((i // 10) * 1480, (i % 10) * 280))
            i += 1
        return res

    def _makerankone(self, who, rank = None):
        money = 0
        if who.id in self.DB['mns']: money = self.DB['mns'][who.id]
        if rank == None: 
            guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
            rank = 1
            for key in self.DB['mns']:
                if guild.get_member(key) == None: continue
                if self.DB['mns'][key] > money: rank += 1

        res = Image.new("RGB", (1500, 300), (50, 50, 50))
        canvas = ImageDraw.Draw(res)
        canvas.rectangle((0, 0, 1500, 300), outline = (70, 70, 70), width = 20)
        canvas.text((1150, 120), '도토리', font = ImageFont.truetype('NanumGothic.ttf', 30), fill = (140, 140, 140), align = 'center', anchor = 'mm')

        if rank < 4: rankcolor = [(212, 175, 55), (208, 208, 208), (138, 84, 30)][rank - 1]
        else: rankcolor = (100, 100, 100)
        darkercolor = tuple(c - 20 for c in rankcolor)
        canvas.ellipse((75, 75, 225, 225), fill = rankcolor, width = 12, outline = darkercolor)
        canvas.text((150, 150), str(rank), font = ImageFont.truetype('NanumGothic.ttf', 90), fill = (255, 255, 255),
            anchor = 'mm', stroke_width = 4, stroke_fill = (0, 0, 0))
     
        name = self.GetDisplayName(who)
        if len(name) > 10: name = name[:9] + '...'
        canvas.text((450, 150), name, font = ImageFont.truetype('NanumGothic.ttf', 60), fill = (255, 255, 255), anchor = 'lm')
        moneystr = str(money)
        if len(moneystr) > 3: moneystr = '%.1fk'%(money / 1000)
        if len(moneystr) > 6: moneystr = '%.1fM'%(money / 1000 ** 2)
        canvas.text((1150, 165), moneystr, font = ImageFont.truetype('NanumGothic.ttf', 48), fill = (255, 255, 255), anchor = 'mm')

        res.convert('RGBA')
        profile = Image.open(requests.get(who.avatar_url, stream = True).raw)
        profile = profile.resize((120, 120))
        mask = Image.new('L', (120, 120), 0)
        mcanvas = ImageDraw.Draw(mask)
        mcanvas.ellipse((0, 0, 120, 120), fill = 255)
        res.paste(profile, (300, 90), mask = mask)
        return res

    @commands.command(name = 'givemoney')
    @commands.has_guild_permissions(administrator = True)
    async def GiveXP(self, ctx, who, val):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['mns']: self.DB['mns'][who.id] = 0
        self.DB['mns'][who.id] += int(val)

    @commands.command(name = 'takemoney')
    @commands.has_guild_permissions(administrator = True)
    async def TakeXP(self, ctx, who, val):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['mns']: self.DB['mns'][who.id] = 0
        self.DB['mns'][who.id] -= int(val)
        if self.DB['mns'][who.id] < 0: self.DB['mns'][who.id] = 0

    @commands.command(name = 'setrichrole')
    @commands.has_guild_permissions(administrator = True)
    async def SetRole(self, ctx, role, val):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        role = self.mention2role(role, ctx.guild)
        self.DB['RichRole'] = role.id
        self.DB['RichPivot'] = int(val)

    @commands.command(name = 'setraidhere')
    @commands.has_guild_permissions(administrator = True)
    async def SetRaid(self, ctx):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        self.DB['RaidChannel'] = ctx.channel.id

    @commands.Cog.listener('on_message')
    async def messageXP(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.author.bot: return
        if message.channel.id in (self.DB['BankChannel'], self.DB['TotoChannel']): return
        whoid = message.author.id
        if whoid not in self.DB['flag']: self.DB['flag'][whoid] = Schedule('0s')
        if self.DB['flag'][whoid].is_done():
            if whoid not in self.DB['mns']: self.DB['mns'][whoid] = 0
            self.DB['mns'][whoid] += 50
            self.DB['flag'][whoid] = Schedule('1m')

    @commands.Cog.listener('on_message')
    async def nomsginrank(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.channel.id != self.DB['BankChannel']: return
        if message.author.id == self.app.user.id: return
        ctx = await self.app.get_context(message)
        if not ctx.valid: await message.delete()

    @tasks.loop(minutes = 10)
    async def AutoRole(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        RichRole = guild.get_role(self.DB['RichRole'])
        if RichRole == None: return
        lst = []
        for key in self.DB['mns']: lst.append([self.DB['mns'][key], key])
        lst.sort(reverse = True)
        if lst: lst[0].append(1)
        for i in range(1, len(lst)):
            lst[i].append(lst[i - 1][2])
            if lst[i - 1][0] > lst[i][0]: lst[i][2] += 1
        for elem in lst:
            who = guild.get_member(elem[1])
            if who == None: continue
            is_rich = elem[2] <= self.DB['RichPivot']
            has_rich = RichRole in who.roles
            if is_rich and not has_rich: await who.add_roles(RichRole)
            if not is_rich and has_rich: await who.remove_roles(RichRole)

    @tasks.loop(minutes = 3)
    async def FeverRaid(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        RaidChannel = guild.get_channel(self.DB['RaidChannel'])
        if RaidChannel == None: return
        try:
            if (await RaidChannel.fetch_message(RaidChannel.last_message_id)).author.bot: return
        except: pass
        if random.random() >= 1 / 10: return
        aww = discord.utils.get(guild.emojis, name = 'rage_aww')
        prize = 500
        if self.LastRaid:
            hdelta = (datetime.now() - self.LastRaid).total_seconds() / 3600
            prize = int(hdelta * 1000)
            prize = max([500, prize])
        self.RaidMessage = await RaidChannel.send(embed = discord.Embed(
            title = '도토리 레이드 도착!',
            description = f'15초 안에 아래 이모지를 눌러서 도토리 {prize}개를 받으세요!'))
        await self.RaidMessage.add_reaction(aww)
        self.raiders = set()
        self.on_raid = True
        await asyncio.sleep(15)
        self.LastRaid = datetime.now()
        self.on_raid = False
        desc = ''
        for raider in self.raiders:
            dispname = self.GetDisplayName(raider)
            desc += dispname + ', '
        desc = f'{desc[:-2]}\n\n도토리 {prize}개를 획득하셨습니다!'
        if len(self.raiders) == 0:
            if prize < 1000: f'아무도 도토리 {prize}개를 획득하지 못하셨습니다!'
            else: f'아무도 레이드를 성공하지 못했습니다!\n무려 {prize}개짜리였는데!'
        await self.RaidMessage.edit(embed = discord.Embed(title = '도토리 레이드 마감~~!', description = desc))
        for user in self.raiders:
            if user.id not in self.DB['mns']: self.DB['mns'][user.id] = 0
            self.DB['mns'][user.id] += prize

    @commands.Cog.listener('on_reaction_add')
    async def onRaidReaction(self, reaction, user):
        if not self.on_raid: return
        if reaction.message != self.RaidMessage: return
        if user.bot: return
        if reaction.emoji.name != 'rage_aww': return
        self.raiders.add(user)
