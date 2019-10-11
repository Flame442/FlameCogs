import discord
from functools import partial
from PIL import Image
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
import asyncio
import logging


class BattleshipGame():
	"""
	A game of Battleship.
	
	Params:
	ctx = redbot.core.commands.context.Context, The context that should be used, used to send messages.
	bot = redbot.core.bot.Red, The bot the game is running on, used to wait for messages.
	cog = battleship.battleship.Battleship, The cog the game is running on, used to stop the game.
	p1 = discord.member.Member, The member object of player 1.
	p2 = discord.member.Member, The member object of player 2.
	"""
	def __init__(self, ctx, bot, cog, p1, p2):
		self.ctx = ctx
		self.bot = bot
		self.cog = cog
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
		self.ship_pos = [[], []]
		self.log = logging.getLogger('red.flamecogs.battleship')
		self._task = asyncio.create_task(self.run())
		self._task.add_done_callback(partial(self.error_callback, ctx)) #Thanks Sinbad <3
	
	async def send_error(self, ctx):
		"""Sends a message to the channel after an error."""
		await ctx.send(
			'A fatal error has occurred, shutting down.\n'
			'Please have the bot owner copy the error from console '
			'and post it in the support channel of <https://discord.gg/bYqCjvu>.'
		)
	
	def error_callback(self, ctx, fut):
		"""Checks for errors in stopped games."""
		try:
			fut.result()
		except asyncio.CancelledError:
			pass
		except Exception as exc:
			asyncio.create_task(self.send_error(ctx))
			msg = 'Error in Battleship.\n'
			self.log.exception(msg)
	
	def _gen_text(self, player, show_unhit):
		"""
		Creates a visualization of the board.
		Returns a str of the board.
		
		Params:
		player = int, Which player's board to print.
		show_unhit = int, Should unhit ships be shown.
		"""
		outputchars = [{0:'· ', 1:'O ', 2:'X ', 3:'· '}, {0:'· ', 1:'O ', 2:'X ', 3:'# '}]
		output = '  ' + ' '.join(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']) #header row
		for y in range(10): #vertical positions
			output += f'\n{y} '
			for x in range(10): #horizontal positions
				output += outputchars[show_unhit][self.board[player][(y*10)+x]]
		return f'```\n{output}```'
	
	def _gen_img(self, player, show_unhit):
		"""
		Creates a visualization of the board.
		Returns a bytes image of the board.
		
		Params:
		player = int, Which player's board to print.
		show_unhit = int, Should unhit ships be shown.
		"""
		path = bundled_data_path(self.cog)
		img = Image.open(path / 'board.png')
		hit = Image.open(path / 'hit.png')
		miss = Image.open(path / 'miss.png')
		ships = [
			[
				Image.open(path / 'len5.png'),
				Image.open(path / 'len4.png'),
				Image.open(path / 'len3.png'),
				Image.open(path / 'len3.png'),
				Image.open(path / 'len2.png')
			], [
				Image.open(path / 'len5destroyed.png'),
				Image.open(path / 'len4destroyed.png'),
				Image.open(path / 'len3destroyed.png'),
				Image.open(path / 'len3destroyed.png'),
				Image.open(path / 'len2destroyed.png')
			]
		]
		len_key = [5, 4, 3, 3, 2]

		#place ships
		for index, pos in enumerate(self.ship_pos[player]):
			x, y, d = pos
			length = len_key[index]
			if show_unhit and not all(self.key[player][index].values()): #show a non-damaged ship
				if d == 'd': #down
					ships[0][index] = ships[0][index].rotate(90, expand=True)
				img.paste(ships[0][index], box=((x*30)+32, (y*30)+32), mask=ships[0][index])
			elif all(self.key[player][index].values()): #show a damaged ship
				if d == 'd': #down
					ships[1][index] = ships[1][index].rotate(90, expand=True)
				img.paste(ships[1][index], box=((x*30)+32, (y*30)+32), mask=ships[1][index])
		
		#place hit/miss markers	
		for y in range(10):
			for x in range(10):
				if self.board[player][((y)*10)+x] == 1: #miss
					img.paste(miss, box=((x*30)+32, (y*30)+32), mask=miss)
				elif self.board[player][((y)*10)+x] == 2: #hit
					img.paste(hit, box=((x*30)+32, (y*30)+32), mask=hit)
			
		temp = BytesIO()
		temp.name = 'board.png'
		img.save(temp)
		temp.seek(0)
		return temp
	
	async def update_dm(self, player):
		"""
		Update the DM board for a specific player.
		Only updates the board if the board is not an image.
		
		Params:
		player = int, Which player's board to print.
		"""
		if not await self.cog.config.guild(self.ctx.guild).doImage():
			content = self._gen_text(player, 1)
			await self.pmsg[player].edit(content=content)
	
	async def send_board(self, player, show_unhit, dest, msg):
		"""
		Send either an image of the board or a text representation of the board.
		
		player = int, Which player's board to print.
		show_unhit = int, Should unhit ships be shown.
		dest = discord.abc.Messageable, Where to send to.
		msg = str, Text to include with the board.
		"""
		if await self.cog.config.guild(self.ctx.guild).doImage():
			img = self._gen_img(player, show_unhit)
			file = discord.File(img, 'board.png')
			m = await dest.send(file=file)
			if msg:
				m = await dest.send(msg)
			return m
		content = self._gen_text(player, show_unhit)
		return await dest.send(f'{content}{msg}')
	
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
			await self.player[player].send('Invalid input, d cord must be a direction of d or r.')
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
		self.ship_pos[player].append((x, y, d))
		return True
	
	async def run(self):
		"""
		Runs the actual game.
		Should only be called by __init__.
		"""
		for x in range(2): #each player
			await self.ctx.send(f'Messaging {self.name[x]} for setup now.')
			privateMessage = await self.player[x].send(
				f'{self.name[x]}, it is your turn to set up your ships.\n'
				'Place ships by entering the top left coordinate as letter of the column followed by the number of the row '
				'and the direction of (r)ight or (d)own in xyd format.'
			)
			for ship_len in [5, 4, 3, 3, 2]: #each ship length
				await self.send_board(x, 1, self.player[x], f'Place your {ship_len} length ship.')
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
					if await self._place(x, ship_len, t.content.lower()): #only break if _place succeeded
						break
			m = await self.send_board(x, 1, self.player[x], '')
			self.pmsg.append(m) #save this message for editing later
		game = True
		pswap = {1:0, 0:1} #helper to swap player
		channel = self.ctx.channel
		while game:
			self.p = pswap[self.p] #swap players
			if await self.cog.config.guild(self.ctx.guild).doMention(): #should player be mentioned
				mention = self.player[self.p].mention
			else:
				mention = self.name[self.p]
			await self.ctx.send(f'{mention}\'s turn!')
			await self.send_board(
				pswap[self.p], 0, self.ctx, f'{self.name[self.p]}, take your shot.'
			)
			while True:
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
				except (ValueError, KeyError, IndexError):
					continue
				if self.board[pswap[self.p]][(y*10)+x] == 0:
					self.board[pswap[self.p]][(y*10)+x] = 1
					await self.update_dm(pswap[self.p])
					await self.send_board(pswap[self.p], 0, self.ctx, '**Miss!**')
					break
				elif self.board[pswap[self.p]][(y*10)+x] in [1, 2]:
					await self.ctx.send('You already shot there!')
				elif self.board[pswap[self.p]][(y*10)+x] == 3:
					self.board[pswap[self.p]][(y*10)+x] = 2
					#DEAD SHIP
					ship_dead = None
					for a in range(5):
						if (y*10)+x in self.key[pswap[self.p]][a]:
							self.key[pswap[self.p]][a][(y*10)+x] = 1
							if all(self.key[pswap[self.p]][a].values()): #if ship destroyed
								ship_dead = [5, 4, 3, 3, 2][a]
					await self.update_dm(pswap[self.p])
					if ship_dead:
						msg = (
							f'**Hit!**\n**{self.name[pswap[self.p]]}\'s '
							f'{ship_dead} length ship was destroyed!**'
						)
						await self.send_board(pswap[self.p], 0, self.ctx, msg)
					else:
						await self.send_board(pswap[self.p], 0, self.ctx, '**Hit!**')
					#DEAD PLAYER
					if 3 not in self.board[pswap[self.p]]:
						await self.ctx.send(f'**{self.name[self.p]} wins!**')
						game = False
					if game:
						if await self.cog.config.guild(self.ctx.guild).extraHit():
							await self.ctx.send('Take another shot.')
						else:
							break
					else:
						self.stop()

	def stop(self):
		"""Stop and cleanup the game."""
		self.cog.games.remove(self)
		self._task.cancel()
