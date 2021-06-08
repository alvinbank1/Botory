import discord, asyncio
from discord.ext import commands, tasks
from StudioBot.pkgs.DBCog import DBCog
from PIL import Image, ImageDraw, ImageFont
import uuid, os
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from io import BytesIO

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Status'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['AllCount'] = None
        self.DB['MemberCount'] = None
        self.DB['BoostCount'] = None
        self.DB['images'] = dict()

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.app.get_guild(GlobalDB['StoryGuildID'])
        self.StatusViewer.start()
        self.BoostStatus.start()

    @commands.group(name = 'status')
    @commands.has_guild_permissions(administrator = True)
    async def StatusGroup(self, ctx):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Status Manager\nSubcommands : setimg, setup')

    @StatusGroup.command(name = 'setup')
    async def StatusSetup(self, ctx, category: discord.CategoryChannel):
        self.DB['AllCount'] = await category.create_voice_channel('전체 멤버 - 측정중🔄')
        self.DB['MemberCount'] = await category.create_voice_channel('정식 멤버 - 측정중🔄')
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        self.DB['BoostCount'] = await category.create_text_channel('부스터 측정중🔄', overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages = False),
                MemberRole: discord.PermissionOverwrite(read_messages = True, send_messages = False, add_reactions = False)
            })
        for key in self.DB:
            if key != 'images': self.DB[key] = self.DB[key].id
        self.StatusViewer.restart()
        self.BoostStatus.restart()

    @StatusGroup.command(name = 'setimg')
    async def StatusSetImages(self, ctx):
        def checker(message): return message.author == ctx.author and message.channel == ctx.channel
        for name in ['header', 'background', 'template']:
            await ctx.send(f'send {name}')
            reply = await self.app.wait_for('message', check = checker)
            filename = f'{uuid.uuid4().hex}.png'
            with open(filename, 'wb') as fp: await reply.attachments[0].save(fp)
            self.DB['images'][name] = Image.open(filename).convert('RGBA')
            os.remove(filename)
        self.BoostStatus.restart()

    @tasks.loop(minutes = 10.0)
    async def StatusViewer(self):
        MemberCount = 0
        async for member in self.guild.fetch_members(limit = None):
            if self.MemberRole in member.roles: MemberCount += 1
        await self.AllCountChannel.edit(name = f'전체 멤버 - {self.guild.member_count}명')
        await self.MemberCountChannel.edit(name = f'정식 멤버 - {MemberCount}명')

    @StatusViewer.before_loop
    async def PreStatusViewer(self):
        self.MemberRole = discord.utils.get(self.guild.roles, name = '멤버')
        self.AllCountChannel = self.guild.get_channel(self.DB['AllCount'])
        self.MemberCountChannel = self.guild.get_channel(self.DB['MemberCount'])

    @tasks.loop(minutes = 10.0)
    async def BoostStatus(self):
        await self.BoostCountChannel.edit(name = f'{self.guild.premium_subscription_count}부스트⚬{self.guild.premium_tier}레벨⚬{len(self.guild.premium_subscribers)}명')
        msgs = await self.BoostCountChannel.history(limit = 10).flatten()
        await self.SendBoostMsgs()
        await self.BoostCountChannel.delete_messages(msgs)

    @BoostStatus.before_loop
    async def PreBoostStatus(self):
        self.BoostCountChannel = self.guild.get_channel(self.DB['BoostCount'])
        await self.BoostCountChannel.delete_messages(await self.BoostCountChannel.history(limit = 6).flatten())

    async def SendBoostMsgs(self):
        boosters = self.guild.premium_subscribers
        db = []
        for key in self.DB['images']:
            img = BytesIO()
            self.DB['images'][key].save(img, 'png')
            db.append((key, img))
        db = tuple(db)
        _bs = []
        for who in boosters:
            _bs.append((str(who.avatar_url), self.GetDisplayName(who)))
        _bs = tuple(_bs)
        func = partial(self.GenImages, db, _bs)
        with ProcessPoolExecutor() as pool:
            imagepaths = await self.app.loop.run_in_executor(pool, func)
        files = []
        for path in imagepaths:
            with open(path, 'rb') as fp: files.append(discord.File(fp))
            os.remove(path)
        await self.BoostCountChannel.send(files = files)
        if len(boosters) == 0: await self.BoostCountChannel.send('부스터가 없습니다.')

    @staticmethod
    def GenImages(_db, boosters):
        DB = dict()
        for item in _db:
            key = item[0]
            img = Image.open(item[1])
            DB[key] = img
        def GetBestArrangement(n):
            if n == 1: return [1], 2250
            arng, sz = [], 0
            for h in range(1, n):
                _arng = [n // h] * h
                for j in range(n % h): _arng[j] += 1
                _sz = min([3000 // _arng[0], 5000 // h])
                if _sz > sz: arng, sz = _arng, _sz
            return arng, sz

        def GenFrame(avatar, nick, length):
            tplt = DB['template'].copy()
            ret = Image.new('RGBA', tplt.size, color = (0, 0, 0, 0))
            l, r, t, b = tplt.width + 1, -1, tplt.height + 1, -1
            for x in range(tplt.width):
                for y in range(tplt.height):
                    if tplt.load()[x, y][3] == 0:
                        l = min([x, l])
                        r = max([x, r])
                        t = min([y, t])
                        b = max([y, b])
            assert r >= 0
            pf = Image.open(avatar).convert('RGBA').resize((r - l + 1, b - t + 1))
            ret.paste(pf, (l, t))
            ret.alpha_composite(tplt)
            textimg = Image.new('RGBA', tplt.size, color = (0, 0, 0, 0))
            canvas = ImageDraw.Draw(textimg)
            if len(nick) > 9: nick = nick[:8] + '...'
            canvas.text((textimg.width // 2, int(textimg.height * 0.8)), nick, font = ImageFont.truetype('NanumGothic.ttf', 65), fill = (255, 0, 255, 255), align = 'center', anchor = 'mm', stroke_width = 2)
            ret.alpha_composite(textimg)
            return ret.resize((length, length))

        arng, sz = GetBestArrangement(len(boosters))
        img = DB['background'].resize((3000, len(arng) * sz))
        index = 0
        dy = (img.height + sz) // (len(arng) + 1)
        y = dy - sz
        for i in range(len(arng)):
            dx = (img.width + sz) // (arng[i] + 1)
            x = dx - sz
            for j in range(arng[i]):
                img.paste(GenFrame(*boosters[index], sz), (x, y))
                x += dx
                index += 1
            y += dy
        cheight = 2250 // sz * sz
        cuts = [0]
        if cheight > 0:
            for i in range(1, 9):
                if cheight * i >= img.height: break
                cuts.append(cheight * i)
        cuts.append(img.height)
        imgs = [DB['header']]
        for i in range(len(cuts) - 1):
            imgs.append(img.crop((0, cuts[i], 3000, cuts[i + 1])))
        res = []
        for img in imgs:
            filename = f'{uuid.uuid4().hex}.png'
            res.append(filename)
            img.save(filename)
        return res
