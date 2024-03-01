import discord
from redbot.core import commands
from functools import partial
import asyncio
import logging
from .views import PickTileView


BLUE = "\u001b[0;34m"
YELLOW = "\u001b[0;33m"
CLEAR = "\u001b[0m"
BAR = "\u275a"
CHAR = {None: ' ', 0: 'X', 1: 'O'}
BIG_CHAR = {
    0: [
        r"   \   /   ",
        r"    \ /    ",
        r"     X     ",
        r"    / \    ",
        r"   /   \   ",
    ],
    1: [
        r"   .---.   ",
        r"  /     \  ",
        r" |       | ",
        r"  \     /  ",
        r"   '---'   ",
    ],
    -1: [
        r"           ",
        r"    _      ",
        r"   / \_/   ",
        r"           ",
        r"           ",
    ],
}
PSWAP = [1, 0]

class UTTTGame():
    def __init__(self, ctx, p1, p2):
        self.bot = ctx.bot
        self.ctx = ctx
        self.cog = ctx.cog
        self.channel = ctx.channel
        self.players = [p1, p2]
        self.big_board = [None] * 9
        self.board = [[None] * 9 for x in range(9)]
        self.p = 0
        self.sub = None
        self._task = asyncio.create_task(self.run())
        self._task.add_done_callback(partial(self.error_callback, ctx))

    async def send_error(self, ctx, exc: Exception):
        """Sends a message to the channel after an error."""
        await ctx.send(
            'A fatal error has occurred, shutting down.\n'
            'Please have the bot owner copy the error from console '
            'and post it in the support channel of <https://discord.gg/bYqCjvu>.'
        ) 

    def error_callback(self, ctx, fut):
        """Checks for errors in stopped games."""
        try:
            fut.result()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            asyncio.create_task(self.send_error(ctx, exc))
            msg = 'Error in UTTT.\n'
            self.cog.log.exception(msg)
            self.bot.dispatch('flamecogs_game_error', self, exc)
        try:
            self.cog.games.remove(self)
        except ValueError:
            pass

    @staticmethod
    def check_board(b):
        _0, _1, _2, _3, _4, _5, _6, _7, _8 = b
        return (
            _0 == _1 == _2 and _0 is not None and _0 != -1
            or _3 == _4 == _5 and _3 is not None and _3 != -1
            or _6 == _7 == _8 and _6 is not None and _6 != -1
            or _0 == _3 == _6 and _0 is not None and _0 != -1
            or _1 == _4 == _7 and _1 is not None and _1 != -1
            or _2 == _5 == _8 and _2 is not None and _2 != -1
            or _0 == _4 == _8 and _0 is not None and _0 != -1
            or _2 == _4 == _6 and _2 is not None and _2 != -1
        )

    def generate_board(self):
        board = '--------=UltimateTicTacToe=--------\n'
        sub_tile = 0 # Which row in each sub board is being printed
        # 9 game tile rows + 8 separator rows
        for n in range(1, 18):
            sub_board = (n // 6) * 3 # Which row of sub boards is being printed
            # big sep row
            if n % 6 == 0:
                board += YELLOW + '―――――――――――――――――――――――――――――――――――\n'
            # little sep row
            elif n % 2 == 0:
                for sub_board_offset in range(3):
                    if self.big_board[sub_board + sub_board_offset] is not None:
                        board += BIG_CHAR[self.big_board[sub_board + sub_board_offset]][(n - 1) % 6]
                    else:
                        board += BLUE if self.sub == sub_board + sub_board_offset else CLEAR
                        board += '― ―|― ―|― ―'
                    board += YELLOW + ('\n' if sub_board_offset == 2 else BAR)
            # game tile row
            else:
                for sub_board_offset in range(3):
                    if self.big_board[sub_board + sub_board_offset] is not None:
                        board += BIG_CHAR[self.big_board[sub_board + sub_board_offset]][(n - 1) % 6]
                    else:
                        board += BLUE if self.sub == sub_board + sub_board_offset else CLEAR
                        board += (
                            f' {CHAR[self.board[sub_board+sub_board_offset][sub_tile]]} |'
                            f' {CHAR[self.board[sub_board+sub_board_offset][sub_tile+1]]} |'
                            f' {CHAR[self.board[sub_board+sub_board_offset][sub_tile+2]]} '
                        )
                    board += YELLOW + BAR
                board = board.rstrip(BAR) + ' \n'
                sub_tile += 3
                if sub_tile == 9:
                    sub_tile = 0
        return f'```ansi\n{board}```'

    async def run(self):
        while True:
            # Pick the sub board
            if self.sub is None:
                view = PickTileView(self, self.big_board)
                await self.ctx.send(
                    f'{self.generate_board()}{self.players[self.p].display_name}, pick a sub board.',
                    view=view,
                )
                await view.wait()
                if view.tile is None:
                    await self.ctx.send(
                        f'{self.players[self.p].display_name} took too long, shutting down.'
                    )
                    return self.stop()
                self.sub = view.tile

            # Pick the tile
            view = PickTileView(self, self.board[self.sub])
            await self.ctx.send(
                f'{self.generate_board()}{self.players[self.p].display_name}, make your move.',
                view=view,
            )
            await view.wait()
            if view.tile is None:
                await self.ctx.send(
                    f'{self.players[self.p].display_name} took too long, shutting down.'
                )
                return self.stop()
            move = view.tile
            self.board[self.sub][move] = self.p
            
            # Check for sub board / game wins
            if self.check_board(self.board[self.sub]):
                self.big_board[self.sub] = self.p
                if self.check_board(self.big_board):
                    await self.ctx.send(f'{self.generate_board()}{self.players[self.p].display_name} wins!')
                    return self.stop()
                if None not in self.big_board:
                    await self.ctx.send(f'{self.generate_board()}Nobody wins...')
                    return self.stop()
            elif None not in self.board[self.sub]:
                self.big_board[self.sub] = -1
            
            # Don't try to continue play on a finished board
            if self.big_board[move] is not None:
                self.sub = None
            else:
                self.sub = move
            
            # Swap turn
            self.p = PSWAP[self.p]

    def stop(self):
        """Stop and cleanup the game."""
        self.cog.games.remove(self)
        self._task.cancel()
