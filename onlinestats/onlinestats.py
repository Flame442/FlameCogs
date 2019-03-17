import discord
from redbot.core import commands


class OnlineStats(commands.Cog):
	"""Information about what devices people are using to run discord."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['onlinestats'])
	async def onlinestatus(self, ctx):
		"""Print how many people are using each type of device."""
		a = ( 
			"offline all: " + str(len([m for m in ctx.guild.members if m.desktop_status == discord.Status.offline and m.web_status == discord.Status.offline and  m.mobile_status == discord.Status.offline])) + "\n"
			"desktop only: " + str(len([m for m in ctx.guild.members if m.desktop_status != discord.Status.offline and m.web_status == discord.Status.offline and  m.mobile_status == discord.Status.offline])) + "\n"
			"web only: " + str(len([m for m in ctx.guild.members if m.desktop_status == discord.Status.offline and m.web_status != discord.Status.offline and  m.mobile_status == discord.Status.offline])) + "\n"
			"mobile only: " + str(len([m for m in ctx.guild.members if m.desktop_status == discord.Status.offline and m.web_status == discord.Status.offline and  m.mobile_status != discord.Status.offline])) + "\n"
			"desktop web: " + str(len([m for m in ctx.guild.members if m.desktop_status != discord.Status.offline and m.web_status != discord.Status.offline and  m.mobile_status == discord.Status.offline])) + "\n"
			"web mobile: " + str(len([m for m in ctx.guild.members if m.desktop_status == discord.Status.offline and m.web_status != discord.Status.offline and  m.mobile_status != discord.Status.offline])) + "\n"
			"desktop mobile: " + str(len([m for m in ctx.guild.members if m.desktop_status != discord.Status.offline and m.web_status == discord.Status.offline and  m.mobile_status != discord.Status.offline])) + "\n"
			"online all: " + str(len([m for m in ctx.guild.members if m.desktop_status != discord.Status.offline and m.web_status != discord.Status.offline and  m.mobile_status != discord.Status.offline]))
			)
		await ctx.send('```py\n'+a+'```')

	@commands.command()
	async def onlineinfo(self, ctx, user: discord.Member=None):
		"""Show what devices a user is using."""
		if user is None:
			user = ctx.author
		d = str(user.desktop_status)
		m = str(user.mobile_status)
		w = str(user.web_status)
		status = {'online':'\N{GREEN BOOK}','idle':'\N{ORANGE BOOK}','dnd':'\N{CLOSED BOOK}','offline':'\N{NOTEBOOK}'}
		msg = user.display_name + '\'s devices:\n'
		msg += status[d] + ' Desktop\n'
		msg += status[m] + ' Mobile\n'
		msg += status[w] + ' Web'
		await ctx.send(msg)
