from .stocks import Stocks

def setup(bot):
	bot.add_cog(Stocks(bot))
