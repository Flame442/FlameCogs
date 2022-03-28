from .monopoly import Monopoly

__red_end_user_data_statement__ = 'This cog stores user ids in order to identify the players in saved games.'

async def setup(bot):
	await bot.add_cog(Monopoly(bot))
