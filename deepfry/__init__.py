from .deepfry import Deepfry

def setup(bot):
	n = Deepfry(bot)
	bot.add_listener(n.run, "on_message")
	bot.add_cog(n)
