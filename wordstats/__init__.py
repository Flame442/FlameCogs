from .wordstats import WordStats

def setup(bot):
	bot.add_cog(WordStats(bot))
