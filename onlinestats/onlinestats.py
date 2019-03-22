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
		device = {
			(True, True, True): 0,
			(False, True, True): 1,
			(True, False, True): 2,
			(True, True, False): 3,
			(False, False, True): 4,
			(True, False, False): 5,
			(False, True, False): 6,
			(False, False, False): 7
		}
		store = [0, 0, 0, 0, 0, 0, 0, 0]
		for m in ctx.guild.members:
			value = (
				m.desktop_status == discord.Status.offline,
				m.web_status == discord.Status.offline,
				m.mobile_status == discord.Status.offline
			)
			store[device[value]] += 1
		messages = [
			'offline all: ',
			'\ndesktop only: ',
			'\nweb only: ',
			'\nmobile only: ',
			'\ndesktop web: ',
			'\nweb mobile: ',
			'\ndesktop mobile: ',
			'\nonline all: '
		]
		msg = ''
		for n in range(8):
			msg += messages[n] + str(store[n])
		await ctx.send('```py\n'+msg+'```')

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
		except discord.errors.Forbidden:
			await ctx.send(msg)
