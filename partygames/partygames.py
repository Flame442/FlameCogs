import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core import checks
from redbot.core.i18n import Translator, cog_i18n, get_locale
import random
import asyncio
import json


CHARS = {
	'en-US': [
		'WEA', 'BRE', 'IST', 'CRA', 'STA',
		'SPL', 'REF', 'MIL', 'FOR', 'GAG',
		'TIC', 'ILL', 'RAF', 'BLA', 'JET',
		'CLA', 'CON', 'SIN', 'INK', 'SAT',
		'MIN', 'SCH', 'BER', 'ISE', 'IDE',
		'LAT', 'IMI', 'ZAP', 'ENT', 'WHI',
		'TRI', 'OVE', 'SAV', 'HAN', 'PUR',
		'LIN', 'LOG', 'CAT', 'INS', 'STI',
		'RIS', 'COM', 'INC', 'ELL', 'MEN',
		'TIN', 'SOF', 'KIL', 'BRO', 'ADJ',
		'PRO', 'BET', 'SHI', 'ORI', 'HUN',
		'LOW', 'LUB', 'ANG', 'SCA', 'RED',
		'DEP', 'PER', 'INT', 'ROA', 'RES',
		'TRA', 'WOR', 'SYR', 'MAT', 'MIS',
		'DIS', 'STR', 'COK', 'GRA', 'INE',
		'UNP', 'ATT', 'DIG', 'IOD', 'CAL',
		'LOV', 'ATE', 'LAG', 'INO', 'CRO',
		'PAL', 'PAT', 'ICA', 'ABS', 'DRA',
		'RAN', 'LIT', 'RAT', 'TRO', 'FLA',
		'REV', 'VER'
	],
	'fr-FR': [
		'ENT', 'ONS', 'ASS', 'RAI', 'ION',
		'SSE', 'RON', 'SSI', 'IEN', 'AIS',
		'AIE', 'AIT', 'TER', 'ERI', 'ONN',
		'ANT', 'ERO', 'RAS', 'ISS', 'SER',
		'TES', 'REN', 'ONT', 'RIE', 'CON',
		'SES', 'LER', 'SIO', 'SEN', 'NER',
		'RIO', 'SIE', 'MES', 'ÈRE', 'QUE',
		'ISE', 'RER', 'CHA', 'TIO', 'NTE',
		'LIS', 'IER', 'ÉES', 'TRA', 'ATI',
		'NNE', 'RES', 'OUR', 'SSA', 'ÂTE',
		'ERE', 'ISA', 'ÂME', 'RIS', 'TAS',
		'LAS', 'SAI', 'CHE', 'RAN', 'IQU',
		'ALI', 'DÉC', 'SAS', 'TAI', 'UER',
		'INE', 'EME', 'LAI', 'NAS', 'PAR',
		'INT', 'AGE', 'BOU', 'PER', 'ESS',
		'EUR', 'PRO', 'LLA'
	]
}

_ = Translator('PartyGames', __file__)

