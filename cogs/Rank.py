import discord
from discord.ext import commands
from pkgs.DBCog import DBCog
from pkgs.GlobalDB import GlobalDB
from pkgs.Scheduler import Schedule

class Core(DBCog):
    def __init__(self, app):
        self.CogName = 'Rank'
        DBCog.__init__(self, app)

    def initDB(self):
        self.DB = dict()
        self.DB['RankChannel'] = None
        self.DB['TotoChannel'] = None
        self.DB['xps'] = None
        self.DB['Cooldown'] = None

    def rank2xp(self, rank):
        return 5 / 3 * rank ** 3 + 45 / 2 * rank ** 2 + 455 / 6 * rank

    def xp2rank(self, xp):
        l = 0, r = 1001
        while r - l > 1:
            mid = (l + r) / 2
            if xp < self.rank2xp(mid): r = mid
            else: l = mid
        return l

    @commands.command(name = 'setup'):
    @commands.has_guild_permissions(administrator = True)
    async def GetRank(self, ctx, CategoryID):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        Category = ctx.guild.get_channel(int(CategoryID))
        RankChannel = await Category.create_text_channel('rank')
        TotoChannel = await Category.create_text_channel('toto')
        self.DB['RankChannel'] = RankChannel.id
        self.DB['TotoChannel'] = TotoChannel.id
        MemberRole = discord.utils.get(ctx.guild.roles, name = '멤버')
        await RankChannel.set_permissions(MemberRole, add_reactions = False)
        await TotoChannel.set_permissions(MemberRole, send_messages = False, add_reactions = False)

    @commands.command(name = 'rank')
    async def GetRank(self, ctx):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        if ctx.author.id in self.DB['xps']: xp = self.DB['xps'][ctx.author.id]
        else: xp = 0
        rank = self.xp2rank(xp)
        tonext = self.rank2xp(rank + 1) - xp
        if rank < 1000: await ctx.send(f'<@{ctx.author.id}>님은 {rank}레벨입니다! {rank + 1} 레벨까지 {tonext} 경험치 남았습니다!', delete_after = 10.0)
        else: await ctx.send(f'<@{ctx.author.id}>님은 {rank}레벨입니다! 만렙이네요!ㄷㄷ', delete_after = 10.0)

    @commands.command(name = 'givexp')
    @commands.has_guild_permissions(administrator = True)
    async def GiveXP(self, ctx, who, val):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['xps']: self.DB['xps'][who.id] = 0
        self.DB['xps'][who.id] += val

    @commands.command(name = 'takexp')
    @commands.has_guild_permissions(administrator = True)
    async def TakeXP(self, ctx, who, val):
        if ctx.guild.id != GlobalDB['StoryGuildID']: return
        await ctx.message.delete()
        who = self.mention2member(who, ctx.guild)
        if who.id not in self.DB['xps']: self.DB['xps'][who.id] = 0
        self.DB['xps'][who.id] -= val
        if self.DB['xps'][who.id] < 0: self.DB['xps'][who.id] = 0

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id != GlobalDB['StoryGuildID']: return
        if message.author.bot: return
        if message.channel.id == self.DB['RankChannel']:
            await message.delete()
            return
        if message.author.id not in self.DB['Cooldown']: self.DB['Cooldown'][message.author.id] = Schedule('0s')
        if self.DB['Cooldown'][message.author.id].is_done():
            self.DB['xps'][message.author.id] += 20;
            self.DB['Cooldown'][message.author.id] = Schedule('1m')
