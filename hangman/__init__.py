from redbot.core import data_manager
from .hangman import Hangman

def setup(bot):
	n = Hangman(bot)
	bot.add_cog(n)
