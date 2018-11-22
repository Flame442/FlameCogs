import discord
import aiohttp
from redbot.core import commands
from PIL import Image, ImageEnhance
from random import randint
from io import BytesIO
from redbot.core.data_manager import cog_data_path
from redbot.core import Config


class Deepfry(commands.Cog):
	"""Deepfries memes."""
	def __init__(self, bot):
		self.bot = bot
		self.f = 0
		self.config = Config.get_conf(self, identifier=7345167900)
		self.config.register_guild(
			chance = 0
		)
		
	@commands.command(aliases=['df'])
	async def deepfry(self, ctx, amount: float=0):
		"""Deepfries images."""
		if ctx.message.attachments == []:
			return await ctx.send('Please provide an attachment.')
		if ctx.message.attachments[0].url[::-1].split(".")[0][::-1] not in ['png', 'jpg']:
			return await ctx.send('"'+ctx.message.attachments[0].url[::-1].split(".")[0][::-1].title()+'" is not a supported filetype.')
		async with aiohttp.ClientSession() as session:
			async with session.get(ctx.message.attachments[0].url) as response:
				r = await response.read()
				img = Image.open(BytesIO(r))
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
		e = ImageEnhance.Contrast(b)
		img = e.enhance(2)
		img = Image.merge("RGB", (r, g, b))
		e = ImageEnhance.Brightness(img)
		img = e.enhance(1.5)
		e = ImageEnhance.Sharpness(img)
		img = e.enhance((amount*99)+1)	
		img.save(str(cog_data_path(self))+'\\temp.jpg')
		await ctx.send(file=discord.File(str(cog_data_path(self))+'\\temp.jpg'))
		
	@commands.command()
	async def nuke(self, ctx):
		"""Demolishes images."""
		if ctx.message.attachments == []:
			return await ctx.send('Please provide an attachment.')
		if ctx.message.attachments[0].url[::-1].split(".")[0][::-1] not in ['png', 'jpg']:
			return await ctx.send('"'+ctx.message.attachments[0].url[::-1].split(".")[0][::-1].title()+'" is not a supported filetype.')
		async with aiohttp.ClientSession() as session:
			async with session.get(ctx.message.attachments[0].url) as response:
				r = await response.read()
				img = Image.open(BytesIO(r))
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
		e = ImageEnhance.Contrast(b)
		img = e.enhance(2)
		img = Image.merge("RGB", (r, g, b))
		e = ImageEnhance.Brightness(img)
		img = e.enhance(1.5)
		e = ImageEnhance.Sharpness(img)
		img = e.enhance(100)
		img = img.resize((w,h),Image.BILINEAR)
		img.save(str(cog_data_path(self))+'\\temp.jpg', quality=1)
		await ctx.send(file=discord.File(str(cog_data_path(self))+'\\temp.jpg'))
	
	@commands.command()
	async def deepfryset(self, ctx, value: int=None):
		"""
		Change the rate images are automatically deepfried.
		Images will have a 1/<value> chance to be deepfried.
		Higher values cause less often fries.
		Set to 0 to disable.
		This value is server based.
		"""
		if value == None:
			v = await self.config.guild(ctx.message.guild).chance()
			if v == 0:
				await ctx.send('Autofrying is currently disabled.')
			else:
				await ctx.send('1 out of every '+str(v)+' images are being fried.')
		else:
			await self.config.guild(ctx.guild).chance.set(value)
			if value == 0:
				await ctx.send('Autofrying is now disabled.')
			else:
				await ctx.send('1 out of every '+str(value)+' images will be fried.')
		
	async def run(self, t):
		"""Passively deepfries random images."""
		if t.author.id != self.bot.user.id:
			v = await self.config.guild(t.guild).chance()
			if t.attachments != [] and t.attachments[0].url[::-1].split(".")[0][::-1] in ['png', 'jpg'] and t.content.find('!deepfry') == -1 and t.content.find('!nuke') == -1 and v != 0:
				l = randint(1,v)
				if l == 1:
					async with aiohttp.ClientSession() as session:
						async with session.get(t.attachments[0].url) as response:
							r = await response.read()
							img = Image.open(BytesIO(r))
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
					e = ImageEnhance.Contrast(b)
					img = e.enhance(2)
					img = Image.merge("RGB", (r, g, b))
					e = ImageEnhance.Brightness(img)
					img = e.enhance(1.5)
					e = ImageEnhance.Sharpness(img)
					img = e.enhance((self.f*99)+1)
					img.save(str(cog_data_path(self))+'\\temp.jpg', quality=10)
					await t.channel.send(file=discord.File(str(cog_data_path(self))+'\\temp.jpg'))
					self.f = 0
				else:
					self.f += 0.07
