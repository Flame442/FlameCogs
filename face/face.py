import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import json
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class Face(commands.Cog):
	"""Find and describe the faces in an image."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167907)
		self.config.register_global(
			api_key = None,
			api_url = None,
		)
		self.config.register_guild(
			doMakeMenu = True
		)
	
	@checks.guildowner()
	@commands.group()
	async def faceset(self, ctx):
		"""Config options for face."""
		pass
	
	@checks.is_owner()
	@faceset.command()
	async def key(self, ctx, key: str):
		"""
		Set the API key for face.
		
		Please follow the guide at https://github.com/Flame442/FlameCogs/blob/master/face/setup.md for instructions.
		"""
		await self.config.api_key.set(key)
		await ctx.send('API key set!')
		try:
			await ctx.message.delete()
		except discord.Forbidden:
			await ctx.send(
				'The command message could not be deleted.'
				'It is highly recomended you remove it to protect your key.'
			)
	
	@checks.is_owner()
	@faceset.command()
	async def url(self, ctx, url: str):
		"""
		Set the API url for face.
		
		Please follow the guide at https://github.com/Flame442/FlameCogs/blob/master/face/setup.md for instructions.
		"""
		if url.startswith('https://') and url.endswith('.api.cognitive.microsoft.com/face/v1.0'):
			await self.config.api_url.set(url + '/detect')
			await ctx.send('API URL set!')
		else:
			await ctx.send(
				'That doesn\'t look like a valid url. '
				'Make sure you are following the guide at '
				'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>.'
			)
	
	@commands.guild_only()
	@faceset.command()
	async def menu(self, ctx, value: bool=None):
		"""
		Set if results should be made into a menu.
		
		If in a menu, one large image with faces marked will be sent instead of cropped images of each face.
		Defaults to True.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doMakeMenu()
			if v:
				await ctx.send('Results are being displayed in a menu.')
			else:
				await ctx.send('Results are being displayed in multiple messages.')
		else:
			await self.config.guild(ctx.guild).doMakeMenu.set(value)
			if value:
				await ctx.send('Results will now be displayed in a menu.')
			else:
				await ctx.send('Results will now be displayed in multiple messages.')

	@commands.bot_has_permissions(embed_links=True)
	@commands.command()
	async def face(self, ctx, face_url: str=None):
		"""Find and describe the faces in an image."""
		api_key = await self.config.api_key()
		if not api_key:
			return await ctx.send(
				'You need to set an API key!\n'
				'Follow this guide for instructions on how to get one:\n'
				'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>'
			)
		api_url = await self.config.api_url()
		if not api_url:
			return await ctx.send(
				'You need to set an API URL!\n'
				'Follow this guide for instructions on how to get one:\n'
				'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>'
			)
		if not ctx.message.attachments and not face_url:
			async for msg in ctx.channel.history(limit=10):
				for a in msg.attachments:
					if a.url.split('.')[-1].lower() in ['png', 'jpg', 'jpeg']:
						face_url = a.url
						break
				if face_url:
					break
		elif not face_url and ctx.message.attachments:
			for a in ctx.message.attachments:
				if a.url.split('.')[-1].lower() in ['png', 'jpg', 'jpeg']:
					face_url = a.url
					break
		if not face_url:
			return await ctx.send('You need to supply an image.')
		headers = {'Ocp-Apim-Subscription-Key': api_key} 
		params = {
			'returnFaceId': 'false',
			'returnFaceLandmarks': 'false',
			'returnFaceAttributes': (
				'age,gender,smile,glasses,emotion,hair,makeup'
			)
		}
		async with ctx.typing():
			async with aiohttp.ClientSession() as session:
				async with session.post(
						api_url,
						params=params,
						headers=headers,
						json={'url': face_url}
					) as response:
					faces = await response.json(content_type=None)
				if 'error' in faces:
					return await ctx.send(f'API Error: {faces["error"]["message"]}')
				try:
					async with session.get(face_url) as response:
						r = await response.read()
					img = Image.open(BytesIO(r)).convert('RGBA')
				except Exception: #an image is not required to function
					img = None
		await ctx.send(f'Found {len(faces)} {"face" if len(faces) == 1 else "faces"}.')
		if ctx.guild:
			doMakeMenu = await self.config.guild(ctx.guild).doMakeMenu()
		else:
			doMakeMenu = True
		faceNumber = 0
		embedlist = []
		glassesformat = {
			'NoGlasses': 'No Glasses',
			'ReadingGlasses': 'Reading Glasses',
			'Sunglasses': 'Sunglasses',
			'SwimmingGoggles': 'Swimming Goggles'
		}
		if img:
			draw = ImageDraw.Draw(img)
		for face in faces:
			faceNumber += 1
			desc = (
				f'*{round(face["faceAttributes"]["age"])} year old '
				f'{face["faceAttributes"]["gender"]}*\n\n'
				'**Eye Makeup:** '
				f'{"Yes" if face["faceAttributes"]["makeup"]["eyeMakeup"] else "No"}\n'
				'**Lip Makeup:** '
				f'{"Yes" if face["faceAttributes"]["makeup"]["lipMakeup"] else "No"}\n'
				'**Glasses:** '
				f'{glassesformat[face["faceAttributes"]["glasses"]]}\n'
				'**Smile:** '
				f'{round(face["faceAttributes"]["smile"] * 100)}%\n'
				'\n'
				'**Anger:** '
				f'{round(face["faceAttributes"]["emotion"]["anger"] * 100)}%\n'
				'**Contempt:** '
				f'{round(face["faceAttributes"]["emotion"]["contempt"] * 100)}%\n'
				'**Disgust:** '
				f'{round(face["faceAttributes"]["emotion"]["disgust"] * 100)}%\n'
				'**Fear:** '
				f'{round(face["faceAttributes"]["emotion"]["fear"] * 100)}%\n'
				'**Happiness:** '
				f'{round(face["faceAttributes"]["emotion"]["happiness"] * 100)}%\n'
				'**Neutral:** '
				f'{round(face["faceAttributes"]["emotion"]["neutral"] * 100)}%\n'
				'**Sadness:** '
				f'{round(face["faceAttributes"]["emotion"]["sadness"] * 100)}%\n'
				'**Surprise:** '
				f'{round(face["faceAttributes"]["emotion"]["surprise"] * 100)}%\n'
				'\n'
				'**Bald:** '
				f'{round(face["faceAttributes"]["hair"]["bald"] * 100)}%'
			)
			if face['faceAttributes']['hair']['hairColor'] != []:
				order = sorted(
					face['faceAttributes']['hair']['hairColor'],
					key=lambda c: c['color']
				)
				for hair in order:
					desc += (
						f'\n**{hair["color"].title()}:** {round(hair["confidence"] * 100)}%'
					)
			embed = discord.Embed(
				title=f'**Face {faceNumber}**',
				description=desc,
				color=await ctx.embed_color()
			)
			if doMakeMenu:
				if img:
					draw.rectangle(
						(
							face['faceRectangle']['left'],
							face['faceRectangle']['top'],
							face['faceRectangle']['left']+face['faceRectangle']['width'],
							face['faceRectangle']['top']+face['faceRectangle']['height']
						),
						outline='red'
					)
					draw.text(
						(face['faceRectangle']['left'], face['faceRectangle']['top']),
						str(faceNumber)
					)
				embedlist.append(embed)
			else:
				file = None
				if img:
					faceimg = img.crop((
						face['faceRectangle']['left'],
						face['faceRectangle']['top'],
						face['faceRectangle']['left']+face['faceRectangle']['width'],
						face['faceRectangle']['top']+face['faceRectangle']['height']
					))
					temp = BytesIO()
					temp.name = 'face.png'
					faceimg.save(temp)
					temp.seek(0)
					file = discord.File(temp, 'face.png')
					embed.set_thumbnail(url='attachment://face.png')
				try:
					await ctx.send(embed=embed, file=file)
				except discord.errors.HTTPException:
					await ctx.send(embed=embed)
		if doMakeMenu:
			temp = BytesIO()
			temp.name = 'faces.png'
			img.save(temp)
			temp.seek(0)
			try:
				await ctx.send(file=discord.File(temp))
			except discord.errors.HTTPException:
				pass
			await menu(ctx, embedlist, DEFAULT_CONTROLS)
