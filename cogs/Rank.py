import discord
from discord.ext import commands, tasks
from StudioBot.pkgs.DBCog import DBCog
from PIL import Image, ImageDraw, ImageFont
import os, uuid, pickle
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from io import BytesIO

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Rank'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['channel'] = None
        self.DB['dcRole'] = None
        self.DB['dcPivot'] = None
        self.DB['xps'] = dict()
        self.DB['flag'] = dict()

    @staticmethod
    def level2xp(level):
        return (10 * level ** 3 + 135 * level ** 2 + 455 * level) // 6

    @staticmethod
    def xp2level(xp):
        l, r = 0, 1001
        while r - l > 1:
            mid = (l + r) // 2
            if xp < Core.level2xp(mid): r = mid
            else: l = mid
        return l

    @commands.command(name = 'ranksetup')
    @commands.has_guild_permissions(administrator = True)
    async def Setup(self, ctx, category: discord.CategoryChannel):
        if ctx.guild.id != self.StoryGuild.id: return
        await ctx.message.delete()
        RankChannel = await category.create_text_channel('랭크확인')
        self.DB['channel'] = RankChannel.id
        await RankChannel.edit(sync_permissions = True)

    @commands.command(name = 'rank')
    async def GetRank(self, ctx, arg: discord.Member = None):
        if ctx.guild.id != self.StoryGuild.id: return
        await ctx.message.delete()
        if ctx.channel.id != self.DB['channel']: return
        who = ctx.author
        if arg and ctx.author.guild_permissions.administrator: who = arg
        imgpath = await self.GenRankFrame(who)
        with open(imgpath, 'rb') as fp:
            await ctx.send(file = discord.File(fp), delete_after = 10.0)
        os.remove(imgpath)

    @commands.Cog.listener()
    async def on_ready(self):
        self.StoryGuild = self.app.get_guild(self.GetGlobalDB()['StoryGuildID'])
        self.TopRankMsg.start()
        self.AutoRole.start()

    @tasks.loop(minutes = 10)
    async def TopRankMsg(self):
        msgs = await RankChannel.history(limit = 20).flatten()
        RankChannel = self.StoryGuild.get_channel(self.DB['channel'])
        assert RankChannel
        imgpath = await self.GenRankTable()
        with open(imgpath, 'rb') as fp:
            self.TopRankMessage = await RankChannel.send(file = discord.File(fp))
        os.remove(imgpath)
        await RankChannel.delete_messages(msgs)

    @TopRankMsg.before_loop
    async def ClearChannel(self):
        RankChannel = self.StoryGuild.get_channel(self.DB['channel'])
        await RankChannel.delete_messages(await RankChannel.history(limit = 20).flatten())

    async def GenRankTable(self):
        lst = []
        for whoid in self.DB['xps']:
            if self.StoryGuild.get_member(whoid):
                lst.append((self.DB['xps'][whoid], whoid))
        lst.sort(reverse = True)
        lst = lst[:20]
        for i in range(len(lst)): lst[i] = await self.GetInfo(lst[i][1])
        data = BytesIO()
        pickle.dump(lst, data)
        func = partial(self.GenImages, data)
        with ProcessPoolExecutor() as pool:
            res = await self.app.loop.run_in_executor(pool, func)
        return res

    async def GenRankFrame(self, who):
        data = BytesIO()
        pickle.dump(await self.GetInfo(who), data)
        func = partial(self.GenFrame, data)
        with ProcessPoolExecutor() as pool:
            res = await self.app.loop.run_in_executor(pool, func)
        return res

    async def GetInfo(self, who: discord.Member):

    @staticmethod
    def GenImages(data):
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

    @staticmethod
    def GenFrame(data):
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
        for key in self.DB['xps']:
            if guild.get_member(key):
                lst.append([self.DB['xps'][key], key])
        lst.sort(reverse = True)
        if lst: lst[0].append(1)
        for i in range(1, len(lst)):
            lst[i].append(lst[i - 1][2])
            if lst[i - 1][0] > lst[i][0]: lst[i][2] += 1
        for elem in lst:
            who = guild.get_member(elem[1])
            is_dc = elem[2] <= self.DB['dcPivot']
            has_dc = dcRole in who.roles
            if is_dc and not has_dc: await who.add_roles(dcRole)
            if not is_dc and has_dc: await who.remove_roles(dcRole)
