from .gamevoice import Gamevoice

def setup(bot):
	n = Gamevoice(bot)
	bot.add_listener(n.update, "on_member_update")
	bot.add_cog(n)
