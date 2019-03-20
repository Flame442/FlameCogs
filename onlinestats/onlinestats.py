import discord
from redbot.core import commands


class OnlineStats(commands.Cog):
	"""Information about what devices people are using to run discord."""
	def __init__(self, bot):
		self.bot = bot

	@commands.guild_only()
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

	@commands.guild_only()
	@commands.command()
	async def onlineinfo(self, ctx, *, user: discord.Member=None):
		"""Show what devices a user is using."""
		if user is None:
			user = ctx.author
		d = str(user.desktop_status)
		m = str(user.mobile_status)
		w = str(user.web_status)
		status = {
			'online': '\N{GREEN BOOK}',
			'idle': '\N{ORANGE BOOK}',
			'dnd': '\N{CLOSED BOOK}',
			'offline': '\N{NOTEBOOK}'
		}
		msg = (
			f'{user.display_name}\'s devices:\n'
			f'{status[d]} Desktop\n'
			f'{status[m]} Mobile\n'
			f'{status[w]} Web'
		)
		
		embed = discord.Embed(
				title=f'**{user.display_name}\'s devices:**',
				description=(
					f'{status[d]} Desktop\n'
					f'{status[m]} Mobile\n'
					f'{status[w]} Web'
				),
				color=await ctx.embed_color()
				)
		embed.set_thumbnail(url=user.avatar_url)
		try:
			await ctx.send(embed=embed)
		except:
			await ctx.send(msg)
