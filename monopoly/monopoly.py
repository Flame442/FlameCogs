import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import humanize_list
from typing import Union
import asyncio, os
from .game import MonopolyGame
from .views import GetPlayersView

#temp imports for backwards compatibility
from redbot.core.data_manager import cog_data_path
import ast


class Monopoly(commands.Cog):
	"""Play monopoly with 2-8 people."""
	def __init__(self, bot):
		self.bot = bot
		self.games = []
		self.config = Config.get_conf(self, identifier=7345167904)
		self.config.register_guild(
			doMention = False,
			startCash = 1500,
			incomeValue = 200,
			luxuryValue = 100,
			doAuction = True,
			bailValue = 50,
			maxJailRolls = 3,
			doDoubleGo = False,
			goValue = 200,
			freeParkingValue = None,
			hotelLimit = 12,
			houseLimit = 32,
			timeoutValue = 60,
			minRaise = 1,
			darkMode = False,
			useThreads = False,
			saves = {},
		)

	@commands.guild_only()
	@commands.group(invoke_without_command=True) 
	async def monopoly(self, ctx, savefile: str=None):
		"""
		Play monopoly with 2-8 people.
		
		Use the optional parameter "savefile" to load a saved game.
		"""
		if [game for game in self.games if game.channel == ctx.channel]:
			return await ctx.send('A game is already running in this channel.')
		channel = ctx.channel
		startCash = await self.config.guild(ctx.guild).startCash()
		if savefile is not None:
			saves = await self.config.guild(ctx.guild).saves()
			if savefile not in saves:
				return await ctx.send(
					'There is no save file with that name.\n'
					'Does it need to be converted? '
					'Is it saved in another guild?\n'
					f'Use `{ctx.prefix}monopoly list` to list save files.'
				)
			data = saves[savefile]
			if ctx.author.id not in data['uid']:
				return await ctx.send('You are not a player in that game!')
			initial_message = await ctx.send(f'Using save file `{savefile}`')
			if (
				await self.config.guild(ctx.guild).useThreads()
				and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
				and ctx.channel.type is discord.ChannelType.text
			):
				try:
					channel = await initial_message.create_thread(
						name='Monopoly',
						reason='Automated thread for Monopoly.',
					)
				except discord.HTTPException:
					pass
			game = MonopolyGame(ctx, channel, data=data)
			self.games.append(game)
		else:
			view = GetPlayersView(ctx, 8)
			initial_message = await ctx.send(view.generate_message(), view=view)
			if (
				await self.config.guild(ctx.guild).useThreads()
				and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
				and ctx.channel.type is discord.ChannelType.text
			):
				try:
					channel = await initial_message.create_thread(
						name='Monopoly',
						reason='Automated thread for Monopoly.',
					)
				except discord.HTTPException:
					pass
			await view.wait()
			players = view.players
			if len(players) < 2:
				return await channel.send('Nobody else wants to play, shutting down.')
			uid = []
			for player in players[:8]:
				if isinstance(player, discord.Member):
					uid.append(player.id)
				else:
					uid.append(player)
			if [game for game in self.games if game.ctx.channel == ctx.channel]:
				return await channel.send('Another game started in this channel while setting up.')
			game = MonopolyGame(ctx, channel, startCash=startCash, uid=uid)
			self.games.append(game)
	
	@monopoly.command(name='list')
	async def monopoly_list(self, ctx):
		"""List available save files."""
		saves = await self.config.guild(ctx.guild).saves()
		if not saves:
			return await ctx.send('There are no save files in this server.')
		savenames_in = '\n'.join(name for name in saves if ctx.author.id in saves[name]['uid'])
		savenames_out = '\n'.join(name for name in saves if ctx.author.id not in saves[name]['uid'])
		msg = ''
		if savenames_in:
			msg += f'\n[Saves you are in]\n{savenames_in}\n'
		if savenames_out:
			msg += f'\n[Saves you are not in]\n{savenames_out}\n'
		await ctx.send(f'```ini{msg}```')			
	
	@checks.guildowner()
	@monopoly.command()
	async def delete(self, ctx, *savefiles: str):
		"""
		Delete one or more save files.
		
		This cannot be undone.
		"""
		if not savefiles:
			return await ctx.send_help()
		success = []
		fail = []
		async with self.config.guild(ctx.guild).saves() as saves:
			for file in savefiles:
				if file not in saves:
					fail.append(file)
					continue
				del saves[file]
				success.append(file)
		msg = ''
		if success:
			msg += f'The following savefiles were deleted: `{humanize_list(success)}`\n'
		if fail:
			msg += f'The following savefiles were not found: `{humanize_list(fail)}`\n'
		await ctx.send(msg)
	
	@commands.guild_only()
	@commands.group(invoke_without_command=True, hidden=True) 
	async def monopolyconvert(self, ctx, savefile: str):
		"""Convert a savefile to work with the latest version of this cog."""
		if savefile in ('delete', 'list'):
			return await ctx.send(
				'You cannot convert a save file with that name as '
				'it conflicts with the name of a new command.'
			)
		hold = []
		for x in os.listdir(cog_data_path(self)):
			if x[-4:] == '.txt':
				hold.append(x[:-4])
		if savefile in hold:
			cfgdict = {}
			with open(f'{cog_data_path(self)}/{savefile}.txt') as f:
				for line in f:
					line = line.strip()
					if not line or line.startswith('#'):
						continue
					try:
						key, value = line.split('=') #split to variable and value
					except ValueError:
						await ctx.send(f'Bad line in save file {savefile}:\n{line}')
						continue
					key, value = key.strip(), value.strip()
					value = ast.literal_eval(value)
					cfgdict[key] = value #put in dictionary
			try:
				uid = cfgdict['id'] 
				del cfgdict['id']
				cfgdict['uid'] = uid
				
				isalive = cfgdict['alive'] 
				del cfgdict['alive']
				cfgdict['isalive'] = isalive
				
				cfgdict['injail'] = cfgdict['injail'][1:]
				cfgdict['tile'] = cfgdict['tile'][1:]
				cfgdict['bal'] = cfgdict['bal'][1:]
				cfgdict['goojf'] = cfgdict['goojf'][1:]
				cfgdict['isalive'] = cfgdict['isalive'][1:]
				cfgdict['jailturn'] = cfgdict['jailturn'][1:]
				cfgdict['injail'] = cfgdict['injail'][1:]
				cfgdict['uid'] = cfgdict['uid'][1:]
				cfgdict['p'] -= 1
				cfgdict['ownedby'] = [x - 1 for x in cfgdict['ownedby']]
				cfgdict['freeparkingsum'] = 0
			except Exception:
				return await ctx.send('One or more values are missing from the config file.')
			try:
				del cfgdict['tilename']
			except Exception:
				pass
			for key in (
				'injail', 'tile', 'bal', 'ownedby', 'numhouse',
				'ismortgaged', 'goojf', 'isalive', 'jailturn', 'p',
				'num', 'numalive', 'uid', 'freeparkingsum'
			):
				if key not in cfgdict:
					return await ctx.send(
						f'The value "{key}" is missing from the config file.'
					)
			savefile = savefile.replace(' ', '')
			async with self.config.guild(ctx.guild).saves() as saves:
				if savefile in saves:
					await ctx.send('There is already another save with that name. Override it?')
					try:
						response = await self.bot.wait_for(
							'message',
							timeout=60,
							check=lambda m: (
								m.channel == ctx.channel
								and m.author == ctx.author
							)
						)
					except asyncio.TimeoutError:
						return await ctx.send('You took too long to respond.')
					if response.content.lower() not in ('yes', 'y'):
						return await ctx.send('Not overriding.')
				saves[savefile] = cfgdict
			await ctx.send('Savefile converted successfully.')
		elif hold:
			savenames = '\n'.join(hold)
			return await ctx.send(
				f'That file does not exist.\nConvertable save files:\n```\n{savenames}```'
			)
		else:
			return await ctx.send('You do not have any save files to convert.')
	
	@monopolyconvert.command(name='list')
	async def monopolyconvert_list(self, ctx):
		"""List save files that can be converted."""
		saves = []
		for x in os.listdir(cog_data_path(self)):
			if x[-4:] == '.txt':
				saves.append(x[:-4])
		if saves:
			savenames = '\n'.join(saves)
			await ctx.send(f'Convertable save files:\n```\n{savenames}```')
		else:
			await ctx.send('You do not have any save files to convert.')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.command()
	async def monopolystop(self, ctx):
		"""Stop the game of monopoly in this channel."""
		wasGame = False
		for game in [g for g in self.games if g.channel == ctx.channel]:
			game._task.cancel()
			wasGame = True
		if wasGame: #prevents multiple messages if more than one game exists for some reason
			await ctx.send('The game was stopped successfully.')
		else:
			await ctx.send('There is no ongoing game in this channel.')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group(invoke_without_command=True)
	async def monopolyset(self, ctx):
		"""Config options for monopoly."""
		await ctx.send_help()
		cfg = await self.config.guild(ctx.guild).all()
		msg = (
			'Hold auctions: {doAuction}\n'
			'Bail price: {bailValue}\n'
			'Double go: {doDoubleGo}\n'
			'Free parking reward: {freeParkingValue}\n'
			'Go reward: {goValue}\n'
			'Hotel Limit: {hotelLimit}\n'
			'House limit: {houseLimit}\n'
			'Income tax: {incomeValue}\n'
			'Luxury tax: {luxuryValue}\n'
			'Max jail rolls: {maxJailRolls}\n'
			'Mention on turn: {doMention}\n'
			'Minimum auction increase: {minRaise}\n'
			'Starting cash: {startCash}\n'
			'Timeout length: {timeoutValue}\n'
			'Dark mode: {darkMode}\n'
			'Game contained to a thread: {useThreads}\n'
		).format_map(cfg)
		await ctx.send(f'```py\n{msg}```')
	
	@monopolyset.command()
	async def auction(self, ctx, value: bool=None):
		"""
		Set if properties should be auctioned when passed on.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doAuction()
			if v:
				await ctx.send('Passed properties are being auctioned.')
			else:
				await ctx.send('Passed properties are not being auctioned.')
		else:
			await self.config.guild(ctx.guild).doAuction.set(value)
			if value:
				await ctx.send('Passed properties will be auctioned.')
			else:
				await ctx.send('Passed properties will not be auctioned.')
	
	@monopolyset.command()
	async def bail(self, ctx, value: int=None):
		"""
		Set how much bail should cost.
		
		Defaults to 50.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).bailValue()
			await ctx.send(f'Bail currently costs ${v}.')
		else:
			await self.config.guild(ctx.guild).bailValue.set(value)
			await ctx.send(f'Bail will now cost ${value}.')
	
	@monopolyset.command()
	async def darkmode(self, ctx, value: bool=None):
		"""
		Set if the board should be a darker varient.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).darkMode()
			if v:
				await ctx.send('The board is currently the darker version.')
			else:
				await ctx.send('The board is currently the lighter version.')
		else:
			await self.config.guild(ctx.guild).darkMode.set(value)
			if value:
				await ctx.send('The board will now be the darker version.')
			else:
				await ctx.send('The board will now be the lighter version.')
	
	@monopolyset.command()
	async def doublego(self, ctx, value: bool=None):
		"""
		Set if landing on go should double the amount of money given.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doDoubleGo()
			if v:
				await ctx.send('Go value is doubled when landed on.')
			else:
				await ctx.send('Go value is not doubled when landed on.')
		else:
			await self.config.guild(ctx.guild).doDoubleGo.set(value)
			if value:
				await ctx.send('Go value will now be doubled when landed on.')
			else:
				await ctx.send('Go value will no longer be doubled when landed on.')
	
	@monopolyset.command()
	async def freeparking(self, ctx, value: Union[int, str]=None):
		"""
		Set the reward for landing on free parking.
		
		Use an integer to set a static reward.
		Use "none" for no reward.
		Use "tax" to use the sum of taxes and fees as the reward.
		Defaults to none.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).freeParkingValue()
			if v is None:
				await ctx.send('There is currently no reward for landing on free parking.')
			elif v == 'tax':
				await ctx.send(
					'The reward for landing on free parking is currently '
					'the sum of taxes and fees.'
				)
			else:
				await ctx.send(f'The reward for landing on free parking is currently ${v}.')
		else:
			if isinstance(value, int):
				await self.config.guild(ctx.guild).freeParkingValue.set(value)
				await ctx.send(f'The reward for landing on free parking is now ${value}.')
			else:
				if value.lower() == 'none':
					await self.config.guild(ctx.guild).freeParkingValue.set(None)
					await ctx.send('There is now no reward for landing on free parking.')
				elif value.lower() == 'tax':
					await self.config.guild(ctx.guild).freeParkingValue.set('tax')
					await ctx.send(
						'The reward for landing on free parking is now '
						'the sum of taxes and fees.'
					)
				else:
					await ctx.send('That is not a valid value.')

				
	@monopolyset.command()
	async def go(self, ctx, value: int=None):
		"""
		Set the base value of passing go.
		
		Defaults to 200.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).goValue()
			await ctx.send(f'You currently get ${v} from passing go.')
		else:
			await self.config.guild(ctx.guild).goValue.set(value)
			await ctx.send(f'You will now get ${value} from passing go.')
	
	@monopolyset.command()
	async def hotellimit(self, ctx, value: int=None):
		"""
		Set a limit on the number of hotels that can be bought.
		
		Use -1 to disable the limit.
		Defaults to 12.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).hotelLimit()
			if v == -1:
				await ctx.send('There is currently no limit on the number of hotels.')
			else:
				await ctx.send(f'The hotel limit is currently set to {v}.')
		else:
			if value < -1:
				return await ctx.send('That is not a valid value.')
			await self.config.guild(ctx.guild).hotelLimit.set(value)
			if value == -1:
				await ctx.send('There is now no limit on the number of hotels.')
			else:
				await ctx.send(f'The hotel limit is now set to {value}.')
				
	@monopolyset.command()
	async def houselimit(self, ctx, value: int=None):
		"""
		Set a limit on the number of houses that can be bought.
		
		Use -1 to disable the limit.
		Defaults to 32.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).houseLimit()
			if v == -1:
				await ctx.send('There is currently no limit on the number of houses.')
			else:
				await ctx.send(f'The house limit is currently set to {v}.')
		else:
			if value < -1:
				return await ctx.send('That is not a valid value.')
			await self.config.guild(ctx.guild).houseLimit.set(value)
			if value == -1:
				await ctx.send('There is now no limit on the number of houses.')
			else:
				await ctx.send(f'The house limit is now set to {value}.')
	
	@monopolyset.command()
	async def income(self, ctx, value: int=None):
		"""
		Set how much Income Tax should cost.
		
		Defaults to 200.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).incomeValue()
			await ctx.send(f'Income Tax currently costs ${v}.')
		else:
			await self.config.guild(ctx.guild).incomeValue.set(value)
			await ctx.send(f'Income Tax will now cost ${value}.')
	
	@monopolyset.command()
	async def luxury(self, ctx, value: int=None):
		"""
		Set how much Luxury Tax should cost.
		
		Defaults to 100.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).luxuryValue()
			await ctx.send(f'Luxury Tax currently costs ${v}.')
		else:
			await self.config.guild(ctx.guild).luxuryValue.set(value)
			await ctx.send(f'Luxury Tax will now cost ${value}.')
	
	@monopolyset.command()
	async def maxjailrolls(self, ctx, value: int=None):
		"""
		Set the maximum number of rolls in jail before bail has to be paid.
		
		Defaults to 3.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).maxJailRolls()
			await ctx.send(f'The maximum number of rolls in jail is {v}.')
		elif value < 0:
			await ctx.send('Players cannot spend a negative number of turns in jail.')
		else:
			await self.config.guild(ctx.guild).maxJailRolls.set(value)
			await ctx.send(f'The maximum number of rolls in jail is now {value}.')
	
	@monopolyset.command()
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
	
	@monopolyset.command()
	async def minraise(self, ctx, value: int=None):
		"""
		Set the minimum raise in auctions.
		
		Defaults to 1.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).minRaise()
			await ctx.send(f'The minimum raise is ${v}.')
		elif value <= 0:
			return await ctx.send('The minimum raise must be positive.')
		else:
			await self.config.guild(ctx.guild).minRaise.set(value)
			await ctx.send(f'The minimum raise is now ${value}.')
	
	@monopolyset.command()
	async def startingcash(self, ctx, value: int=None):
		"""
		Set how much money players should start the game with.
		
		Defaults to 1500.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).startCash()
			await ctx.send(f'Players are starting with ${v}.')
		elif value < 0:
			return await ctx.send('Players cannot start the game in debt. This isn\'t real life.')
		else:
			await self.config.guild(ctx.guild).startCash.set(value)
			await ctx.send(f'Players will start with ${value}.')

	@monopolyset.command()
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
	
	@monopolyset.command()
	async def timeout(self, ctx, value: int=None):
		"""
		Set the amount of time before the game times out.
		
		Value is in seconds.
		Use -1 to disable the timeout.
		Defaults to 60.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).timeoutValue()
			if v is None:
				await ctx.send('There is currently no timeout.')
			else:
				await ctx.send(f'The timeout is currently set to {v} seconds.')
		else:
			if value < -1:
				return await ctx.send('That is not a valid value.')
			if value == -1:
				await self.config.guild(ctx.guild).timeoutValue.set(None)
				await ctx.send('There is no longer a timeout.')
			else:
				await self.config.guild(ctx.guild).timeoutValue.set(value)
				await ctx.send(f'The timeout is now set to {value} seconds.')

	def cog_unload(self):
		return [game._task.cancel() for game in self.games]

	async def red_delete_data_for_user(self, *, requester, user_id):
		"""Replace a user with an AI in all of their games."""
		data = await self.config.all_guilds()
		for guild_id, config in data.items():
			for name, save in config['saves'].items():
				userinfo = save['uid']
				change = False
				for idx, uid in enumerate(save['uid']):
					if uid == user_id:
						userinfo[idx] = {'me': idx, 'display_name': '[AI]'}
						change = True
				if change:
					await self.config.guild_from_id(guild_id).set_raw('saves', name, 'uid', value=userinfo)
