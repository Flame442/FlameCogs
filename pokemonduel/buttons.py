import discord
import asyncio
from .move import Move

# pylint: disable=C0116,W0613,W0221
BUTTON_TIMEOUT = 60


class DuelAcceptView(discord.ui.View):
    """View to accept a duel."""
    def __init__(self, ctx: "commands.Context", opponent: discord.Member):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.ctx = ctx
        self.confirm = False
        self.event = asyncio.Event()
        self.opponent = opponent

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction, button):
        self.confirm = True
        await interaction.response.edit_message(view=None)
        self.stop()
    
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction, button):
        await interaction.response.edit_message(view=None)
        self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        await self.message.edit(view=None)
        self.stop()
    
    async def on_error(self, interaction, error, item):
        await self.ctx.cog.log.error("Exception in a button.", exc_info=error)


class PreviewPromptView(discord.ui.View):
    """Prompts a user to select their lead pokemon when previewing both player's parties."""
    def __init__(self, battle):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.battle = battle
        self.child_views = []

    @discord.ui.button(label="Select a lead pokemon", style=discord.ButtonStyle.primary)
    async def actions(self, interaction, button):
        if interaction.user.id == self.battle.trainer1.id:
            trainer = self.battle.trainer1
        else:
            trainer = self.battle.trainer2
        view = LeadView(trainer, self.battle)
        self.child_views.append(view)
        await interaction.response.send_message(content="Pick a pokemon to lead with:", view=view, ephemeral=True)

    async def interaction_check(self, interaction):
        if interaction.user.id == self.battle.trainer1.id:
            if self.battle.trainer1.event.is_set():
                await interaction.response.send_message(content="You have already selected a lead.", ephemeral=True)
                return False
            return True
        if interaction.user.id == self.battle.trainer2.id:
            if self.battle.trainer2.event.is_set():
                await interaction.response.send_message(content="You have already selected a lead.", ephemeral=True)
                return False
            return True
        return False

    async def on_timeout(self):
        self.battle.trainer1.event.set()
        self.battle.trainer2.event.set()
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)
    
    def stop(self):
        """Override to stop child views when this view is stopped."""
        for view in self.child_views:
            view.stop()
        super().stop()


class LeadView(discord.ui.View):
    """Shows the user their pokemon, allowing them to click one to make their lead to."""
    def __init__(self, trainer, battle):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.battle = battle
        for poke in trainer.party:
            self.add_item(LeadButton(poke))
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)


class LeadButton(discord.ui.Button):
    """A button that makes the pokemon the user's lead when pressed."""
    def __init__(self, poke):
        super().__init__(style=discord.ButtonStyle.secondary, label=f"{poke._name} | {poke.hp}hp")
        self.poke = poke

    async def callback(self, interaction):
        content = f"You will lead with {self.poke.name}. Waiting for opponent."
        self.view.trainer.switch_poke(self.view.trainer.party.index(self.poke))
        self.view.trainer.event.set()
        await interaction.response.edit_message(content=content, view=None)


class BattlePromptView(discord.ui.View):
    """Prompts users to select an action for their turn."""
    def __init__(self, battle):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.battle = battle
        self.turn = battle.turn
        self.child_views = []

    @discord.ui.button(label="View your actions", style=discord.ButtonStyle.primary)
    async def actions(self, interaction, button):
        if interaction.user.id == self.battle.trainer1.id:
            trainer = self.battle.trainer1
            opponent = self.battle.trainer2
        else:
            trainer = self.battle.trainer2
            opponent = self.battle.trainer1
        view = MoveSelectView(self.battle, trainer, opponent)
        self.child_views.append(view)
        await interaction.response.send_message(content="Pick an action:", view=view, ephemeral=True)

    async def interaction_check(self, interaction):
        if self.battle.turn != self.turn:
            await interaction.response.send_message(content="This button has expired.", ephemeral=True)
            return False
        if self.battle.trainer1.is_human() and interaction.user.id == self.battle.trainer1.id:
            if self.battle.trainer1.selected_action is not None:
                await interaction.response.send_message(content="You have already selected an action.", ephemeral=True)
                return False
            return True
        if self.battle.trainer2.is_human() and interaction.user.id == self.battle.trainer2.id:
            if self.battle.trainer2.selected_action is not None:
                await interaction.response.send_message(content="You have already selected an action.", ephemeral=True)
                return False
            return True
        return False

    async def on_timeout(self):
        self.battle.trainer1.event.set()
        self.battle.trainer2.event.set()
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)
    
    def stop(self):
        """Override to stop child views when this view is stopped."""
        for view in self.child_views:
            view.stop()
        super().stop()