@cog_i18n(_)
class PartyGames(commands.Cog):
	"""Chat games focused on coming up with words from 3 letters."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_guild(
			locale = None,
			timeBomb = 7,
			timeFast = 15,
			timeLong = 15,
			timeMost = 15
		)
		self.waiting = {}
		self.games = []

	@commands.group(aliases=['pg'])
	async def partygames(self, ctx):
		"""Group command for party games."""
		pass

	async def _get_players(self, ctx):
		"""Helper function to set up a game."""
		msg = await ctx.send(
			_('React to this message to join. The game will start in 15 seconds.')
		)
		await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')
		await asyncio.sleep(15)
		msg = await ctx.channel.fetch_message(msg.id) #get the latest version of the message
		reaction = [r for r in msg.reactions if r.emoji == '\N{WHITE HEAVY CHECK MARK}']
		#edge case test for the reaction being removed from the message
		if not reaction:
			return []
		reaction = reaction[0]
		players = []
		async for user in reaction.users():
			players.append(user)
		return [p for p in players if not p.bot]

	async def _get_wordlist(self, ctx):
		"""Get the proper wordlist for the current locale."""
		locale = await self.config.guild(ctx.guild).locale()
		if locale is None:
			locale = get_locale()
		for char in CHARS:
			if locale.lower() == char.lower():
				locale = char #convert case to the one used by the file
				break
		if locale not in CHARS: #now case insensitive 
			await ctx.send(_('Your locale is not available. Using `en-US`.'))
			locale = 'en-US'
		with open(bundled_data_path(self) / f'{locale}.json') as f:
			wordlist = json.load(f)
		return wordlist, locale

	@staticmethod
	def _get_name_string(ctx, uid: int, domention: bool):
		"""Returns a member identification string from an id, checking for exceptions."""
		member = ctx.guild.get_member(uid)
		if member:
			return member.mention if domention else member.display_name
		return _('<removed member {uid}>').format(uid=uid)

	def _make_leaderboard(self, ctx, scores):
		"""Returns a printable version of the dictionary."""
		order = list(reversed(sorted(scores, key=lambda m: scores[m])))
		msg = _('Number of points:\n')
		for uid in order:
			name = self._get_name_string(ctx, uid, False)
			msg += f'{scores[uid]} {name}\n'
		return f'```{msg}```'

	@partygames.command()
	async def bombparty(self, ctx, hp: int=3):
		"""
		Start a game of bombparty.
		
		Each player will be asked to come up with a word that contains the given characters.
		If they are unable to do so, they will lose a life.
		Words cannot be reused.
		The last person to have lives left wins.
		"""
		if ctx.channel.id in self.games:
			await ctx.send(_('There is already a game running in this channel!'))
			return
		self.games.append(ctx.channel.id)
		players = await self._get_players(ctx)
		if len(players) <= 1:
			await ctx.send(_('Not enough players to play.'))
			if ctx.channel.id in self.games:
				self.games.remove(ctx.channel.id)
			return
		wordlist, locale = await self._get_wordlist(ctx)
		health = {p.id: hp for p in players}
		game = True
		used = []
		while game:
			for p in players:
				if health[p.id] == 0:
					continue
				c = random.choice(CHARS[locale])
				await ctx.send(
					_('{p}, type a word containing: **{char}**').format(p=p.mention, char=c)
				)
				try:
					word = await self.bot.wait_for(
						'message',
						timeout=await self.config.guild(ctx.guild).timeBomb(),
						check=lambda m: (
							m.channel == ctx.channel
							and m.author.id == p.id
							and c.lower() in m.content.lower()
							and m.content.lower() in wordlist
							and not m.content.lower() in used
						)
					)
				except asyncio.TimeoutError:
					health[p.id] -= 1
					await ctx.send(
						_('Time\'s up! -1 HP ({health} remaining)').format(health=health[p.id])
					)
					if health[p.id] == 0:
						await ctx.send(_('{p} is eliminated!').format(p=p.mention))
						players.remove(p)
						if len(players) == 1:
							await ctx.send(_('{p} wins!').format(p=players[0].mention))
							if ctx.channel.id in self.games:
								self.games.remove(ctx.channel.id)
							return
				else:
					await word.add_reaction('\N{WHITE HEAVY CHECK MARK}')
					used.append(word.content.lower())
				await asyncio.sleep(3)
			msg = _('Current lives remaining:\n')
			order = list(reversed(sorted(health, key=lambda m: health[m])))
			for uid in order:
				name = self._get_name_string(ctx, uid, False)
				msg += f'{health[uid]} {name}\n'
			await ctx.send(f'```{msg}```')
			await asyncio.sleep(3)
	
	@partygames.command()
	async def fast(self, ctx, maxpoints: int=5):
		"""
Race to type a word the fastest.

