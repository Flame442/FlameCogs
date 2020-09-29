from .monopoly import Monopoly

__red_end_user_data_statement__ = 'This cog stores user ids in order to identify the players in saved games.'

def setup(bot):
	bot.add_cog(Monopoly(bot))
