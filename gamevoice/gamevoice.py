import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks

class Gamevoice(commands.Cog):
	"""Create game specific voice channels."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167903)
		self.config.register_guild(
			rolelist = {}
		)

	@commands.guild_only()
	@commands.group(aliases=['gv'])
	async def gamevoice(self, ctx):
		"""Create game specific voice channels."""
		pass

	@commands.guild_only()
	@checks.guildowner()
	@gamevoice.command(name='set')
	async def gamevoice_set(self, ctx):
		"""
		Create game specific voice channels.
		Sets the voice channel you are in to only work with the game you are playing.
		If you are not playing a game, the channel will be reset.
		Any activity will count, including Spotify, so make sure discord thinks you are doing the correct activity.
		"""
		if ctx.message.author.voice == None:
			return await ctx.send('You need to be in a voice channel.')
		if ctx.message.author.activity == None:
			list = ctx.message.guild.roles
			everyone = list[0]
			rolelist = await self.config.guild(ctx.guild).rolelist()
			await ctx.message.author.voice.channel.set_permissions(everyone, connect=True, speak=True)
			for x in rolelist.keys():
				role = ctx.message.guild.get_role(rolelist[x])
				try:
					await ctx.message.author.voice.channel.set_permissions(role, overwrite=None)
				except:
					pass
			await ctx.send(str(ctx.message.author.voice.channel)+' is now open.')
		else:
			list = ctx.message.guild.roles
			roleid = None
			for x in list:
				if str(ctx.message.author.activity) == x.name: #find role if it exists
					roleid = x.id
			everyone = list[0]
			if roleid == None: #create role if it doesnt exist
				roleid = await ctx.message.guild.create_role(name=str(ctx.message.author.activity))
				roleid = roleid.id
			rolelist = await self.config.guild(ctx.guild).rolelist()	#add
			rolelist[str(ctx.message.author.activity)] = roleid			#to
			await self.config.guild(ctx.guild).rolelist.set(rolelist)	#dict
			await ctx.message.author.voice.channel.set_permissions(everyone, connect=False, speak=False)
			role = ctx.message.guild.get_role(roleid)
			await ctx.message.author.voice.channel.set_permissions(role, connect=True, speak=True)
			await ctx.send('`'+str(ctx.message.author.voice.channel)+'` will now only allow people playing `'+str(ctx.message.author.activity)+'` to join.')

	@commands.guild_only()
	@gamevoice.command(name='recheck')
	async def gamevoice_recheck(self, ctx):
		"""Force a recheck of your current game."""
		list = []
		rolelist = await self.config.guild(ctx.guild).rolelist()
		for x in rolelist.keys():
			await ctx.message.author.remove_roles(ctx.message.guild.get_role(rolelist[x]))
		try:
			roleid = rolelist[str(ctx.message.author.activity)]
			role = ctx.message.guild.get_role(roleid)
			await ctx.message.author.add_roles(role)
		except:
			pass
		await ctx.send('You have been updated.')

	async def update(self, beforeMem, afterMem):
		"""Update a user's roles."""
		if beforeMem.activity != afterMem.activity:
			list = []
			rolelist = await self.config.guild(afterMem.guild).rolelist()
			for x in rolelist.keys():
				await afterMem.remove_roles(afterMem.guild.get_role(rolelist[x]))
			try:
				roleid = rolelist[str(afterMem.activity)]
				role = afterMem.guild.get_role(roleid)
				await afterMem.add_roles(role)
			except:
				pass
