import discord


class ConfirmView(discord.ui.View):
	def __init__(self, member: discord.Member):
		super().__init__(timeout=60)
		self.member = member
		self.result = False

	async def interaction_check(self, interaction):
		if interaction.user.id != self.member.id:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True

	@discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
	async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		self.result = True
		self.stop()

	@discord.ui.button(label='Deny', style=discord.ButtonStyle.red)
	async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		self.stop()


class GetPlayersView(discord.ui.View):
    """View to gather the players that will play in a game."""
    def __init__(self, ctx, max_players):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.max_players = max_players
        self.players = [ctx.author]
    
    def generate_message(self):
        """Generates a message to show the players currently added to the game."""
        msg = ""
        for idx, player in enumerate(self.players, start=1):
            msg += f"Player {idx} - {player.display_name}\n"
        msg += (
            f"\nClick the `Join Game` button to join. Up to {self.max_players} players can join. "
            #"To start with less than that many, use the `Start Game` button to begin."
        )
        return msg
    
    async def interaction_check(self, interaction):
        if len(self.players) >= self.max_players:
            await interaction.response.send_message(content='The game is full.', ephemeral=True)
            return False
        if interaction.user.id != self.ctx.author.id and interaction.user in self.players:
            await interaction.response.send_message(
                content='You have already joined the game. Please wait for others to join or for the game to be started.',
                ephemeral=True,
            )
            return False
        return True
    
    async def on_error(self, interaction, error, item):
        self.ctx.cog.log.error("Exception in a button.", exc_info=error)
    
    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Allows a user not currently added to join."""
        if interaction.user.id == self.ctx.author.id:
            await interaction.response.send_message(
                content='You have already joined the game.', # "You can add AI players or start the game early with the other two buttons."
                ephemeral=True,
            )
            return
        self.players.append(interaction.user)
        #self.start.disabled = False
        if len(self.players) >= self.max_players:
            view = None
            self.stop()
        else:
            view = self
        await interaction.response.edit_message(content=self.generate_message(), view=view)
    
    #@discord.ui.button(label="Add an AI", style=discord.ButtonStyle.blurple)
    #async def ai(self, interaction: discord.Interaction, button: discord.ui.Button):
    #    """Fills the next player slot with an AI player."""
    #    if interaction.user.id != self.ctx.author.id:
    #        await interaction.response.send_message(
    #            content='Only the host can use this button.',
    #            ephemeral=True,
    #        )
    #        return
    #    self.players.append(<AISubclass>(self.ctx.guild.me.display_name))
    #    self.start.disabled = False
    #    if len(self.players) >= self.max_players:
    #        view = None
    #        self.stop()
    #    else:
    #        view = self
    #    await interaction.response.edit_message(content=self.generate_message(), view=view)
    
    #@discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, disabled=True)
    #async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
    #    """Starts the game with less than max_players players."""
    #    if interaction.user.id != self.ctx.author.id:
    #        await interaction.response.send_message(
    #            content='Only the host can use this button.',
    #            ephemeral=True,
    #        )
    #        return
    #    await interaction.response.edit_message(view=None)
    #    self.stop()


class TileButton(discord.ui.Button):
    def __init__(self, idx, **kwargs):
        super().__init__(**kwargs)
        self.idx = idx
    
    async def callback(self, interaction):
        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(view=self.view)
        self.view.tile = self.idx
        self.view.stop()

class PickTileView(discord.ui.View):
    def __init__(self, game, board):
        super().__init__(timeout=60)
        self.game = game
        self.tile = None
        for idx in range(9):
            row = idx // 3
            label = {None: '\u200B', -1: '-', 0: 'X', 1: 'O'}[board[idx]]
            disabled = board[idx] is not None
            self.add_item(TileButton(
                idx,
                label=label,
                style=discord.ButtonStyle.gray,
                row=row,
                disabled=disabled
            ))
    
    async def interaction_check(self, interaction):
        if interaction.user != self.game.players[self.game.p]:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True
    
    async def on_error(self, interaction, error, item):
        self.game.cog.log.error("Exception in a button.", exc_info=error)
