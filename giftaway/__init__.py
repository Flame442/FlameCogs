from .giftaway import GiftAway

async def setup(bot):
	await bot.add_cog(GiftAway(bot))
