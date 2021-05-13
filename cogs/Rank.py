import discord
from discord.ext import commands, tasks
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from pkgs.Scheduler import Schedule
from PIL import Image, ImageDraw, ImageFont
import requests, os, uuid

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Rank'
        DBCog.__init__(self, app)
        self.TopRankMessage = None

    def initDB(self):
        self.DB = dict()
        self.DB['channel'] = None
        self.DB['xps'] = dict()
        self.DB['flag'] = dict()
        self.DB['dcRole'] = None
        self.DB['dcPivot'] = None

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
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        Category = ctx.guild.get_channel(int(CategoryID))
        RankChannel = await Category.create_text_channel('랭크확인')
        self.DB['channel'] = RankChannel.id
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await RankChannel.edit(sync_permissions = True)

    @commands.command(name = 'rank')
    async def GetRank(self, ctx, arg = None):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        if ctx.channel.id != self.DB['channel']: return
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
        await self.ClearChannel()
        self.TopRankMsg.start()
        self.AutoRole.start()

    async def ClearChannel(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        RankChannel = guild.get_channel(self.DB['channel'])
        OldMessages = await RankChannel.history(limit = 100).flatten()
        RankChannel.delete_messages(*OldMessages)

    @tasks.loop(minutes = 10)
    async def TopRankMsg(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        RankChannel = guild.get_channel(self.DB['channel'])
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
        for key in self.DB['xps']: lst.append([self.DB['xps'][key], key])
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
        xp = 0
        if who.id in self.DB['xps']: xp = self.DB['xps'][who.id]
        if rank == None: 
            guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
            rank = 1
            for key in self.DB['xps']:
                if guild.get_member(key) == None: continue
                if self.DB['xps'][key] > xp: rank += 1
        level = self.xp2level(xp)
        if level == 1000: prop = 1
        else: prop = (xp - self.level2xp(level)) / (self.level2xp(level + 1) - self.level2xp(level))

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
     
        name = self.GetDisplayName(who)
        if len(name) > 9: name = name[:8] + '...'
        if level == 1000: level = 'MAX'
        else: level = str(level)
        canvas.text((450, 150), name, font = ImageFont.truetype('NanumGothic.ttf', 60), fill = (255, 255, 255), anchor = 'lm')
        canvas.text((1350, 165), level, font = ImageFont.truetype('NanumGothic.ttf', 48), fill = (255, 255, 255), align = 'center', anchor = 'mm')
        canvas.text((1110, 165), '%.1fk'%(xp / 1000), font = ImageFont.truetype('NanumGothic.ttf', 48), fill = (255, 255, 255), anchor = 'mm')

        res.convert('RGBA')
        profile = Image.open(requests.get(who.avatar_url, stream = True).raw)
        profile = profile.resize((120, 120))
        mask = Image.new('L', (120, 120), 0)
        mcanvas = ImageDraw.Draw(mask)
        mcanvas.ellipse((0, 0, 120, 120), fill = 255)
        res.paste(profile, (300, 90), mask = mask)
        return res

    @commands.command(name = 'givexp')
    @commands.has_guild_permissions(administrator = True)
    async def GiveXP(self, ctx, who, val):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['xps']: self.DB['xps'][who.id] = 0
        self.DB['xps'][who.id] += int(val)
        embed = discord.Embed(title = '', description = f'<@{who.id}> 님께 {val}xp가 지급되었습니다.')
        await ctx.channel.send(embed = embed)

    @commands.command(name = 'takexp')
    @commands.has_guild_permissions(administrator = True)
    async def TakeXP(self, ctx, who, val):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['xps']: self.DB['xps'][who.id] = 0
        self.DB['xps'][who.id] -= int(val)
        if self.DB['xps'][who.id] < 0: self.DB['xps'][who.id] = 0
        embed = discord.Embed(title = '', description = f'<@{who.id}> 님에게서 {val}xp가 제거되었습니다.')
        await ctx.channel.send(embed = embed)

    @commands.Cog.listener('on_message')
    async def messageXP(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.author.bot: return
        if message.channel.id == self.DB['channel']: return
        whoid = message.author.id
        if whoid not in self.DB['flag']: self.DB['flag'][whoid] = Schedule('0s')
        if self.DB['flag'][whoid].is_done():
            if whoid not in self.DB['xps']: self.DB['xps'][whoid] = 0
            self.DB['xps'][whoid] += 20
            self.DB['flag'][whoid] = Schedule('1m')

    @commands.Cog.listener('on_message')
    async def nomsginrank(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.channel.id != self.DB['channel']: return
        if message.author.id == self.app.user.id: return
        ctx = await self.app.get_context(message)
        if not ctx.valid: await message.delete()

    @commands.command(name = 'setdcrole')
    @commands.has_guild_permissions(administrator = True)
    async def SetRole(self, ctx, role, val):
        await ctx.message.delete()
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        role = self.mention2role(role, ctx.guild)
        self.DB['dcRole'] = role.id
        self.DB['dcPivot'] = int(val)

    @tasks.loop(minutes = 10)
    async def AutoRole(self):
        guild = self.app.get_guild(GlobalDB['StoryGuildID'])        
        dcRole = guild.get_role(self.DB['dcRole'])
        if dcRole == None: return
        lst = []
        for key in self.DB['xps']: lst.append([self.DB['xps'][key], key])
        lst.sort(reverse = True)
        if lst: lst[0].append(1)
        for i in range(1, len(lst)):
            lst[i].append(lst[i - 1][2])
            if lst[i - 1][0] > lst[i][0]: lst[i][2] += 1
        for elem in lst:
            who = guild.get_member(elem[1])
            if who == None: continue
            is_dc = elem[2] <= self.DB['dcPivot']
            has_dc = dcRole in who.roles
            if is_dc and not has_dc: await who.add_roles(dcRole)
            if not is_dc and has_dc: await who.remove_roles(dcRole)
