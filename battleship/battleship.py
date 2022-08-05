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
		view = GetPlayersView(ctx, 2)
		await ctx.send(view.generate_message(), view=view)
		await view.wait()
		players = view.players
		if len(players) < 2:
			return await ctx.send('Nobody else wants to play, shutting down.')
		players = players[:2]
		if [game for game in self.games if game.ctx.channel == ctx.channel]:
			return await ctx.send('Another game started in this channel while setting up.')
		await ctx.send(
			'A game of battleship will be played between '
			f'{" and ".join(p.display_name for p in players)}.'
		)
		game = BattleshipGame(ctx, self.bot, self, *players)
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

class GetPlayersView(discord.ui.View):
	"""View to gather the players that will play in a game."""
	def __init__(self, ctx, max_players):
		super().__init__(timeout=60)
		self.ctx = ctx
		self.max_players = max_players
		self.players = [ctx.author]
	
	def generate_message(self):
		"""Generates a message to show the players currently added to the game."""
		msg = ""
		for idx, player in enumerate(self.players, start=1):
			msg += f"Player {idx} - {player.display_name}\n"
		msg += f"\nClick the `Join Game` button to join. Up to {self.max_players} players can join. To start with less than that many, use the `Start Game` button to begin."
		return msg
	
	async def interaction_check(self, interaction):
		if len(self.players) >= self.max_players:
			await interaction.response.send_message(content='The game is full.', ephemeral=True)
			return False
		if interaction.user.id != self.ctx.author.id and interaction.user in self.players:
			await interaction.response.send_message(content='You have already joined the game. Please wait for others to join or for the game to be started.', ephemeral=True)
			return False
		return True
	
	@discord.ui.button(label="Join Game", style=discord.ButtonStyle.blurple)
	async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Allows a user not currently added to join."""
		if interaction.user.id == self.ctx.author.id:
			await interaction.response.send_message(content='You have already joined the game. You can add AI players or start the game early with the other two buttons.', ephemeral=True)
			return
		self.players.append(interaction.user)
		self.start.disabled = False
		if len(self.players) >= self.max_players:
			view = None
			self.stop()
		else:
			view = self
		await interaction.response.edit_message(content=self.generate_message(), view=view)
	
	@discord.ui.button(label="Add an AI", style=discord.ButtonStyle.blurple)
	async def ai(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Fills the next player slot with an AI player."""
		self.players.append(BattleshipAI(self.ctx.guild.me.display_name))
		self.start.disabled = False
		if len(self.players) >= self.max_players:
			view = None
			self.stop()
		else:
			view = self
		await interaction.response.edit_message(content=self.generate_message(), view=view)
	
	@discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, disabled=True)
	async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Starts the game with less than max_players players."""
		if interaction.user.id != self.ctx.author.id:
			await interaction.response.send_message(content='Only the host can use this button.', ephemeral=True)
			return
		await interaction.response.edit_message(view=None)
		self.stop()
