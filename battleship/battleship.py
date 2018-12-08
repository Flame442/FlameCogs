import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio

class Battleship(commands.Cog):
	"""Play battleship with one other person"""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167901)
		self.config.register_guild(
			extraHit = True
		)

	@commands.guild_only()
	@commands.command()
	async def battleship(self, ctx):
		"""Start a game of battleship"""
		await ctx.send('Setting up, please wait')
		channel = ctx.message.channel
		name = [ctx.message.author.display_name]
		board = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
		let = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
		letnum = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7, 'i': 8, 'j': 9, 'k': 10, 'l': 11, 'm': 12, 'n': 13, 'o': 14, 'p': 15, 'q': 16, 'r': 17, 's': 18, 't': 19, 'u': 20, 'v': 21, 'w': 22, 'x': 23, 'y': 24, 'z': 25}
		bkey = [{0:'· ',1:'O ',2:'X ',3:'· '},{0:'· ',1:'O ',2:'X ',3:'# '}]
		pswap = {1:0,0:1}
		key = [[],[]]
		key2 = {0:0,1:0,2:0,3:0,4:0}
		namekey = {0:'5',1:'4',2:'3',3:'3',4:'2'}
		pid = [ctx.message.author]

		def bprint(player,bt): #creates a display of the board for printing
			b = '  '
			for z in range(10): b += let[z]+' '
			b += '\n'
			for y in range(10): #vertical positions
				b += str(y)+' '
				for x in range(10): b += bkey[bt][board[player][(y*10)+x]] #horizontal positions
				b += '\n'
			return '```'+b+'```'

		async def place(player,length,value): #create a ship for player of length at position value
			hold = {}
			try:
				x = letnum[value[0]]
			except:
				await pid[player].send('Invalid input, x cord must be a letter from A-J.')
				return False
			try:
				y = int(value[1])
			except:
				await pid[player].send('Invalid input, y cord must be a number from 0-9.')
				return False
			try:
				d = value[2]
			except:
				await pid[player].send('Invalid input, d cord must be d or r')
				return False
			try:
				if d == 'r': #right
					if 10 - length < x: #ship would wrap over right edge
						await pid[player].send('Invalid input, too far to the right.')
						return False
					for z in range(length):
						if board[player][(y*10)+x+z] != 0: #a spot taken by another ship
							await pid[player].send('Invalid input, another ship is in that range.')
							return False
					for z in range(length):
						board[player][(y*10)+x+z] = 3
						hold[(y*10)+x+z] = 0
				elif d == 'd': #down
					for z in range(length):
						if board[player][((y+z)*10)+x] != 0: #a spot taken by another ship
							await pid[player].send('Invalid input, another ship is in that range.')
							return False
					for z in range(length):
						board[player][((y+z)*10)+x] = 3
						hold[((y+z)*10)+x] = 0
				else:
					await pid[player].send('Invalid input, choose a direction of "d" or "r".')
					return False
			except:
				await pid[player].send('Invalid input, too far down.')
				return False
			key[player].append(hold)
			return True

		#RUN CODE
		check = lambda m: m.author != ctx.message.author and m.author.bot == False and m.channel == ctx.message.channel
		await ctx.send('Second player, say I.')
		try:
			r = await self.bot.wait_for('message', timeout=60, check=check)
		except asyncio.TimeoutError:
			return await ctx.send('You took too long, shutting down.')
		name.append(r.author.display_name)
		pid.append(r.author)
		await ctx.send('A game of battleship will be played between '+name[0]+' and '+name[1]+'.')
		for x in range(2): #each player
			await ctx.send('Messaging '+name[x]+' for setup now.')
			await pid[x].send(str(name[x]+', it is your turn to set up your ships. Place ships by entering the top left cord in xyd format.'))
			for k in [5,4,3,3,2]: #each ship length
				await pid[x].send(bprint(x,1))
				stupid = await pid[x].send('Place your '+str(k)+' length ship.')
				while True:
					try:
						t = await self.bot.wait_for('message', timeout=120, check=lambda m:m.channel == stupid.channel and m.author.bot == False)
					except asyncio.TimeoutError:
						return await ctx.send(name[x]+' took too long, shutting down.')
					if await place(x,k,t.content.lower()) == True:
						break
		###############################################################
		game = True
		p = 1
		while game == True:
			p = pswap[p]
			await ctx.send(name[p]+'\'s turn!\n'+bprint(pswap[p],0)+name[p]+', take your shot.')
			i = 0
			while i == 0:
				try:
					s = await self.bot.wait_for('message', timeout=120, check=lambda m: m.author == pid[p] and m.channel == channel)
				except asyncio.TimeoutError:
					return await ctx.send('You took too long, shutting down.')
				try: #makes sure input is valid
					x = letnum[s.content[0].lower()]
					y = int(s.content[1])
					board[pswap[p]][(y*10)+x]
				except:
					await ctx.send('Invalid input')
					continue
				if board[pswap[p]][(y*10)+x] == 0:
					board[pswap[p]][(y*10)+x] = 1
					await pid[pswap[p]].send(bprint(pswap[p],1))
					await ctx.send(bprint(pswap[p],0)+'Miss!')
					i = 1
				elif board[pswap[p]][(y*10)+x] in [1,2]:
					await ctx.send('You already shot there!')
				elif board[pswap[p]][(y*10)+x] == 3:
					board[pswap[p]][(y*10)+x] = 2
					await pid[pswap[p]].send(bprint(pswap[p],1))
					await ctx.send(bprint(pswap[p],0)+'Hit!')
					l = -1
					for a in range(5):
						if ((y*10)+x) in key[pswap[p]][a]:
							key[pswap[p]][a][(y*10)+x] = 1
							l = 0
							for b in key[pswap[p]][a]:
								if key[pswap[p]][a][b] == 0: #if any position in the ship is still there, l = 1
									l = 1
									break
							if l == 0: #if ship destroyed
								await ctx.send(name[pswap[p]]+'\'s '+namekey[a]+' length ship was destroyed!')
								key2[a] = 1 #mark ship as destroyed
								for c in key2:
									if key2[c] == 0: #if any ship is not destroyed, l = 1
										l = 1
										break
								if l == 0: #if all ships destroyed
									await ctx.send(name[p]+' wins!')
									game = False
									i = 1
							if game == True:
								if await self.config.guild(ctx.guild).extraHit() == True:
									await ctx.send('Take another shot.')
								else:
									i = 1

	@checks.guildowner()
	@commands.command()
	async def battleshipset(self, ctx, value: bool=None):
		"""
		Set if an extra shot should be given after a hit.
		Defaults to True.
		This value is global.
		"""
		if value == None:
			v = await self.config.guild(ctx.guild).extraHit()
			if v == True:
				await ctx.send('You are currently able to shoot again after a hit')
			else:
				await ctx.send('You are currently not able to shoot again after a hit')
		else:
			await self.config.guild(ctx.guild).extraHit.set(value)
			if value == True:
				await ctx.send('You will now be able to shoot again after a hit')
			else:
				await ctx.send('You will no longer be able to shoot again after a hit')
