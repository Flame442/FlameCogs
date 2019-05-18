import discord, re
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.data_manager import cog_data_path
from redbot.core.config import Group
from copy import deepcopy
from typing import Optional, Union, Dict
from random import randint
import time
import asyncio


class WordStats(commands.Cog):
	"""Tracks commonly used words."""
	def __init__(self, bot):
		self.bot = bot
		self.members_to_update = {}
		self.guilds_to_update = {}
		self.last_save = time.time()
		self.config = Config.get_conf(self, identifier=7345167905)
		self.config.register_guild(
			enableGuild = True,
			disabledChannels = []
		)
		self.config.register_member(
			worddict = {}
		)
	
	class GuildConvert(commands.Converter):
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

	def _combine_dicts(self, dicts: dict):
		"""Combine multiple dicts into one"""
		result = {}
		for m in dicts:
			for w in dicts[m]['worddict']:
				if w in result:
					result[w] += dicts[m]['worddict'][w]
				else:
					result[w] = dicts[m]['worddict'][w]
		return result

	def _combine_dicts_global(self, dicts: dict):
		"""Combine multiple dicts into one"""
		result = {}
		for g in dicts:
			for m in g:
				for w in dicts[g][m]['worddict']:
					if w in result:
						result[w] += dicts[g][m]['worddict'][w]
					else:
						result[w] = dicts[g][m]['worddict'][w]
		return result
	
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
		
		Use the optional paramater "member_or_guild" to see the stats of a member or guild.
		Use the optional paramater "amount_or_word" to change the number of words that are displayed or to check the stats of a specific word.
		"""
		if isinstance(amount_or_word, int):
			if amount_or_word <= 0:
				return await ctx.send('At least one word needs to be displayed.')
		async with ctx.typing():
			await self.update_data()
			if member_or_guild is None:
				mention = 'this server'
				dicts = await self.config.all_members(ctx.guild)
				worddict = self._combine_dicts(dicts)
			elif isinstance(member_or_guild, discord.Member):
				mention = member_or_guild.display_name
				worddict = await self.config.member(member_or_guild).worddict()
			else:
				mention = member_or_guild.name
				dicts = await self.config.all_members(member_or_guild)
				worddict = self._combine_dicts(dicts)
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
		
		Use the optional paramater "amount_or_word" to change the number of words that are displayed or to check the stats of a specific word.
		"""
		if isinstance(amount_or_word, int):
			if amount_or_word <= 0:
				return await ctx.send('At least one word needs to be displayed.')
		async with ctx.typing():
			await self.update_data()
			dicts = await self.config.all_members()
			worddict = self._combine_dicts_global(dicts)
			order = list(reversed(sorted(worddict, key=lambda w: worddict[w])))
		if worddict == {}:
			return await ctx.send(f'No words have been said yet.')
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
		
		Use the optional paramater "guild" to see the topchatters in a specific guild.
		Use the optional paramater "word" to see the topchatters of a specific word.
		Use the optional paramater "amount" to change the number of members that are displayed.
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
		async with ctx.typing():
			await self.update_data()
			data = await self.config.all_members(guild)
			sumdict = {}
			for memid in data:
				if word:
					if word in data[memid]['worddict']:
						sumdict[memid] = data[memid]['worddict'][word]
				else:
					n = 0
					for w in data[memid]['worddict']:
						n += data[memid]['worddict'][w]
					sumdict[memid] = n
			order = list(reversed(sorted(sumdict, key=lambda x: sumdict[x])))
		if sumdict == {}:
			return await ctx.send(f'No one has chatted yet.')
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
		
		Use the optional paramater "word" to see the topchatters of a specific word.
		Use the optional paramater "amount" to change the number of members that are displayed.
		"""
		if word:
			if word.isdigit(): #fix for str being greedy
				amount = int(word)
				word = None
			else: #word is actually a word
				word = word.lower()
		if amount <= 0:
			return await ctx.send('At least one member needs to be displayed.')
		async with ctx.typing():
			await self.update_data()
			data = await self.config.all_members()
			sumdict = {}
			for guild in data:
				for memid in data[guild]:
					if word:
						if word in data[guild][memid]['worddict']:
							if memid in sumdict:
								sumdict[memid] += data[guild][memid]['worddict'][word]
							else:
								sumdict[memid] = data[guild][memid]['worddict'][word]
					else:
						n = 0
						for w in data[guild][memid]['worddict']:
							n += data[guild][memid]['worddict'][w]
						if memid in sumdict:
							sumdict[memid] += n
						else:
							sumdict[memid] = n
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
	@checks.guildowner()
	@commands.group()
	async def wordstatsset(self, ctx):
		"""Config options for wordstats."""
		pass
			
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
			v = await self.config.guild(msg.guild).enableGuild()
			if v:
				await ctx.send('Stats are being recorded in this server.')
			else:
				await ctx.send('Stats are not being recorded in this server.')
		else:
			await self.config.guild(msg.guild).enableGuild.set(value)
			if value:
				await ctx.send('Stats will now be recorded in this server.')
			else:
				await ctx.send('Stats will no longer be recorded in this server.')
			
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
			
	async def update_data(self):
		"""Saves everything to disk."""
		self.members_to_update = {}
	
	async def on_message(self, msg):
		"""Passively records all message contents."""
		if not msg.author.bot and isinstance(msg.channel, discord.TextChannel):
			enableGuild = await self.config.guild(msg.guild).enableGuild()
			disabledChannels = await self.config.guild(msg.guild).disabledChannels()
			if enableGuild and not msg.channel.id in disabledChannels:
				p = await self.bot.get_prefix(msg)
				if any([msg.content.startswith(x) for x in p]):
					return
				words = str(re.sub(r'[^a-zA-Z ]', '', msg.content.lower())).split(' ')
				if msg.author not in self.members_to_update:
					self.members_to_update[msg.author] = await self.config.member(msg.author).all()
				memdict = self.members_to_update[msg.author]['worddict']
				for word in words:
					if not word:
						continue
					if word in memdict:
						memdict[word] += 1
					else:
						memdict[word] = 1
				self.members_to_update[msg.author]['worddict'] = memdict
				if time.time() - self.last_save >= 600: #10 minutes per save
					await self.update_data()
