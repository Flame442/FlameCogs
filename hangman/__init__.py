from .hangman import Hangman

__red_end_user_data_statement__ = 'This cog does not store user data.'

def setup(bot):
	bot.add_cog(Hangman(bot))
