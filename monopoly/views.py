import discord

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
	async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.edit_message(view=None)
		self.result = True
		self.stop()

	@discord.ui.button(label='No', style=discord.ButtonStyle.red)
	async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.edit_message(view=None)
		self.stop()

class LabledButton(discord.ui.Button):
	def __init__(self, result, **kwargs):
		super().__init__(**kwargs)
		self.result = result

	async def callback(self, interaction):
		await interaction.response.edit_message(view=None)
		self.view.result = self.result
		self.view.stop()

class LabledSelect(discord.ui.Select):
	def __init__(self, *, options: list, enabled: list=None, return_list: bool=False, **kwargs):
		if enabled is None:
			enabled = [False for x in options]
		self.choices = [str(i) for i in range(len(options))]
		super().__init__(options=[discord.SelectOption(label=x, value=self.choices[idx], default=enabled[idx]) for idx, x in enumerate(options)], **kwargs)
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

class JailView(discord.ui.View):
	def __init__(self, game, config, choices: list):
		super().__init__(timeout=config['timeoutValue'])
		self.game = game
		self.config = config
		self.uid = self.game.uid[self.game.p]
		self.result = None
		if 'r' in choices:
			self.add_item(LabledButton('r', label='Roll', style=discord.ButtonStyle.blurple))
		if 'b' in choices:
			self.add_item(LabledButton('b', label=f'Post Bail (${config["bailValue"]})', style=discord.ButtonStyle.gray))
		if 'g' in choices:
			self.add_item(LabledButton('g', label=f'Use a "Get Out of Jail Free" card ({self.game.goojf[self.game.p]} left)', style=discord.ButtonStyle.gray))
	
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
			self.add_item(LabledButton('r', label='Roll', style=discord.ButtonStyle.blurple))
		if 'd' in choices:
			self.add_item(LabledButton('d', label='End turn', style=discord.ButtonStyle.blurple))
		if 'g' in choices:
			self.add_item(LabledButton('g', label='Give up', style=discord.ButtonStyle.red))
		if 't' in choices:
			self.add_item(LabledButton('t', label='Trade', style=discord.ButtonStyle.gray))
		if 'h' in choices:
			self.add_item(LabledButton('h', label='Manage Houses', style=discord.ButtonStyle.gray))
		if 'm' in choices:
			self.add_item(LabledButton('m', label='Mortgage Properties', style=discord.ButtonStyle.gray))
		if 's' in choices:
			self.add_item(LabledButton('s', label='Save', style=discord.ButtonStyle.gray))
	
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
		self.add_item(LabledSelect(options=choices))
		if 'c' in buttons:
			self.add_item(LabledButton('c', label='Cancel', style=discord.ButtonStyle.red))
		if 'd' in buttons:
			self.add_item(LabledButton('d', label='Done', style=discord.ButtonStyle.blurple))
		if 'e' in buttons:
			self.add_item(LabledButton('e', label='Exit without saving', style=discord.ButtonStyle.red))
	
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
			self.add_item(LabledSelect(options=choices, enabled=enabled, return_list=True, max_values=len(choices)))
		self.add_item(LabledButton('d', label='Done', style=discord.ButtonStyle.blurple))
		self.add_item(LabledButton('m', label='Modify money', style=discord.ButtonStyle.gray))
		self.add_item(LabledButton('j', label='Modify get out of jail free cards', style=discord.ButtonStyle.gray))
		self.add_item(LabledButton('c', label='Cancel', style=discord.ButtonStyle.red))
	
	async def interaction_check(self, interaction):
		if interaction.user.id != self.uid:
			await interaction.response.send_message(content='You are not allowed to interact with this button.', ephemeral=True)
			return False
		return True
