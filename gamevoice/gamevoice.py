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
		Any activity will count, including Spotify, so make sure discord thinks you are doing the correct activity.
		"""
		if ctx.message.author.voice == None:
			return await ctx.send('You need to be in a voice channel.')
		elif ctx.message.author.activity == None:
			return await ctx.send('You need to be playing a game.')
		else:
			l = ctx.message.guild.roles
			roleid = None
			for x in l:
				if str(ctx.message.author.activity.name) == x.name: #find role if it exists
					roleid = x.id
			everyone = l[0]
			if roleid == None: #create role if it doesnt exist
				try:
					roleid = await ctx.message.guild.create_role(name=str(ctx.message.author.activity.name))
				except discord.errors.Forbidden:
					return await ctx.send('I need permission to create roles.')
				roleid = roleid.id
			rolelist = await self.config.guild(ctx.guild).rolelist()  #add
			rolelist[str(ctx.message.author.activity.name)] = roleid  #to
			await self.config.guild(ctx.guild).rolelist.set(rolelist) #dict
			try:
				await ctx.message.author.voice.channel.set_permissions(everyone, connect=False, speak=False)
				role = ctx.message.guild.get_role(roleid)
				await ctx.message.author.voice.channel.set_permissions(role, connect=True, speak=True)
			except discord.errors.Forbidden:
				return await ctx.send('I need permission to edit channels.')
			await ctx.send('`'+str(ctx.message.author.voice.channel)+'` will now only allow people playing `'+str(ctx.message.author.activity.name)+'` and any other previously added restrictions to join.')

	@commands.guild_only()
	@checks.guildowner()
	@gamevoice.command(name='reset')
	async def gamevoice_reset(self, ctx):
		"""
		Resets the voice channel you are in to defaults.
		Will remove ALL permissions, not just those set by the cog, making it completely open.
		"""
		if ctx.message.author.voice == None:
			return await ctx.send('You need to be in a voice channel.')
		l = ctx.message.guild.roles
		everyone = l[0]
		rolelist = await self.config.guild(ctx.guild).rolelist()
		try:
			await ctx.message.author.voice.channel.set_permissions(everyone, connect=True, speak=True)
		except discord.errors.Forbidden:
			return await ctx.send('I need permission to edit channels.')
		for x in rolelist.keys():
			role = ctx.message.guild.get_role(rolelist[x])
			try:
				await ctx.message.author.voice.channel.set_permissions(role, overwrite=None)
			except:
				pass
		await ctx.send(str(ctx.message.author.voice.channel)+' is now unrestricted.')
			
	@commands.guild_only()
	@gamevoice.command(name='recheck')
	async def gamevoice_recheck(self, ctx):
		"""Force a recheck of your current game."""
		rolelist = await self.config.guild(ctx.guild).rolelist()
		try:
			for x in rolelist.keys():
				await ctx.message.author.remove_roles(ctx.message.guild.get_role(rolelist[x]))
		except discord.errors.Forbidden:
			return await ctx.send('I need permission to edit user\'s roles.')
		try:
			roleid = rolelist[str(ctx.message.author.activity.name)]
			role = ctx.message.guild.get_role(roleid)
			await ctx.message.author.add_roles(role)
		except discord.errors.Forbidden:
			return await ctx.send('I need permission to edit user\'s roles.')
		except:
			pass
		await ctx.send('You have been updated.')

	@commands.guild_only()
	@gamevoice.command(name='listroles')
	async def gamevoice_listroles(self, ctx):
		"""Lists all the roles created for games."""
		rolelist = await self.config.guild(ctx.guild).rolelist()
		namelist = list(rolelist.keys())
		if namelist == []:
			await ctx.send('There are no game roles on this server.')
		else:
			p = 'The game roles on this server are:\n`'
			for x in namelist:
				p += x+'\n'
			await ctx.send(p+'`')
		
	@commands.guild_only()
	@checks.guildowner()
	@gamevoice.command(name='deleterole', aliases=['delrole'])
	async def gamevoice_deleterole(self, ctx, *, r: str):
		"""
		Delete a role from the server.
		Also removes that game's restrictions from all channels.
		Case sensitive.
		Use [p]gv listroles to see all roles.
		"""
		rolelist = await self.config.guild(ctx.guild).rolelist()
		try:
			id = rolelist[r]
		except:
			return await ctx.send('Role not found.')
		role = ctx.guild.get_role(id)
		try:
			await role.delete()
		except discord.errors.Forbidden:
			return await ctx.send('I need permission to delete roles.')
		del rolelist[r]
		await self.config.guild(ctx.guild).rolelist.set(rolelist)
		await ctx.send('Role deleted.')

	async def update(self, beforeMem, afterMem):
		"""Update a user's roles."""
		if beforeMem.activity != afterMem.activity:
			rolelist = await self.config.guild(afterMem.guild).rolelist()
			for x in rolelist.keys():
				await afterMem.remove_roles(afterMem.guild.get_role(rolelist[x]))
			try:
				roleid = rolelist[str(afterMem.activity.name)]
				role = afterMem.guild.get_role(roleid)
				await afterMem.add_roles(role)
			except:
				pass
