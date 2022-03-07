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
		msg = (
			f'offline all: {store[0]}'
			f'\ndesktop only: {store[1]}'
			f'\nweb only: {store[2]}'
			f'\nmobile only: {store[3]}'
			f'\ndesktop web: {store[4]}'
			f'\nweb mobile: {store[5]}'
			f'\ndesktop mobile: {store[6]}'
			f'\nonline all: {store[7]}'
		)
		await ctx.send(f'```py\n{msg}```')

	@commands.guild_only()
	@commands.command()
	async def onlineinfo(self, ctx, *, member: discord.Member=None):
		"""Show what devices a member is using."""
		if member is None:
			member = ctx.author
		d = str(member.desktop_status)
		m = str(member.mobile_status)
		w = str(member.web_status)
		#because it isn't supported in d.py, manually override if streaming
		if any([isinstance(a, discord.Streaming) for a in member.activities]):
			d = d if d == 'offline' else 'streaming'
			m = m if m == 'offline' else 'streaming'
			w = w if w == 'offline' else 'streaming'
		status = {
			'online': '\U0001f7e2',
			'idle': '\U0001f7e0',
			'dnd': '\N{LARGE RED CIRCLE}',
			'offline': '\N{MEDIUM WHITE CIRCLE}',
			'streaming': '\U0001f7e3'
		}
		embed = discord.Embed(
			title=f'**{member.display_name}\'s devices:**',
			description=(
				f'{status[d]} Desktop\n'
				f'{status[m]} Mobile\n'
				f'{status[w]} Web'
			),
			color=await ctx.embed_color()
		)
		if discord.version_info.major == 1:
			embed.set_thumbnail(url=member.avatar_url)
		else:
			embed.set_thumbnail(url=member.display_avatar.url)
		try:
			await ctx.send(embed=embed)
		except discord.errors.Forbidden:
			await ctx.send(
				f'{member.display_name}\'s devices:\n'
				f'{status[d]} Desktop\n'
				f'{status[m]} Mobile\n'
				f'{status[w]} Web'
			)

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
