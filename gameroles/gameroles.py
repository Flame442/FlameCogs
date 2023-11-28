import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import humanize_list
import logging
from typing import Union


class GameRoles(commands.Cog):
	"""Grant roles when a user is playing a specific game."""
	def __init__(self, bot):
		self.bot = bot
		self.log = logging.getLogger('red.flamecogs.gameroles')
		self.cache = {}
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
		if ctx.guild.id in self.cache:
			del self.cache[ctx.guild.id]
	
	@checks.guildowner()
	@gameroles.command()
	async def delrole(self, ctx, role: Union[discord.Role, int]):
		"""
		Stop a role from being managed by gameroles.
		
		Roles with multiple words need to be surrounded in quotes.
		Accepts the ID of the role in case it was deleted.
		"""
		roledict = await self.config.guild(ctx.guild).roledict()
		if isinstance(role, discord.Role):
			rid = str(role.id)
			name = role.name
		else:
			rid = str(role)
			name = rid
		if rid not in roledict:
			return await ctx.send(f'`{name}` is not managed by gameroles.')
		del roledict[rid]
		await self.config.guild(ctx.guild).roledict.set(roledict)
		await ctx.send(f'`{name}` is no longer managed by gameroles!')
		if ctx.guild.id in self.cache:
			del self.cache[ctx.guild.id]
	
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
		if ctx.guild.id in self.cache:
			del self.cache[ctx.guild.id]
	
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
		if ctx.guild.id in self.cache:
			del self.cache[ctx.guild.id]
	
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
		if not ctx.message.author.activities:
			activity = 'None'
		else:
			activity = '\n'.join(a.name for a in ctx.message.author.activities)
		await ctx.send(f'```\n{activity}```')

	@gameroles.command()
	async def recheck(self, ctx):
		"""Force a recheck of your current activities."""
		if not ctx.guild.me.guild_permissions.manage_roles:
			return await ctx.send('I do not have permission to manage roles in this server.')
		data = await self.config.guild(ctx.guild).all()
		roledict = data['roledict']
		doAdd = data['doAdd']
		doRemove = data['doRemove']
		torem = set()
		toadd = set()
		failed = set()
		for role in ctx.author.roles:
			if str(role.id) in roledict:
				if ctx.guild.me.top_role > role:
					torem.add(role)
				else:
					failed.add(role) 
		activities = [a.name for a in ctx.author.activities]
		for role in [rid for rid in roledict if any(a in roledict[rid] for a in activities)]:
			role = ctx.guild.get_role(int(role))
			if role is not None and ctx.guild.me.top_role > role:
				toadd.add(role)
			elif role:
				failed.add(role)
		setsum = torem & toadd
		torem -= setsum
		toadd -= setsum
		#Filter out managed roles like Nitro Booster
		torem = [r for r in torem if not r.managed]
		toadd = [r for r in toadd if not r.managed]
		if toadd and doAdd:
			try:
				await ctx.author.add_roles(*toadd, reason='Gameroles')
			except discord.errors.Forbidden:
				return await ctx.send(
					'Encountered an unexpected discord.errors.Forbidden adding roles, canceling'
				)
		if torem and doRemove:
			try:
				await ctx.author.remove_roles(*torem, reason='Gameroles')
			except discord.errors.Forbidden:
				return await ctx.send(
					'Encountered an unexpected discord.errors.Forbidden removing roles, canceling'
				)
		if failed:
			await ctx.send(
				'The following roles could not be managed '
				f'because they are higher than my highest role:\n`{humanize_list(list(failed))}`'
			)
		await ctx.tick()

	@commands.guild_only()
	@checks.guildowner()
	@commands.group(aliases=['grset'], invoke_without_command=True)
	async def gameroleset(self, ctx):
		"""Config options for gameroles."""
		await ctx.send_help()
		data = await self.config.guild(ctx.guild).all()
		msg = (
			'Add roles: {doAdd}\n'
			'Remove roles: {doRemove}\n'
		).format_map(data)
		await ctx.send(f'```py\n{msg}```')
		
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
			if ctx.guild.id in self.cache:
				del self.cache[ctx.guild.id]
		
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
			if ctx.guild.id in self.cache:
				del self.cache[ctx.guild.id]

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
				
	@commands.Cog.listener()
	async def on_member_update(self, beforeMem, afterMem):
		"""Updates a member's roles. dpy 1.7"""
		if discord.version_info.major == 1:
			await self.update_gameroles(beforeMem, afterMem)
	
	@commands.Cog.listener()
	async def on_presence_update(self, beforeMem, afterMem):
		"""Updates a member's roles. dpy 2.0"""
		# This should never be run on dpy 1.7, but just in case I don't want to try to apply the same change twice.
		if discord.version_info.major == 2:
			await self.update_gameroles(beforeMem, afterMem)
		
	async def update_gameroles(self, beforeMem, afterMem):
		"""Update a member's roles."""
		if beforeMem.activities == afterMem.activities:
			return
		if await self.bot.cog_disabled_in_guild(self, afterMem.guild):
			return
		if afterMem.guild.id not in self.cache:
			data = await self.config.guild(afterMem.guild).all()
			self.cache[afterMem.guild.id] = data
		roledict = self.cache[afterMem.guild.id]['roledict']
		if not roledict:
			return
		doAdd = self.cache[afterMem.guild.id]['doAdd']
		doRemove = self.cache[afterMem.guild.id]['doRemove']
		if not (doAdd or doRemove):
			return
		torem = set()
		toadd = set()
		#REMOVE
		for role_obj in afterMem.roles:
			if str(role_obj.id) in roledict:
				if afterMem.guild.me.top_role > role_obj:
					torem.add(role_obj)
				else:
					self.log.warning(
						f'Role {role_obj} ({role_obj.id}) from guild '
						f'{afterMem.guild} ({afterMem.guild.id}) is higher than my highest role.'
					)
		#ADD
		activities = [a.name for a in afterMem.activities]
		for role in [rid for rid in roledict if any(a in roledict[rid] for a in activities)]:
			role_obj = afterMem.guild.get_role(int(role))
			if role_obj is not None and afterMem.guild.me.top_role > role_obj:
				toadd.add(role_obj)
			elif role_obj:
				self.log.warning(
					f'Role {role_obj} ({role}) from guild '
					f'{afterMem.guild} ({afterMem.guild.id}) is higher than my highest role.'
				)
			else:
				self.log.warning(
					f'Role {role} from guild {afterMem.guild} ({afterMem.guild.id}) '
					'may no longer exist.'
				)
		setsum = torem & toadd
		torem -= setsum
		toadd -= setsum
		if not (torem or toadd):
			return
		if not afterMem.guild.me.guild_permissions.manage_roles:
			self.log.debug(
				f'I do not have manage_roles permission in {afterMem.guild} ({afterMem.guild.id}).'
			)
			return
		#Filter out managed roles like Nitro Booster
		torem = [r for r in torem if not r.managed]
		toadd = [r for r in toadd if not r.managed]
		if torem and doRemove:
			try:
				await afterMem.remove_roles(*torem, reason='Gameroles')
			except discord.errors.Forbidden:
				self.log.exception(
					'Encountered an unexpected discord.errors.Forbidden removing roles '
					f'from {afterMem} in {afterMem.guild} ({afterMem.guild.id}).'
				)
		if toadd and doAdd:
			try:
				await afterMem.add_roles(*toadd, reason='Gameroles')
			except discord.errors.Forbidden:
				self.log.exception(
					'Encountered an unexpected discord.errors.Forbidden adding roles '
					f'to {afterMem} in {afterMem.guild} ({afterMem.guild.id}).'
				)
