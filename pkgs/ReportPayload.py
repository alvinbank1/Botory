import discord
from datetime import datetime, timedelta

class ReportPayload:
    def __init__(self): return
    def __init__(self, reporter):
        self.guild = reporter.guild
        self.type = self.reporter = self.caption = None
        self.reaction = self.message = self.user = None

    def __hash__(self): return hash((self.type, self.reaction, self.message, self.user))
    def __eq__(self, other):
        return (self.type, self.reaction, self.message, self.user) == (other.type, other.reaction, other.message, other.user)

    @classmethod
    def fromMessage(cls, reporter, message, caption = None):
        self.__init__(reporter)
        cls.type = 'message'
        cls.message = message
        cls.user = message.author
        cls.caption = caption

    @classmethod
    def fromReaction(cls, reporter, reaction, user, caption = None):
        self.__init__(reporter)
        cls.type = 'reaction'
        cls.reaction = reaction
        cls.message = reaction.message
        cls.user = user
        cls.caption = caption

    @classmethod
    def fromUser(cls, reporter, user, caption = None):
        self.__init__(reporter)
        cls.type = 'user'
        cls.user = user
        cls.caption = caption

    @classmethod
    def fromUserPresence(cls, reporter, user, caption = None):
        self = self.fromUser(reporter, user, caption)
        cls.type = 'presence'

    @classmethod
    def fromUserNick(cls, reporter, user, caption = None):
        self = self.fromUser(reporter, user, caption)
        cls.type = 'nick'

    @classmethod
    def fromCaption(cls, reporter, caption):
        self.__init__(reporter)
        cls.type = 'others'
        cls.caption = caption

    def toEmbed(self):
        embed = discord.Embed(title = '신고', description = '')
        embed.add_field(name = '신고자', value = f'<@{self.reporter.id}>', inline = False)
        embed.add_field(name = '신고자 id', value = str(self.reporter.id), inline = False)
        embed.add_field(name = '신고유형', value = self.getKorType(), inline = False)
        if self.user:
            embed.add_field(name = '신고대상자', value = f'<@{self.user.id}>', inline = False)
            embed.add_field(name = '신고대상자 id', value = str(self.user.id), inline = False)
        if self.message:
            embed.add_field(name = '신고대상 메세지 채널', value = f'<#{self.message.channel.id}>', inline = False)
            embed.add_field(name = '신고대상 메세지 링크', value = f'[이동하기]({self.message.jump_url})', inline = False)
            embed.add_field(name = '신고대상 메세지 id', value = str(self.message.id), inline = False)
        if self.reaction:
            embed.add_field(name = '신고대상 이모지', value = str(self.reaction.emoji), inline = False)
            embed.set_thumbnail(url = self.reaction.emoji.url)
        if self.caption:
            embed.add_field(name = '신고사유', value = self.caption, inline = False)
        return embed

    def getKorType(self):
        if self.type == 'message': return '메시지'
        if self.type == 'reaction': return '반응 이모지'
        if self.type == 'nick': return '사용자 닉네임'
        if self.type == 'presence': return '사용자 상태 메시지'
        if self.type == 'user': return '사용자'
        if self.type == 'other': return '기타'
