from .onlinestats import OnlineStats

def setup(bot):
	bot.add_cog(OnlineStats(bot))
