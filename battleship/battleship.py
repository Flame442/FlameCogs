import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio


class Battleship(commands.Cog):
	"""Play battleship with one other person."""
	def __init__(self, bot):
		self.bot = bot
		self.games = []
		self.bs = BattleshipGame
		self.config = Config.get_conf(self, identifier=7345167901)
		self.config.register_guild(
			extraHit = True,
			doMention = False
		)
	
	@commands.guild_only()
	@commands.command()
	async def battleship(self, ctx):
		"""Start a game of battleship."""
		if [game for game in self.games if game.ctx.channel == ctx.channel]:
			return await ctx.send('A game is already running in this channel.')
		dm = await self.config.guild(ctx.guild).doMention()
		eh = await self.config.guild(ctx.guild).extraHit()
		check = lambda m: (
			m.author != ctx.message.author 
			and not m.author.bot 
			and m.channel == ctx.message.channel 
			and m.content.lower() == 'i'
		)
		await ctx.send('Second player, say I.')
		try:
			r = await self.bot.wait_for('message', timeout=60, check=check)
		except asyncio.TimeoutError:
			return await ctx.send('Nobody else wants to play, shutting down.')
		if [game for game in self.games if game.ctx.channel == ctx.channel]:
			return await ctx.send('Another game started in this channel while setting up.')
		await ctx.send(
			'A game of battleship will be played between '
			f'{ctx.author.display_name} and {r.author.display_name}.'
		)
		game = BattleshipGame(ctx, self.bot, dm, eh, ctx.author, r.author, self)
		self.games.append(game)
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.command()
	async def battleshipstop(self, ctx):
		"""Stop the game of battleship in this channel."""
		wasGame = False
		for x in [game for game in self.games if game.ctx.channel == ctx.channel]:
			x.stop()
			wasGame = True
		if wasGame: #prevent multiple messages if more than one game exists for some reason
			await ctx.send('The game was stopped successfully.')
		else:
			await ctx.send('There is no ongoing game in this channel.')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group()
	async def battleshipset(self, ctx):
		"""Config options for batteship."""
		if ctx.invoked_subcommand is None:
			extraHit = await self.config.guild(ctx.guild).extraHit()
			doMention = await self.config.guild(ctx.guild).doMention()
			msg = (
				f'Extra shot on hit: {extraHit}\n'
				f'Mention on turn: {doMention}'
			)
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
	
	def cog_unload(self):
		return [game.stop() for game in self.games]

