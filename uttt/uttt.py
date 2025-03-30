import discord
from redbot.core import commands, Config
import asyncio
import logging
from .game import UTTTGame
from .views import ConfirmView, GetPlayersView


class UTTT(commands.Cog):
    """Play ultimate tic tac toe with one other person."""
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger('red.flamecogs.uttt')
        self.games = []
        self.config = Config.get_conf(self, identifier=145519400223506432)
        self.config.register_guild(
            deleteHistory=False,
        )
    
    @commands.guild_only()
    @commands.command()
    async def uttt(self, ctx, opponent: discord.Member=None):
        """
        Play a game of ultimate tic tac toe.
        
        You may only play in the sub board that corresponds to the last
        spot your opponent played. If you are sent to a sub board that
        has been finished, you can choose any sub board. First to win
        three sub boards in a row wins.
        """
        if [game for game in self.games if game.channel == ctx.channel]:
            await ctx.send('A game is already running in this channel.')
            return
        
        if opponent is None:
            view = GetPlayersView(ctx, 2)
            initial_message = await ctx.send(view.generate_message(), view=view)
            await view.wait()
            players = view.players
        else:
            view = ConfirmView(opponent)
            await ctx.send(f'{opponent.mention} You have been challenged to a game of UTTT by {ctx.author.display_name}!', view=view)
            await view.wait()
            if not view.result:
                await ctx.send(f'{opponent.display_name} does not want to play, shutting down.')
                return
            players = [ctx.author, opponent]
        
        if len(players) < 2:
            await ctx.send('Nobody else wants to play, shutting down.')
            return
        players = players[:2]
        
        if [game for game in self.games if game.channel == ctx.channel]:
            await ctx.send('Another game started in this channel while setting up.')
            return
        
        game = UTTTGame(ctx, *players)
        self.games.append(game)
    
    @commands.guild_only()
    @commands.guildowner()
    @commands.group(invoke_without_command=True)
    async def utttset(self, ctx):
        """Config options for UTTT."""
        await ctx.send_help()
        cfg = await self.config.guild(ctx.guild).all()
        msg = (
            'Delete previous messages: {deleteHistory}\n'
        ).format_map(cfg)
        await ctx.send(f'```py\n{msg}```')
    
    @utttset.command()
    async def delete(self, ctx, value: bool=None):
        """
        Set if old messages should be deleted when new ones are sent.
        
        Defaults to False.
        This value is server specific.
        """
        if value is None:
            v = await self.config.guild(ctx.guild).deleteHistory()
            if v:
                await ctx.send('Messages are currently deleted when new ones are sent.')
            else:
                await ctx.send('Messages are currently retained.')
        else:
            await self.config.guild(ctx.guild).deleteHistory.set(value)
            if value:
                await ctx.send('Messages will now be deleted when new ones are sent.')
            else:
                await ctx.send('Messages will now be retained.')
    
    @commands.guild_only()
    @commands.guildowner()
    @commands.command()
    async def utttstop(self, ctx):
        """Stop the game of ultimate tic tac toe in this channel."""
        wasGame = False
        for x in [game for game in self.games if game.channel == ctx.channel]:
            x.stop()
            wasGame = True
        if wasGame: #prevent multiple messages if more than one game exists for some reason
            await ctx.send('The game was stopped successfully.')
        else:
            await ctx.send('There is no ongoing game in this channel.')
    
    def cog_unload(self):
        return [game.stop() for game in self.games]
    
    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return
