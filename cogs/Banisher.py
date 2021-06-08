import discord, asyncio
from discord.ext import commands, tasks
from StudioBot.pkgs.DBCog import DBCog
from datetime import datetime

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Banisher'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB['ModRoles'] = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.StoryGuild = self.app.get_guild(self.GetGlobalDB()['StoryGuildID'])
        self.AutoForgiver.start()

    @tasks.loop()
    async def AutoForgiver(self):
        whoid_list = []
        for whoid in self.DB:
            if whoid == 'ModRoles': continue
            if self.DB[whoid]['expire']: whoid_list.append(whoid)
        whoid_list.sort(key = lambda whoid: self.DB[whoid]['expire'])
        for whoid in whoid_list:
            try:
                who = self.StoryGuild.get_member(whoid)
                time_left = (datetime.now() - self.DB[who.id]['expire_at']).total_seconds()
                time_left = max([0, time_left])
                await asyncio.sleep(time_left)
                await self._forgive(StoryGuild.get_channel(self.DB[who.id]['channel']), who)
            except: del self.DB[whoid]

    @commands.command(name = 'banish')
    @commands.has_guild_permissions(administrator = True)
    async def Banish(self, ctx, who: discord.Member):
        if ctx.guild.id != self.StoryGuild.id: return
        await ctx.message.delete()
        if await self._banish(ctx, who):
            await ctx.channel.send(embed = discord.Embed(title = '', description = f'<@{who.id}> 님을 유배했습니다.'))
        self.AutoForgiver.restart()

    @commands.command(name = 'tempbanish')
    @commands.has_guild_permissions(administrator = True)
    async def TempBanish(self, ctx, who: discord.Member, duration):
        if ctx.guild.id != self.StoryGuild.id: return
        await ctx.message.delete()
        if await self._banish(ctx, who):
            seconds = self.ParseDuration(duration)
            self.DB[who.id]['expire'] = datetime.now() + timedelta(seconds = seconds)
            await ctx.channel.send(embed = discord.Embed(title = '',
                description = f'<@{who.id}> 님을 {self.Duration2text(timedelta(seconds = seconds))}동안 유배했습니다.'))
        self.AutoForgiver.restart()

    @commands.command(name = 'forgive')
    @commands.has_guild_permissions(administrator = True)
    async def Forgive(self, ctx, who: discord.Member):
        if ctx.guild.id != self.StoryGuild.id: return
        await ctx.message.delete()
        await self._forgive(ctx.channel, who)
        self.AutoForgiver.restart()

    async def _banish(self, ctx, who):
        if who.id in self.DB:
            await ctx.channel.send(embed = discord.Embed(title = '', description = f'<@{who.id}> 님은 이미 유배중입니다.'))
            return False
        await who.edit(nick = '[유배중] ' + self.GetDisplayName(who))
        roles = []
        for role in who.roles:
            if role.id in self.DB['ModRoles']: roles.append(role)
        await who.remove_roles(*roles[::-1])
        roles = list(map(lambda role: role.id, roles))
        self.DB[who.id] = {'channel' : ctx.channel.id, 'nick' : nick, 'roles' : roles, 'expire' : None}

    async def _forgive(self, channel, who):
        if who.id not in self.DB:
            await channel.send(embed = discord.Embed(title = '', description = f'<@{who.id}> 님은 유배중이 아닙니다.'))
            return 
        nick = self.DB[who.id]['nick']
        roles = []
        for role_id in self.DB[who.id]['roles']:
            role = who.guild.get_role(role_id)
            roles.append(role)
        del self.DB[who.id]
        await who.edit(nick = nick)
        await who.add_roles(*roles)
        await channel.send(embed = discord.Embed(title = '', description = f'<@{who.id}> 님을 복직시켰습니다.'))
