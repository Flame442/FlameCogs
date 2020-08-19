from .stocks import Stocks

__red_end_user_data_statement__ = 'This cog stores a user id in order to know what stocks have been purchased by each user. Data is only collected when a user directly interacts with the cog and its commands.'

def setup(bot):
	bot.add_cog(Stocks(bot))
