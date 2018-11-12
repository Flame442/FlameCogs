from redbot.core import data_manager
from .hangman import Hangman

def setup(bot):
	n = Hangman()
	data_manager.load_bundled_data(n, __file__)
	bot.add_cog(n)
