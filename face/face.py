import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import json
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS, close_menu


class Face(commands.Cog):
	"""Find and describe the faces in an image."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=7345167907)
		self.config.register_guild(
			doMakeMenu = True
		)
	
	@commands.guild_only()
	@checks.guildowner()
	@commands.group()
	async def faceset(self, ctx):
		"""Config options for face."""
		pass
	
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
		if hasattr(self.bot, 'get_shared_api_tokens'): #3.2
			api = await self.bot.get_shared_api_tokens('faceapi')
			api_key = api.get('key')
			api_url = api.get('url')
		else: #3.1	
			api = await self.bot.db.api_tokens.get_raw('faceapi', default={'key': None, 'url': None})
			api_key = api['key']
			api_url = api['url']
		
		if not api_key:
			return await ctx.send(
				'You need to set an API key!\n'
				'Follow this guide for instructions on how to get one:\n'
				'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>'
			)
		if not api_url:
			return await ctx.send(
				'You need to set an API URL!\n'
				'Follow this guide for instructions on how to get one:\n'
				'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>'
			)
		if (
			api_url.startswith('https://')
			and api_url.endswith('.api.cognitive.microsoft.com/face/v1.0')
		):
			api_url += '/detect'
		else:
			return await ctx.send(
				'The URL you set does not seem valid. '
				'Make sure you are following the guide at '
				'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>.'
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
				try:
					async with session.post(
							api_url,
							params=params,
							headers=headers,
							json={'url': face_url}
						) as response:
						faces = await response.json(content_type=None)
				except aiohttp.client_exceptions.ClientConnectorError:
					return await ctx.send(
						'The URL you set does not seem valid. '
						'Make sure you are following the guide at '
						'<https://github.com/Flame442/FlameCogs/blob/master/face/setup.md>.'
					)
				if 'error' in faces:
					return await ctx.send(f'API Error: {faces["error"]["message"]}')
				try:
					async with session.get(face_url) as response:
						r = await response.read()
					img = Image.open(BytesIO(r)).convert('RGBA')
				except Exception: #an image is not required to function
					img = None
		await ctx.send(f'Found {len(faces)} {"face" if len(faces) == 1 else "faces"}.')
		if len(faces) == 0:
			return
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
			)
			for emotion in face["faceAttributes"]["emotion"]:
				desc += (
					f'**{emotion.title()}:** '
					f'{round(face["faceAttributes"]["emotion"][emotion] * 100)}%\n'
				)
			desc += (
				'\n**Bald:** '
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
			if img:
				temp = BytesIO()
				temp.name = 'faces.png'
				img.save(temp)
				temp.seek(0)
				try:
					await ctx.send(file=discord.File(temp))
				except discord.errors.HTTPException:
					pass
			c = DEFAULT_CONTROLS if len(embedlist) > 1 else {"\N{CROSS MARK}": close_menu}
			await menu(ctx, embedlist, c)
