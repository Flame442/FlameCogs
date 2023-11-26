import discord
from .ai import MonopolyAI


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
		msg += f"\nClick the `Join Game` button to join. Up to {self.max_players} players can join. To start with less than that many, use the `Start Game` button to begin."
		return msg
	
	async def interaction_check(self, interaction):
		if len(self.players) >= self.max_players:
			await interaction.response.send_message(content='The game is full.', ephemeral=True)
			return False
		if interaction.user.id != self.ctx.author.id and interaction.user in self.players:
			await interaction.response.send_message(content='You have already joined the game. Please wait for others to join or for the game to be started.', ephemeral=True)
			return False
		return True
	
	@discord.ui.button(label="Join Game", style=discord.ButtonStyle.blurple)
	async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Allows a user not currently added to join."""
		if interaction.user.id == self.ctx.author.id:
			await interaction.response.send_message(content='You have already joined the game. You can add AI players or start the game early with the other two buttons.', ephemeral=True)
			return
		self.players.append(interaction.user)
		self.start.disabled = False
		if len(self.players) >= self.max_players:
			view = None
			self.stop()
		else:
			view = self
		await interaction.response.edit_message(content=self.generate_message(), view=view)
	
	@discord.ui.button(label="Add an AI", style=discord.ButtonStyle.blurple)
	async def ai(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Fills the next player slot with an AI player."""
		if interaction.user.id != self.ctx.author.id:
			await interaction.response.send_message(content='Only the host can use this button.', ephemeral=True)
			return
		self.players.append(MonopolyAI(len(self.players), f'[AI] ({len(self.players) + 1})'))
		self.start.disabled = False
		if len(self.players) >= self.max_players:
			view = None
			self.stop()
		else:
			view = self
		await interaction.response.edit_message(content=self.generate_message(), view=view)
	
	@discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, disabled=True)
	async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Starts the game with less than max_players players."""
		if interaction.user.id != self.ctx.author.id:
			await interaction.response.send_message(content='Only the host can use this button.', ephemeral=True)
			return
		await interaction.response.edit_message(view=None)
		self.stop()

class ConfirmView(discord.ui.View):
	def __init__(self, game, config, *, pid: int=None):
		super().__init__(timeout=config['timeoutValue'])
		self.game = game
		if pid is None:
			self.uid = self.game.uid[self.game.p]
		else:
			self.uid = self.game.uid[pid]
		self.result = False

	async def interaction_check(self, interaction):
		if interaction.user.id != self.uid:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True

	@discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
	async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		self.result = True
		self.stop()

	@discord.ui.button(label='No', style=discord.ButtonStyle.red)
	async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=None)
		self.stop()

class LabeledButton(discord.ui.Button):
	def __init__(self, result, **kwargs):
		super().__init__(**kwargs)
		self.result = result

	async def callback(self, interaction):
		await interaction.response.edit_message(view=None)
		self.view.result = self.result
		self.view.stop()

class LabeledSelect(discord.ui.Select):
	def __init__(self, *, options: list, enabled: list=None, return_list: bool=False, **kwargs):
		if enabled is None:
			enabled = [False for x in options]
		self.choices = [str(i) for i in range(len(options))]
		self.all_options = [discord.SelectOption(label=x, value=self.choices[idx], default=enabled[idx]) for idx, x in enumerate(options)]
		self.page = 0
		super().__init__(options=self.all_options[self.page * 25:(self.page + 1) * 25], **kwargs)
		self.return_list = return_list

	async def callback(self, interaction):
		await interaction.response.edit_message(view=None)
		result = []
		for value in self.values:
			result.append(self.choices.index(value))
		if not self.return_list:
			self.view.result = result[0]
		else:
			self.view.result = result
		self.view.stop()

class NextPageButton(discord.ui.Button):
	def __init__(self, labeled_select):
		super().__init__(label="Next Page", style=discord.ButtonStyle.blurple)
		self.labeled_select = labeled_select
	
	async def callback(self, interaction):
		self.labeled_select.page = (self.labeled_select.page + 1) % 2
		self.labeled_select.options = self.labeled_select.all_options[self.labeled_select.page * 25:(self.labeled_select.page + 1) * 25]
		await interaction.response.edit_message(view=self.view)

class JailView(discord.ui.View):
	def __init__(self, game, config, choices: list):
		super().__init__(timeout=config['timeoutValue'])
		self.game = game
		self.config = config
		self.uid = self.game.uid[self.game.p]
		self.result = None
		if 'r' in choices:
			self.add_item(LabeledButton('r', label='Roll', style=discord.ButtonStyle.blurple))
		if 'b' in choices:
			self.add_item(LabeledButton('b', label=f'Post Bail (${config["bailValue"]})', style=discord.ButtonStyle.gray))
		if 'g' in choices:
			self.add_item(LabeledButton('g', label=f'Use a "Get Out of Jail Free" card ({self.game.goojf[self.game.p]} left)', style=discord.ButtonStyle.gray))
	
	async def interaction_check(self, interaction):
		if interaction.user.id != self.uid:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True

class TurnView(discord.ui.View):
	def __init__(self, game, config, choices: list):
		super().__init__(timeout=config['timeoutValue'])
		self.game = game
		self.config = config
		self.uid = self.game.uid[self.game.p]
		self.result = None
		if 'r' in choices:
			self.add_item(LabeledButton('r', label='Roll', style=discord.ButtonStyle.blurple))
		if 'd' in choices:
			self.add_item(LabeledButton('d', label='End turn', style=discord.ButtonStyle.blurple))
		if 'g' in choices:
			self.add_item(LabeledButton('g', label='Give up', style=discord.ButtonStyle.red))
		if 't' in choices:
			self.add_item(LabeledButton('t', label='Trade', style=discord.ButtonStyle.gray))
		if 'h' in choices:
			self.add_item(LabeledButton('h', label='Manage Houses', style=discord.ButtonStyle.gray))
		if 'm' in choices:
			self.add_item(LabeledButton('m', label='Mortgage Properties', style=discord.ButtonStyle.gray))
		if 's' in choices:
			self.add_item(LabeledButton('s', label='Save', style=discord.ButtonStyle.gray))
	
	async def interaction_check(self, interaction):
		if interaction.user.id != self.uid:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True

class SelectView(discord.ui.View):
	def __init__(self, game, config, choices: list, buttons: list):
		super().__init__(timeout=config['timeoutValue'])
		self.game = game
		self.config = config
		self.uid = self.game.uid[self.game.p]
		self.result = None
		labeled_select = LabeledSelect(options=choices)
		self.add_item(labeled_select)
		if 'c' in buttons:
			self.add_item(LabeledButton('c', label='Cancel', style=discord.ButtonStyle.red))
		if 'd' in buttons:
			self.add_item(LabeledButton('d', label='Done', style=discord.ButtonStyle.blurple))
		if 'e' in buttons:
			self.add_item(LabeledButton('e', label='Exit without saving', style=discord.ButtonStyle.red))
		if len(choices) > 25:
			self.add_item(NextPageButton(labeled_select))
	
	async def interaction_check(self, interaction):
		if interaction.user.id != self.uid:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True

class TradeView(discord.ui.View):
	def __init__(self, game, config, choices: list, enabled: list):
		super().__init__(timeout=config['timeoutValue'])
		self.game = game
		self.config = config
		self.uid = self.game.uid[self.game.p]
		self.result = None
		if len(choices) > 0:
			# Trades will not support the up to 3 properties at the end if the user has more than 25.
			labeled_select = LabeledSelect(options=choices, enabled=enabled, return_list=True, max_values=min(25, len(choices)))
			self.add_item(labeled_select)
		self.add_item(LabeledButton('d', label='Done', style=discord.ButtonStyle.blurple))
		self.add_item(LabeledButton('m', label='Modify money', style=discord.ButtonStyle.gray))
		self.add_item(LabeledButton('j', label='Modify get out of jail free cards', style=discord.ButtonStyle.gray))
		self.add_item(LabeledButton('c', label='Cancel', style=discord.ButtonStyle.red))
	
	async def interaction_check(self, interaction):
		if interaction.user.id != self.uid:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True
