import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio


class BattleshipGame():
	"""
	A game of Battleship
	Params:
	ctx, bot, doMention, extraHit, p1, p2
	Create a game using BattleshipGame.create(params)
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
		self.board = [[0 for x in range(100)], [0 for x in range(100)]]
		self.letnum = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7, 'i': 8, 'j': 9}
		self.pmsg = []
		self.key = [[],[]]
	
	@classmethod
	def create(cls, ctx, bot, doMention, extraHit, p1, p2, cog):
		game = cls(ctx, bot, doMention, extraHit, p1, p2, cog)
		game._task = ctx.bot.loop.create_task(game.run())
		return game
	
	def _bprint(self, player, bt):
		b = '  '
		for z in range(10): b += ['A','B','C','D','E','F','G','H','I','J'][z]+' '
		b += '\n'
		for y in range(10): #vertical positions
			b += str(y)+' '
			for x in range(10):
				b += [{0:'· ',1:'O ',2:'X ',3:'· '},{0:'· ',1:'O ',2:'X ',3:'# '}][bt][self.board[player][(y*10)+x]] #horizontal positions
			b += '\n'
		return '```'+b+'```'
	
	async def _place(self, player, length, value): #create a ship for player of length at position value
		hold = {}
		try:
			x = self.letnum[value[0]]
		except:
			await self.player[player].send('Invalid input, x cord must be a letter from A-J.')
			return False
		try:
			y = int(value[1])
		except:
			await self.player[player].send('Invalid input, y cord must be a number from 0-9.')
			return False
		try:
			d = value[2]
		except:
			await self.player[player].send('Invalid input, d cord must be a direction of d or r.')
			return False
		try:
			if d == 'r': #right
				if 10 - length < x: #ship would wrap over right edge
					await self.player[player].send('Invalid input, too far to the right.')
					return False
				for z in range(length):
					if self.board[player][(y*10)+x+z] != 0: #a spot taken by another ship
						await self.player[player].send('Invalid input, another ship is in that range.')
						return False
				for z in range(length):
					self.board[player][(y*10)+x+z] = 3
					hold[(y*10)+x+z] = 0
			elif d == 'd': #down
				for z in range(length):
					if self.board[player][((y+z)*10)+x] != 0: #a spot taken by another ship
						await self.player[player].send('Invalid input, another ship is in that range.')
						return False
				for z in range(length):
					self.board[player][((y+z)*10)+x] = 3
					hold[((y+z)*10)+x] = 0
			else:
				await self.player[player].send('Invalid input, d cord must be a direction of d or r.')
				return False
		except:
			await self.player[player].send('Invalid input, too far down.')
			return False
		self.key[player].append(hold)
		return True
	
	async def run(self):
		for x in range(2): #each player
			await self.ctx.send('Messaging '+self.name[x]+' for setup now.')
			await self.player[x].send(str(self.name[x]+', it is your turn to set up your ships.\nPlace ships by entering the top left coordinate and the direction of (r)ight or (d)own in xyd format.'))
			for k in [5,4,3,3,2]: #each ship length
				privateMessage = await self.player[x].send(self._bprint(x,1)+'Place your '+str(k)+' length ship.')
				while True:
					try:
						t = await self.bot.wait_for('message', timeout=120, check=lambda m:m.channel == privateMessage.channel and m.author.bot == False)
					except asyncio.TimeoutError:
						await self.ctx.send(self.name[x]+' took too long, shutting down.')
						self.stop()
					if await self._place(x,k,t.content.lower()) == True:
						break
			m = await self.player[x].send(self._bprint(x,1))
			self.pmsg.append(m)
		game = True
		pswap = {1:0,0:1}
		channel = self.ctx.channel
		while game:
			self.p = pswap[self.p]
			if self.dm:
				mention = self.player[self.p].mention
			else:
				mention = self.name[self.p]
			await self.ctx.send(mention+'\'s turn!\n'+self._bprint(pswap[self.p],0)+self.name[self.p]+', take your shot.')
			i = 0
			while i == 0:
				try:
					s = await self.bot.wait_for('message', timeout=120, check=lambda m: m.author == self.player[self.p] and m.channel == channel and len(m.content) == 2)
				except asyncio.TimeoutError:
					await self.ctx.send('You took too long, shutting down.')
					self.stop()
				try: #makes sure input is valid
					x = self.letnum[s.content[0].lower()]
					y = int(s.content[1])
					self.board[pswap[self.p]][(y*10)+x]
				except:
					continue
				if self.board[pswap[self.p]][(y*10)+x] == 0:
					self.board[pswap[self.p]][(y*10)+x] = 1
					await self.pmsg[pswap[self.p]].edit(content=self._bprint(pswap[self.p],1))
					await self.ctx.send(self._bprint(pswap[self.p],0)+'Miss!')
					i = 1
				elif self.board[pswap[self.p]][(y*10)+x] in [1,2]:
					await self.ctx.send('You already shot there!')
				elif self.board[pswap[self.p]][(y*10)+x] == 3:
					self.board[pswap[self.p]][(y*10)+x] = 2
					await self.pmsg[pswap[self.p]].edit(content=self._bprint(pswap[self.p],1))
					await self.ctx.send(self._bprint(pswap[self.p],0)+'Hit!')
					'''dead ship'''
					for a in range(5):
						if ((y*10)+x) in self.key[pswap[self.p]][a]:
							self.key[pswap[self.p]][a][(y*10)+x] = 1
							l = 0
							for b in self.key[pswap[self.p]][a]:
								if self.key[pswap[self.p]][a][b] == 0: #if any position in the ship is still there, l = 1
									l = 1
									break
							if l == 0: #if ship destroyed
								await self.ctx.send(self.name[pswap[self.p]]+'\'s '+str([5,4,3,3,2][a])+' length ship was destroyed!')
					'''dead player'''
					if 3 not in self.board[pswap[self.p]]:
						await self.ctx.send(self.name[self.p]+' wins!')
						game = False
					if game:
						if self.eh:
							await self.ctx.send('Take another shot.')
						else:
							i = 1
					else:
						self.stop()
	
	
	def stop(self):
		self.cog.games.remove([game for game in self.cog.games if game.ctx.channel == self.ctx.channel][0])
		self._task.cancel()

class Battleship(commands.Cog):
	"""Play battleship with one other person."""
	def __init__(self, bot):
		self.bot = bot
		self.games = []
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
		check = lambda m: m.author != ctx.message.author and m.author.bot == False and m.channel == ctx.message.channel and m.content.lower() == 'i'
		await ctx.send('Second player, say I.')
		try:
			r = await self.bot.wait_for('message', timeout=60, check=check)
		except asyncio.TimeoutError:
			return await ctx.send('You took too long, shutting down.')
		await ctx.send('A game of battleship will be played between '+ctx.author.display_name+' and '+r.author.display_name+'.')
		game = BattleshipGame.create(ctx, self.bot, dm, eh, ctx.author, r.author, self)
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
		if wasGame:
			await ctx.send('The game was stopped successfully.')
		else:
			await ctx.send('There is no ongoing game in this channel.')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group()
	async def battleshipset(self, ctx):
		pass
	
	@commands.guild_only()
	@checks.guildowner()
	@battleshipset.command()
	async def extra(self, ctx, value: bool=None):
		"""
		Set if an extra shot should be given after a hit.
		Defaults to True.
		This value is server specific.
		"""
		if value == None:
			v = await self.config.guild(ctx.guild).extraHit()
			if v == True:
				await ctx.send('You are currently able to shoot again after a hit.')
			else:
				await ctx.send('You are currently not able to shoot again after a hit.')
		else:
			await self.config.guild(ctx.guild).extraHit.set(value)
			if value == True:
				await ctx.send('You will now be able to shoot again after a hit.')
			else:
				await ctx.send('You will no longer be able to shoot again after a hit.')
	
	@commands.guild_only()
	@checks.guildowner()
	@battleshipset.command()
	async def mention(self, ctx, value: bool=None):
		"""
		Set if players should be mentioned when their turn begins.
		Defaults to False.
		This value is server specific.
		"""
		if value == None:
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
