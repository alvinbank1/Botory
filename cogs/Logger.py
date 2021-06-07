import discord
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog
from datetime import datetime, timezone, timedelta

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Logger'
        self.LogChannelNames = ['Reaction', 'Attachments']
        DBCog.__init__(self, app)

    def initDB(self):
        for ChannelName in self.LogChannelNames: self.DB[ChannelName] = None

    @commands.group(name = 'logger')
    @commands.has_guild_permissions(administrator = True)
    async def LoggerGroup(self, ctx):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Logger system.\nSubcommands : setcnl')

    @LoggerGroup.command(name = 'setcnl')
    async def SetChannels(self, ctx, ChannelName = None):
        if ChannelName not in self.LogChannelNames:
            await ctx.channel.send('Available channels : Reaction, Attachments')
            return
        self.DB[ChannelName] = ctx.channel.id

    @commands.Cog.listener()
    async def on_message(self, message):
        if ctx.guild.id != self.GetGlobalDB()['StoryGuildID']: return
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
    async def on_reaction_remove(self, reaction, user):
        if reaction.message.guild.id != GlobalDB['StoryGuildID']: return
        if user.bot: return
        if self.DB['Reaction']:
            embed = discord.Embed(title = '',
                    description = f'Reaction deleted from [a message]({reaction.message.jump_url}) in <#{reaction.message.channel.id}>',
                    timestamp = datetime.now(tz = timezone(timedelta(hours = 9))))
            embed.set_author(name = f'{user.name}#{user.discriminator}', icon_url = str(user.avatar_url))
            embed.add_field(name = 'emoji', value = str(reaction.emoji), inline = False)
            embed.add_field(name = 'User ID', value = str(user.id), inline = False)
            embed.add_field(name = 'Message ID', value = str(reaction.message.id), inline = False)
            LogChannel = reaction.message.guild.get_channel(self.DB['Reaction'])
            await LogChannel.send(embed = embed)
