from .battleship import Battleship

def setup(bot):
	bot.add_cog(Battleship(bot))
