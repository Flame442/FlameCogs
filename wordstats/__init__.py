from .wordstats import WordStats

__red_end_user_data_statement__ = (
	'This cog persistently stores the number of times every unique word is said per-user per-guild. '
	'Data is collected on every message the bot can see unless the guild, channel, or user have opted out. '
	'Users can request that their data is deleted using `[p]wordstatsset forgetme` '
	'and can request to opt out of data collection using `[p]wordstatsset user no`.'
)

def setup(bot):
	bot.add_cog(WordStats(bot))
