import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio
from .game import BattleshipGame
from .ai import BattleshipAI


class Battleship(commands.Cog):
	"""Play battleship with one other person."""
	def __init__(self, bot):
		self.bot = bot
		self.games = []
		self.config = Config.get_conf(self, identifier=7345167901)
		self.config.register_guild(
			extraHit = True,
			doMention = False,
			doImage = True
		)
	
	@commands.guild_only()
	@commands.command()
	async def battleship(self, ctx):
		"""Start a game of battleship."""
		if [game for game in self.games if game.ctx.channel == ctx.channel]:
			return await ctx.send('A game is already running in this channel.')
		check = lambda m: (
			not m.author.bot
			and m.channel == ctx.message.channel
			and (
				(m.author != ctx.message.author and m.content.lower() == 'i')
				or (m.author == ctx.message.author and m.content.lower() == 'ai')
			)
		)
		await ctx.send('Second player, say I.\nOr say AI to play against the bot.')
		try:
			r = await self.bot.wait_for('message', timeout=60, check=check)
		except asyncio.TimeoutError:
			return await ctx.send('Nobody else wants to play, shutting down.')
		if [game for game in self.games if game.ctx.channel == ctx.channel]:
			return await ctx.send('Another game started in this channel while setting up.')
		if r.content.lower() == 'ai':
			p2 = BattleshipAI(ctx.guild.me.display_name)
		else:
			p2 = r.author
		await ctx.send(
			'A game of battleship will be played between '
			f'{ctx.author.display_name} and {p2.display_name}.'
		)
		game = BattleshipGame(ctx, self.bot, self, ctx.author, p2)
		self.games.append(game)
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.command()
	async def battleshipstop(self, ctx):
		"""Stop the game of battleship in this channel."""
		wasGame = False
		for game in [g for g in self.games if g.ctx.channel == ctx.channel]:
			game._task.cancel()
			wasGame = True
		if wasGame: #prevent multiple messages if more than one game exists for some reason
			await ctx.send('The game was stopped successfully.')
		else:
			await ctx.send('There is no ongoing game in this channel.')
	
	@commands.command()
	async def battleshipboard(self, ctx, channel: int):
		"""
		View your current board in an ongoing game.
		
		Specify the channel ID of the channel the game is in.
		"""
		game = [game for game in self.games if game.ctx.channel.id == channel]
		if not game:
			return await ctx.send(
				'There is no game in that channel or that channel does not exist.'
			)
		game = [g for g in game if ctx.author.id in [m.id for m in g.player]]
		if not game:
			return await ctx.send('You are not in that game.')
		game = game[0]
		p = [m.id for m in game.player].index(ctx.author.id)
		await game.send_board(p, 1, ctx, '')
	
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
			'Display the board using an image: {doImage}'
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
	
	def cog_unload(self):
		return [game._task.cancel() for game in self.games]
	
	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
