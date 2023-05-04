from .commands import PokemonDuel

__red_end_user_data_statement__ = "This cog stores user ids in order to track your party of pokemon."

async def setup(bot):
    await bot.add_cog(PokemonDuel(bot))
