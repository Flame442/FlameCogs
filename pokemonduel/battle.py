import asyncio
import random
from .buttons import SwapPromptView
from .data import generate_main_battle_message, generate_text_battle_message, find
from .enums import Ability, DamageClass
from .misc import ExpiringEffect, Weather, Terrain


class Battle():
    """
    Represents a battle between two trainers and their pokemon.
    
    This object holds all necessary information for a battle & runs the battle.
    """
    def __init__(self, ctx, channel, trainer1, trainer2, *, inverse_battle=False):
        self.ctx = ctx
        self.channel = channel
        self.trainer1 = trainer1
        for poke in trainer1.party:
            poke.held_item.battle = self
        self.trainer2 = trainer2
        for poke in trainer2.party:
            poke.held_item.battle = self
        self.bg_num = random.randint(1, 4)
        self.trick_room = ExpiringEffect(0)
        self.magic_room = ExpiringEffect(0)
        self.wonder_room = ExpiringEffect(0)
        self.gravity = ExpiringEffect(0)
        self.weather = Weather(self)
        self.terrain = Terrain(self)
        self.plasma_fists = False
        self.turn = 0
        self.last_move_effect = None
        self.metronome_moves_raw = []
        #(AttackerType, DefenderType): Effectiveness
        self.type_effectiveness = {}
        self.inverse_battle = inverse_battle
        self.msg = ""

    async def run(self):
        """Runs the duel."""
        self.msg = ""
        # Moves which are immune to metronome
        immune_ids = [
            68, 102, 119, 144, 165, 166, 168, 173, 182, 194, 197, 203, 214, 243, 264, 266,
            267, 270, 271, 274, 289, 343, 364, 382, 383, 415, 448, 469, 476, 495, 501, 511,
            516, 546, 547, 548, 553, 554, 555, 557, 561, 562, 578, 588, 591, 592, 593, 596,
            606, 607, 614, 615, 617, 621, 661, 671, 689, 690, 704, 705, 712, 720, 721, 722
        ]
        # Moves which are not coded in the bot
        uncoded_ids = [
            266, 270, 476, 495, 502, 511, 597, 602, 603, 607, 622, 623, 624, 625, 626, 627,
            628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643,
            644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 671,
            695, 696, 697, 698, 699, 700, 701, 702, 703, 719, 723, 724, 725, 726, 727, 728,
            811, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10009, 10010, 10011,
            10012, 10013, 10014, 10015, 10016, 10017, 10018
        ]
        ignored_ids = list(set(immune_ids) | set(uncoded_ids))
        self.metronome_moves_raw = await find(self.ctx, "moves", {"id": {"$nin": ignored_ids}})
        for te in await find(self.ctx, "type_effectiveness", {}):
            self.type_effectiveness[(te["damage_type_id"], te["target_type_id"])] = te["damage_factor"]
        #This calculation only uses the primative speed attr as the pokes have not been fully initiaized yet.
        if self.trainer1.current_pokemon.get_raw_speed() > self.trainer2.current_pokemon.get_raw_speed():
            self.msg += self.trainer1.current_pokemon.send_out(self.trainer2.current_pokemon, self)
            self.msg += self.trainer2.current_pokemon.send_out(self.trainer1.current_pokemon, self)
        else:
            self.msg += self.trainer2.current_pokemon.send_out(self.trainer1.current_pokemon, self)
            self.msg += self.trainer1.current_pokemon.send_out(self.trainer2.current_pokemon, self)
        await self.send_msg()
        winner = None
        while True:
            # Swap pokes for any users w/o an active poke
            while self.trainer1.current_pokemon is None or self.trainer2.current_pokemon is None:
                swapped1 = False
                swapped2 = False
                
                if self.trainer1.current_pokemon is None:
                    swapped1 = True
                    winner = await self.run_swap(self.trainer1, self.trainer2)
                    if winner:
                        break
                
                if self.trainer2.current_pokemon is None:
                    swapped2 = True
                    winner = await self.run_swap(self.trainer2, self.trainer1)
                    if winner:
                        break
                
                # Send out the pokes that were just swapped to
                if swapped1 and swapped2:
                    if self.trainer1.current_pokemon.get_raw_speed() > self.trainer2.current_pokemon.get_raw_speed():
                        self.msg += self.trainer1.current_pokemon.send_out(self.trainer2.current_pokemon, self)
                        if not self.trainer1.has_alive_pokemon():
                            self.msg += f"{self.trainer2.name} wins!\n"
                            winner = self.trainer2
                            break
                        self.msg += self.trainer2.current_pokemon.send_out(self.trainer1.current_pokemon, self)
                        if not self.trainer2.has_alive_pokemon():
                            self.msg += f"{self.trainer1.name} wins!\n"
                            winner = self.trainer1
                            break
                    else:
                        self.msg += self.trainer2.current_pokemon.send_out(self.trainer1.current_pokemon, self)
                        if not self.trainer2.has_alive_pokemon():
                            self.msg += f"{self.trainer1.name} wins!\n"
                            winner = self.trainer1
                            break
                        self.msg += self.trainer1.current_pokemon.send_out(self.trainer2.current_pokemon, self)
                        if not self.trainer1.has_alive_pokemon():
                            self.msg += f"{self.trainer2.name} wins!\n"
                            winner = self.trainer2
                            break
                elif swapped1:
                    self.msg += self.trainer1.current_pokemon.send_out(self.trainer2.current_pokemon, self)
                    if not self.trainer1.has_alive_pokemon():
                        self.msg += f"{self.trainer2.name} wins!\n"
                        winner = self.trainer2
                        break
                elif swapped2:
                    self.msg += self.trainer2.current_pokemon.send_out(self.trainer1.current_pokemon, self)
                    if not self.trainer2.has_alive_pokemon():
                        self.msg += f"{self.trainer1.name} wins!\n"
                        winner = self.trainer1
                        break
            # Handle breaking out of the main game loop when a winner happens in the poke select loop
            if winner:
                break
            
            # Get trainer actions
            await self.send_msg()

            self.trainer1.event.clear()
            self.trainer2.event.clear()
            if not self.trainer1.is_human():
                self.trainer1.move(self.trainer2.current_pokemon, self)
            if not self.trainer2.is_human():
                self.trainer2.move(self.trainer1.current_pokemon, self)
            
            battle_view = await generate_main_battle_message(self)
            await self.trainer1.event.wait()
            await self.trainer2.event.wait()
            battle_view.stop()
            
            # Check for forfeits
            if self.trainer1.selected_action is None and self.trainer2.selected_action is None:
                await self.channel.send("Both players forfeited...")
                return #TODO: ???
            if self.trainer1.selected_action is None:
                self.msg += f"{self.trainer1.name} forfeited, {self.trainer2.name} wins!\n"
                winner = self.trainer2
                break
            if self.trainer2.selected_action is None:
                self.msg += f"{self.trainer2.name} forfeited, {self.trainer1.name} wins!\n"
                winner = self.trainer1
                break
            
            # Run setup for both pokemon
            t1, t2 = self.who_first()
            if t1.current_pokemon is not None and t2.current_pokemon is not None:
                if not isinstance(t1.selected_action, int):
                    self.msg += t1.selected_action.setup(t1.current_pokemon, t2.current_pokemon, self)
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            if t1.current_pokemon is not None and t2.current_pokemon is not None:
                if not isinstance(t2.selected_action, int):
                    self.msg += t2.selected_action.setup(t2.current_pokemon, t1.current_pokemon, self)
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            
            # Run moves for both pokemon
            # Trainer 1's move
            ran_megas = False
            if not isinstance(t1.selected_action, int):
                self.handle_megas(t1, t2)
                ran_megas = True
            
            if t1.current_pokemon is not None and t2.current_pokemon is not None:
                if isinstance(t1.selected_action, int):
                    self.msg += t1.current_pokemon.remove(self)
                    t1.switch_poke(t1.selected_action, mid_turn=True)
                    self.msg += t1.current_pokemon.send_out(t2.current_pokemon, self)
                    if t1.current_pokemon is not None:
                        t1.current_pokemon.has_moved = True
                else:
                    self.msg += t1.selected_action.use(t1.current_pokemon, t2.current_pokemon, self)
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            
            # Pokes who die do NOT get attacked, but pokes who retreat *do*
            if t1.current_pokemon is False:
                t1.current_pokemon = None
                winner = await self.run_swap(t1, t2, mid_turn=True)
                if winner:
                    break
                    
            # EDGE CASE - Poke uses a switch-out move like baton pass on a poke with magic bounce
            if t2.current_pokemon is False:
                t2.current_pokemon = None
            
            # EDGE CASE - Moves that DO NOT target the opponent (and swapping) SHOULD run 
            # even if there is no other poke on the field. Right now everything is hardcoded
            # to require two pokes to work, on a rewrite the `use` function should be the
            # one handling the job of checking if the attacked poke is `None` before using a
            # move that targets opponents.
            if (
                t1.current_pokemon is None and t2.current_pokemon is not None
                and (isinstance(t2.selected_action, int) or not t2.selected_action.targets_opponent())
            ):
                winner = await self.run_swap(t1, t2, mid_turn=True)
                if winner:
                    break
            
            self.msg += "\n"
            
            # Trainer 2's move
            if not ran_megas and not isinstance(t2.selected_action, int):
                self.handle_megas(t1, t2)
                ran_megas = True
            
            if t1.current_pokemon is not None and t2.current_pokemon is not None:
                if isinstance(t2.selected_action, int):
                    self.msg += t2.current_pokemon.remove(self)
                    t2.switch_poke(t2.selected_action, mid_turn=True)
                    self.msg += t2.current_pokemon.send_out(t1.current_pokemon, self)
                    if t2.current_pokemon is not None:
                        t2.current_pokemon.has_moved = True
                else:
                    self.msg += t2.selected_action.use(t2.current_pokemon, t1.current_pokemon, self)
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            
            self.msg += "\n"
            if t2.current_pokemon is False:
                t2.current_pokemon = None
                # This DOES need to be here, otherwise end of turn effects aren't handled right
                winner = await self.run_swap(t2, t1, mid_turn=True)
                if winner:
                    break
           
           #EDGE CASE - poke uses a switch-out move like baton pass on a poke with magic bounce
            if t1.current_pokemon is False:
                t1.current_pokemon = None
            
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            
            if not ran_megas:
                self.handle_megas(t1, t2)
            
            #Progress turns
            self.turn += 1
            self.plasma_fists = False
            if self.weather.next_turn():
                self.msg += "The weather cleared!\n"
            if self.terrain.next_turn():
                self.msg += "The terrain cleared!\n"
            self.last_move_effect = None
            t1, t2 = self.who_first(False)
            self.msg += t1.next_turn(self)
            if t1.current_pokemon is not None:
                self.msg += t1.current_pokemon.next_turn(t2.current_pokemon, self)
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            self.msg += t2.next_turn(self)
            if t2.current_pokemon is not None:
                self.msg += t2.current_pokemon.next_turn(t1.current_pokemon, self)
            if not t2.has_alive_pokemon():
                self.msg += f"{t1.name} wins!\n"
                winner = t1
                break
            if not t1.has_alive_pokemon():
                self.msg += f"{t2.name} wins!\n"
                winner = t2
                break
            if self.trick_room.next_turn():
                self.msg += "The Dimensions returned back to normal!\n"
            if self.gravity.next_turn():
                self.msg += "Gravity returns to normal!\n"
            if self.magic_room.next_turn():
                self.msg += "The room returns to normal, and held items regain their effect!\n"
            if self.wonder_room.next_turn():
                self.msg += "The room returns to normal, and stats swap back to what they were before!\n"

        #The game is over, and we broke out before sending, send the remaining cache
        await self.send_msg()
        return winner
        
    def who_first(self, check_move=True):
        """
        Determines which move should go.
        
        Returns the two trainers and their moves, in the order they should go.
        """
        T1FIRST = (self.trainer1, self.trainer2)
        T2FIRST = (self.trainer2, self.trainer1)
        
        if self.trainer1.current_pokemon is None or self.trainer2.current_pokemon is None:
            return T1FIRST 
        
        speed1 = self.trainer1.current_pokemon.get_speed(self)
        speed2 = self.trainer2.current_pokemon.get_speed(self)
        
        #Pokes that are switching go before pokes making other moves
        if check_move:
            if isinstance(self.trainer1.selected_action, int) and isinstance(self.trainer2.selected_action, int):
                if self.trainer1.current_pokemon.get_raw_speed() > self.trainer2.current_pokemon.get_raw_speed():
                    return T1FIRST
                return T2FIRST
            if isinstance(self.trainer1.selected_action, int):
                return T1FIRST
            if isinstance(self.trainer2.selected_action, int):
                return T2FIRST
        
        #Priority brackets & abilities
        if check_move:
            prio1 = self.trainer1.selected_action.get_priority(self.trainer1.current_pokemon, self.trainer2.current_pokemon, self)
            prio2 = self.trainer2.selected_action.get_priority(self.trainer2.current_pokemon, self.trainer1.current_pokemon, self)
            if prio1 > prio2:
                return T1FIRST
            if prio2 > prio1:
                return T2FIRST
            t1_quick = False
            t2_quick = False
            # Quick draw/claw
            if (
                self.trainer1.current_pokemon.ability() == Ability.QUICK_DRAW
                and self.trainer1.selected_action.damage_class != DamageClass.STATUS
                and random.randint(1, 100) <= 30
            ):
                t1_quick = True
            if (
                self.trainer2.current_pokemon.ability() == Ability.QUICK_DRAW
                and self.trainer2.selected_action.damage_class != DamageClass.STATUS
                and random.randint(1, 100) <= 30
            ):
                t2_quick = True
            if (
                self.trainer1.current_pokemon.held_item == "quick-claw"
                and random.randint(1, 100) <= 20
            ):
                t1_quick = True
            if (
                self.trainer2.current_pokemon.held_item == "quick-claw"
                and random.randint(1, 100) <= 20
            ):
                t2_quick = True
            #if both pokemon activate a quick, priority bracket proceeds as normal
            if t1_quick and not t2_quick:
                return T1FIRST
            if t2_quick and not t1_quick:
                return T2FIRST
            # Move last in prio bracket
            t1_slow = False
            t2_slow = False
            if self.trainer1.current_pokemon.ability() == Ability.STALL:
                t1_slow = True
            if (
                self.trainer1.current_pokemon.ability() == Ability.MYCELIUM_MIGHT
                and self.trainer1.selected_action.damage_class == DamageClass.STATUS
            ):
                t1_slow = True
            if self.trainer2.current_pokemon.ability() == Ability.STALL:
                t2_slow = True
            if (
                self.trainer2.current_pokemon.ability() == Ability.MYCELIUM_MIGHT
                and self.trainer2.selected_action.damage_class == DamageClass.STATUS
            ):
                t2_slow = True
            if t1_slow and t2_slow:
                if speed1 == speed2:
                    return random.choice([T1FIRST, T2FIRST])
                if speed1 > speed2:
                    return T2FIRST
                return T1FIRST
            if t1_slow:
                return T2FIRST
            if t2_slow:
                return T1FIRST
        
        #Equal speed
        if speed1 == speed2:
            return random.choice([T1FIRST, T2FIRST])
        
        #Trick room
        if self.trick_room.active():
            if speed1 > speed2:
                return T2FIRST
            return T1FIRST
        
        #Default handling
        if speed1 > speed2:
            return T1FIRST
        return T2FIRST
    
    async def send_msg(self):
        """
        Send the msg in a boilerplate embed.
        
        Handles the message being too long.
        """
        await generate_text_battle_message(self)
    
    async def run_swap(self, swapper, othertrainer, *, mid_turn=False):
        """
        Called when swapper does not have a pokemon selected, and needs a new one.
        
        Prompts the swapper to pick a pokemon.
        If mid_turn is set to True, the pokemon is being swapped in the middle of a turn (NOT at the start of a turn).
        Returns None if the trainer swapped, and the trainer that won if they did not.
        """
        await self.send_msg()

        swapper.event.clear()
        if swapper.is_human():
            swap_view = SwapPromptView(swapper, othertrainer, self, mid_turn=mid_turn)
            await self.channel.send(
                f"{swapper.name}, pick a pokemon to swap to!",
                view=swap_view
            )
        else:
            swapper.swap(othertrainer, self, mid_turn=mid_turn)
        
        try:
            await swapper.event.wait()
        except asyncio.TimeoutError:
            self.msg += f"{swapper.name} did not select a poke, {othertrainer.name} wins!\n"
            return othertrainer

        if swapper.is_human():
            swap_view.stop()

        if swapper.current_pokemon is None:
            self.msg += f"{swapper.name} did not select a poke, {othertrainer.name} wins!\n"
            return othertrainer
        
        if mid_turn:
            self.msg += swapper.current_pokemon.send_out(othertrainer.current_pokemon, self)
            if swapper.current_pokemon is not None:
                swapper.current_pokemon.has_moved = True
        
        return None
    
    def handle_megas(self, t1, t2):
        """Handle mega evolving pokemon who mega evolve this turn."""
        for at, dt in ((t1, t2), (t2, t1)):
            if at.current_pokemon is not None and at.current_pokemon.should_mega_evolve:
                # Bit of a hack, since it is in its mega form and dashes are removed from `name`, it will show as "<poke> mega evolved!".
                if (at.current_pokemon.held_item == "mega-stone" or at.current_pokemon._name == "Rayquaza") and at.current_pokemon.form(at.current_pokemon._name + "-mega"):
                    self.msg += f"{at.current_pokemon.name} evolved!\n"
                elif at.current_pokemon.held_item == "mega-stone-x" and at.current_pokemon.form(at.current_pokemon._name + "-mega-x"):
                    self.msg += f"{at.current_pokemon.name} evolved!\n"
                elif at.current_pokemon.held_item == "mega-stone-y" and at.current_pokemon.form(at.current_pokemon._name + "-mega-y"):
                    self.msg += f"{at.current_pokemon.name} evolved!\n"
                else:
                    raise ValueError("expected to mega evolve but no valid mega condition")
                at.current_pokemon.ability_id = at.current_pokemon.mega_ability_id
                at.current_pokemon.starting_ability_id = at.current_pokemon.mega_ability_id
                at.current_pokemon.type_ids = at.current_pokemon.mega_type_ids.copy()
                at.current_pokemon.starting_type_ids = at.current_pokemon.mega_type_ids.copy()
                self.msg += at.current_pokemon.send_out_ability(dt.current_pokemon, self)
                at.has_mega_evolved = True
    
    def __repr__(self):
        return f"Battle(trainer1={self.trainer1!r}, trainer2={self.trainer2!r})"
