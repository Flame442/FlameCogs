import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio
from .game import BattleshipGame
from .ai import BattleshipAI
from .views import ConfirmView, GetPlayersView


class Battleship(commands.Cog):
	"""Play battleship with one other person."""
	def __init__(self, bot):
		self.bot = bot
		self.games = []
		self.config = Config.get_conf(self, identifier=7345167901)
		self.config.register_guild(
			extraHit = True,
			doMention = False,
			doImage = True,
			useThreads = False,
		)
	
	@commands.guild_only()
	@commands.command()
	async def battleship(self, ctx, opponent: discord.Member=None):
		"""Start a game of battleship."""
		if [game for game in self.games if game.channel == ctx.channel]:
			return await ctx.send('A game is already running in this channel.')
		
		if opponent is None:
			view = GetPlayersView(ctx, 2)
			initial_message = await ctx.send(view.generate_message(), view=view)
		else:
			view = ConfirmView(opponent)
			initial_message = await ctx.send(f'{opponent.mention} You have been challenged to a game of Battleship by {ctx.author.display_name}!', view=view)

		channel = ctx.channel
		if (
			await self.config.guild(ctx.guild).useThreads()
			and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
			and ctx.channel.type is discord.ChannelType.text
		):
			try:
				channel = await initial_message.create_thread(
					name='Battleship',
					reason='Automated thread for Battleship.',
				)
			except discord.HTTPException:
				pass

		await view.wait()

		if opponent is None:
			players = view.players
		else:
			if not view.result:
				await channel.send(f'{opponent.display_name} does not want to play, shutting down.')
				return
			players = [ctx.author, opponent]

		if len(players) < 2:
			return await channel.send('Nobody else wants to play, shutting down.')
		players = players[:2]
		
		if [game for game in self.games if game.channel == channel]:
			return await channel.send('Another game started in this channel while setting up.')
		
		await channel.send(
			'A game of battleship will be played between '
			f'{" and ".join(p.display_name for p in players)}.'
		)
		game = BattleshipGame(ctx, channel, *players)
		self.games.append(game)
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.command()
	async def battleshipstop(self, ctx):
		"""Stop the game of battleship in this channel."""
		wasGame = False
		for game in [g for g in self.games if g.channel == ctx.channel]:
			game._task.cancel()
			wasGame = True
		if wasGame: #prevent multiple messages if more than one game exists for some reason
			await ctx.send('The game was stopped successfully.')
		else:
			await ctx.send('There is no ongoing game in this channel.')
	
	@commands.command()
	async def battleshipboard(self, ctx, channel: discord.TextChannel=None):
		"""
		View your current board from an ongoing game in your DMs.
		
		Specify the channel ID of the channel the game is in.
		"""
		if channel is None:
			channel = ctx.channel
		game = [game for game in self.games if game.channel.id == channel.id]
		if not game:
			return await ctx.send(
				'There is no game in that channel or that channel does not exist.'
			)
		game = [g for g in game if ctx.author.id in [m.id for m in g.player]]
		if not game:
			return await ctx.send('You are not in that game.')
		game = game[0]
		p = [m.id for m in game.player].index(ctx.author.id)
		await game.send_board(p, 1, ctx.author, '')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group(invoke_without_command=True)
	async def battleshipset(self, ctx):
		"""Config options for battleship."""
		await ctx.send_help()
		cfg = await self.config.guild(ctx.guild).all()
		msg = (
			'Extra shot on hit: {extraHit}\n'
			'Mention on turn: {doMention}\n'
			'Display the board using an image: {doImage}\n'
			'Game contained to a thread: {useThreads}\n'
		).format_map(cfg)
		await ctx.send(f'```py\n{msg}```')
	
	@battleshipset.command()
	async def extra(self, ctx, value: bool=None):
		"""
		Set if an extra shot should be given after a hit.
		
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).extraHit()
			if v:
				await ctx.send('You are currently able to shoot again after a hit.')
			else:
				await ctx.send('You are currently not able to shoot again after a hit.')
		else:
			await self.config.guild(ctx.guild).extraHit.set(value)
			if value:
				await ctx.send('You will now be able to shoot again after a hit.')
			else:
				await ctx.send('You will no longer be able to shoot again after a hit.')
	
	@battleshipset.command()
	async def mention(self, ctx, value: bool=None):
		"""
		Set if players should be mentioned when their turn begins.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doMention()
			if v:
				await ctx.send('Players are being mentioned when their turn begins.')
			else:
				await ctx.send('Players are not being mentioned when their turn begins.')
		else:
			await self.config.guild(ctx.guild).doMention.set(value)
			if value:
				await ctx.send('Players will be mentioned when their turn begins.')
			else:
				await ctx.send('Players will not be mentioned when their turn begins.')
	
	@battleshipset.command()
	async def imgboard(self, ctx, value: bool=None):
		"""
		Set if the board should be displayed using an image.
		
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doImage()
			if v:
				await ctx.send('The board is currently displayed using an image.')
			else:
				await ctx.send('The board is currently displayed using text.')
		else:
			await self.config.guild(ctx.guild).doImage.set(value)
			if value:
				await ctx.send('The board will now be displayed using an image.')
			else:
				await ctx.send('The board will now be displayed using text.')
	
	@battleshipset.command()
	async def thread(self, ctx, value: bool=None):
		"""
		Set if a thread should be created per-game to contain game messages.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).useThreads()
			if v:
				await ctx.send('The game is currently run in a per-game thread.')
			else:
				await ctx.send('The game is not currently run in a thread.')
		else:
			await self.config.guild(ctx.guild).useThreads.set(value)
			if value:
				await ctx.send('The game will now be run in a per-game thread.')
			else:
				await ctx.send('The game will not be run in a thread.')
	
	def cog_unload(self):
		return [game._task.cancel() for game in self.games]
	
	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
