import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks


class GameRoles(commands.Cog):
	"""Grant roles when a user is playing a specific game."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167903)
		self.config.register_guild(
			roledict = {},
			doAdd = True,
			doRemove = True
		)

	@commands.guild_only()
	@commands.group(aliases=['gr'])
	async def gameroles(self, ctx):
		"""Group command for game roles."""
		pass
	
	@checks.guildowner()
	@gameroles.command()
	async def addrole(self, ctx, role: discord.Role):
		"""
		Sets a role to be managed by gameroles.
		
		Roles with multiple words need to be surrounded in quotes.
		The bot's highest role needs to be above the role that you are adding and the bot needs permission to manage roles.
		"""
		roledict = await self.config.guild(ctx.guild).roledict()
		rid = str(role.id)
		if rid in roledict:
			return await ctx.send(
				f'`{role.name}` is already managed by gameroles. '
				f'Use `{ctx.prefix}gameroles addactivity` to add activities.'
			)
		roledict[role.id] = []
		await self.config.guild(ctx.guild).roledict.set(roledict)
		await ctx.send(
			f'`{role.name}` is now managed by gameroles! '
			f'Use `{ctx.prefix}gameroles addactivity` to add activities.'
		)
	
	@checks.guildowner()
	@gameroles.command()
	async def delrole(self, ctx, role: discord.Role):
		"""
		Stop a role from being managed by gameroles.
		
		Roles with multiple words need to be surrounded in quotes.
		"""
		roledict = await self.config.guild(ctx.guild).roledict()
		rid = str(role.id)
		if rid not in roledict:
			return await ctx.send(f'`{role.name}` is not managed by gameroles.')
		del roledict[rid]
		await self.config.guild(ctx.guild).roledict.set(roledict)
		await ctx.send(f'`{role.name}` is no longer managed by gameroles!')
	
	@checks.guildowner()
	@gameroles.command()
	async def addactivity(self, ctx, role: discord.Role, activity: str):
		"""
		Add an activity to trigger a role.
		
		Roles and activities with multiple words need to be surrounded in quotes.
		You can get the name of your current activity with [p]gameroles currentactivity.
		"""
		roledict = await self.config.guild(ctx.guild).roledict()
		rid = str(role.id)
		if rid not in roledict:
			return await ctx.send(f'`{role.name}` is not managed by gameroles.')
		if activity in roledict[rid]:
			return await ctx.send(f'`{activity}` already triggers `{role.name}`.')
		roledict[rid].append(activity)
		await self.config.guild(ctx.guild).roledict.set(roledict)
		await ctx.send(f'`{role.name}` is now triggered by `{activity}`!')
	
	@checks.guildowner()
	@gameroles.command()
	async def delactivity(self, ctx, role: discord.Role, activity: str):
		"""
		Remove an activity from triggering a role.
		
		Roles and activities with multiple words need to be surrounded in quotes.
		You can get the name of your current activity with [p]gameroles currentactivity.
		"""
		roledict = await self.config.guild(ctx.guild).roledict()
		rid = str(role.id)
		if rid not in roledict:
			return await ctx.send(f'`{role.name}` is not managed by gameroles.')
		if activity not in roledict[rid]:
			return await ctx.send(f'`{activity}` does not trigger `{role.name}`.')
		roledict[rid].remove(activity)
		await self.config.guild(ctx.guild).roledict.set(roledict)
		await ctx.send(f'`{role.name}` is no longer triggered by `{activity}`!')
	
	@checks.guildowner()
	@gameroles.command()
	async def listroles(self, ctx):
		"""List the roles currently managed by gameroles."""
		roledict = await self.config.guild(ctx.guild).roledict()
		rolelist = []
		for rid in roledict:
			role = ctx.guild.get_role(int(rid))
			if role:
				rolelist.append(role.name)
		if rolelist == []:
			return await ctx.send('Gameroles is currently not managing any roles.')
		roles = '\n'.join(rolelist)
		await ctx.send(
			'Roles currently managed by gameroles:\n'
			f'```\n{roles}```'
		)

	@checks.guildowner()
	@gameroles.command()
	async def listactivities(self, ctx, role: discord.Role):
		"""
		List the activities that trigger a role.
		
		Roles with multiple words need to be surrounded in quotes.
		"""
		roledict = await self.config.guild(ctx.guild).roledict()
		rid = str(role.id)
		if rid not in roledict:
			return await ctx.send(f'`{role.name}` is not managed by gameroles.')
		if roledict[rid] == []:
			return await ctx.send(f'`{role.name}` currently has no activities that trigger it.')
		activities = '\n'.join(roledict[rid])
		await ctx.send(
			f'Activities that currently trigger `{role.name}`:\n'
			f'```\n{activities}```'
		)

	@checks.guildowner()
	@gameroles.command()
	async def currentactivity(self, ctx):
		"""Get your current activity."""
		if ctx.message.author.activity is None:
			activity = 'None'
		else:
			activity = ctx.message.author.activity.name
		await ctx.send(f'```\n{activity}```')

	@gameroles.command()
	async def recheck(self, ctx):
		"""Force a recheck of your current activities."""
		if not ctx.guild.me.guild_permissions.manage_roles:
			return await ctx.send('I do not have permission to manage roles in this server.')
		roledict = await self.config.guild(ctx.guild).roledict()
		doAdd = await self.config.guild(ctx.guild).doAdd()
		doRemove = await self.config.guild(ctx.guild).doRemove()
		if doRemove:
			torem = [role for role in ctx.author.roles if str(role.id) in roledict]
			torem = [role for role in torem if ctx.guild.me.top_role > role]
			if torem != []:
				try:
					await ctx.author.remove_roles(*torem)
				except discord.errors.Forbidden:
					pass
		if doAdd:
			toadd = []
			activities = [a.name for a in ctx.author.activities]
			for role in [rid for rid in roledict if any(a in roledict[rid] for a in activities)]:
				role = ctx.guild.get_role(int(role))
				if role is not None and ctx.guild.me.top_role > role:
					toadd.append(role)
			if toadd != []:
				try:
					await ctx.author.add_roles(*toadd)
				except discord.errors.Forbidden:
					pass
		await ctx.tick()

	@commands.guild_only()
	@checks.guildowner()
	@commands.group(aliases=['grset'])
	async def gameroleset(self, ctx):
		"""Config options for gameroles."""
		pass
		
	@gameroleset.command()
	async def add(self, ctx, value: bool=None):
		"""
		Set if roles should be added when someone starts playing a game.
		
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doAdd()
			if v:
				await ctx.send('Roles are added when someone starts playing.')
			else:
				await ctx.send('Roles are not added when someone starts playing.')
		else:
			await self.config.guild(ctx.guild).doAdd.set(value)
			if value:
				await ctx.send('Roles will now be added when someone starts playing.')
			else:
				await ctx.send('Roles will no longer be added when someone starts playing.')
		
	@gameroleset.command()
	async def remove(self, ctx, value: bool=None):
		"""
		Set if roles should be removed when someone stops playing a game.
		
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doRemove()
			if v:
				await ctx.send('Roles are removed when someone stops playing.')
			else:
				await ctx.send('Roles are not removed when someone stops playing.')
		else:
			await self.config.guild(ctx.guild).doRemove.set(value)
			if value:
				await ctx.send('Roles will now be removed when someone stops playing.')
			else:
				await ctx.send('Roles will no longer be removed when someone stops playing.')
	
	@commands.Cog.listener()
	async def on_member_update(self, beforeMem, afterMem):
		"""Updates a member's roles."""
		if not afterMem.guild.me.guild_permissions.manage_roles:
			return
		if beforeMem.activities == afterMem.activities:
			return
		roledict = await self.config.guild(afterMem.guild).roledict()
		doAdd = await self.config.guild(afterMem.guild).doAdd()
		doRemove = await self.config.guild(afterMem.guild).doRemove()
		if beforeMem.activity is not None and doRemove:
			torem = []
			activities = [a.name for a in beforeMem.activities]
			for role in [rid for rid in roledict if any(a in roledict[rid] for a in activities)]:
				role = afterMem.guild.get_role(int(role))
				if role is not None and afterMem.guild.me.top_role > role:
					torem.append(role)
			if torem != []:
				try:
					await afterMem.remove_roles(*torem)
				except discord.errors.Forbidden:
					pass
		if afterMem.activity is not None and doAdd:
			toadd = []
			activities = [a.name for a in afterMem.activities]
			for role in [rid for rid in roledict if any(a in roledict[rid] for a in activities)]:
				role = afterMem.guild.get_role(int(role))
				if role is not None and afterMem.guild.me.top_role > role:
					toadd.append(role)
			if toadd != []:
				try:
					await afterMem.add_roles(*toadd)
				except discord.errors.Forbidden:
					pass
