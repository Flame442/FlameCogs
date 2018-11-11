from .hangman import Hangman

def setup(bot):
	bot.add_cog(Hangman(bot))
