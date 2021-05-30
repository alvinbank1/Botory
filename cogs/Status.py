import discord, asyncio
from discord.ext import commands, tasks
from pkgs.GlobalDB import GlobalDB
from pkgs.DBCog import DBCog
from PIL import Image, ImageDraw, ImageFont
import uuid, os, requests

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Status'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB = dict()
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
    async def StatusSetup(self, ctx, CategoryID):
        SetupCategory = discord.utils.get(ctx.guild.categories, id = int(CategoryID))
        self.DB['AllCount'] = await SetupCategory.create_voice_channel('전체 멤버 - 측정중🔄')
        self.DB['MemberCount'] = await SetupCategory.create_voice_channel('정식 멤버 - 측정중🔄')
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        self.DB['BoostCount'] = await SetupCategory.create_text_channel('부스터 측정중🔄', overwrites = {
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
            with open(filename, 'wb') as fp:
                await reply.attachments[0].save(fp)
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
        await self.BoostCountChannel.delete_messages(await self.BoostCountChannel.history(limit = 6).flatten())
        await self.SendBoostMsgs()

    @BoostStatus.before_loop
    async def PreBoostStatus(self):
        self.BoostCountChannel = self.guild.get_channel(self.DB['BoostCount'])
        await self.BoostCountChannel.delete_messages(await self.BoostCountChannel.history(limit = 6).flatten())

    async def SendBoostMsgs(self):
        await self._SendHeader()
        boosters = self.guild.premium_subscribers
        if len(boosters) == 0: await self.BoostCountChannel.send('부스터가 없습니다ㅠㅠ')
        elif len(boosters) < 7: await self._SendOne(boosters)
        else:
            pivot = (len(boosters) + 1) // 2
            await self._SendOne(boosters[:pivot])
            await self._SendOne(boosters[pivot:])

    async def _SendHeader(self):
        await self._SendImage(self.DB['images']['header'], self.BoostCountChannel)

    async def _SendOne(self, boosters):
        hcnt = int(len(boosters) ** 0.5)
        lst = [len(boosters) // hcnt] * hcnt
        for i in range(len(boosters) % hcnt): lst[i] += 1
        img = self.DB['images']['background'].copy()
        tplt = self.DB['images']['template'].copy()
        length = min((img.height // hcnt, img.width // lst[0]))
        dy = (img.height + length) // (hcnt + 1)
        y = dy - length
        index = 0
        for i in range(hcnt):
            dx = (img.width + length) // (lst[i] + 1)
            x = dx - length
            for j in range(lst[i]):
                img.paste(await self.makeframe(boosters[index], length), (x, y))
                x += dx
                index += 1
            y += dy
        await self._SendImage(img, self.BoostCountChannel)

    async def makeframe(self, who, length):
        tplt = self.DB['images']['template'].copy()
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
        pf = Image.open(requests.get(who.avatar_url, stream = True).raw).convert('RGBA').resize((r - l + 1, b - t + 1))
        ret.paste(pf, (l, t))
        ret.alpha_composite(tplt)
        textimg = Image.new('RGBA', tplt.size, color = (0, 0, 0, 0))
        canvas = ImageDraw.Draw(textimg)
        nick = self.GetDisplayName(who)
        if len(nick) > 9: nick = nick[:8] + '...'
        canvas.text((textimg.width // 2, int(textimg.height * 0.8)), nick, font = ImageFont.truetype('NanumGothic.ttf', 65), fill = (255, 0, 255, 255), align = 'center', anchor = 'mm', stroke_width = 2)
        ret.alpha_composite(textimg)
        return ret.resize((length, length))

    async def _SendImage(self, img, channel):
        filename = f'{uuid.uuid4().hex}.png'
        img.save(filename)
        with open(filename, 'rb') as fp:
            await channel.send(file = discord.File(fp))
        os.remove(filename)