The first person to type a word that contains the given characters gets a point.
Words cannot be reused.
The first person to get `maxpoints` points wins.
		"""
		if ctx.channel.id in self.games:
			await ctx.send(_('There is already a game running in this channel!'))
			return
		self.games.append(ctx.channel.id)
		players = await self._get_players(ctx)
		if len(players) <= 1:
			await ctx.send(_('Not enough players to play.'))
			if ctx.channel.id in self.games:
				self.games.remove(ctx.channel.id)
			return
		wordlist, locale = await self._get_wordlist(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			score, used, mem = await self._fast(ctx, score, used, players, wordlist, locale)
			if mem is None:
				afk += 1
				if afk == 3:
					await ctx.send(_(
						'No one wants to play :(\n{board}'
					).format(board=self._make_leaderboard(ctx, score)))
					game = False
				else:
					await ctx.send(_('No one was able to come up with a word!'))
			else:
				afk = 0
				if score[mem.id] >= maxpoints:
					await ctx.send(_(
						'{mem} wins!\n{board}'
					).format(mem=mem.mention, board=self._make_leaderboard(ctx, score)))
					game = False
			await asyncio.sleep(3)
		if ctx.channel.id in self.games:
			self.games.remove(ctx.channel.id)
	
	async def _fast(self, ctx, score, used, players, wordlist, locale):
		c = random.choice(CHARS[locale])
		await ctx.send(
			_('Be the first person to type a word containing: **{char}**').format(char=c)
		)
		try:
			word = await self.bot.wait_for(
				'message',
				timeout=await self.config.guild(ctx.guild).timeFast(),
				check=lambda m: (
					m.channel == ctx.channel
					and m.author.id in score
					and c.lower() in m.content.lower()
					and m.content.lower() in wordlist
					and not m.content.lower() in used
				)
			)
		except asyncio.TimeoutError:
			return score, used, None
		else:
			await word.add_reaction('\N{WHITE HEAVY CHECK MARK}')
			score[word.author.id] += 1
			await ctx.send(_(
				'{mem} gets a point! ({score} total)'
			).format(mem=word.author.mention, score=score[word.author.id]))
			used.append(word.content.lower())
			return score, used, word.author
			
	@partygames.command()
	async def long(self, ctx, maxpoints: int=5):
		"""
		Type the longest word.
		
		The person to type the longest word that contains the given characters gets a point.
		Words cannot be reused.
		The first person to get `maxpoints` points wins.
		"""
		if ctx.channel.id in self.games:
			await ctx.send(_('There is already a game running in this channel!'))
			return
		self.games.append(ctx.channel.id)
		players = await self._get_players(ctx)
		if len(players) <= 1:
			await ctx.send(_('Not enough players to play.'))
			if ctx.channel.id in self.games:
				self.games.remove(ctx.channel.id)
			return
		wordlist, locale = await self._get_wordlist(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			score, used, mem = await self._long(ctx, score, used, players, wordlist, locale)
			if mem is None:
				afk += 1
				if afk == 3:
					await ctx.send(_(
						'No one wants to play :(\n{board}'
					).format(board=self._make_leaderboard(ctx, score)))
					game = False
				else:
					await ctx.send(_('No one was able to come up with a word!'))
			else:
				afk = 0
				if score[mem.id] >= maxpoints:
					await ctx.send(_(
						'{mem} wins!\n{board}'
					).format(mem=mem.mention, board=self._make_leaderboard(ctx, score)))
					game = False
			await asyncio.sleep(3)
		if ctx.channel.id in self.games:
			self.games.remove(ctx.channel.id)
		
	async def _long(self, ctx, score, used, players, wordlist, locale):
		c = random.choice(CHARS[locale])
		timeLong = await self.config.guild(ctx.guild).timeLong()
		await ctx.send(_('Type the longest word containing: **{char}**').format(char=c))
		self.waiting[ctx.channel.id] = {
			'type': 'long',
			'plist': [p.id for p in players],
			'chars': c,
			'used': used,
			'best': '',
			'bestmem': None,
			'wordlist': wordlist
		}
		await asyncio.sleep(timeLong)
		resultdict = self.waiting[ctx.channel.id]
		del self.waiting[ctx.channel.id]
		if resultdict['best'] == '':
			return score, used, None
		score[resultdict['bestmem'].id] += 1
		await ctx.send(_(
			'{mem} gets a point! ({score} total)'
		).format(mem=resultdict['bestmem'].mention, score=score[resultdict['bestmem'].id]))
		used.append(resultdict['best'].lower())
		return score, used, resultdict['bestmem']
	
	@partygames.command()
	async def most(self, ctx, maxpoints: int=5):
		"""
		Type the most words.
		
		The person to type the most words that contain the given characters gets a point.
		Words cannot be reused.
		The first person to get `maxpoints` points wins.
		"""
		if ctx.channel.id in self.games:
			await ctx.send(_('There is already a game running in this channel!'))
			return
		self.games.append(ctx.channel.id)
		players = await self._get_players(ctx)
		if len(players) <= 1:
			await ctx.send(_('Not enough players to play.'))
			if ctx.channel.id in self.games:
				self.games.remove(ctx.channel.id)
			return
		wordlist, locale = await self._get_wordlist(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			score, used, mem = await self._most(ctx, score, used, players, wordlist, locale)
			if mem is None:
				afk += 1
				if afk == 3:
					await ctx.send(_(
						'No one wants to play :(\n{board}'
					).format(board=self._make_leaderboard(ctx, score)))
					game = False
				else:
					await ctx.send(_('No one was able to come up with a word!'))
			elif mem is False:
				afk = 0
				await ctx.send(_('There was a tie! Nobody gets points...'))
			else:
				afk = 0
				if score[mem.id] >= maxpoints:
					await ctx.send(_(
						'{mem} wins!\n{board}'
					).format(mem=mem.mention, board=self._make_leaderboard(ctx, score)))
					game = False
			await asyncio.sleep(3)
		if ctx.channel.id in self.games:
			self.games.remove(ctx.channel.id)
		
	async def _most(self, ctx, score, used, players, wordlist, locale):
		c = random.choice(CHARS[locale])
		await ctx.send(_('Type the most words containing: **{char}**').format(char=c))
		timeMost = await self.config.guild(ctx.guild).timeMost()
		self.waiting[ctx.channel.id] = {
			'type': 'most',
			'pdict': {p.id: [] for p in players},
			'chars': c,
			'used': used,
			'wordlist': wordlist
		}
		await asyncio.sleep(timeMost)
		resultdict = self.waiting[ctx.channel.id]
		del self.waiting[ctx.channel.id]
		used = resultdict['used']
		order = list(reversed(sorted(
			resultdict['pdict'],
			key=lambda m: len(resultdict['pdict'][m])
		)))
		if resultdict['pdict'][order[0]] == []:
			return score, used, None
		winners = []
		for uid in order:
			if len(resultdict['pdict'][uid]) == len(resultdict['pdict'][order[0]]):
				winners.append(uid)
			else:
				break
		msg = _('Number of words found:\n')
		for uid in order:
			name = self._get_name_string(ctx, uid, False)
			msg += f'{len(resultdict["pdict"][uid])} {name}\n'
		await ctx.send(f'```{msg}```')
		if len(winners) == 1:
			score[order[0]] += 1
			await ctx.send(_(
				'{mem} gets a point! ({score} total)'
			).format(mem=self._get_name_string(ctx, order[0], True), score=score[order[0]]))
			return score, used, ctx.guild.get_member(order[0])
			#in the very specific case of a member leaving after becoming the person 
			#with the most words, this will return None and do a weird double print.
			#deal with it.
		return score, used, False #tie
	
	@partygames.command()
	async def mix(self, ctx, maxpoints: int=5):
		"""
		Play a mixture of all 4 games.

		Words cannot be reused.
		The first person to get `maxpoints` points wins.
		"""
		if ctx.channel.id in self.games:
			await ctx.send(_('There is already a game running in this channel!'))
			return
		self.games.append(ctx.channel.id)
		players = await self._get_players(ctx)
		if len(players) <= 1:
			await ctx.send(_('Not enough players to play.'))
			if ctx.channel.id in self.games:
				self.games.remove(ctx.channel.id)
			return
		wordlist, locale = await self._get_wordlist(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			g = random.randint(0,3)
			if g == 3:
				for p in players:
					c = random.choice(CHARS[locale])
					await ctx.send(_(
						'{mem}, type a word containing: **{char}**'
					).format(mem=p.mention, char=c))
					try:
						word = await self.bot.wait_for(
							'message',
							timeout=await self.config.guild(ctx.guild).timeBomb(),
							check=lambda m: (
								m.channel == ctx.channel
								and m.author.id == p.id
								and c.lower() in m.content.lower()
								and m.content.lower() in wordlist
								and not m.content.lower() in used
							)
						)
					except asyncio.TimeoutError:
						await ctx.send(_('Time\'s up! No points for you...'))
					else:
						await word.add_reaction('\N{WHITE HEAVY CHECK MARK}')
						used.append(word.content.lower())
						score[p.id] += 1
						await ctx.send(_(
							'{mem} gets a point! ({score} total)'
						).format(mem=p.mention, score=score[p.id]))
						if score[p.id] >= maxpoints:
							await ctx.send(_(
								'{mem} wins!\n{board}'
							).format(mem=p.mention, board=self._make_leaderboard(ctx, score)))
							game = False
					await asyncio.sleep(3)
			else:
				func = [self._fast, self._long, self._most][g]
				score, used, mem = await func(ctx, score, used, players, wordlist, locale)
				if mem is None:
					afk += 1
					if afk == 3:
						await ctx.send(_(
							'No one wants to play :(\n{board}'
						).format(board=self._make_leaderboard(ctx, score)))
						game = False
					else:
						await ctx.send(_('No one was able to come up with a word!'))
				elif mem is False:
					afk = 0
					await ctx.send(_('There was a tie! Nobody gets points...'))
				else:
					afk = 0
					if score[mem.id] >= maxpoints:
						await ctx.send(_(
							'{mem} wins!\n{board}'
						).format(mem=mem.mention, board=self._make_leaderboard(ctx, score)))
						game = False
			await asyncio.sleep(3)
		if ctx.channel.id in self.games:
			self.games.remove(ctx.channel.id)
	
	@checks.guildowner()
	@commands.group(aliases=['pgset'])
	async def partygamesset(self, ctx):
		"""Config options for partygames."""
		pass
	
	@partygamesset.group(invoke_without_command=True)
	async def locale(self, ctx, locale: str):
		"""
