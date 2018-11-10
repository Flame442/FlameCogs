from .wordstats import WordStats

def setup(bot):
	n = WordStats(bot)
	bot.add_listener(n.run, "on_message")
	bot.add_cog(n)
