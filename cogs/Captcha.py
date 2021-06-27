import discord, asyncio
from StudioBot.pkgs.DBCog import DBCog
from discord.ext import commands
from captcha.image import ImageCaptcha
import uuid, random, os
from concurrent.futures import ProcessPoolExecutor

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Captcha'
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        channel = await member.create_dm()
        with ProcessPoolExecutor() as pool:
            filename, txt = await self.app.loop.run_in_executor(pool, self.GenImage)
        with open(filename, 'rb') as fp: att = discord.File(fp)
        msg = None
        for i in range(12):
            try:
                msg = await channel.send('' + 
                    '30초 안에 아래 사진의 문자를 정확히 입력하지 않으면 강퇴됩니다.\n' +
                    '영어 대문자로 구성되어있습니다.\n' +
                    '반응이 없으면 틀려서 그런겁니다. O와 Q, 일그러진 D와 O 등을 잘 구분해보세요.', file = att)
                break
            except discord.HTTPException: await asyncio.sleep(5)
        os.remove(filename)
        try:
            if msg == None: raise asyncio.TimeoutError()
            await self.app.wait_for('message', check = lambda msg: msg.channel.id == channel.id and msg.content == txt, timeout = 30.0)
            await channel.send('인증되었습니다')
        except asyncio.TimeoutError:
            await channel.send('시간초과입니다. 다시 시도해주세요.')
            await member.kick(reason = 'CAPTCHA timeout')

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
