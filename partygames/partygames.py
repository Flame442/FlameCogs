import discord
from redbot.core import commands
from redbot.core.data_manager import bundled_data_path
from redbot.core import checks
import random
import asyncio


CHARS = {
	'en-US': [
		'STR', 'REF', 'WEA', 'ZAP', 'ANG',
		'DIS', 'INT', 'MIL', 'LAG', 'CRA',
		'WHI', 'IDE', 'LOV', 'FOR', 'INK',
		'BER', 'ATT', 'CAL', 'SAV', 'OVE',
		'CRO', 'DRA', 'LOW', 'IOD', 'BRO',
		'INO', 'BRE', 'REV', 'LUB', 'SCA',
		'FLA', 'HUN', 'SOF', 'RAF', 'COM',
		'IMI', 'GAG', 'CLA', 'WOR', 'BLA',
		'SCH', 'ABS', 'PAL', 'PUR', 'SHL',
		'INC', 'MIS', 'DIG', 'SPL', 'SHI',
		'PRO', 'ROA', 'SYR', 'INS', 'COK',
		'KIL', 'JET', 'RES', 'UNP', 'PAT',
		'DEP', 'ADJ', 'LIT', 'SAT', 'HAN', 
		'BET', 'TIC'
	]
}

class PartyGames(commands.Cog):
	"""Chat games focused on coming up with words from 3 letters."""
	def __init__(self, bot):
		self.bot = bot
		self.waiting = {}

	@commands.group(aliases=['pg'])
	async def partygames(self, ctx):
		"""Group command for party games."""
		pass

	async def _get_players(self, ctx):
		"""Helper function to set up a game."""
		msg = await ctx.send('React to this message to join. The game will start in 15 seconds.')
		await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')
		await asyncio.sleep(15)
		msg = await ctx.channel.get_message(msg.id) #get the latest version of the message
		reaction = [r for r in msg.reactions if r.emoji == '\N{WHITE HEAVY CHECK MARK}'][0]
		players = []
		async for user in reaction.users():
			players.append(user)
		return [p for p in players if not p.bot]

	async def _get_worddict(self, ctx):
		"""Get the proper worddict for the current locale."""
		locale = await ctx.bot.db.locale()
		if locale not in CHARS:
			await ctx.send('Your locale is not available. Using `en-US`.')
			locale = 'en-US'
		with open(bundled_data_path(self) / f'{locale}.txt') as f:
			worddict = [line.strip().lower() for line in f]
		return worddict, locale

	@staticmethod
	def _get_name_string(ctx, uid: int, domention: bool):
		"""Returns a member identification string from an id, checking for exceptions."""
		member = ctx.guild.get_member(uid)
		if member:
			return member.mention if domention else member.display_name
		return f'<removed member {uid}>'

	def _make_leaderboard(self, ctx, scores):
		"""Returns a printable version of the dictionary."""
		order = list(reversed(sorted(scores, key=lambda m: scores[m])))
		msg = 'Number of points:\n'
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
		players = await self._get_players(ctx)
		if len(players) <= 1:
			return await ctx.send('Not enough players to play.')
		worddict, locale = await self._get_worddict(ctx)
		health = {p.id: hp for p in players}
		game = True
		used = []
		while game:
			for p in players:
				if health[p.id] == 0:
					continue
				c = random.choice(CHARS[locale])
				await ctx.send(f'{p.mention}, type a word containing: **{c}**')
				try:
					word = await self.bot.wait_for(
						'message',
						timeout=7,
						check=lambda m: (
							m.channel == ctx.channel
							and m.author.id == p.id
							and c.lower() in m.content.lower()
							and m.content.lower() in worddict
							and not m.content.lower() in used
						)
					)
				except asyncio.TimeoutError:
					health[p.id] -= 1
					await ctx.send(f'Time\'s up! -1 HP ({health[p.id]} remaining)')
					if health[p.id] == 0:
						await ctx.send(f'{p.mention} is eliminated!')
						players.remove(p)
						if len(players) == 1:
							await ctx.send(f'{players[0].mention} wins!')
							game = False
							break
				else:
					await word.add_reaction('\N{WHITE HEAVY CHECK MARK}')
					used.append(word.content.lower())
				await asyncio.sleep(3)
			msg = 'Current lives remaining:\n'
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
		players = await self._get_players(ctx)
		if len(players) <= 1:
			return await ctx.send('Not enough players to play.')
		worddict, locale = await self._get_worddict(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			score, used, mem = await self._fast(ctx, score, used, players, worddict, locale)
			if mem is None:
				afk += 1
				if afk == 3:
					await ctx.send(
						'No one wants to play :(\n'
						f'{self._make_leaderboard(ctx, score)}'
					)
					game = False
				else:
					await ctx.send('No one was able to come up with a word!')
			else:
				afk = 0
				if score[mem.id] >= maxpoints:
					await ctx.send(
						f'{mem.mention} wins!\n'
						f'{self._make_leaderboard(ctx, score)}'
					)
					game = False
			await asyncio.sleep(3)
	
	async def _fast(self, ctx, score, used, players, worddict, locale):
		c = random.choice(CHARS[locale])
		await ctx.send(
			f'Be the first person to type a word containing: **{c}**'
		)
		try:
			word = await self.bot.wait_for(
				'message',
				timeout=15,
				check=lambda m: (
					m.channel == ctx.channel
					and m.author.id in score
					and c.lower() in m.content.lower()
					and m.content.lower() in worddict
					and not m.content.lower() in used
				)
			)
		except asyncio.TimeoutError:
			return score, used, None
		else:
			await word.add_reaction('\N{WHITE HEAVY CHECK MARK}')
			score[word.author.id] += 1
			await ctx.send(
				f'{word.author.mention} gets a point! '
				f'({score[word.author.id]} total)'
			)
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
		players = await self._get_players(ctx)
		if len(players) <= 1:
			return await ctx.send('Not enough players to play.')
		worddict, locale = await self._get_worddict(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			score, used, mem = await self._long(ctx, score, used, players, worddict, locale)
			if mem is None:
				afk += 1
				if afk == 3:
					await ctx.send(
						'No one wants to play :(\n'
						f'{self._make_leaderboard(ctx, score)}'
					)
					game = False
				else:
					await ctx.send('No one was able to come up with a word!')
			else:
				afk = 0
				if score[mem.id] >= maxpoints:
					await ctx.send(
						f'{mem.mention} wins!\n'
						f'{self._make_leaderboard(ctx, score)}'
					)
					game = False
			await asyncio.sleep(3)
		
	async def _long(self, ctx, score, used, players, worddict, locale):
		c = random.choice(CHARS[locale])
		await ctx.send(f'Type the longest word containing: **{c}**')
		self.waiting[ctx.channel.id] = {
			'type': 'long',
			'plist': [p.id for p in players],
			'chars': c,
			'used': used,
			'best': '',
			'bestmem': None,
			'worddict': worddict
		}
		await asyncio.sleep(15)
		resultdict = self.waiting[ctx.channel.id]
		del self.waiting[ctx.channel.id]
		if resultdict['best'] == '':
			return score, used, None
		score[resultdict['bestmem'].id] += 1
		await ctx.send(
			f'{resultdict["bestmem"].mention} gets a point! '
			f'({score[resultdict["bestmem"].id]} total)'
		)
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
		players = await self._get_players(ctx)
		if len(players) <= 1:
			return await ctx.send('Not enough players to play.')
		worddict, locale = await self._get_worddict(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			score, used, mem = await self._most(ctx, score, used, players, worddict, locale)
			if mem is None:
				afk += 1
				if afk == 3:
					await ctx.send(
						'No one wants to play :(\n'
						f'{self._make_leaderboard(ctx, score)}'
					)
					game = False
				else:
					await ctx.send('No one was able to come up with a word!')
			elif mem is False:
				afk = 0
				await ctx.send('There was a tie! Nobody gets points...')
			else:
				afk = 0
				if score[mem.id] >= maxpoints:
					await ctx.send(
						f'{mem.mention} wins!\n'
						f'{self._make_leaderboard(ctx, score)}'
					)
					game = False
			await asyncio.sleep(3)
		
	async def _most(self, ctx, score, used, players, worddict, locale):
		c = random.choice(CHARS[locale])
		await ctx.send(f'Type the most words containing: **{c}**')
		self.waiting[ctx.channel.id] = {
			'type': 'most',
			'pdict': {p.id: [] for p in players},
			'chars': c,
			'used': used,
			'worddict': worddict
		}
		await asyncio.sleep(15)
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
		msg = 'Number of words found:\n'
		for uid in order:
			name = self._get_name_string(ctx, uid, False)
			msg += f'{len(resultdict["pdict"][uid])} {name}\n'
		await ctx.send(f'```{msg}```')
		if len(winners) == 1:
			score[order[0]] += 1
			await ctx.send(
				f'{self._get_name_string(ctx, order[0], True)} gets a point! '
				f'({score[order[0]]} total)'
			)
			return score, used, ctx.guild.get_member(order[0])
			#in the very specific case of a member leaving after becoming the person 
			#with the most words, this will return None and do a werid double print.
			#deal with it.
		return score, used, False #tie
	
	@partygames.command()
	async def mix(self, ctx, maxpoints: int=5):
		"""
		Play a mixture of all 4 games.

		Words cannot be reused.
		The first person to get `maxpoints` points wins.
		"""
		players = await self._get_players(ctx)
		if len(players) <= 1:
			return await ctx.send('Not enough players to play.')
		worddict, locale = await self._get_worddict(ctx)
		score = {p.id: 0 for p in players}
		game = True
		used = []
		afk = 0
		while game:
			g = random.randint(0,3)
			if g == 3:
				for p in players:
					c = random.choice(CHARS[locale])
					await ctx.send(f'{p.mention}, type a word containing: **{c}**')
					try:
						word = await self.bot.wait_for(
							'message',
							timeout=7,
							check=lambda m: (
								m.channel == ctx.channel
								and m.author.id == p.id
								and c.lower() in m.content.lower()
								and m.content.lower() in worddict
								and not m.content.lower() in used
							)
						)
					except asyncio.TimeoutError:
						await ctx.send(f'Time\'s up! No points for you...')
					else:
						await word.add_reaction('\N{WHITE HEAVY CHECK MARK}')
						used.append(word.content.lower())
						score[p.id] += 1
						await ctx.send(
							f'{p.mention} gets a point! '
							f'({score[p.id]} total)'
						)
						if score[p.id] >= maxpoints:
							await ctx.send(
								f'{p.mention} wins!\n'
								f'{self._make_leaderboard(ctx, score)}'
							)
							game = False
							break
					await asyncio.sleep(3)
			else:
				func = [self._fast, self._long, self._most][g]
				score, used, mem = await func(ctx, score, used, players, worddict, locale)
				if mem is None:
					afk += 1
					if afk == 3:
						await ctx.send(
							'No one wants to play :(\n'
							f'{self._make_leaderboard(ctx, score)}'
						)
						game = False
					else:
						await ctx.send('No one was able to come up with a word!')
				elif mem is False:
					afk = 0
					await ctx.send('There was a tie! Nobody gets points...')
				else:
					afk = 0
					if score[mem.id] >= maxpoints:
						await ctx.send(
							f'{mem.mention} wins!\n'
							f'{self._make_leaderboard(ctx, score)}'
						)
						game = False
			await asyncio.sleep(3)
	
	async def on_message(self, message):
		if message.author.bot:
			return
		if message.guild is None:
			return
		if message.channel.id in self.waiting:
			if self.waiting[message.channel.id]['type'] == 'long':
				if message.author.id in self.waiting[message.channel.id]['plist']:
					if (
						self.waiting[message.channel.id]['chars'].lower() in message.content.lower()
						and message.content.lower() in self.waiting[message.channel.id]['worddict']
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
						and message.content.lower() in self.waiting[message.channel.id]['worddict']
						and not message.content.lower() in self.waiting[message.channel.id]['used']
					):
						self.waiting[message.channel.id]['used'].append(message.content.lower())
						self.waiting[message.channel.id]['pdict'][message.author.id].append(message.content.lower())
						await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