class MoveSelectView(discord.ui.View):
    """Prompts the user to pick a move, enter the swap pokes view, or cancel the duel."""
    def __init__(self, battle, trainer, opponent):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.battle = battle
        self.turn = battle.turn
        self.trainer = trainer
        self.opponent = opponent
        self.child_views = []
        status_code, movedata = trainer.valid_moves(opponent.current_pokemon)
        if status_code == "forced":
            trainer.selected_action = movedata
            trainer.event.set()
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="You were forced to play:", disabled=True))
            self.add_item(MoveButton(movedata, disabled=True))
            return
        swapdata = trainer.valid_swaps(opponent.current_pokemon, battle)
        if status_code == "struggle":
            self.add_item(MoveButton(Move.struggle()))
            self.add_item(SwapRequestButton(disabled=not swapdata))
            self.add_item(ForfeitButton(row=0))
            return
        
        for idx, move in enumerate(trainer.current_pokemon.moves):
            self.add_item(MoveButton(move, disabled=idx not in movedata, row=idx // 2))
        self.add_item(SwapRequestButton(disabled=not swapdata))
        self.add_item(ForfeitButton())
        if (
            trainer.current_pokemon is not None
            and trainer.current_pokemon.mega_type_ids is not None
            and not trainer.has_mega_evolved
        ):
            self.add_item(MegaEvolveButton())
        
    async def interaction_check(self, interaction):
        if self.battle.turn != self.turn:
            await interaction.response.send_message(content="This button has expired.", ephemeral=True)
            return False
        # Should never be hit, but just in case :P
        if interaction.user.id != self.trainer.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        if self.trainer.selected_action is not None:
            await interaction.response.send_message(content="You have already selected an action.", ephemeral=True)
            return False
        return True
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)
    
    def stop(self):
        """Override to stop child views when this view is stopped."""
        for view in self.child_views:
            view.stop()
        super().stop()


class MoveButton(discord.ui.Button):
    """A button that represents a selection of a specific move."""
    def __init__(self, move, *, disabled=False, row=0):
        label = f"{move.pretty_name}"
        if move.id != 165:
            label += f" | {move.pp}pp"
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=disabled, row=row)
        self.move = move

    async def callback(self, interaction):
        self.view.trainer.selected_action = self.move
        self.view.trainer.event.set()
        await interaction.response.edit_message(content=f"You picked {self.move.pretty_name}. Waiting for opponent.", view=None)


class SwapRequestButton(discord.ui.Button):
    """A button that represents a request to swap pokemon."""
    def __init__(self, *, disabled=False):
        super().__init__(style=discord.ButtonStyle.primary, label="Swap pokemon", disabled=disabled)

    async def callback(self, interaction):
        view = SwapView(self.view.trainer, self.view.opponent, self.view.battle, set_move=True)
        self.view.child_views.append(view)
        await interaction.response.edit_message(content="Pick a pokemon:", view=view)


class DuelForfeitView(discord.ui.View):
    """View to forfeit a duel."""
    def __init__(self, trainer):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.confirm = False
    
    @discord.ui.button(label="Forfeit", style=discord.ButtonStyle.red)
    async def actuallyforfeit(self, interaction, button):
        await interaction.response.edit_message(content="Forfeited.", view=None)
        self.confirm = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Not forfeiting.", view=None)
        self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.trainer.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True
    
    async def on_error(self, interaction, error, item):
        await self.trainer.party[0].held_item.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)


