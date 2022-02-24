import discord
import aiohttp
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from PIL import Image, ImageEnhance
from random import randint
from io import BytesIO
import functools
import asyncio
import urllib
from typing import Union


MAX_SIZE = 8 * 1000 * 1000

class ImageFindError(Exception):
	"""Generic error for the _get_image function."""
	pass

class Deepfry(commands.Cog):
	"""Deepfries memes."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167900)
		self.config.register_guild(
			fryChance = 0,
			nukeChance = 0,
			allowAllTypes = False
		)
		self.imagetypes = ['png', 'jpg', 'jpeg']
		self.videotypes = ['gif', 'webp']
	
	@staticmethod
	def _fry(img):
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		e = ImageEnhance.Contrast(img)
		img = e.enhance(100)
		e = ImageEnhance.Brightness(img)
		img = e.enhance(.27)
		r, b, g = img.split()
		e = ImageEnhance.Brightness(r)
		r = e.enhance(4)
		e = ImageEnhance.Brightness(g)
		g = e.enhance(1.75)
		e = ImageEnhance.Brightness(b)
		b = e.enhance(.6)
		img = Image.merge('RGB', (r, g, b))
		e = ImageEnhance.Brightness(img)
		img = e.enhance(1.5)
		temp = BytesIO()
		temp.name = 'deepfried.png'
		img.save(temp)
		temp.seek(0)
		return temp
	
	@staticmethod
	def _videofry(img, duration):
		imgs = []
		frame = 0
		while img:
			i = img.copy()
			i = i.convert('RGB')
			e = ImageEnhance.Sharpness(i)
			i = e.enhance(100)
			e = ImageEnhance.Contrast(i)
			i = e.enhance(100)
			e = ImageEnhance.Brightness(i)
			i = e.enhance(.27)
			r, g, b = i.split()
			e = ImageEnhance.Brightness(r)
			r = e.enhance(4)
			e = ImageEnhance.Brightness(g)
			g = e.enhance(1.75)
			e = ImageEnhance.Brightness(b)
			b = e.enhance(.6)
			e = ImageEnhance.Contrast(b)
			i = Image.merge('RGB', (r, g, b))
			e = ImageEnhance.Brightness(i)
			i = e.enhance(1.5)
			imgs.append(i)
			frame += 1
			try:
				img.seek(frame)
			except EOFError:
				break
		temp = BytesIO()
		temp.name = 'deepfried.gif'
		if duration:
			imgs[0].save(temp, format='GIF', save_all=True, append_images=imgs[1:], loop=0, duration=duration)
		else:
			imgs[0].save(temp, format='GIF', save_all=True, append_images=imgs[1:], loop=0)
		temp.seek(0)
		return temp
	
	@staticmethod
	def _nuke(img):
		w, h = img.size[0], img.size[1]
		dx = ((w+200)//200)*2
		dy = ((h+200)//200)*2
		img = img.resize(((w+1)//dx,(h+1)//dy))
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		e = ImageEnhance.Contrast(img)
		img = e.enhance(100)
		e = ImageEnhance.Brightness(img)
		img = e.enhance(.27)
		r, b, g = img.split()
		e = ImageEnhance.Brightness(r)
		r = e.enhance(4)
		e = ImageEnhance.Brightness(g)
		g = e.enhance(1.75)
		e = ImageEnhance.Brightness(b)
		b = e.enhance(.6)
		img = Image.merge('RGB', (r, g, b))
		e = ImageEnhance.Brightness(img)
		img = e.enhance(1.5)
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		img = img.resize((w,h),Image.BILINEAR)
		temp = BytesIO()
		temp.name = 'nuke.jpg'
		img.save(temp, quality=1)
		temp.seek(0)
		return temp
	
	@staticmethod
	def _videonuke(img, duration):
		imgs = []
		frame = 0
		while img:
			i = img.copy()
			i = i.convert('RGB')
			w, h = i.size[0], i.size[1]
			dx = ((w+200)//200)*2
			dy = ((h+200)//200)*2
			i = i.resize(((w+1)//dx,(h+1)//dy))
			e = ImageEnhance.Sharpness(i)
			i = e.enhance(100)
			e = ImageEnhance.Contrast(i)
			i = e.enhance(100)
			e = ImageEnhance.Brightness(i)
			i = e.enhance(.27)
			r, g, b = i.split()
			e = ImageEnhance.Brightness(r)
			r = e.enhance(4)
			e = ImageEnhance.Brightness(g)
			g = e.enhance(1.75)
			e = ImageEnhance.Brightness(b)
			b = e.enhance(.6)
			i = Image.merge('RGB', (r, g, b))
			e = ImageEnhance.Brightness(i)
			i = e.enhance(1.5)
			e = ImageEnhance.Sharpness(i)
			i = e.enhance(100)
			i = i.resize((w,h),Image.BILINEAR)
			imgs.append(i)
			frame += 1
			try:
				img.seek(frame)
			except EOFError:
				break
		temp = BytesIO()
		temp.name = 'nuke.gif'
		if duration:
			imgs[0].save(temp, save_all=True, append_images=imgs[1:], loop=0, duration=duration)
		else:
			imgs[0].save(temp, save_all=True, append_images=imgs[1:], loop=0)
		temp.seek(0)
		return temp
	
	async def _get_image(self, ctx, link: Union[discord.Member, str]):
		"""Helper function to find an image."""
		if ctx.guild:
			allowAllTypes = await self.config.guild(ctx.message.guild).allowAllTypes()
			filesize_limit = ctx.guild.filesize_limit
		else:
			allowAllTypes = False
			filesize_limit = MAX_SIZE
		if not ctx.message.attachments and not link:
			async for msg in ctx.channel.history(limit=10):
				for a in msg.attachments:
					path = urllib.parse.urlparse(a.url).path
					if (
						any(path.lower().endswith(x) for x in self.imagetypes)
						or any(path.lower().endswith(x) for x in self.videotypes)
						or allowAllTypes
					):
						link = a.url
						break
				if link:
					break
			if not link:
				raise ImageFindError('Please provide an attachment.')
		if isinstance(link, discord.Member): #member avatar
			if discord.version_info.major == 1:
				avatar = link.avatar_url_as(static_format="png")
			else:
				avatar = link.display_avatar.with_static_format("png").url
			# dpy will add a ?size= flag to the end, so for this one case we only need to check gif in
			if ".gif" in str(avatar):
				isgif = True
			else:
				isgif = False
			data = await avatar.read()
			img = Image.open(BytesIO(data))
		elif link: #linked image
			path = urllib.parse.urlparse(link).path
			if any(path.lower().endswith(x) for x in self.imagetypes):
				isgif = False
			elif any(path.lower().endswith(x) for x in self.videotypes) or allowAllTypes:
				isgif = True
			else:
				raise ImageFindError(
					f'That does not look like an image of a supported filetype. Make sure you provide a direct link.'
				)
			async with aiohttp.ClientSession() as session:
				try:
					async with session.get(link) as response:
						r = await response.read()
						img = Image.open(BytesIO(r))
				except (OSError, aiohttp.ClientError):
					raise ImageFindError(
						'An image could not be found. Make sure you provide a direct link.'
					)
		else: #attached image
			path = urllib.parse.urlparse(ctx.message.attachments[0].url).path
			if any(path.lower().endswith(x) for x in self.imagetypes):
				isgif = False
			elif any(path.lower().endswith(x) for x in self.videotypes) or allowAllTypes:
				isgif = True
			else:
				raise ImageFindError(f'That does not look like an image of a supported filetype.')
			if ctx.message.attachments[0].size > filesize_limit:
				raise ImageFindError('That image is too large.')
			temp_orig = BytesIO()
			await ctx.message.attachments[0].save(temp_orig)
			temp_orig.seek(0)
			img = Image.open(temp_orig)
		if max(img.size) > 3840:
			raise ImageFindError('That image is too large.')
		duration = None
		if isgif and 'duration' in img.info:
			duration = img.info['duration']
		else:
			img = img.convert('RGB')
		return img, isgif, duration
	
	@commands.command(aliases=['df'])
	@commands.bot_has_permissions(attach_files=True)
	async def deepfry(self, ctx, link: Union[discord.Member, str]=None):
		"""
		Deepfries images.
		
		The optional parameter "link" can be either a member or a **direct link** to an image.
		"""
		async with ctx.typing():
			try:
				img, isgif, duration = await self._get_image(ctx, link)
			except ImageFindError as e:	
				return await ctx.send(e)
			if isgif:
				task = functools.partial(self._videofry, img, duration)
			else:
				task = functools.partial(self._fry, img)
			task = self.bot.loop.run_in_executor(None, task)
			try:
				image = await asyncio.wait_for(task, timeout=60)
			except asyncio.TimeoutError:
				return await ctx.send('The image took too long to process.')
			try:
				await ctx.send(file=discord.File(image))
			except discord.errors.HTTPException:
				return await ctx.send('That image is too large.')

	@commands.command()
	@commands.bot_has_permissions(attach_files=True)
	async def nuke(self, ctx, link: Union[discord.Member, str]=None):
		"""
		Demolishes images.
		
		The optional parameter "link" can be either a member or a **direct link** to an image.
		"""
		async with ctx.typing():
			try:
				img, isgif, duration = await self._get_image(ctx, link)
			except ImageFindError as e:	
				return await ctx.send(e)
			if isgif:
				task = functools.partial(self._videonuke, img, duration)
			else:
				task = functools.partial(self._nuke, img)
			task = self.bot.loop.run_in_executor(None, task)
			try:
				image = await asyncio.wait_for(task, timeout=60)
			except asyncio.TimeoutError:
				return await ctx.send('The image took too long to process.')
			try:
				await ctx.send(file=discord.File(image))
			except discord.errors.HTTPException:
				return await ctx.send('That image is too large.')
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group(invoke_without_command=True)
	async def deepfryset(self, ctx):
		"""Config options for deepfry."""
		await ctx.send_help()
		cfg = await self.config.guild(ctx.guild).all()
		msg = (
			'Allow all filetypes: {allowAllTypes}\n'
			'Deepfry chance: {fryChance}\n'
			'Nuke chance: {nukeChance}'
		).format_map(cfg)
		await ctx.send(f'```py\n{msg}```')
	
	@deepfryset.command()	
	async def frychance(self, ctx, value: int=None):
		"""
		Change the rate images are automatically deepfried.
		
		Images will have a 1/<value> chance to be deepfried.
		Higher values cause less often fries.
		Set to 0 to disable.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.message.guild).fryChance()
			if v == 0:
				await ctx.send('Autofrying is currently disabled.')
			elif v == 1:
				await ctx.send('All images are being fried.')
			else:
				await ctx.send(f'1 out of every {str(v)} images are being fried.')
		else:
			if value < 0:
				return await ctx.send('Value cannot be less than 0.')
			await self.config.guild(ctx.guild).fryChance.set(value)
			if value == 0:
				await ctx.send('Autofrying is now disabled.')
			elif value == 1:
				await ctx.send('All images will be fried.')
			else:
				await ctx.send(f'1 out of every {str(value)} images will be fried.')

	@deepfryset.command()	
	async def nukechance(self, ctx, value: int=None):
		"""
		Change the rate images are automatically nuked.
		
		Images will have a 1/<value> chance to be nuked.
		Higher values cause less often nukes.
		Set to 0 to disable.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.message.guild).nukeChance()
			if v == 0:
				await ctx.send('Autonuking is currently disabled.')
			elif v == 1:
				await ctx.send('All images are being nuked.')
			else:
				await ctx.send(f'1 out of every {str(v)} images are being nuked.')
		else:
			if value < 0:
				return await ctx.send('Value cannot be less than 0.')
			await self.config.guild(ctx.guild).nukeChance.set(value)
			if value == 0:
				await ctx.send('Autonuking is now disabled.')
			elif value == 1:
				await ctx.send('All images will be nuked.')
			else:
				await ctx.send(f'1 out of every {str(value)} images will be nuked.')

	@deepfryset.command()	
	async def allowalltypes(self, ctx, value: bool=None):
		"""
		Allow filetypes that have not been verified to be valid.
		
		Can cause errors if enabled, use at your own risk.
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).allowAllTypes()
			if v:
				await ctx.send('You are currently able to use unverified types.')
			else:
				await ctx.send('You are currently not able to use unverified types.')
		else:
			await self.config.guild(ctx.guild).allowAllTypes.set(value)
			if value:
				await ctx.send(
					'You will now be able to use unverified types.\n'
					'This mode can cause errors. Use at your own risk.'
				)
			else:
				await ctx.send('You will no longer be able to use unverified types.')

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return

	@commands.Cog.listener()
	async def on_message(self, msg):
		"""Passively deepfries random images."""
		#CHECKS
		if msg.author.bot:
			return
		if not msg.attachments:
			return
		if msg.guild is None:
			return
		if await self.bot.cog_disabled_in_guild(self, msg.guild):
			return
		if not msg.channel.permissions_for(msg.guild.me).attach_files:
			return
		if any([msg.content.startswith(x) for x in await self.bot.get_prefix(msg)]):
			return
		if msg.attachments[0].size > msg.guild.filesize_limit:
			return
		ext = msg.attachments[0].url.split('.')[-1].lower()
		if ext in self.imagetypes:
			isgif = False
		elif ext in self.videotypes:
			isgif = True
		else:
			return
		#GUILD SETTINGS
		vfry = await self.config.guild(msg.guild).fryChance()
		vnuke = await self.config.guild(msg.guild).nukeChance()
		#NUKE
		if vnuke != 0:
			l = randint(1,vnuke)
			if l == 1:
				temp = BytesIO()
				temp.filename = f'nuked.{ext}'
				await msg.attachments[0].save(temp)
				temp.seek(0)
				img = Image.open(temp)
				duration = None
				if isgif:
					if 'duration' in img.info:
						duration = img.info['duration']
					task = functools.partial(self._videonuke, img, duration)
				else:
					img = img.convert('RGB')
					task = functools.partial(self._nuke, img)
				task = self.bot.loop.run_in_executor(None, task)
				try:
					image = await asyncio.wait_for(task, timeout=60)
				except asyncio.TimeoutError:
					return
				await msg.channel.send(file=discord.File(image))
				return #prevent a nuke and a fry
		#FRY
		if vfry != 0:
			l = randint(1,vfry)
			if l == 1:
				temp = BytesIO()
				temp.filename = f'deepfried.{ext}'
				await msg.attachments[0].save(temp)
				temp.seek(0)
				img = Image.open(temp)
				duration = None
				if isgif:
					if 'duration' in img.info:
						duration = img.info['duration']
					task = functools.partial(self._videofry, img, duration)
				else:
					img = img.convert('RGB')
					task = functools.partial(self._fry, img)
				task = self.bot.loop.run_in_executor(None, task)
				try:
					image = await asyncio.wait_for(task, timeout=60)
				except asyncio.TimeoutError:
					return
				await msg.channel.send(file=discord.File(image))
