import discord
from discord.ext import commands, tasks
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from pkgs.Scheduler import Schedule
import youtube_dl, os, uuid, asyncio
from youtubesearchpython import VideosSearch
from functools import wraps

def check_dj(func):
    @wraps(func)
    async def wrapper(self, ctx, *args):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        if ctx.author.guild_permissions.administrator: return await func(self, ctx, *args)
        role = ctx.guild.get_role(self.DB['role'])
        if role in ctx.author.roles: return await func(self, ctx, *args)
    return wrapper

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Stage'
        DBCog.__init__(self, app)
        self.playlist = []
        self.vc = None

    def initDB(self):
        self.DB = dict()
        self.DB['channel'] = None
        self.DB['role'] = None

    @commands.command(name = 'djsetcnl')
    async def SetChannel(self, ctx, ChannelID):
        await ctx.message.delete()
        self.DB['channel'] = int(ChannelID)

    @commands.command(name = 'djsetrole')
    async def SetRole(self, ctx, role: discord.Role):
        await ctx.message.delete()
        self.DB['role'] = role.id

    @commands.group(name = 'dj')
    async def DJGroup(self, ctx):
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Stage DJ.\nSubcommands : add, remove, queue, play, pause, stop, join, leave')

    @DJGroup.command(name = 'add')
    @check_dj
    async def add(self, ctx, *title): await self._add(ctx, False, *title)

    @DJGroup.command(name = 'ads')
    @check_dj
    async def addsong(self, ctx, *title): await self._add(ctx, True, *title)

    async def _add(self, ctx, isos, *title):
        if len(title) == 0: return
        song = self.ydl(title[0])
        title = list(title)
        if isos: title.append('official audio')
        video = VideosSearch(' '.join(title), limit = 1).result()['result']
        if len(video) == 0: return
        video = video[0]
        if song == None: song = self.ydl(video['link'])
        self.playlist.append((video, song))
        await ctx.send(embed = discord.Embed(title = '대기열에 곡이 추가되었습니다', description = video['title']))

    @DJGroup.command(name = 'remove')
    @check_dj
    async def remove(self, ctx, index):
        try:
            index = int(index)
            await ctx.send(embed = discord.Embed(title = '대기열에 곡이 삭제되었습니다', description = self.playlist[index][0]['title']))
            self.playlist.pop(int(index))
        except: pass

    @DJGroup.command(name = 'queue')
    @check_dj
    async def queue(self, ctx):
        txt = []
        for i in range(len(self.playlist), 0, -1): txt.append(f'{i} - {self.playlist[i - 1][0]["title"]}')
        try:
            embed = discord.Embed(title = '현재 재생중', description = f'{self.np["title"]}')
            embed.set_image(url = self.np['thumbnails'][0]['url'])
        except: embed = discord.Embed(title = '현재 재생중인 곡이 없습니다')
        await ctx.send('\n'.join(txt), embed = embed)

    @DJGroup.command(name = 'play')
    @check_dj
    async def play(self, ctx):
        try:
            self.vc.resume()
            if self.flag: self.flag = False
            return
        except: pass
        await self.join(ctx)
        self.flag = False
        while True:
            await asyncio.sleep(0.1)
            try:
                if not self.flag and not self.vc.is_playing():
                    try: os.remove(song)
                    except: pass
                    if len(self.playlist) == 0: continue
                    self.np, song = self.playlist[0]
                    self.playlist.pop(0)
                    self.vc.play(discord.FFmpegPCMAudio(source = song))
                if self.flag and self.vc.is_playing(): self.vc.pause()
            except: break
        os.system('rm *.mp3')
        del(self.np)
        del(self.flag)

    @DJGroup.command(name = 'pause')
    @check_dj
    async def pause(self, ctx):
        try:
            if not self.flag: self.flag = True
        except: pass

    @DJGroup.command(name = 'skip')
    @check_dj
    async def skip(self, ctx):
        try: self.vc.stop()
        except: pass

    @DJGroup.command(name = 'stop')
    @check_dj
    async def stop(self, ctx):
        try:
            if not self.flag: self.flag = True
            self.playlist = []
            self.vc.stop()
            self.flag = False
            await self.vc.disconnected()
        except: pass

    @DJGroup.command(name = 'join')
    @check_dj
    async def join(self, ctx):
        channel = ctx.guild.get_channel(self.DB['channel'])
        if channel == None: return
        if self.vc == None: self.vc = await channel.connect()
        await ctx.guild.get_member(self.app.user.id).edit(suppress = False)

    @DJGroup.command(name = 'leave')
    @check_dj
    async def leave(self, ctx):
        await self.vc.disconnect()
        self.vc = None

    def ydl(self, url):
        songname = f'{uuid.uuid4().hex}.mp3'
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                }],
            'outtmpl': songname, #파일 이름
            }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try: ydl.download([url])
            except: return
        return songname
