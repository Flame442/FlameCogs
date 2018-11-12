from .monopoly import Monopoly

def setup(bot):
	n = Monopoly(bot)
	data_manager.load_bundled_data(n, __file__)
	bot.add_cog(n)
