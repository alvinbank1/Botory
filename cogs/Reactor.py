import discord
from discord.ext import commands, tasks
from StudioBot.pkgs.DBCog import DBCog
from datetime import datetime
from typing import Union

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Reactor'
        DBCog.__init__(self, app)

    def initDB(self): self.DB['ReactChannelID'] = None

    @commands.group(name = 'reactor')
    @commands.has_guild_permissions(administrator = True)
    async def ReactorGroup(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Automatic reactor.\n'
                + 'Subcommands : set, tempset, unset')

    async def SetReactDB(self, who, whats):
        self.DB[who.id] = dict()
        emojis = []
        for what in whats:
            try: emojis.append(int(what.split(':')[2][:-1]))
            except: emojis.append(what)
        self.DB[who.id]['emojis'] = emojis

    @ReactorGroup.command(name = 'set')
    async def SetReact(self, ctx, who: discord.Member, *whats):
        await self.SetReactDB(who, whats)
        self.DB[who.id]['expire'] = None
        embed = discord.Embed(title = '', description = f'<@{who.id}> 님께 자동 이모지가 등록되었습니다.')
        await ctx.channel.send(embed = embed)

    @ReactorGroup.command(name = "tempset")
    async def SetTempReact(self, ctx, who: discord.Member, duration, *whats):
        await self.SetReactDB(who, whats)
        durationtext = self.Duration2text(self.ParseDuration(duration))
        embed = discord.Embed(title = '', description = f'<@{who.id}> 님께 {durationtext}동안 자동 이모지가 등록되었습니다.')
        self.DB[who.id]['expire'] = datetime.now() + self.ParseDuration(duration)
        await ctx.channel.send(embed = embed)

    @ReactorGroup.command(name = "unset")
    async def UnsetReact(self, ctx, who: Union[str, discord.Member]):
        if who == "all": self.DB = dict()
        else: del self.DB[who.id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild == None: return
        if message.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        if message.author.id in self.DB:
            expiration = self.DB[message.author.id]['expire']
            if expiration:
                if expiration <= datetime.now():
                    del self.DB[message.author.id]
                    return
            emojis = self.DB[message.author.id]['emojis']
            for emoji in emojis:
                if type(emoji) == int: emoji = discord.utils.get(self.app.emojis, id = emoji)
                await message.add_reaction(emoji)

    @commands.command(name = 'reacthere')
    @commands.has_guild_permissions(administrator = True)
    async def SetReact(self, ctx):
        await ctx.message.delete()
        self.DB['ReactChannelID'] = ctx.channel.id

    @commands.Cog.listener()
    async def on_ready(self): self.ReactSender.start()

    @tasks.loop(seconds = 5)
    async def ReactSender(self):
        StoryGuild = self.app.get_guild(self.GetGlobalDB()['StoryGuildID'])
        if not self.DB['ReactChannelID']: return
        ReactChannel = StoryGuild.get_channel(self.DB['ReactChannelID'])
        LastMessage = await ReactChannel.history(limit = 1).flatten()
        if not LastMessage: return
        LastMessage = LastMessage[0]
        if len(LastMessage.reactions) < 20: return
        await ReactChannel.send(chr(8203))
