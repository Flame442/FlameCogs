import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.i18n import Translator, cog_i18n
import aiohttp
import asyncio
from datetime import date
from io import BytesIO


_ = Translator('GiftAway', __file__)


class GuildConvert(commands.Converter):
	"""Attempts to convert a value into a guild object."""
	async def convert(self, ctx, value):
		try:
			guild = ctx.bot.get_guild(int(value))
			if guild is not None:
				return guild
			raise commands.BadArgument(_('Could not find guild `{value}`.').format(value=value))
		except ValueError:
			for guild in ctx.bot.guilds:
				if guild.name == value:
					return guild
			raise commands.BadArgument(_('Could not find guild `{value}`.').format(value=value))


class GiftError(RuntimeError):
	"""Generic error for the Gift class."""
	pass


class Gift:
	"""Object representing a specific gift."""
	
	def __repr__(self):
		return f'<Gift game_name={self.game_name!r}, invoke_id={self.invoke_id!r}>'
	
	@classmethod
	async def create(cls, cog, ctx, channels: list, game_name: str, keys: list):
		obj = cls()
		obj.cog = cog
		obj.author = ctx.author
		obj.invoke_id = str(ctx.message.id) #keys auto cast to str, avoid confusion
		obj.game_name = game_name
		obj.keys = keys
		obj.claimed = []
		obj.claimed_by_text = []
		obj.claimed_by_id = []
		obj.link_url = None
		obj.cover_url = None
		obj.fields = []
		if len(keys) == 0:
			raise GiftError(_('At least one key must be provided.'))
		if not channels:
			raise GiftError(_('No channels provided.'))
		await obj.get_game_data()
		embed = obj.gen_embed()
		messages = await asyncio.gather(*(channel.send(embed=embed) for channel in channels), return_exceptions=True)
		#filter exceptions
		obj.messages = [x for x in messages if isinstance(x, discord.Message)]
		asyncio.gather(*(message.add_reaction('\N{WHITE HEAVY CHECK MARK}') for message in obj.messages), return_exceptions=True)
		return obj
	
	@classmethod
	async def from_dict(cls, cog, invoke_id, dict):
		obj = cls()
		obj.cog = cog
		author = cog.bot.get_user(dict['author'])
		if not author:
			raise GiftError(_('Could not find the author.'))
		obj.author = author
		obj.invoke_id = invoke_id
		obj.game_name = dict['game_name']
		obj.keys = dict['keys']
		obj.claimed = dict['claimed']
		obj.claimed_by_id = dict['claimed_by_id']
		obj.claimed_by_text = dict['claimed_by_text']
		obj.link_url = dict['link_url']
		obj.cover_url = dict['cover_url']
		obj.fields = dict['fields']
		messages = []
		for message_data in dict['messages']:
			g = cog.bot.get_guild(message_data[0])
			if not g:
				continue
			c = g.get_channel(message_data[1])
			if not c:
				continue
			try:
				m = await c.fetch_message(message_data[2])
			except discord.NotFound:
				continue
			messages.append(m)
		if not messages:
			raise GiftError(_('No messages could be found.'))
		obj.messages = messages
		return obj

	def to_dict(self):
		return self.invoke_id, {
			'author': self.author.id,
			'game_name': self.game_name,
			'keys': self.keys.copy(),
			'claimed': self.claimed.copy(),
			'claimed_by_id': self.claimed_by_id.copy(),
			'claimed_by_text': self.claimed_by_text.copy(),
			'link_url': self.link_url,
			'cover_url': self.cover_url,
			'fields': self.fields.copy(),
			'messages': [[message.guild.id, message.channel.id, message.id] for message in self.messages]
		}

	def gen_embed(self):
		total = len(self.keys) + len(self.claimed)
		if self.keys:
			desc = _(
				'Click the reaction below to grab a key.\n\n'
				'Currently available: **{top}/{bottom}**'
			).format(top=len(self.keys), bottom=total)
		else:
			desc = _('All keys have been claimed!')
		if self.claimed_by_text:
			desc += _('\n\nGrabbed by:')
			for text in self.claimed_by_text:
				desc += text
		embed = discord.Embed(
			title=_(
				'{author} is gifting {num} keys for **{game}**.'
			).format(author=self.author.display_name, num=total, game=self.game_name),
			description=desc,
			url = self.link_url or discord.Embed.Empty
		)
		for field in self.fields:
			embed.add_field(name=field[0], value=field[1], inline=False)
		if self.cover_url:
			embed.set_image(url=self.cover_url)
		return embed
	
	async def get_game_data(self):
		"""Get some data for a game from IGDB"""
		if hasattr(self.cog.bot, 'get_shared_api_tokens'): #3.2
			api = await self.cog.bot.get_shared_api_tokens('igdb')
			key = api.get('key')
		else: #3.1	
			api = await self.cog.bot.db.api_tokens.get_raw('igdb', default={'key': None})
			key = api['key']
		
		if not key:
			return
		
		async with aiohttp.ClientSession() as session:
			async with session.post(
				'https://api-v3.igdb.com/games',
				headers={'Accept': 'application/json', 'user-key': key},
				data=f'search "{self.game_name}"; fields cover,first_release_date,genres,rating,summary,url,websites; limit 1;'
			) as response:
				resp = await response.json(content_type=None)
			#The game could not be found
			if not resp:
				return
			game = resp[0]
			
			released = game.get('first_release_date', None)
			rating = game.get('rating', None)
			summary = game.get('summary', None)
			game_url = game.get('url', None)
			
			cover_id = game.get('cover', None)
			if game.get('genres', None):
				genre_ids = '(' + ','.join(str(g) for g in game['genres']) + ')'
			else:
				genre_ids = None
			if game.get('websites', None):
				website_ids = '(' + ','.join(str(w) for w in game['websites']) + ')'
			else:
				website_ids = None

			if cover_id:
				async with session.post(
					'https://api-v3.igdb.com/covers',
					headers={'Accept': 'application/json', 'user-key': key},
					data=f'where id = {cover_id}; fields url; limit 1;'
				) as response:
					resp = await response.json(content_type=None)
				if resp:
					cover_url = resp[0]['url'][2:].replace('t_thumb', 't_cover_big_2x')
					self.cover_url = 'https://' + cover_url
				
			if genre_ids:
				async with session.post(
					'https://api-v3.igdb.com/genres',
					headers={'Accept': 'application/json', 'user-key': key},
					data=f'where id = {genre_ids}; fields name;'
				) as response:
					resp = await response.json(content_type=None)
				genres = [g['name'] for g in resp]
			else:
				genres = None
			
			if website_ids:
				async with session.post(
					'https://api-v3.igdb.com/websites',
					headers={'Accept': 'application/json', 'user-key': key},
					data=f'where id = {website_ids} & category = 1; fields url; limit 1;'
				) as response:
					resp = await response.json(content_type=None)
				if not resp:
					website = None
				else:
					website = resp[0]['url']
			else:
				website = None
			
		game_info = ''
		if released:
			game_info += _('**Released:** {released}\n').format(released=date.fromtimestamp(released))
		if genres:
			game_info += _('**Genres:** {genres}\n').format(genres=", ".join(genres))
		if rating:
			game_info += _('**Rating:** {rating:.1f}').format(rating=rating)
		
		self.link_url = website or game_url
		if game_info:
			self.fields.append([_('Game info'), game_info])
		if summary:
			self.fields.append([_('Summary'), summary[:1000]])
	
	async def give_key(self, member):
		"""Give one of the keys to a particular user."""
		key = self.keys.pop(0)
		self.claimed_by_id.append(member.id)
		self.claimed_by_text.append(_(
			'\n**{name}** in **{guild}**'
		).format(name=member.display_name, guild=member.guild.name))
		self.claimed.append(key)
		await member.send(_('Here is your key for `{game}`: `{key}`').format(game=self.game_name, key=key))
		await self.refresh_messages()
		if len(self.keys) == 0:
			async with self.cog.config.gifts() as gifts:
				del gifts[self.invoke_id]
			self.cog.gifts.remove(self)
		else:
			async with self.cog.config.gifts() as gifts:
				gifts[self.invoke_id] = self.to_dict()[1]
		
	async def refresh_messages(self):
		"""Edits all existing messages to match the current state of the gift."""
		embed = self.gen_embed()
		await asyncio.gather(*(message.edit(embed=embed) for message in self.messages))


