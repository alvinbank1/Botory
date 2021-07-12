import discord, asyncio
from StudioBot.pkgs.DBCog import DBCog
from discord.ext import commands
from captcha.image import ImageCaptcha
import uuid, random, os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Captcha'
        self.flags = []
        self.running = set()
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.Cog.listener('on_member_join')
    async def RunCaptcha(self, member):
        if member.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        if member.id in self.running: return
        self.running.add(member.id)
        channel = await member.create_dm()
        with ProcessPoolExecutor() as pool:
            filename, txt = await self.app.loop.run_in_executor(pool, self.GenImage)
        with open(filename, 'rb') as fp: att = discord.File(fp)
        msg = None
        for i in range(6):
            try:
                msg = await channel.send('' + 
                    '30초 안에 아래 사진의 문자를 정확히 입력하지 않으면 강퇴됩니다.\n' +
                    '영어 대문자로 구성되어있습니다.\n' +
                    '팁) 반응이 없으면 틀려서 그런겁니다. O와 Q, 일그러진 D와 O 등을 잘 구분해보세요.', file = att)
                break
            except discord.HTTPException: await asyncio.sleep(5)
        os.remove(filename)
        try:
            if msg == None: raise asyncio.TimeoutError()
            await self.app.wait_for('message', check = lambda msg: msg.channel.id == channel.id and msg.content == txt, timeout = 30.0)
            await channel.send('인증되었습니다')
        except asyncio.TimeoutError:
            try: await channel.send('시간초과입니다. 다시 시도해주세요.')
            except: pass
            try: await member.kick(reason = 'CAPTCHA timeout')
            except: pass
        except: pass
        self.running.remove(member.id)

    @commands.command(name = 'setvanishurl')
    @commands.has_guild_permissions(administrator = True)
    async def SetVanishUrl(self, ctx, url):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        await ctx.guild.edit(vanity_code = url)

    @commands.Cog.listener('on_member_join')
    async def CheckRush(self, member):
        if member.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        i = 0
        while i < len(self.flags):
            if self.flags[i][1] == member.id:
                del self.flags[i]
                i -= 1
            i += 1
        self.flags.append((datetime.now(), member.id))
        if len(self.flags) > 4:
            if self.flags[-1][0] - self.flags.pop(0)[0] < timedelta(minutes = 1):
                await member.guild.edit(vanity_code = None)
                owner = self.app.get_user(self.GetGlobalDB()['OwnerID'])
                channel = await owner.create_dm()
                await channel.send('Join rush가 감지되어 초대코드를 제거하였습니다.')

    @staticmethod
    def GenImage():
        filename = f'{uuid.uuid4().hex}.png'
        img = ImageCaptcha(fonts = ['NanumGothic.ttf'])
        txt = ''
        chrs = ''
        for i in range(26): chrs += chr(i + ord('A'))
        for i in range(6): txt += random.choice(chrs)
        img.write(txt, filename)
        return filename, txt
