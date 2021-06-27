import discord, json
from discord.ext import commands
from StudioBot.pkgs.DBCog import DBCog

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'MessageManager'
        DBCog.__init__(self, app)

    def initDB(self): return

    @commands.group(name = 'msg')
    @commands.has_guild_permissions(administrator = True)
    async def MsgGroup(self, ctx):
        await ctx.message.delete()
        if ctx.invoked_subcommand == None:
            await ctx.channel.send('Message manager.\nSubcommands : send, edit')

    @MsgGroup.command(name = 'send')
    async def SendMessage(self, ctx):
        def checker(message):
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.channel.send('Where to send?')
        WhereMessage = await self.app.wait_for('message', check = checker)
        Channel = ctx.guild.get_channel(int(WhereMessage.content[2:-1]))

        await ctx.channel.send('Tell me the link of reference message')
        jump_url = (await self.app.wait_for('message', check = checker)).content
        ReferenceMessage = await self.MessageFromLink(jump_url)
        ReferenceDict = {'content' : ReferenceMessage.content, 'embed' : None}
        if len(ReferenceMessage.embeds) > 0: ReferenceDict['embed'] = ReferenceMessage.embeds[0].to_dict()

        try:
            await Channel.send(content = ReferenceDict['content'], embed = discord.Embed.from_dict(ReferenceDict['embed']))
        except:
            await Channel.send(content = ReferenceDict['content'])

    @MsgGroup.command(name = 'edit')
    async def EditMessage(self, ctx):
        def checker(message):
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.channel.send('Tell me the link of message to edit')
        jump_url = (await self.app.wait_for('message', check = checker)).content
        TargetMessage = await self.MessageFromLink(jump_url)

        await ctx.channel.send('Tell me the link of reference message')
        jump_url = (await self.app.wait_for('message', check = checker)).content
        ReferenceMessage = await self.MessageFromLink(jump_url)
        ReferenceDict = {'content' : ReferenceMessage.content, 'embed' : None}
        if len(ReferenceMessage.embeds) > 0: ReferenceDict['embed'] = ReferenceMessage.embeds[0].to_dict()

        try:
            await TargetMessage.edit(content = ReferenceDict['content'], embed = discord.Embed.from_dict(ReferenceDict['embed']))
        except:
            await TargetMessage.edit(content = ReferenceDict['content'], embed = None)
