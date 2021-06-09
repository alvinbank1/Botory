import discord, asyncio
from StudioBot.pkgs.DBCog import DBCog
from discord.ext import commands
from captcha.image import ImageCaptcha
import uuid, random, os

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Captcha'
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        try: channel = await asyncio.wait_for(member.create_dm(), timeout = 60.0)
        except:
            await member.kick(reason = 'CAPTCHA timeout')
            return
        filename = f'{uuid.uuid4().hex}.png'
        img = ImageCaptcha(fonts = ['NanumGothic.ttf'])
        txt = ''
        chrs = ''
        for i in range(10): chrs += str(i)
        for i in range(26): chrs += chr(i + ord('A'))
        for i in range(6): txt += random.choice(chrs)
        img.write(txt, filename)
        with open(filename, 'rb') as fp: att = discord.File(fp)
        await channel.send('30초 안에 아래 사진의 문자를 정확히 입력하지 않으면 강퇴됩니다. 영어 대문자와 숫자로 구성되어있습니다.', file = att)
        os.remove(filename)
        try:
            await self.app.wait_for('message', check = lambda msg: msg.channel.id == channel.id and msg.content == txt, timeout = 30.0)
            await channel.send('인증되었습니다')
        except asyncio.TimeoutError:
            await channel.send('시간초과입니다. 다시 시도해주세요.')
            await member.kick(reason = 'CAPTCHA timeout')
