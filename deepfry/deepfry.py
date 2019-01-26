import discord
import aiohttp
from redbot.core.data_manager import cog_data_path
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from PIL import Image, ImageEnhance
from random import randint
from io import BytesIO
import functools
import asyncio

MAX_SIZE = 8 * 1000 * 1000


class Deepfry(commands.Cog):
	"""Deepfries memes."""

	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167900)
		self.config.register_guild(
			chance = 0
		)
		self.imagetypes = ['png', 'jpg', 'jpeg']
		self.videotypes = ['gif']
	
	def _fry(self, img):
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		e = ImageEnhance.Contrast(img)
		img = e.enhance(100)
		e = ImageEnhance.Brightness(img)
		img = e.enhance(.27)
		try:
			r, g, b, a = img.split()
		except:
			r, g, b = img.split()
		e = ImageEnhance.Brightness(r)
		r = e.enhance(4)
		e = ImageEnhance.Brightness(g)
		g = e.enhance(1.75)
		e = ImageEnhance.Brightness(b)
		b = e.enhance(.6)
		img = Image.merge("RGB", (r, g, b))
		e = ImageEnhance.Brightness(img)
		img = e.enhance(1.5)
		temp = BytesIO()
		temp.name = "deepfried.png"
		img.save(temp)
		temp.seek(0)
		return temp
	
	def _videofry(self, img):
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
			i = Image.merge("RGB", (r, g, b))
			e = ImageEnhance.Brightness(i)
			i = e.enhance(1.5)
			imgs.append(i)
			frame += 1
			try:
				img.seek(frame)
			except EOFError:
				break
		temp = BytesIO()
		temp.name = "deepfried.gif"
		imgs[0].save(temp, format="GIF", save_all=True, append_images=imgs, loop=0)
		temp.seek(0)
		return temp
		
	def _nuke(self, img):
		w, h = img.size[0], img.size[1]
		dx = ((w+200)//200)*2
		dy = ((h+200)//200)*2
		img = img.resize((w//dx,h//dy))
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		e = ImageEnhance.Contrast(img)
		img = e.enhance(100)
		e = ImageEnhance.Brightness(img)
		img = e.enhance(.27)
		try:
			r, g, b, a = img.split()
		except:
			r, g, b = img.split()
		e = ImageEnhance.Brightness(r)
		r = e.enhance(4)
		e = ImageEnhance.Brightness(g)
		g = e.enhance(1.75)
		e = ImageEnhance.Brightness(b)
		b = e.enhance(.6)
		img = Image.merge("RGB", (r, g, b))
		e = ImageEnhance.Brightness(img)
		img = e.enhance(1.5)
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		img = img.resize((w,h),Image.BILINEAR)
		temp = BytesIO()
		temp.name = "nuke.jpg"
		img.save(temp, quality=1)
		temp.seek(0)
		return temp
		
	def _videonuke(self, img):
		imgs = []
		frame = 0
		while img:
			i = img.copy()
			i = i.convert('RGB')
			w, h = i.size[0], i.size[1]
			dx = ((w+200)//200)*2
			dy = ((h+200)//200)*2
			i = i.resize((w//dx,h//dy))
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
			i = Image.merge("RGB", (r, g, b))
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
		temp.name = "nuke.gif"
		imgs[0].save(temp, save_all=True, append_images=imgs[1:], loop=0)
		temp.seek(0)
		return temp
			
	@commands.command(aliases=['df'])
	@commands.bot_has_permissions(attach_files=True)
	async def deepfry(self, ctx):
		"""Deepfries images."""
		if ctx.message.attachments == []:
			return await ctx.send('Please provide an attachment.')
		if ctx.message.attachments[0].url.split(".")[-1] in self.imagetypes:
			isgif = False
		elif ctx.message.attachments[0].url.split(".")[-1] in self.videotypes:
			isgif = True
		else:
			ext = ctx.message.attachments[0].url.split(".")[-1].title()
			return await ctx.send('"{}" is not a supported filetype.'.format(ext))
		if ctx.message.attachments[0].size > MAX_SIZE:
			return await ctx.send('That image is too large. Max image size is 8MB.')
		temp_orig = BytesIO()
		r = await ctx.message.attachments[0].save(temp_orig)
		temp_orig.seek(0)
		img = Image.open(temp_orig)
		if isgif:
			task = functools.partial(self._videofry, img)
			task = self.bot.loop.run_in_executor(None, task)
			try:
				image = await asyncio.wait_for(task, timeout=60)
			except asyncio.TimeoutError:
				return
			
			try:
				await ctx.send(file=discord.File(image))
			except discord.errors.HTTPException:
				return await ctx.send('That image is too large.')
		else:
			task = functools.partial(self._fry, img)
			task = self.bot.loop.run_in_executor(None, task)
			try:
				image = await asyncio.wait_for(task, timeout=60)
			except asyncio.TimeoutError:
				return
			await ctx.send(file=discord.File(image))
		
	@commands.command()
	@commands.bot_has_permissions(attach_files=True)
	async def nuke(self, ctx):
		"""Demolishes images."""
		if ctx.message.attachments == []:
			return await ctx.send('Please provide an attachment.')
		if ctx.message.attachments[0].url.split(".")[-1] in self.imagetypes:
			isgif = False
		elif ctx.message.attachments[0].url.split(".")[-1] in self.videotypes:
			isgif = True
		else:
			ext = ctx.message.attachments[0].url.split(".")[-1].title()
			return await ctx.send('"{}" is not a supported filetype.'.format(ext))
		if ctx.message.attachments[0].size > MAX_SIZE:
			return await ctx.send('That image is too large. Max image size is 8MB.')
		temp_orig = BytesIO()
		r = await ctx.message.attachments[0].save(temp_orig)
		temp_orig.seek(0)
		img = Image.open(temp_orig)
		if isgif:
			task = functools.partial(self._videonuke, img)
			task = self.bot.loop.run_in_executor(None, task)
			try:
				image = await asyncio.wait_for(task, timeout=60)
			except asyncio.TimeoutError:
				return
			try:
				await ctx.send(file=discord.File(image))
			except discord.errors.HTTPException:
				return await ctx.send('That image is too large.')
		else:
			task = functools.partial(self._nuke, img)
			task = self.bot.loop.run_in_executor(None, task)
			try:
				image = await asyncio.wait_for(task, timeout=60)
			except asyncio.TimeoutError:
				return
			await ctx.send(file=discord.File(image))
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.command()
	async def deepfryset(self, ctx, value: int=None):
		"""
		Change the rate images are automatically deepfried.
		Images will have a 1/<value> chance to be deepfried.
		Higher values cause less often fries.
		Set to 0 to disable.
		This value is server specific.
		"""
		if value == None:
			v = await self.config.guild(ctx.message.guild).chance()
			if v == 0:
				await ctx.send('Autofrying is currently disabled.')
			elif v == 1:
				await ctx.send('All images are being fried.')
			else:
				await ctx.send('1 out of every '+str(v)+' images are being fried.')
		else:
			await self.config.guild(ctx.guild).chance.set(value)
			if value == 0:
				await ctx.send('Autofrying is now disabled.')
			elif value == 1:
				await ctx.send('All images will be fried.')
			else:
				await ctx.send('1 out of every '+str(value)+' images will be fried.')
		
	async def run(self, t):
		"""Passively deepfries random images."""
		if t.author.bot:
			return
		if not t.attachments:
			return
		if t.guild is None:
			return
		v = await self.config.guild(t.guild).chance()
		if t.attachments[0].url.split(".")[-1] not in self.imagetypes:
			return
		if t.attachments[0].size > MAX_SIZE:
			return
		if v == 0:
			return
		if not any([t.content.startswith(x) for x in await self.bot.get_prefix(t)]):
			l = randint(1,v)
			if l == 1:
				ext = t.attachments[0].url.split(".")[-1]
				temp = BytesIO()
				temp.filename = f"deepfried.{ext}"
				r = await t.attachments[0].save(temp)
				temp.seek(0)
				img = Image.open(temp)
				task = fuctools.partial(self._fry, img)
				task = self.bot.loop.run_in_executor(None, task)
				try:
					image = await asyncio.wait_for(task, timeout=60)
				except asyncio.TimeoutError:
					return
				await t.channel.send(file=discord.File(image))
			else:
				pass