Override the bot's locale for partygames.

Defaults to None.
This value is server specific.
		"""
		for char in CHARS:
			if locale.lower() == char.lower():
				locale = char #convert case to the one used by the file
				break
		if locale not in CHARS:
			return await ctx.send(_('That locale is not valid or is not supported.'))
		await self.config.guild(ctx.guild).locale.set(locale)
		await ctx.send(_('Locale override is now set to `{locale}`.').format(locale=locale))
	
	@locale.command()
	async def remove(self, ctx):
		"""
Remove the locale override and use the bot's locale.
		"""
		await self.config.guild(ctx.guild).locale.set(None)
		await ctx.send(_('Locale override removed.'))
	
	@partygamesset.command()
	async def bombtime(self, ctx, value: int=None):
		"""
		Set the timeout of bombparty.
		
		Defaults to 7.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).timeBomb()
			await ctx.send(_('The timeout is currently set to {v}.').format(v=v))
		else:
			if value <= 0:
				return await ctx.send(_('That value is too low.'))
			await self.config.guild(ctx.guild).timeBomb.set(value)
			await ctx.send(_('The timeout is now set to {value}.').format(value=value))
	
	@partygamesset.command()
	async def fasttime(self, ctx, value: int=None):
		"""
		Set the timeout of fast.
		
		Defaults to 15.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).timeFast()
			await ctx.send(_('The timeout is currently set to {v}.').format(v=v))
		else:
			if value <= 0:
				return await ctx.send(_('That value is too low.'))
			await self.config.guild(ctx.guild).timeFast.set(value)
			await ctx.send(_('The timeout is now set to {value}.').format(value=value))
	
	@partygamesset.command()
	async def longtime(self, ctx, value: int=None):
		"""