class ForfeitButton(discord.ui.Button):
    """A button that forfeits the game when pressed."""
    def __init__(self, *, row=1):
        super().__init__(style=discord.ButtonStyle.danger, label="Forfeit duel", row=row)

    async def callback(self, interaction):
        view = DuelForfeitView(self.view.trainer)
        self.view.child_views.append(view)
        await interaction.response.send_message(content="Are you sure you want to forfeit?", view=view, ephemeral=True)
        await view.wait()
        if view.confirm:
            self.view.trainer.event.set()


class SwapPromptView(discord.ui.View):
    """Prompts the trainer to view their pokemon."""
    def __init__(self, trainer, opponent, battle, *, mid_turn=False):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.opponent = opponent
        self.battle = battle
        self.turn = battle.turn
        self.mid_turn = mid_turn
        self.child_views = []

    @discord.ui.button(label="View your pokemon", style=discord.ButtonStyle.primary)
    async def swap(self, interaction, button):
        view = SwapView(self.trainer, self.opponent, self.battle, mid_turn=self.mid_turn)
        self.child_views.append(view)
        await interaction.response.send_message(
            content="Pick a pokemon to swap to:",
            view=view,
            ephemeral=True
        )

    async def interaction_check(self, interaction):
        if self.battle.turn != self.turn:
            await interaction.response.send_message(content="This button has expired.", ephemeral=True)
            return False
        if interaction.user.id != self.trainer.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        self.battle.trainer1.event.set()
        self.battle.trainer2.event.set()
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)
    
    def stop(self):
        """Override to stop child views when this view is stopped."""
        for view in self.child_views:
            view.stop()
        super().stop()


class SwapView(discord.ui.View):
    """Shows the user their pokemon, allowing them to click one to swap to."""
    def __init__(self, trainer, opponent, battle, *, set_move=False, mid_turn=False):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.trainer = trainer
        self.opponent = opponent
        self.battle = battle
        self.set_move = set_move
        self.mid_turn = mid_turn
        swapdata = trainer.valid_swaps(opponent.current_pokemon, battle, check_trap=set_move)
        for idx, poke in enumerate(trainer.party):
            self.add_item(SwapButton(poke, disabled=idx not in swapdata))
    
    async def on_error(self, interaction, error, item):
        self.battle.ctx.cog.log.error("Exception in a button.", exc_info=error)


class SwapButton(discord.ui.Button):
    """A button that swaps to that pokemon when pressed."""
    def __init__(self, poke, *, disabled=False):
        super().__init__(style=discord.ButtonStyle.secondary, label=f"{poke._name} | {poke.hp}hp", disabled=disabled)
        self.poke = poke

    async def callback(self, interaction):
        content = f"You picked {self.poke.name}."
        if self.view.set_move:
            self.view.trainer.selected_action = self.view.trainer.party.index(self.poke)
            content += " Waiting for opponent."
        else:
            self.view.trainer.switch_poke(self.view.trainer.party.index(self.poke), mid_turn=self.view.mid_turn)
        self.view.trainer.event.set()
        await interaction.response.edit_message(content=content, view=None)


class MegaEvolveButton(discord.ui.Button):
    """A button that toggles whether the trainer's pokemon should mega evolve this turn."""
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Mega Evolve", row=0)

    def get_color(self):
        return [discord.ButtonStyle.gray, discord.ButtonStyle.green][self.view.trainer.current_pokemon.should_mega_evolve]

    async def callback(self, interaction):
        self.view.trainer.current_pokemon.should_mega_evolve = not self.view.trainer.current_pokemon.should_mega_evolve
        self.style = self.get_color()
        await interaction.response.edit_message(view=self.view)