class BattleshipGame():
	"""
	A game of Battleship.
	
	Params:
	ctx = redbot.core.commands.context.Context, The context that should be used, used to send messages.
	bot = redbot.core.bot.Red, The bot the game is running on, used to wait for messages.
	doMention = bool, Should players be mentioned on the begining of their turn.
	extraHit = bool, Should players get an extra shot on a hit.
	p1 = discord.member.Member, The member object of player 1.
	p2 = discord.member.Member, The member object of player 2.
	cog = battleship.battleship.Battleship, The cog the game is running on, used to stop the game.
	"""
	def __init__(self, ctx, bot, doMention, extraHit, p1, p2, cog):
		self.ctx = ctx
		self.bot = bot
		self.cog = cog
		self.dm = doMention
		self.eh = extraHit
		self.player = [p1, p2]
		self.name = [p1.display_name, p2.display_name]
		self.p = 1
		self.board = [[0] * 100, [0] * 100]
		self.letnum = {
			'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4,
			'f': 5, 'g': 6, 'h': 7, 'i': 8, 'j': 9
		}
		self.pmsg = []
		self.key = [[], []]
		self._task = self.bot.loop.create_task(self.run())
	
	def _bprint(self, player, bt):
		"""
		Creates a visualization of the board.
		Returns a str of the board.
		
		Params:
		player = int, Which player's board to print.
		bt = int, Should unhit ships be shown.
		"""
		outputchars = [{0:'· ', 1:'O ', 2:'X ', 3:'· '}, {0:'· ', 1:'O ', 2:'X ', 3:'# '}]
		b = '  ' + ' '.join(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']) #header row
		for y in range(10): #vertical positions
			b += f'\n{str(y)} '
			for x in range(10):
				b += outputchars[bt][self.board[player][(y*10)+x]] #horizontal positions
		return f'```\n{b}```'
	
	async def _place(self, player, length, value):
		"""
		Add a ship to the board.
		Returns True when the ship is successfully placed.
		Returns False and sends a message when the ship cannot be placed.
		
		Params:
		player = int, Which player's board to place to.
		length = int, Length of the ship to place.
		value = str, The XYD to place ship at.
		"""
		hold = {}
		try:
			x = self.letnum[value[0]]
		except (KeyError, IndexError):
			await self.player[player].send('Invalid input, x cord must be a letter from A-J.')
			return False
		try:
			y = int(value[1])
		except (ValueError, IndexError):
			await self.player[player].send('Invalid input, y cord must be a number from 0-9.')
			return False
		try:
			d = value[2]
		except IndexError:
			await self.player[player].send(
				'Invalid input, d cord must be a direction of d or r.'
			)
			return False
		try:
			if d == 'r': #right
				if 10 - length < x: #ship would wrap over right edge
					await self.player[player].send('Invalid input, too far to the right.')
					return False
				for z in range(length):
					if self.board[player][(y*10)+x+z] != 0: #a spot taken by another ship
						await self.player[player].send(
							'Invalid input, another ship is in that range.'
						)
						return False
				for z in range(length):
					self.board[player][(y*10)+x+z] = 3
					hold[(y*10)+x+z] = 0
			elif d == 'd': #down
				for z in range(length):
					if self.board[player][((y+z)*10)+x] != 0: #a spot taken by another ship
						await self.player[player].send(
							'Invalid input, another ship is in that range.'
						)
						return False
				for z in range(length):
					self.board[player][((y+z)*10)+x] = 3
					hold[((y+z)*10)+x] = 0
			else:
				await self.player[player].send(
					'Invalid input, d cord must be a direction of d or r.'
				)
				return False
		except IndexError:
			await self.player[player].send('Invalid input, too far down.')
			return False
		self.key[player].append(hold)
		return True
	
	async def run(self):
		"""
		Runs the actuall game.
		Should only be called by __init__.
		"""
		for x in range(2): #each player
			await self.ctx.send(f'Messaging {self.name[x]} for setup now.')
			await self.player[x].send(
				f'{self.name[x]}, it is your turn to set up your ships.\n'
				'Place ships by entering the top left coordinate '
				'and the direction of (r)ight or (d)own in xyd format.'
			)
			for k in [5, 4, 3, 3, 2]: #each ship length
				privateMessage = await self.player[x].send(
					f'{self._bprint(x,1)}Place your {str(k)} length ship.'
				)
				while True:
					try:
						t = await self.bot.wait_for(
							'message',
							timeout=120,
							check=lambda m: (
								m.channel == privateMessage.channel 
								and not m.author.bot
							)
						)
					except asyncio.TimeoutError:
						await self.ctx.send(f'{self.name[x]} took too long, shutting down.')
						return self.stop()
					if await self._place(x, k, t.content.lower()): #only break if _place succeeded
						break
			m = await self.player[x].send(self._bprint(x, 1))
			self.pmsg.append(m) #save this message for editing later
		game = True
		pswap = {1:0, 0:1} #helper to swap player
		channel = self.ctx.channel
		while game:
			self.p = pswap[self.p] #swap players
			if self.dm: #should player be mentioned
				mention = self.player[self.p].mention
			else:
				mention = self.name[self.p]
			await self.ctx.send(
				f'{mention}\'s turn!\n'
				f'{self._bprint(pswap[self.p], 0)}'
				f'{self.name[self.p]}, take your shot.'
			)
			i = 0
			while i == 0:
				try:
					s = await self.bot.wait_for(
						'message',
						timeout=120,
						check=lambda m: (
							m.author == self.player[self.p] 
							and m.channel == channel 
							and len(m.content) == 2
						)
					)
				except asyncio.TimeoutError:
					await self.ctx.send('You took too long, shutting down.')
					self.stop()
				try: #makes sure input is valid
					x = self.letnum[s.content[0].lower()]
					y = int(s.content[1])
					self.board[pswap[self.p]][(y*10)+x]
				except (ValueError, KeyError, IndexError):
					continue
				if self.board[pswap[self.p]][(y*10)+x] == 0:
					self.board[pswap[self.p]][(y*10)+x] = 1
					await self.pmsg[pswap[self.p]].edit(content=self._bprint(pswap[self.p], 1))
					await self.ctx.send(f'{self._bprint(pswap[self.p], 0)}**Miss!**')
					i = 1
				elif self.board[pswap[self.p]][(y*10)+x] in [1, 2]:
					await self.ctx.send('You already shot there!')
				elif self.board[pswap[self.p]][(y*10)+x] == 3:
					self.board[pswap[self.p]][(y*10)+x] = 2
					await self.pmsg[pswap[self.p]].edit(content=self._bprint(pswap[self.p], 1))
					await self.ctx.send(f'{self._bprint(pswap[self.p], 0)}**Hit!**')
					#DEAD SHIP
					for a in range(5):
						if (y*10)+x in self.key[pswap[self.p]][a]:
							self.key[pswap[self.p]][a][(y*10)+x] = 1
							l = 0
							for b in self.key[pswap[self.p]][a]:
								if self.key[pswap[self.p]][a][b] == 0: #if any position in the ship is still there, l = 1
									l = 1
									break
							if l == 0: #if ship destroyed
								await self.ctx.send(
									f'**{self.name[pswap[self.p]]}\'s {str([5, 4, 3, 3, 2][a])} '
									'length ship was destroyed!**'
								)
					#DEAD PLAYER
					if 3 not in self.board[pswap[self.p]]:
						await self.ctx.send(f'**{self.name[self.p]} wins!**')
						game = False
					if game:
						if self.eh:
							await self.ctx.send('Take another shot.')
						else:
							i = 1
					else:
						self.stop()

	def stop(self):
		"""Stop and cleanup the game."""
		self.cog.games.remove(self)
		self._task.cancel()
