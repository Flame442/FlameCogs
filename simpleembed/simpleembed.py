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
	async def sendembed(self, ctx, color:Optional[discord.Color]=None, *, text):
		"""
		Send an embed.
		
		Use the optional paramter `color` to change the color of the embed.
		The embed will contain the text `text`.
		All normal discord formatting will work inside the embed. 
		"""
		if color is None:
			color = await ctx.embed_color()
		embed = discord.Embed(
			description=text,
			color=color
		)
		await ctx.send(embed=embed)
		try:
			await ctx.message.delete()
		except discord.Forbidden:
			pass