@cog_i18n(_)
class GiftAway(commands.Cog):
	"""Create grabbable key giveaways."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			gifts = {}
		)
		self.config.register_guild(
			giftChannel = None
		)
		self.gifts = []
		asyncio.create_task(self.setup())

	async def setup(self):
		to_del = []
		async with self.config.gifts() as data:
			for invoke_id in data:
				try:
					gift = await Gift.from_dict(self, invoke_id, data[invoke_id])
				except GiftError as e:
					to_del.append(invoke_id)
					continue
				self.gifts.append(gift)
			for invoke_id in to_del:
				del data[invoke_id]

	@commands.command(aliases=['ga'])
	async def giftaway(self, ctx, guild: GuildConvert, game_name, *keys):
		"""
		Giftaway a key to a specific server.
		
		Wrap any parameters that require spaces in quotes.
		"""
		try:
			await ctx.message.delete()
		except:
			pass
		cid = await self.config.guild(guild).giftChannel()
		if not cid:
			return await ctx.send(_('That guild has not set up a giftaway channel.'))
		channel = guild.get_channel(cid)
		if not channel:
			return await ctx.send(_('That giftaway channel for that guild does not exist.'))
		if not guild.me.permissions_in(channel).embed_links:
			return await ctx.send(_('I do not have permission to send embeds in the giftaway channel.'))
		try:
			gift = await Gift.create(self, ctx, [channel], game_name, list(keys))
		except GiftError as e:
			return await ctx.send(e)
		self.gifts.append(gift)
		key, value = gift.to_dict()
		async with self.config.gifts() as gifts:
			gifts[key] = value
		await ctx.tick()

	@commands.command(aliases=['gg'])
	async def globalgift(self, ctx, game_name, *keys):
		"""
		Giftaway a key to all servers.
		
		Wrap any parameters that require spaces in quotes.
		"""
		try:
			await ctx.message.delete()
		except:
			pass
		guilds = []
		for guild in self.bot.guilds:
			cid = await self.config.guild(guild).giftChannel()
			if not cid:
				continue
			channel = guild.get_channel(cid)
			if not channel:
				continue
			if not guild.me.permissions_in(channel).embed_links:
				continue
			guilds.append(channel)
		try:
			gift = await Gift.create(self, ctx, guilds, game_name, list(keys))
		except GiftError as e:
			return await ctx.send(e)
		self.gifts.append(gift)
		key, value = gift.to_dict()
		async with self.config.gifts() as gifts:
			gifts[key] = value
		await ctx.tick()
	
	@commands.guild_only()
	@commands.command()
	async def giftat(self, ctx, channel: discord.TextChannel, game_name, *keys):
		"""
		Giftaway a key to a specific channel.
		
		You probably should run this command from a location people can't see to protect the keys.
		Wrap any parameters that require spaces in quotes.
		"""
		try:
			await ctx.message.delete()
		except:
			pass
		if not ctx.guild.me.permissions_in(channel).embed_links:
			return await ctx.send(_('I do not have permission to send embeds in the giftaway channel.'))
		try:
			gift = await Gift.create(self, ctx, [channel], game_name, list(keys))
		except GiftError as e:
			return await ctx.send(e)
		self.gifts.append(gift)
		key, value = gift.to_dict()
		async with self.config.gifts() as gifts:
			gifts[key] = value
		await ctx.tick()
	
	@commands.guild_only()
	@commands.group()
	async def giftawayset(self, ctx):
		"""Group command for giftaway."""
		pass
		
	@giftawayset.group(invoke_without_command=True)
	async def channel(self, ctx, channel: discord.TextChannel=None):
		"""Set the channel that giftaway messages will be sent to in this server."""
		if channel is None:
			cid = await self.config.guild(ctx.guild).giftChannel()
			if cid is None:
				return await ctx.send(_('The giftaway channel has not been set up.'))
			channel = ctx.guild.get_channel(cid)
			if channel is None:
				await self.config.guild(ctx.guild).giftChannel.set(None)
				return await ctx.send(_('The giftaway channel has been deleted or could not be found.'))
			await ctx.send(_('The current giftaway channel is {channel}.').format(channel=channel.mention))
		else:
			await self.config.guild(ctx.guild).giftChannel.set(channel.id)
			await ctx.send(_('The giftaway channel is now {channel}.').format(channel=channel.mention))

	@channel.command()
	async def remove(self, ctx):
		"""Remove the giftaway channel from this server and stop receiving giftaway messages."""
		await self.config.guild(ctx.guild).giftChannel.set(None)
		await ctx.send(_('Removed.'))

	@commands.Cog.listener()
	async def on_reaction_add(self, reaction, user):
		if user.bot:
			return
		if str(reaction.emoji) != '\N{WHITE HEAVY CHECK MARK}':
			return 
		gift = None
		for g in self.gifts:
			if reaction.message.id in [x.id for x in g.messages]:
				gift = g
				break
		if not gift:
			return
		if not gift.keys:
			return
		if user.id in gift.claimed_by_id:
			return
		await gift.give_key(user)
