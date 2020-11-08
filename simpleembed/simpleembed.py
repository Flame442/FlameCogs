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
	async def sendembed(self, ctx, color: Optional[discord.Color] = None, image=None, thumbnail=None, *, text):
		"""
		Send an embed.

		Use the optional parameter `color` to change the color of the embed.
		Use the parameter 'image' to include an image url
		Use the parameter 'thumbnail' to include an thumbnail image url
		The embed will contain the text `text`.

		"""
		if color is None:
			color = await ctx.embed_color()
		embed = discord.Embed(
			description=text,
			color=color
		)

		if image is not None:
			embed.set_image(url=image)

		if thumbnail is not None:
			embed.set_thumbnail(url=thumbnail)

		await ctx.send(embed=embed)
		try:
			await ctx.message.delete()
		except discord.Forbidden:
			pass

	async def red_delete_data_for_user(self, **kwargs):
		"""Nothing to delete."""
		return
