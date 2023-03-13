import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks


class Hider(commands.Cog):
	"""Hide commands from users in help."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			hidden = []
		)
	
	@checks.is_owner()
	@commands.group()
	async def hider(self, ctx):
		"""Hide commands from users in help."""
		pass
		
	@hider.command()
	async def hide(self, ctx, *, command):
		"""
		Hide a command from being displayed in help.
		
		This will not work if [p]helpset showhidden is enabled.
		"""
		async with self.config.hidden() as hidden:
			if command in hidden:
				return await ctx.send('That command is already being hidden.')
			hidden.append(command)		
		await self.run_hide()
		await ctx.tick()
	
	@hider.command()
	async def show(self, ctx, *, command):
		"""Show a command that was previously hidden by Hider."""
		async with self.config.hidden() as hidden:
			if command not in hidden:
				return await ctx.send('That command was not being hidden.')
			hidden.remove(command)
		result = self.bot.get_command(command)
		if result and not isinstance(result, commands.commands._AlwaysAvailableMixin):
			result.hidden = False
		await ctx.tick()
	
	@hider.command()
	async def list(self, ctx):
		"""List the commands that Hider is hiding."""
		hidden = await self.config.hidden()
		if not hidden:
			return await ctx.send('There are currently no hidden commands.')
		msg = '```\n'
		for command in hidden:
			msg += command + '\n'
		msg += '```'
		await ctx.send(msg)
	
	async def run_hide(self):
		"""Hides every command configured to be hidden."""
		for command in await self.config.hidden():
			result = self.bot.get_command(command)
			if result and not isinstance(result, commands.commands._AlwaysAvailableMixin):
				result.hidden = True

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return

	@commands.Cog.listener()
	async def on_command_add(self, command):
		"""Hides commands from newly loaded cogs."""
		await self.run_hide()
