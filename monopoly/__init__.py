from redbot.core import data_manager
from .monopoly import Monopoly

def setup(bot):
	n = Monopoly(bot)
	bot.add_cog(n)
