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
			worddict = {},
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
			await self.update_data(members=self.members_to_update, guilds=self.guilds_to_update)
			if member_or_guild is None:
				mention = 'this server'
				worddict = await self.config.guild(ctx.guild).worddict()
			elif isinstance(member_or_guild, discord.Member):
				mention = member_or_guild.display_name
				worddict = await self.config.member(member_or_guild).worddict()
			else:
				mention = member_or_guild.name
				worddict = await self.config.guild(member_or_guild).worddict()
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
			await self.update_data(members=self.members_to_update, guilds=self.guilds_to_update)
			guilddicts = await self.config.all_guilds()
			worddict = {}
			for g in guilddicts:
				for w in guilddicts[g]['worddict']:
					if w in worddict:
						worddict[w] += guilddicts[g]['worddict'][w]
					else:
						worddict[w] = guilddicts[g]['worddict'][w]
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
			await self.update_data(members=self.members_to_update, guilds=self.guilds_to_update)
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
			await self.update_data(members=self.members_to_update, guilds=self.guilds_to_update)
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
		if ctx.guild not in self.guilds_to_update:
			self.guilds_to_update[ctx.guild] = await self.config.guild(ctx.guild).all()
		if value is None:
			v = self.guilds_to_update[ctx.guild]['enableGuild']
			if v:
				await ctx.send('Stats are being recorded in this server.')
			else:
				await ctx.send('Stats are not being recorded in this server.')
		else:
			self.guilds_to_update[ctx.guild]['enableGuild'] = value
			await self.update_data(members=self.members_to_update, guilds=self.guilds_to_update)
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
		if ctx.guild not in self.guilds_to_update:
			self.guilds_to_update[ctx.guild] = await self.config.guild(ctx.guild).all()
		v = self.guilds_to_update[ctx.guild]['disabledChannels']
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
					self.guilds_to_update[ctx.guild]['disabledChannels'] = v
					await self.update_data(
						members=self.members_to_update,
						guilds=self.guilds_to_update
					)
					await ctx.send('Stats will now be recorded in this channel.')
			else:
				if ctx.channel.id in v:
					await ctx.send('Stats are already not being recorded in this channel.')
				else:
					v.append(ctx.channel.id)
					self.guilds_to_update[ctx.guild]['disabledChannels'] = v
					await self.update_data(
						members=self.members_to_update,
						guilds=self.guilds_to_update
					)
					await ctx.send('Stats will no longer be recorded in this channel.')
			
	async def update_data(
		self,
		members: Dict[discord.Member, dict],
		guilds: Dict[discord.Guild, dict]
	):
		"""Thanks to Sinbad for this dark magic."""
		self.last_save = time.time()
		base_group = Group(
			identifiers=(), 
			defaults={}, 
			driver=self.config.driver,
			force_registration=self.config.force_registration,
		)

		def nested_update(d, keys, value):
			partial = d
			for i in keys[:-1]:
				if i not in partial:
					partial.update({i: {}})
				partial = partial[i]
			partial[keys[-1]] = value

		async with base_group() as data:
			# this is a workaround for needing to switch contexts safely
			# to prevent heartbeat issues
			member_iterator = enumerate(list(members.items()), 1)
			guild_iterator = enumerate(list(guilds.items()), 1)
			for index, (member, member_data) in member_iterator:
				keys = (self.config.MEMBER, str(member.guild.id), str(member.id))
				value = deepcopy(member_data)
				nested_update(data, keys, value)
				if index % 10:
					await asyncio.sleep(0)
			for index, (guild, guild_data) in guild_iterator:
				keys = (self.config.GUILD, str(guild.id))
				value = deepcopy(guild_data)
				nested_update(data, keys, value)
				if index % 10:
					await asyncio.sleep(0)

		self.members_to_update = {}
		self.guilds_to_update = {}
	
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
				if msg.guild not in self.guilds_to_update:
					self.guilds_to_update[msg.guild] = await self.config.guild(msg.guild).all()
				guilddict = self.guilds_to_update[msg.guild]['worddict']
				if msg.author not in self.members_to_update:
					self.members_to_update[msg.author] = await self.config.member(msg.author).all()
				memdict = self.members_to_update[msg.author]['worddict']
				for word in words:
					if not word:
						continue
					if word in guilddict:
						guilddict[word] += 1
					else:
						guilddict[word] = 1
					if word in memdict:
						memdict[word] += 1
					else:
						memdict[word] = 1
				self.guilds_to_update[msg.guild]['worddict'] = guilddict
				self.members_to_update[msg.author]['worddict'] = memdict
				if time.time() - self.last_save >= 600: #10 minutes per save
					await self.update_data(
						members=self.members_to_update,
						guilds=self.guilds_to_update
					)
