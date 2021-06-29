import discord
from discord.ext import commands, tasks
from StudioBot.pkgs.DBCog import DBCog
from datetime import datetime, timezone, timedelta

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Logger'
        self.ChannelNames = ['Reaction', 'Attachments']
        self.queue = []
        DBCog.__init__(self, app)

    def initDB(self):
        for ChannelName in self.ChannelNames: self.DB[ChannelName] = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.app.get_guild(self.GetGlobalDB()['StoryGuildID'])
        try:
            RLogChannel = self.guild.get_channel(self.DB['Reaction'][0])
            for self.hook in await RLogChannel.webhooks():
                if self.hook.id == self.DB['Reaction'][1]: break
        except: pass
        self.AutoFlush.start()
        self.Undead.start()

    @commands.group(name = 'logger')
    @commands.has_guild_permissions(administrator = True)
    async def LoggerGroup(self, ctx):
        if ctx.guild.id != self.guild.id: return
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Logger system.\nSubcommands : setcnl')

    @LoggerGroup.command(name = 'setcnl')
    async def SetChannels(self, ctx, ChannelName = None):
        if ChannelName not in self.ChannelNames:
            await ctx.channel.send('Available channels : Reaction, Attachments')
            return
        if ChannelName[0] == 'R':
            self.hook = await ctx.channel.create_webhook(name = 'BOTORY', avatar = await self.app.user.avatar_url.read())
            self.DB[ChannelName] = (ctx.channel.id, self.hook.id)
        else: self.DB[ChannelName] = ctx.channel.id

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild == None: return
        if message.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        if message.author.bot: return
        if len(message.attachments) and self.DB['Attachments']:
            files = [await attachment.to_file(spoiler = attachment.is_spoiler(), use_cached = True) for attachment in message.attachments]
            LogChannel = message.guild.get_channel(self.DB['Attachments'])
            embed = discord.Embed(title = '',
                    description = f'Attachment from [a message]({message.jump_url}) in <#{message.channel.id}>',
                    timestamp = datetime.now(tz = timezone(timedelta(hours = 9))))
            author = message.author
            embed.set_author(name = f'{author.name}#{author.discriminator}', icon_url = str(author.avatar_url))
            embed.add_field(name = 'User ID', value = str(author.id), inline = False)
            embed.add_field(name = 'Message ID', value = str(message.id), inline = False)
            LogChannel = message.guild.get_channel(self.DB['Attachments'])
            await LogChannel.send(embed = embed, files = files)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id != self.guild.id: return
        user = self.app.get_user(payload.user_id)
        if user == None or user.bot: return
        if self.DB['Reaction']:
            jump_url = f'https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}'
            embed = discord.Embed(title = '',
                    description = f'Reaction deleted from [a message]({jump_url}) in <#{payload.channel_id}>',
                    timestamp = datetime.now(tz = timezone(timedelta(hours = 9))))
            embed.set_author(name = f'{user.name}#{user.discriminator}', icon_url = str(user.avatar_url))
            embed.add_field(name = 'emoji', value = str(payload.emoji), inline = False)
            embed.add_field(name = 'User ID', value = str(payload.user_id), inline = False)
            embed.add_field(name = 'Message ID', value = str(payload.message_id), inline = False)
            for i in range(len(self.queue)):
                _dict = self.queue[i].to_dict()
                if _dict['fields'][:3] == embed.to_dict()['fields'][:3]:
                    if len(_dict['fields']) < 4: _dict['fields'].append({'name' : 'Count', 'value' : '1', 'inline' : False})
                    _dict['fields'][3]['value'] = str(int(_dict['fields'][3]['value']) + 1)
                    self.queue[i] = discord.Embed.from_dict(_dict)
                    return
            self.queue.append(embed)

    @tasks.loop(seconds = 1)
    async def AutoFlush(self):
        if len(self.queue) > 9: await self.flush()

    async def flush(self):
        try:
            await self.hook.send(embeds = self.queue[:10])
            self.queue = self.queue[10:]
        except: pass

    @tasks.loop()
    async def Undead(self):
        if 'deadflag' in self.GetGlobalDB():
            self.GetGlobalDB()['deadflag'].add('logger')
            self.AutoFlush.cancel()
            self.printlog('Start flushing emoji log...')
            while self.queue: await self.flush()
            self.printlog('Flushing end.')
            self.GetGlobalDB()['deadflag'].remove('logger')
            self.Undead.cancel()
