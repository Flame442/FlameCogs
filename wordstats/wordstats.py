import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.data_manager import cog_data_path
from typing import Optional, Union
import apsw
import asyncio
import re


STOPWORDS = (
	'a', 'able', 'about', 'across', 'after', 'all', 'almost', 'also', 'am', 'among',
	'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'but', 'by', 'can',
	'cannot', 'could', 'dear', 'did', 'do', 'does', 'either', 'else', 'ever', 'every',
	'for', 'from', 'get', 'got', 'had', 'has', 'have', 'he', 'her', 'hers', 'him',
	'his', 'how', 'however', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'just',
	'least', 'let', 'like', 'likely', 'may', 'me', 'might', 'most', 'must', 'my',
	'neither', 'no', 'nor', 'not', 'of', 'off', 'often', 'on', 'only', 'or', 'other',
	'our', 'own', 'rather', 'said', 'say', 'says', 'she', 'should', 'since', 'so',
	'some', 'than', 'that', 'the', 'their', 'them', 'then', 'there', 'these', 'they',
	'this', 'tis', 'to', 'too', 'twas', 'us', 'wants', 'was', 'we', 'were', 'what',
	'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'would',
	'yet', 'you', 'your'
)

class WordStats(commands.Cog):
	"""Tracks commonly used words."""
	def __init__(self, bot):
		self.bot = bot
		self.ignore_cache = {}
		self.config = Config.get_conf(self, identifier=7345167905)
		self.config.register_guild(
			enableGuild = True,
			disabledChannels = [],
			displayStopwords = True
		)
		self._connection = apsw.Connection(str(cog_data_path(self) / 'wordstats.db'))
		self.cursor = self._connection.cursor()
		self.cursor.execute('PRAGMA journal_mode = wal;')
		self.cursor.execute('PRAGMA wal_autocheckpoint;')
		self.cursor.execute('PRAGMA read_uncommitted = 1;')
		self.cursor.execute(
			'CREATE TABLE IF NOT EXISTS guild_words ('
			'guild_id INTEGER NOT NULL,'
			'user_id INTEGER NOT NULL,'
			'word TEXT NOT NULL,'
			'quantity INTEGER DEFAULT 1,'
			'PRIMARY KEY (guild_id, user_id, word)'
			');'
		)
	
	class GuildConvert(commands.Converter):
		"""Attempts to convert a value into a guild object."""
		async def convert(self, ctx, value):
			try:
				guild = ctx.bot.get_guild(int(value))
				if guild is not None:
					return guild
				raise commands.BadArgument()
			except ValueError:
				for guild in ctx.bot.guilds:
					if guild.name == value:
						return guild
				raise commands.BadArgument()
	
	async def maybe_filter_stopwords(self, ctx, to_filter):
		"""Maybe remove stopwords from display outputs."""
		if not await self.config.guild(ctx.guild).displayStopwords():
			to_filter = [word for word in to_filter if word not in STOPWORDS]
		return to_filter
	
	@commands.guild_only()
	@commands.group(invoke_without_command=True)
	async def wordstats(
		self,
		ctx,
		member_or_guild: Optional[Union[discord.Member, GuildConvert]]=None,
		amount_or_word: Optional[Union[int, str]]=30
	):
		"""
		Prints the most commonly used words.
		
		Use the optional parameter "member_or_guild" to see the stats of a member or guild.
		Use the optional parameter "amount_or_word" to change the number of words that are displayed or to check the stats of a specific word.
		"""
		if isinstance(amount_or_word, int):
			if amount_or_word <= 0:
				return await ctx.send('At least one word needs to be displayed.')
		worddict = {}
		async with ctx.typing():
			if isinstance(member_or_guild, discord.Member):
				mention = member_or_guild.display_name
				for word, quantity in self.cursor.execute(
					'SELECT word, quantity FROM guild_words '
					'WHERE guild_id = ? AND user_id = ?',
					(ctx.guild.id, member_or_guild.id)
				):
					worddict[word] = quantity
			else:
				if member_or_guild is None:
					mention = 'this server'
					guild = ctx.guild
				else:
					mention = member_or_guild.name
					guild = member_or_guild
				for word, quantity in self.cursor.execute(
					'SELECT word, sum(quantity) FROM guild_words '
					'WHERE guild_id = ?'
					'GROUP BY word',
					(guild.id,)
				):
					worddict[word] = quantity
			order = list(reversed(sorted(worddict, key=lambda w: worddict[w])))
		if worddict == {}:
			if mention == 'this server':
				mention = 'This server'
			return await ctx.send(f'{mention} has not said any words yet.')
		if isinstance(amount_or_word, str): #specific word
			if amount_or_word.lower() not in worddict:
				return await ctx.send(
					f'The word **{amount_or_word}** has not been said by {mention} yet.'
				)
			ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
			rank = order.index(amount_or_word.lower())
			number = worddict[amount_or_word.lower()]
			if rank == 0: #most common
				mc = '**most common**'
			else: #not the most common
				mc = f'**{ordinal(rank+1)}** most common' #accounts for zero-indexing
			return await ctx.send(
				f'The word **{amount_or_word}** has been said by {mention} '
				f'**{number}** {"times" if number != 1 else "time"}.\n'
				f'It is the {mc} word {mention} has said.'
			)
		order = await self.maybe_filter_stopwords(ctx, order)
		result = ''
		n = 0
		total = sum(worddict.values())
		maxwidth = len(str(worddict[order[0]])) + 2 #max width of a number + extra for space
		for word in order:
			currentwidth = len(str(worddict[word]))   
			result += (
				f'{worddict[word]}{" " * (maxwidth-currentwidth)}{word}\n'
			)
			n += 1
			if n == amount_or_word:
				break
		if n == 1:
			mc = '**most common** word'
		else:
			mc = f'**{n}** most common words'
		try:
			await ctx.send(
				f'Out of **{total}** words and **{len(worddict)}** unique words, '
				f'the {mc} that {mention} has said {"is" if n == 1 else "are"}:\n'
				f'```{result.rstrip()}```'
			)
		except discord.errors.HTTPException:
			await ctx.send('The result is too long to send.')
	
	@wordstats.command(name='global')
	async def wordstats_global(self, ctx, amount_or_word: Optional[Union[int, str]]=30):
		"""
		Prints the most commonly used words across all guilds.
		
		Use the optional parameter "amount_or_word" to change the number of words that are displayed or to check the stats of a specific word.
		"""
		if isinstance(amount_or_word, int):
			if amount_or_word <= 0:
				return await ctx.send('At least one word needs to be displayed.')
		worddict = {}
		async with ctx.typing():
			for word, quantity in self.cursor.execute(
				'SELECT word, sum(quantity) FROM guild_words '
				'GROUP BY word'
			):
				worddict[word] = quantity
			order = list(reversed(sorted(worddict, key=lambda w: worddict[w])))
		if worddict == {}:
			return await ctx.send('No words have been said yet.')
		if isinstance(amount_or_word, str): #specific word
			if amount_or_word.lower() not in worddict:
				return await ctx.send(
					f'The word **{amount_or_word}** has not been said yet.'
				)
			ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
			rank = order.index(amount_or_word.lower())
			number = worddict[amount_or_word.lower()]
			if rank == 0: #most common
				mc = '**most common**'
			else: #not the most common
				mc = f'**{ordinal(rank+1)}** most common' #accounts for zero-indexing
			return await ctx.send(
				f'The word **{amount_or_word}** has been said '
				f'**{number}** {"times" if number != 1 else "time"} globally.\n'
				f'It is the {mc} word said.'
			)
		order = await self.maybe_filter_stopwords(ctx, order)
		result = ''
		n = 0
		total = sum(worddict.values())
		maxwidth = len(str(worddict[order[0]])) + 2 #max width of a number + extra for space
		for word in order:
			currentwidth = len(str(worddict[word]))
			result += (
				f'{worddict[word]}{" " * (maxwidth-currentwidth)}{word}\n'
			)
			n += 1
			if n == amount_or_word:
				break
		if n == 1:
			mc = '**most common** word'
		else:
			mc = f'**{n}** most common words'
		try:
			await ctx.send(
				f'Out of **{total}** words and **{len(worddict)}** unique words, '
				f'the {mc} said globally {"is" if n == 1 else "are"}:\n'
				f'```{result.rstrip()}```'
			)
		except discord.errors.HTTPException:
			await ctx.send('The result is too long to send.')
	
	@commands.guild_only()
	@commands.group(invoke_without_command=True)
	async def topchatters(
		self,
		ctx,
		guild: Optional[GuildConvert]=None,
		word: Optional[str]=None,
		amount: int=10
	):
		"""
		Prints the members who have said the most words.
		
		Use the optional parameter "guild" to see the topchatters in a specific guild.
		Use the optional parameter "word" to see the topchatters of a specific word.
		Use the optional parameter "amount" to change the number of members that are displayed.
		"""
		if word:
			if word.isdigit(): #fix for str being greedy
				amount = int(word)
				word = None
			else: #word is actually a word
				word = word.lower()
		if amount <= 0:
			return await ctx.send('At least one member needs to be displayed.')
		if guild is None:
			guild = ctx.guild
		sumdict = {}
		async with ctx.typing():
			if word:
				for user_id, quantity in self.cursor.execute(
					'SELECT user_id, sum(quantity) FROM guild_words '
					'WHERE guild_id = ? AND word = ?'
					'GROUP BY user_id',
					(guild.id, word)
				):
					sumdict[user_id] = quantity
			else:
				for user_id, quantity in self.cursor.execute(
					'SELECT user_id, sum(quantity) FROM guild_words '
					'WHERE guild_id = ?'
					'GROUP BY user_id',
					(guild.id,)
				):
					sumdict[user_id] = quantity
			order = list(reversed(sorted(sumdict, key=lambda x: sumdict[x])))
		if sumdict == {}:
			return await ctx.send('No one has chatted yet.')
		result = ''
		n = 0
		total = sum(sumdict.values())
		maxwidth = len(str(sumdict[order[0]])) + 2 #max width of a number + extra for space
		for memid in order:
			mem = guild.get_member(memid)
			if mem is None:
				name = f'<removed member {memid}>'
			else:
				name = mem.display_name
			currentwidth = len(str(sumdict[memid]))
			result += (
				f'{sumdict[memid]}{" " * (maxwidth-currentwidth)}{name}\n'
			)
			n += 1
			if n == amount:
				break
		if word:
			wordprint = f'the word **{word}** the most'
		else:
			wordprint = 'the most words'
		if n == 1:
			memberprint = 'member'
		else:
			memberprint = f'**{n}** members'
		if guild == ctx.guild:
			guildprint = 'this server'
		else:
			guildprint = guild.name
		try:
			await ctx.send(
				f'Out of **{total}** words, the {memberprint} who {"has" if n == 1 else "have"} '
				f'said {wordprint} in {guildprint} {"is" if n == 1 else "are"}:\n```{result}```'
			)
		except discord.errors.HTTPException:
			await ctx.send('The result is too long to send.')
	
	@topchatters.command(name='global')
	async def topchatters_global(self, ctx, word: Optional[str]=None, amount: int=10):
		"""
		Prints the members who have said the most words across all guilds.
		
		Use the optional parameter "word" to see the topchatters of a specific word.
		Use the optional parameter "amount" to change the number of members that are displayed.
		"""
		if word:
			if word.isdigit(): #fix for str being greedy
				amount = int(word)
				word = None
			else: #word is actually a word
				word = word.lower()
		if amount <= 0:
			return await ctx.send('At least one member needs to be displayed.')
		sumdict = {}
		async with ctx.typing():
			if word:
				for user_id, quantity in self.cursor.execute(
					'SELECT user_id, sum(quantity) FROM guild_words '
					'WHERE word = ?'
					'GROUP BY user_id',
					(word,)
				):
					sumdict[user_id] = quantity
			else:
				for user_id, quantity in self.cursor.execute(
					'SELECT user_id, sum(quantity) FROM guild_words '
					'GROUP BY user_id'
				):
					sumdict[user_id] = quantity
			order = list(reversed(sorted(sumdict, key=lambda x: sumdict[x])))
		if sumdict == {}:
			return await ctx.send(f'No one has chatted yet.')
		result = ''
		n = 0
		total = sum(sumdict.values())
		maxwidth = len(str(sumdict[order[0]])) + 2 #max width of a number + extra for space
		for memid in order:
			user = self.bot.get_user(memid)
			if user is None:
				name = f'<removed user {memid}>'
			else:
				name = user.name
			currentwidth = len(str(sumdict[memid]))
			result += (
				f'{sumdict[memid]}{" " * (maxwidth-currentwidth)}{name}\n'
			)
			n += 1
			if n == amount:
				break
		if word:
			wordprint = f'the word **{word}** the most'
		else:
			wordprint = 'the most words'
		if n == 1:
			memberprint = 'user'
		else:
			memberprint = f'**{n}** users'
		try:
			await ctx.send(
				f'Out of **{total}** words, the {memberprint} who {"has" if n == 1 else "have"} '
				f'said {wordprint} globally {"is" if n == 1 else "are"}:\n```{result}```'
			)
		except discord.errors.HTTPException:
			await ctx.send('The result is too long to send.')
	
	@commands.guild_only()
	@commands.group(invoke_without_command=True)
	async def topratio(
		self,
		ctx,
		word: str,
		guild: Optional[GuildConvert]=None,
		amount: int=10,
		min_total: int=0
	):
		"""
		Prints the members with the highest "word to all words" ratio.
		
		Use the parameter "word" to set the word to compare.
		Use the optional parameter "guild" to see the ratio in a specific guild.
		Use the optional parameter "amount" to change the number of members that are displayed.
		Use the optional parameter "min_total" to change the minimum number of words a user needs to have said to be shown.
		"""
		if amount <= 0:
			return await ctx.send('At least one member needs to be displayed.')
		if min_total < 0:
			min_total = 0
		if guild is None:
			guild = ctx.guild
		word = word.lower()
		worddict = {}
		async with ctx.typing():
			for user_id, w, quantity in self.cursor.execute(
				'SELECT user_id, word, quantity FROM guild_words '
				'WHERE guild_id = ? ',
				(guild.id,)
			):
				if user_id not in worddict:
					worddict[user_id] = {}
				worddict[user_id][w] = quantity
			sumdict = {}
			for user_id in worddict:
				if word in worddict[user_id] and sum(worddict[user_id].values()) >= min_total:
					sumdict[user_id] = worddict[user_id][word] / sum(worddict[user_id].values())
			order = list(reversed(sorted(sumdict, key=lambda x: sumdict[x])))
		if sumdict == {}:
			return await ctx.send('No one has chatted yet.')
		result = ''
		n = 0
		for memid in order:
			mem = guild.get_member(memid)
			if mem is None:
				name = f'<removed member {memid}>'
			else:
				name = mem.display_name
			result += (
				'{:4f} {}\n'.format(sumdict[memid], name)
			)
			n += 1
			if n == amount:
				break
		if n == 1:
			memberprint = 'member'
			have_has = 'has'
		else:
			memberprint = f'**{n}** members'
			have_has = 'have'
		if guild == ctx.guild:
			guildprint = 'this server'
		else:
			guildprint = guild.name
		min_words_msg = ''
		if min_total > 0:
			min_words_msg = f'that {have_has} said at least **{min_total}** messages '
		try:
			await ctx.send(
				f'The {memberprint} in {guildprint} {min_words_msg}who {have_has} '
				f'said the word **{word}** the most compared to other words '
				f'{"is" if n == 1 else "are"}:\n```{result}```'
			)
		except discord.errors.HTTPException:
			await ctx.send('The result is too long to send.')
	
	@topratio.command(name='global')
	async def topratio_global(self, ctx, word: str, amount: int=10, min_total: int=0):
		"""
		Prints the members with the highest "word to all words" ratio in all guilds.
		
		Use the parameter "word" to set the word to compare.
		Use the optional parameter "amount" to change the number of members that are displayed.
		Use the optional parameter "min_total" to change the minimum number of words a user needs to have said to be shown.
		"""
		if amount <= 0:
			return await ctx.send('At least one member needs to be displayed.')
		if min_total < 0:
			min_total = 0
		word = word.lower()
		worddict = {}
		async with ctx.typing():
			for user_id, w, quantity in self.cursor.execute(
				'SELECT user_id, word, quantity FROM guild_words'
			):
				if user_id not in worddict:
					worddict[user_id] = {}
				if w not in worddict[user_id]:
					worddict[user_id][w] = quantity
				else:
					worddict[user_id][w] += quantity
			sumdict = {}
			for user_id in worddict:
				if word in worddict[user_id] and sum(worddict[user_id].values()) >= min_total:
					sumdict[user_id] = worddict[user_id][word] / sum(worddict[user_id].values())
			order = list(reversed(sorted(sumdict, key=lambda x: sumdict[x])))
		if sumdict == {}:
			return await ctx.send('No one has chatted yet.')
		result = ''
		n = 0
		for memid in order:
			mem = ctx.guild.get_member(memid)
			if mem is None:
				name = f'<removed member {memid}>'
			else:
				name = mem.display_name
			result += (
				'{:4f} {}\n'.format(sumdict[memid], name)
			)
			n += 1
			if n == amount:
				break
		if n == 1:
			memberprint = 'member'
			have_has = 'has'
		else:
			memberprint = f'**{n}** members'
			have_has = 'have'
		min_words_msg = ''
		if min_total > 0:
			min_words_msg = f'that {have_has} said at least **{min_total}** messages '
		try:
			await ctx.send(
				f'The {memberprint} {min_words_msg}who {have_has} '
				f'globally said the word **{word}** the most compared to other words '
				f'{"is" if n == 1 else "are"}:\n```{result}```'
			)
		except discord.errors.HTTPException:
			await ctx.send('The result is too long to send.')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group()
	async def wordstatsset(self, ctx):
		"""Config options for wordstats."""
		pass
	
	@checks.is_owner()
	@wordstatsset.command()
	async def deleteall(self, ctx, confirm: bool=False):
		"""
		Dalete all wordstats data.
		
		This removes all existing data, creating a blank state.
		This cannot be undone.
		"""
		if not confirm:
			await ctx.send(
				'Running this command will delete all wordstats data. '
				'This cannot be undone. '
				f'Run `{ctx.prefix}wordstatsset deleteall yes` to confirm.'
			)
			return
		self.cursor.execute('DROP TABLE guild_words;')
		self.cursor.execute(
			'CREATE TABLE IF NOT EXISTS guild_words ('
			'guild_id INTEGER NOT NULL,'
			'user_id INTEGER NOT NULL,'
			'word TEXT NOT NULL,'
			'quantity INTEGER DEFAULT 1,'
			'PRIMARY KEY (guild_id, user_id, word)'
			');'
		)
		await ctx.send('Wordstats data has been reset.')
	
	@checks.is_owner()
	@wordstatsset.command()
	async def convert(self, ctx):
		"""Convert data from config to the SQLite database."""
		await ctx.send('Begining conversion, this may take a while.')
		async with ctx.typing():
			self.cursor.execute('BEGIN TRANSACTION;')
			data = await self.config.all_members()
			for guild_id in data:
				for member_id in data[guild_id]:
					for word in data[guild_id][member_id]['worddict']:
						value = data[guild_id][member_id]['worddict'][word]
						self.cursor.execute(
							'INSERT INTO guild_words (guild_id, user_id, word, quantity)'
							'VALUES (?, ?, ?, ?)'
							'ON CONFLICT(guild_id, user_id, word) DO UPDATE SET quantity = quantity + ?;',
							(guild_id, member_id, word, value, value)
						)
					await asyncio.sleep(0)
			self.cursor.execute('COMMIT;')
		await ctx.send('Done converting.')
	
	@wordstatsset.command()
	async def server(self, ctx, value: bool=None):
		"""
		Set if wordstats should record stats for this server.
		
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).enableGuild()
			if v:
				await ctx.send('Stats are being recorded in this server.')
			else:
				await ctx.send('Stats are not being recorded in this server.')
		else:
			await self.config.guild(ctx.guild).enableGuild.set(value)
			if value:
				await ctx.send('Stats will now be recorded in this server.')
			else:
				await ctx.send('Stats will no longer be recorded in this server.')
			if ctx.guild.id in self.ignore_cache:
				del self.ignore_cache[ctx.guild.id]
	
	@wordstatsset.command()
	async def channel(self, ctx, value: bool=None):
		"""
		Set if wordstats should record stats for this channel.
		
		Defaults to True.
		This value is channel specific.
		"""
		v = await self.config.guild(ctx.guild).disabledChannels()
		if value is None:
			if ctx.channel.id not in v:
				await ctx.send('Stats are being recorded in this channel.')
			else:
				await ctx.send('Stats are not being recorded in this channel.')
		else:
			if value:
				if ctx.channel.id not in v:
					await ctx.send('Stats are already being recorded in this channel.')
				else:
					v.remove(ctx.channel.id)
					await self.config.guild(ctx.guild).disabledChannels.set(v)
					await ctx.send('Stats will now be recorded in this channel.')
			else:
				if ctx.channel.id in v:
					await ctx.send('Stats are already not being recorded in this channel.')
				else:
					v.append(ctx.channel.id)
					await self.config.guild(ctx.guild).disabledChannels.set(v)
					await ctx.send('Stats will no longer be recorded in this channel.')
			if ctx.guild.id in self.ignore_cache:
				del self.ignore_cache[ctx.guild.id]
	
	@wordstatsset.command()
	async def stopwords(self, ctx, value: bool=None):
		"""
		Set if stopwords should be included in outputs.
		
		Stopwords are common words such as "a", "it" and "the".
		Stopwords will still be included in numerical counts, they will only be hidden from list displays.
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).displayStopwords()
			if v:
				await ctx.send('Stopwords are included in outputs.')
			else:
				await ctx.send('Stopwords are not included in outputs.')
		else:
			await self.config.guild(ctx.guild).displayStopwords.set(value)
			if value:
				await ctx.send('Stopwords will now be included in outputs.')
			else:
				await ctx.send('Stopwords will no longer be included in outputs.')
	
	@commands.Cog.listener()
	async def on_message_without_command(self, msg):
		"""Passively records all message contents."""
		if not msg.author.bot and isinstance(msg.channel, discord.TextChannel):
			if msg.guild.id not in self.ignore_cache:
				cfg = await self.config.guild(msg.guild).all()
				self.ignore_cache[msg.guild.id] = cfg
			enableGuild = self.ignore_cache[msg.guild.id]['enableGuild']
			disabledChannels = self.ignore_cache[msg.guild.id]['disabledChannels']
			if enableGuild and not msg.channel.id in disabledChannels:
				#Strip any characters besides letters and spaces.
				words = re.sub(r'[^a-z \n]', '', msg.content.lower()).split()
				for word in words:
					self.cursor.execute(
						'INSERT INTO guild_words (guild_id, user_id, word)'
						'VALUES (?, ?, ?)'
						'ON CONFLICT(guild_id, user_id, word) DO UPDATE SET quantity = quantity + 1;',
						(msg.guild.id, msg.author.id, word)
					)
