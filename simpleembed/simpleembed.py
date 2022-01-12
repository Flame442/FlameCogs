import discord
from redbot.core import commands
from redbot.core import checks
from typing import Optional


class SimpleEmbed(commands.Cog):
	"""Simply send embeds."""
	def __init__(self, bot):
		self.bot = bot
	
	@checks.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(embed_links=True)
	@commands.command()
	async def sendembed(self, ctx, color: Optional[discord.Color]=None, *, text):
		"""
		Send an embed.
		
		Use the optional parameter `color` to change the color of the embed.
		The embed will contain the text `text`.
		All normal discord formatting will work inside the embed.
		If an imaged is attached with the command, it will be inserted at the bottom of the embed.
		"""
		if color is None:
			color = await ctx.embed_color()
		embed = discord.Embed(
			description=text,
			color=color
		)
		if ctx.message.attachments:
			content = await ctx.message.attachments[0].to_file()
			embed.set_image(url="attachment://" + str(content.filename))
		await ctx.send(embed=embed, file=content if ctx.message.attachments else None)
		try:
			await ctx.message.delete()
		except discord.Forbidden:
			pass

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
