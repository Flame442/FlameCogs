from .commands import PokemonDuel


async def setup(bot):
    await bot.add_cog(PokemonDuel(bot))
