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
	
	@commands.group()
	@checks.guildowner()
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
	
	@checks.guildowner()
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
		headers = {'Ocp-Apim-Subscription-Key': api_key} 
		params = {
			'returnFaceId': 'false',
			'returnFaceLandmarks': 'false',
			'returnFaceAttributes': (
				'age,gender,headPose,smile,facialHair,glasses,emotion,'
				'hair,makeup,occlusion,accessories,blur,exposure,noise'
			)
		}
		img = None
		if not ctx.message.attachments and not face_url:
			async for msg in ctx.channel.history(limit=10):
				for a in msg.attachments:
					if a.url.split('.')[-1].lower() in ['png', 'jpg', 'jpeg']:
						face_url = a.url
						break
				if face_url:
					break
			if not face_url:
				return await ctx.send('You need to supply an image.')
		if not face_url:
			try:
				face_url = ctx.message.attachments[0].url
				temp_orig = BytesIO()
				r = await ctx.message.attachments[0].save(temp_orig)
				temp_orig.seek(0)
				img = Image.open(temp_orig).convert('RGBA')
			except Exception: #ANY failure to find an image needs to cancel
				return await ctx.send('You need to supply an image.')
		async with ctx.typing():
			async with aiohttp.ClientSession() as session:
				async with session.post(
						api_url,
						params=params,
						headers=headers,
						json={'url': face_url}
					) as response:
					faces = await response.json(content_type=None)
				if not img:
					try:
						async with session.get(face_url) as response:
							r = await response.read()
							img = Image.open(BytesIO(r)).convert('RGBA')
					except Exception: #ANY failure to find an image can pass silently
						img = None
			try:
				return await ctx.send(f'API Error: {faces["error"]["message"]}')
			except TypeError:
				pass
		await ctx.send(f'Found {len(faces)} {"face" if len(faces) == 1 else "faces"}.\n\n')
		if ctx.guild:
			doMakeMenu = await self.config.guild(ctx.guild).doMakeMenu()
		else:
			doMakeMenu = True
		faceNumber = 0
		embedlist = []
		if img:
			draw = ImageDraw.Draw(img)
		for face in faces:
			faceNumber += 1
			faceRectangle = face['faceRectangle'] #dict of top, left, width, height
			faceAttributes = face['faceAttributes'] #dict of all other attributes
			smile = faceAttributes['smile'] #float, 0-1. intensity of smile
			gender = faceAttributes['gender'] #male or female
			age = faceAttributes['age'] #estimated age
			facialHair = faceAttributes['facialHair'] #dict of moustache, beard, sideburns, estimated thickness of facial hair
			glasses = faceAttributes['glasses'] #one of NoGlasses, ReadingGlasses, Sunglasses, SwimmingGoggles
			emotion = faceAttributes['emotion'] #dict of anger, contempt, disgust, fear, happiness, neutral, saddness, surprise, intensity of each emotion
			makeup = faceAttributes['makeup'] #dict of eyeMakeup, lipMakeup, value is bool
			hair = faceAttributes['hair'] #dict of bald, float of probability of bald, plus inside dicts for color chances
			hairColor = {}
			for color in hair['hairColor']:
				hairColor[color['color']] = color['confidence']
			embed = discord.Embed(
				title=f'**Face {faceNumber}**',
				description=f'{round(age)} year old {gender}',
				color=await ctx.embed_color()
				)
			if doMakeMenu and img:
				draw.rectangle(
					(
						faceRectangle['left'],
						faceRectangle['top'],
						faceRectangle['left']+faceRectangle['width'],
						faceRectangle['top']+faceRectangle['height']
					),
					outline='red'
				)
				draw.text((faceRectangle['left'], faceRectangle['top']), str(faceNumber))
			else:
				if img:
					faceimg = img.crop((
						faceRectangle['left'],
						faceRectangle['top'],
						faceRectangle['left']+faceRectangle['width'],
						faceRectangle['top']+faceRectangle['height']
					))
					temp = BytesIO()
					temp.name = 'face.png'
					faceimg.save(temp)
					temp.seek(0)
					file = discord.File(temp, 'face.png')
					embed.set_image(url='attachment://face.png')
				else:
					file = None
			glassesformat = {
				'NoGlasses': 'No Glasses',
				'ReadingGlasses': 'Reading Glasses',
				'Sunglasses': 'Sunglasses',
				'SwimmingGoggles': 'Swimming Goggles'
			}
			embed.add_field(name='Eye Makeup', value=f'{"Yes" if makeup["eyeMakeup"] else "No"}')
			embed.add_field(name='Lip Makeup', value=f'{"Yes" if makeup["lipMakeup"] else "No"}')
			embed.add_field(name='Glasses', value=f'{glassesformat[glasses]}')
			embed.add_field(name='Anger', value=f'{round(emotion["anger"] * 100)}%')
			embed.add_field(name='Contempt', value=f'{round(emotion["contempt"] * 100)}%')
			embed.add_field(name='Disgust', value=f'{round(emotion["disgust"] * 100)}%')
			embed.add_field(name='Fear', value=f'{round(emotion["fear"] * 100)}%')
			embed.add_field(name='Happiness', value=f'{round(emotion["happiness"] * 100)}%')
			embed.add_field(name='Neutral', value=f'{round(emotion["neutral"] * 100)}%')
			embed.add_field(name='Sadness', value=f'{round(emotion["sadness"] * 100)}%')
			embed.add_field(name='Surprise', value=f'{round(emotion["surprise"] * 100)}%')
			embed.add_field(name='Smile', value=f'{round(smile * 100)}%')
			embed.add_field(name='Bald', value=f'{round(hair["bald"] * 100)}%')
			if hairColor == {}:
				pass
			else:
				embed.add_field(name='Brown', value=f'{round(hairColor["brown"] * 100)}%')
				embed.add_field(name='Black', value=f'{round(hairColor["black"] * 100)}%')
				embed.add_field(name='Blond', value=f'{round(hairColor["blond"] * 100)}%')
				embed.add_field(name='Gray', value=f'{round(hairColor["gray"] * 100)}%')
				embed.add_field(name='Red', value=f'{round(hairColor["red"] * 100)}%')
				embed.add_field(name='Other', value=f'{round(hairColor["other"] * 100)}%')
			if not doMakeMenu:
				if file:
					try:
						await ctx.send(embed=embed, files=[file])
					except discord.errors.HTTPException:
						await ctx.send(embed=embed)
				else:
					await ctx.send(embed=embed)
			else:
				embedlist.append(embed)
		if embedlist != []:
			temp = BytesIO()
			temp.name = 'faces.png'
			img.save(temp)
			temp.seek(0)
			try:
				await ctx.send(file=discord.File(temp))
			except discord.errors.HTTPException:
				pass
			await menu(ctx, embedlist, DEFAULT_CONTROLS)