Set the timeout of long.

Defaults to 15.
This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).timeLong()
			await ctx.send(_('The timeout is currently set to {v}.').format(v=v))
		else:
			if value <= 0:
				return await ctx.send(_('That value is too low.'))
			await self.config.guild(ctx.guild).timeLong.set(value)
			await ctx.send(_('The timeout is now set to {value}.').format(value=value))
	
	@partygamesset.command()
	async def mosttime(self, ctx, value: int=None):
		"""
		Set the timeout of most.
		
		Defaults to 15.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).timeMost()
			await ctx.send(_('The timeout is currently set to {v}.').format(v=v))
		else:
			if value <= 0:
				return await ctx.send(_('That value is too low.'))
			await self.config.guild(ctx.guild).timeMost.set(value)
			await ctx.send(_('The timeout is now set to {value}.').format(value=value))

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return

	@commands.Cog.listener()
	async def on_message(self, message):
		#This func cannot use cog_disabled_in_guild, or the game will continute to running
		#and send messages w/o any way to stop it.
		if message.author.bot:
			return
		if message.guild is None:
			return
		if message.channel.id in self.waiting:
			if self.waiting[message.channel.id]['type'] == 'long':
				if message.author.id in self.waiting[message.channel.id]['plist']:
					if (
						self.waiting[message.channel.id]['chars'].lower() in message.content.lower()
						and message.content.lower() in self.waiting[message.channel.id]['wordlist']
						and not message.content.lower() in self.waiting[message.channel.id]['used']
						and len(message.content) > len(self.waiting[message.channel.id]['best'])
					):
						self.waiting[message.channel.id]['best'] = message.content.lower()
						self.waiting[message.channel.id]['bestmem'] = message.author
						await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
			elif self.waiting[message.channel.id]['type'] == 'most':
				if message.author.id in self.waiting[message.channel.id]['pdict']:
					if (
						self.waiting[message.channel.id]['chars'].lower() in message.content.lower()
						and message.content.lower() in self.waiting[message.channel.id]['wordlist']
						and not message.content.lower() in self.waiting[message.channel.id]['used']
					):
						self.waiting[message.channel.id]['used'].append(message.content.lower())
						self.waiting[message.channel.id]['pdict'][message.author.id].append(message.content.lower())
						await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
