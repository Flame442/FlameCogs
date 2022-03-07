import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.data_manager import cog_data_path
from typing import Optional, Union
import apsw
import asyncio
import concurrent.futures
import functools
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
		self.ignore_cache_guild = {}
		self.ignore_cache_user = {}
		self.config = Config.get_conf(self, identifier=7345167905)
		self.config.register_guild(
			enableGuild = True,
			disabledChannels = [],
			displayStopwords = True,
			minWordLength = 0,
		)
		self.config.register_user(
			enableUser = True,
		)
		self._connection = apsw.Connection(str(cog_data_path(self) / 'wordstats.db'))
		self.cursor = self._connection.cursor()
		self.cursor.execute('PRAGMA journal_mode = wal;')
		self.cursor.execute('PRAGMA read_uncommitted = 1;')
		self.cursor.execute(
			'CREATE TABLE IF NOT EXISTS member_words ('
			'guild_id INTEGER NOT NULL,'
			'user_id INTEGER NOT NULL,'
			'word TEXT NOT NULL,'
			'quantity INTEGER DEFAULT 1,'
			'PRIMARY KEY (guild_id, user_id, word)'
			');'
		)
		self._executor = concurrent.futures.ThreadPoolExecutor(1)
	
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
			if amount_or_word > 100:
				return await ctx.send('You cannot request more than 100 words.')
			amount = amount_or_word
			word = None
		else:
			amount = None
			word = amount_or_word.lower()
		if isinstance(member_or_guild, discord.Member):
			guild = ctx.guild
			member = member_or_guild
			mention = member.display_name
		else:
			if member_or_guild is None:
				guild = ctx.guild
				member = None
				mention = 'this server'
			else:
				guild = member_or_guild
				member = None
				mention = guild.name
		async with ctx.typing():
			if word:
				if member:
					result = self.cursor.execute(
						'SELECT rank, count FROM '
						'( '
						'SELECT rank() OVER win AS rank, word AS word, count AS count '
						'FROM ( '
						'SELECT SUM(quantity) AS count, word FROM member_words '
						'WHERE guild_id = ? AND user_id = ? '
						'GROUP BY word '
						') '
						'WINDOW win AS (ORDER BY count DESC) '
						') '
						'WHERE word = ? '
						'LIMIT 1',
						(guild.id, member.id, word)
					).fetchone()
				else:
					result = self.cursor.execute(
						'SELECT rank, count FROM '
						'('
						'SELECT rank() OVER win AS rank, word AS word, count AS count '
						'FROM ( '
						'SELECT SUM(quantity) AS count, word FROM member_words '
						'WHERE guild_id = ? '
						'GROUP BY word '
						') '
						'WINDOW win AS (ORDER BY count DESC) '
						') '
						'WHERE word = ? '
						'LIMIT 1',
						(guild.id, word)
					).fetchone()
				if not result:
					return await ctx.send(
						f'The word **{word}** has not been said by {mention} yet.'
					)
				rank, count = result
				ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
				if rank == 1: #most common
					mc = '**most common**'
				else: #not the most common
					mc = f'**{ordinal(rank)}** most common'
				return await ctx.send(
					f'The word **{word}** has been said by {mention} '
					f'**{count}** {"times" if count != 1 else "time"}.\n'
					f'It is the {mc} word {mention} has said.'
				)
			if member:
				result = self.cursor.execute(
					'SELECT sum(quantity), count(DISTINCT word) FROM member_words WHERE guild_id = ? AND user_id = ? LIMIT 1',
					(guild.id, member.id)
				).fetchone()
			else:
				result = self.cursor.execute(
					'SELECT sum(quantity), count(DISTINCT word) FROM member_words WHERE guild_id = ? LIMIT 1',
					(guild.id,)
				).fetchone()
			if not result[0]:
				return await ctx.send('No words have been said yet.')
			total, unique = result
			amount = min(unique, amount)
			if await self.config.guild(ctx.guild).displayStopwords():
				stop = tuple()
			else:
				stop = STOPWORDS
			minWordLength = await self.config.guild(ctx.guild).minWordLength()
			if member:
				result = self.cursor.execute(
					'SELECT word, quantity FROM member_words '
					f'WHERE guild_id = ? AND user_id = ? AND word NOT IN {stop} AND length(word) >= ? '
					'ORDER BY quantity DESC '
					'LIMIT ? ',
					(guild.id, member.id, minWordLength, amount)
				).fetchall()
			else:
				result = self.cursor.execute(
					'SELECT word, sum(quantity) AS total FROM member_words '
					f'WHERE guild_id = ? AND word NOT IN {stop} AND length(word) >= ? '
					'GROUP BY word '
					'ORDER BY total DESC '
					'LIMIT ? ',
					(guild.id, minWordLength, amount)
				).fetchall()
		if not result:
			return await ctx.send('No words have been said yet.')
		msg = ''
		maxwidth = len(str(result[0][1])) + 2 #max width of a number + extra for space
		for value in result:
			currentwidth = len(str(value[1]))   
			msg += (
				f'{value[1]}{" " * (maxwidth-currentwidth)}{value[0]}\n'
			)
		if amount == 1:
			mc = '**most common** word'
			is_are = 'is'
		else:
			mc = f'**{amount}** most common words'
			is_are = 'are'
		try:
			await ctx.send(
				f'Out of **{total}** words and **{unique}** unique words, '
				f'the {mc} that {mention} has said {is_are}:\n'
				f'```{msg.rstrip()}```'
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
			if amount_or_word > 100:
				return await ctx.send('You cannot request more than 100 words.')
			amount = amount_or_word
			word = None
		else:
			amount = None
			word = amount_or_word.lower()
		async with ctx.typing():
			if word:
				result = self.cursor.execute(
					'SELECT rank, count FROM '
					'( '
					'SELECT rank() OVER win AS rank, word AS word, count AS count '
					'FROM ( '
					'SELECT SUM(quantity) AS count, word FROM member_words '
					'GROUP BY word '
					') '
					'WINDOW win AS (ORDER BY count DESC) '
					') '
					'WHERE word = ? '
					'LIMIT 1',
					(word,)
				).fetchone()
				if not result:
					return await ctx.send(
						f'The word **{word}** has not been said yet.'
					)
				rank, count = result
				ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
				if rank == 1: #most common
					mc = '**most common**'
				else: #not the most common
					mc = f'**{ordinal(rank)}** most common'
				return await ctx.send(
					f'The word **{word}** has been said globally '
					f'**{count}** {"times" if count != 1 else "time"}.\n'
					f'It is the {mc} word said.'
				)
			result = self.cursor.execute(
				'SELECT sum(quantity), count(DISTINCT word) FROM member_words LIMIT 1'
			).fetchone()
			if not result[0]:
				return await ctx.send('No words have been said yet.')
			total, unique = result
			amount = min(unique, amount)
			if await self.config.guild(ctx.guild).displayStopwords():
				stop = tuple()
			else:
				stop = STOPWORDS
			minWordLength = await self.config.guild(ctx.guild).minWordLength()
			result = self.cursor.execute(
				'SELECT word, sum(quantity) AS total FROM member_words '
				f'WHERE word NOT IN {stop} AND length(word) >= ? '
				'GROUP BY word '
				'ORDER BY total DESC '
				'LIMIT ? ',
				(minWordLength, amount)
			).fetchall()
		if not result:
			return await ctx.send('No words have been said yet.')
		msg = ''
		maxwidth = len(str(result[0][1])) + 2 #max width of a number + extra for space
		for value in result:
			currentwidth = len(str(value[1]))   
			msg += (
				f'{value[1]}{" " * (maxwidth-currentwidth)}{value[0]}\n'
			)
		if amount == 1:
			mc = '**most common** word'
			is_are = 'is'
		else:
			mc = f'**{amount}** most common words'
			is_are = 'are'
		try:
			await ctx.send(
				f'Out of **{total}** words and **{unique}** unique words, '
				f'the {mc} said globally {is_are}:\n'
				f'```{msg.rstrip()}```'
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
		if amount > 100:
			return await ctx.send('You cannot request more than 100 members.')
		if guild is None:
			guild = ctx.guild
		async with ctx.typing():
			if word:
				result = self.cursor.execute(
					'SELECT sum(quantity), count(DISTINCT user_id) FROM member_words '
					'WHERE guild_id = ? AND word = ? LIMIT 1',
					(guild.id, word)
				).fetchone()
			else:
				result = self.cursor.execute(
					'SELECT sum(quantity), count(DISTINCT user_id) FROM member_words '
					'WHERE guild_id = ? LIMIT 1',
					(guild.id,)
				).fetchone()
			if not result[0]:
				return await ctx.send('No words have been said yet.')
			total, unique = result
			amount = min(unique, amount)
			if word:
				result = self.cursor.execute(
					'SELECT user_id, sum(quantity) AS total FROM member_words '
					'WHERE guild_id = ? AND word = ?'
					'GROUP BY user_id '
					'ORDER BY total DESC '
					'LIMIT ?',
					(guild.id, word, amount)
				).fetchall()
			else:
				result = self.cursor.execute(
					'SELECT user_id, sum(quantity) AS total FROM member_words '
					'WHERE guild_id = ?'
					'GROUP BY user_id '
					'ORDER BY total DESC '
					'LIMIT ?',
					(guild.id, amount)
				).fetchall()
		msg = ''
		maxwidth = len(str(result[0][1])) + 2 #max width of a number + extra for space
		for value in result:
			currentwidth = len(str(value[1]))  
			mem = guild.get_member(value[0])
			if mem is None:
				name = f'<removed member {value[0]}>'
			else:
				name = mem.display_name
			msg += (
				f'{value[1]}{" " * (maxwidth-currentwidth)}{name}\n'
			)
		if word:
			wordprint = f'the word **{word}** the most'
		else:
			wordprint = 'the most words'
		if amount == 1:
			memberprint = 'member'
			is_are = 'is'
			has_have = 'has'
		else:
			memberprint = f'**{amount}** members'
			is_are = 'are'
			has_have = 'have'
		if guild == ctx.guild:
			guildprint = 'this server'
		else:
			guildprint = guild.name
		try:
			await ctx.send(
				f'Out of **{total}** words, the {memberprint} who {has_have} '
				f'said {wordprint} in {guildprint} {is_are}:\n```{msg}```'
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
			return await ctx.send('At least one user needs to be displayed.')
		if amount > 100:
			return await ctx.send('You cannot request more than 100 users.')
		async with ctx.typing():
			if word:
				result = self.cursor.execute(
					'SELECT sum(quantity), count(DISTINCT user_id) FROM member_words '
					'WHERE word = ? LIMIT 1',
					(word,)
				).fetchone()
			else:
				result = self.cursor.execute(
					'SELECT sum(quantity), count(DISTINCT user_id) FROM member_words LIMIT 1'
				).fetchone()
			if not result[0]:
				return await ctx.send('No words have been said yet.')
			total, unique = result
			amount = min(unique, amount)
			if word:
				result = self.cursor.execute(
					'SELECT user_id, sum(quantity) AS total FROM member_words '
					'WHERE word = ? '
					'GROUP BY user_id '
					'ORDER BY total DESC '
					'LIMIT ?',
					(word, amount)
				).fetchall()
			else:
				result = self.cursor.execute(
					'SELECT user_id, sum(quantity) AS total FROM member_words '
					'GROUP BY user_id '
					'ORDER BY total DESC '
					'LIMIT ?',
					(amount,)
				).fetchall()
		msg = ''
		maxwidth = len(str(result[0][1])) + 2 #max width of a number + extra for space
		for value in result:
			currentwidth = len(str(value[1]))  
			user = self.bot.get_user(value[0])
			if user is None:
				name = f'<removed user {value[0]}>'
			else:
				name = user.name
			msg += (
				f'{value[1]}{" " * (maxwidth-currentwidth)}{name}\n'
			)
		if word:
			wordprint = f'the word **{word}** the most'
		else:
			wordprint = 'the most words'
		if amount == 1:
			memberprint = 'user'
			is_are = 'is'
			has_have = 'has'
		else:
			memberprint = f'**{amount}** users'
			is_are = 'are'
			has_have = 'have'
		try:
			await ctx.send(
				f'Out of **{total}** words, the {memberprint} who {has_have} '
				f'said {wordprint} globally {is_are}:\n```{msg}```'
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
		if amount > 100:
			return await ctx.send('You cannot request more than 100 members.')
		if min_total < 0:
			min_total = 0
		if guild is None:
			guild = ctx.guild
		word = word.lower()
		worddict = {}
		async with ctx.typing():
			for user_id, w, quantity in self.cursor.execute(
				'SELECT user_id, word, quantity FROM member_words '
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
			return await ctx.send('At least one user needs to be displayed.')
		if amount > 100:
			return await ctx.send('You cannot request more than 100 users.')
		if min_total < 0:
			min_total = 0
		word = word.lower()
		worddict = {}
		async with ctx.typing():
			for user_id, w, quantity in self.cursor.execute(
				'SELECT user_id, word, quantity FROM member_words'
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
	
	@commands.group()
	async def wordstatsset(self, ctx):
		"""Config options for wordstats."""
		pass
	
	@checks.is_owner()
	@wordstatsset.command()
	async def deleteall(self, ctx, confirm: bool=False):
		"""
		Delete all wordstats data.
		
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
		self.cursor.execute('DROP TABLE member_words;')
		self.cursor.execute(
			'CREATE TABLE IF NOT EXISTS member_words ('
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
			hold = []
			data = await self.config.all_members()
			for guild_id in data:
				for member_id in data[guild_id]:
					for word in data[guild_id][member_id]['worddict']:
						value = data[guild_id][member_id]['worddict'][word]
						hold.append((guild_id, member_id, word, value, value))
					await asyncio.sleep(0)
			self.cursor.execute('BEGIN TRANSACTION;')
			self.cursor.executemany(
				'INSERT INTO member_words (guild_id, user_id, word, quantity)'
				'VALUES (?, ?, ?, ?)'
				'ON CONFLICT(guild_id, user_id, word) DO UPDATE SET quantity = quantity + ?;',
				(hold)
			)
			self.cursor.execute('COMMIT;')
		await ctx.send('Done converting.')
	
	@commands.guild_only()
	@checks.guildowner()
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
			if ctx.guild.id in self.ignore_cache_guild:
				del self.ignore_cache_guild[ctx.guild.id]
	
	@commands.guild_only()
	@checks.guildowner()
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
			if ctx.guild.id in self.ignore_cache_guild:
				del self.ignore_cache_guild[ctx.guild.id]
	
	@wordstatsset.command()
	async def user(self, ctx, value: bool=None):
		"""
		Set if wordstats should record stats for you.
		
		Defaults to True.
		This value is user specific.
		"""
		if value is None:
			v = await self.config.user(ctx.author).enableUser()
			if v:
				await ctx.send(f'Stats are being recorded for you. Use `{ctx.prefix}wordstatsset user no` to disable.')
			else:
				await ctx.send('Stats are not being recorded for you.')
		else:
			await self.config.user(ctx.author).enableUser.set(value)
			if value:
				await ctx.send('Stats will now be recorded for you.')
			else:
				await ctx.send('Stats will no longer be recorded for you.')
			if ctx.author.id in self.ignore_cache_user:
				del self.ignore_cache_user[ctx.author.id]
	
	@wordstatsset.command()
	async def forgetme(self, ctx):
		"""
		Make wordstats forget all data about you.
		
		This is equivalent to `[p]mydata forgetme`, but only for wordstats.
		This cannot be undone.
		"""
		await self.red_delete_data_for_user(requester='user_strict', user_id=ctx.author.id)
		await ctx.send(
			'Done!\nThis does **not** prevent wordstats from continuing to track you. '
			'If you do not want more data to be collected, make sure you run `[p]wordstatsset user no`.'
		)
	
	@commands.guild_only()
	@checks.guildowner()
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
	
	@commands.guild_only()
	@checks.guildowner()
	@wordstatsset.command()
	async def minlength(self, ctx, value: int=None):
		"""
		Set the minimum length a word has to be in order to be displayed.
		
		Shorter words will still be included in numerical counts, they will only be hidden from list displays.
		Set to 0 to disable.
		Defaults to 0.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).minWordLength()
			await ctx.send(f'The minimum word length is currently {v}.')
			return
		if value < 0:
			await ctx.send('You must provide a number that is 0 or greater.')
			return
		await self.config.guild(ctx.guild).minWordLength.set(value)
		await ctx.send(f'The minimum word length is now set to {value}.')
	
	def cog_unload(self):
		self._executor.shutdown()
	
	async def red_delete_data_for_user(self, *, requester, user_id):
		"""Delete all data from a particular user."""
		query = (
			'DELETE FROM member_words '
			'WHERE user_id = ?;'
		)
		self.cursor.execute(query, (user_id,))
	
	def safe_write(self, query, data):
		"""Func for safely writing in another thread."""
		cursor = self._connection.cursor()
		cursor.executemany(query, data)
	
	@commands.Cog.listener()
	async def on_message_without_command(self, msg):
		"""Passively records all message contents."""
		if msg.author.bot or not isinstance(msg.channel, discord.TextChannel):
			return
		if await self.bot.cog_disabled_in_guild(self, msg.guild):
			return
		if msg.guild.id not in self.ignore_cache_guild:
			cfg = await self.config.guild(msg.guild).all()
			self.ignore_cache_guild[msg.guild.id] = cfg
		if msg.author.id not in self.ignore_cache_user:
			cfg = await self.config.user(msg.author).all()
			self.ignore_cache_user[msg.author.id] = cfg
		enableGuild = self.ignore_cache_guild[msg.guild.id]['enableGuild']
		disabledChannels = self.ignore_cache_guild[msg.guild.id]['disabledChannels']
		enableUser = self.ignore_cache_user[msg.author.id]['enableUser']
		if not enableGuild or msg.channel.id in disabledChannels or not enableUser:
			return
		#Strip any characters besides letters and spaces.
		words = re.sub(r'[^a-z \n]', '', msg.content.lower()).split()
		query = (
			'INSERT INTO member_words (guild_id, user_id, word)'
			'VALUES (?, ?, ?)'
			'ON CONFLICT(guild_id, user_id, word) DO UPDATE SET quantity = quantity + 1;'
		)
		data = ((msg.guild.id, msg.author.id, word) for word in words)
		task = functools.partial(self.safe_write, query, data)
		await self.bot.loop.run_in_executor(self._executor, task)
