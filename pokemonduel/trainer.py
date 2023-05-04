import discord
import asyncio
import random
from .enums import Ability, DamageClass, ElementType
from .misc import ExpiringEffect, ExpiringWish, ExpiringItem
from .move import Move


class Trainer():
    """
    Represents a genereric pokemon trainer.
    
    This class outlines the methods that Trainer objects 
    should have, but should not be used directly.
    """
    def __init__(self, name: str, party: list):
        self.name = name
        self.party = party
        self.current_pokemon = party[0] if len(party) > 0 else None
        for poke in self.party:
            poke.owner = self
        self.event = asyncio.Event()
        self.selected_action = None
        self.baton_pass = None
        #Int - Stacks of spikes on this trainer's side of the field
        self.spikes = 0
        #Int - Stacks of toxic spikes on this trainer's side of the field
        self.toxic_spikes = 0
        #Boolean - Whether stealth rocks are on this trainer's side of the field
        self.stealth_rock = False
        #Boolean - Whether a sticky web is on this trainer's side of the field
        self.sticky_web = False
        #Int - The last index of self.party that was selected
        self.last_idx = 0
        self.wish = ExpiringWish()
        self.aurora_veil = ExpiringEffect(0)
        self.light_screen = ExpiringEffect(0)
        self.reflect = ExpiringEffect(0)
        self.mist = ExpiringEffect(0)
        #ExpiringEffect - Stores the number of turns that pokes are protected from NV effects
        self.safeguard = ExpiringEffect(0)
        #Boolean - Whether the next poke to swap in should be restored via healing wish
        self.healing_wish = False
        #Boolean - Whether the next poke to swap in should be restored via lunar dance
        self.lunar_dance = False
        #ExpiringEffect - Stores the number of turns that pokes have doubled speed
        self.tailwind = ExpiringEffect(0)
        #ExpiringEffect - Stores the number of turns that electric moves have 1/3 power
        self.mud_sport = ExpiringEffect(0)
        #ExpiringEffect - Stores the number of turns that fire moves have 1/3 power
        self.water_sport = ExpiringEffect(0)
        #ExpiringEffect - Stores the fact that a party member recently fainted.
        self.retaliate = ExpiringEffect(0)
        #ExpiringItem - Stores the turns until future sight attacks this trainer's pokemon.
        self.future_sight = ExpiringItem()
        #Boolean - Whether or not any of this trainer's pokemon have mega evolved yet this battle.
        self.has_mega_evolved = False
        #Int - Stores the number of times a pokemon in this trainer's party has fainted, including after being revived.
        self.num_fainted = 0
        #Int - Stores the HP of the subsitute this trainer's next pokemon on the field will receive.
        self.next_substitute = 0

    def has_alive_pokemon(self) -> bool:
        """Returns True if this trainer still has at least one pokemon that is alive."""
        return any((poke.hp > 0 for poke in self.party))
    
    def next_turn(self, battle):
        """
        Updates this trainer for a new turn.
        
        Returns a formatted message.
        """
        msg = ""
        self.selected_action = None
        hp = self.wish.next_turn()
        if hp and self.current_pokemon is not None:
            msg += self.current_pokemon.heal(hp, source="its wish")
        if self.aurora_veil.next_turn():
            msg += f"{self.name}'s aurora veil wore off!\n"
        if self.light_screen.next_turn():
            msg += f"{self.name}'s light screen wore off!\n"
        if self.reflect.next_turn():
            msg += f"{self.name}'s reflect wore off!\n"
        if self.mist.next_turn():
            msg += f"{self.name}'s mist wore off!\n"
        if self.safeguard.next_turn():
            msg += f"{self.name}'s safeguard wore off!\n"
        if self.tailwind.next_turn():
            msg += f"{self.name}'s tailwind died down!\n"
        if self.mud_sport.next_turn():
            msg += f"{self.name}'s mud sport wore off!\n"
        if self.water_sport.next_turn():
            msg += f"{self.name}'s water sport evaporated!\n"  
        self.retaliate.next_turn()
        future_sight_data = self.future_sight.item
        if self.future_sight.next_turn() and self.current_pokemon is not None:
            msg += f"{self.current_pokemon.name} took the future sight attack!\n"
            future_sight_attacker, future_sight_move = future_sight_data
            msgadd, _ = future_sight_move.attack(future_sight_attacker, self.current_pokemon, battle)
            msg += msgadd
        return msg
    
    def switch_poke(self, slot: int, *, mid_turn=False):
        """Switch the currently active poke to the given slot."""
        if slot < 0 or slot >= len(self.party):
            raise ValueError("out of bounds")
        if not self.party[slot].hp > 0:
            raise ValueError("no hp")
        self.current_pokemon = self.party[slot]
        self.last_idx = slot
        if mid_turn:
            self.current_pokemon.swapped_in = True
    
    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        raise NotImplementedError()
        
    def valid_swaps(self, defender, battle, *, check_trap=True):
        """Returns a list of indexes of pokes in the party that can be swapped to."""
        if self.current_pokemon is not None and ElementType.GHOST in self.current_pokemon.type_ids:
            check_trap = False
        if check_trap and self.current_pokemon is not None:
            if self.current_pokemon.trapping:
                return []
            if self.current_pokemon.ingrain:
                return []
            if self.current_pokemon.fairy_lock.active() or defender.fairy_lock.active():
                return []
            if self.current_pokemon.no_retreat:
                return []
            if self.current_pokemon.bind.active() and not self.current_pokemon.substitute:
                return []
            if defender.ability() == Ability.SHADOW_TAG and not self.current_pokemon.ability() == Ability.SHADOW_TAG:
                return []
            if defender.ability() == Ability.MAGNET_PULL and ElementType.STEEL in self.current_pokemon.type_ids:
                return []
            if defender.ability() == Ability.ARENA_TRAP and self.current_pokemon.grounded(battle):
                return []
        result = [idx for idx, poke in enumerate(self.party) if poke.hp > 0]
        if self.last_idx in result:
            result.remove(self.last_idx)
        return result
    
    def valid_moves(self, defender):
        """
        https://www.smogon.com/dp/articles/move_restrictions
        
        Returns
        - ("forced", Move) - The move-action this trainer is FORCED to use.
        - ("idxs", List[int]) - The indexes of moves that are valid to CHOOSE to use.
        - ("struggle", List[int]) - If the user attempts to use any move, use struggle instead (no valid moves).
        """
        # Check if they are FORCED to use a certain move
        if self.current_pokemon.locked_move:
            return ("forced", self.current_pokemon.locked_move.move)
        # Remove all moves not matching a restriction
        result = []
        for idx, move in enumerate(self.current_pokemon.moves):
            if move.pp <= 0:
                continue
            if move.damage_class == DamageClass.STATUS and self.current_pokemon.held_item == "assault-vest":
                continue
            if move.damage_class == DamageClass.STATUS and self.current_pokemon.taunt.active():
                continue
            if move.effect == 247 and not all(m.used for m in self.current_pokemon.moves if m.effect != 247):
                continue
            if self.current_pokemon.disable.active() and move is self.current_pokemon.disable.item:
                continue
            if self.current_pokemon.held_item in ("choice-scarf", "choice-band", "choice-specs") or self.current_pokemon.ability() == Ability.GORILLA_TACTICS:
                if self.current_pokemon.choice_move is not None and move is not self.current_pokemon.choice_move:
                    continue
            if self.current_pokemon.torment and self.current_pokemon.last_move is move:
                continue
            if (
                self.current_pokemon.last_move is not None
                and self.current_pokemon.last_move.effect == 492
                and self.current_pokemon.last_move.id == move.id
                and not self.current_pokemon.last_move_failed
            ):
                continue
            if defender.imprison and move.id in [x.id for x in defender.moves]:
                continue
            if self.current_pokemon.heal_block.active() and move.is_affected_by_heal_block():
                continue
            if self.current_pokemon.silenced.active() and move.is_sound_based():
                continue
            if move.effect == 339 and not self.current_pokemon.ate_berry:
                continue
            if move.effect == 453 and not self.current_pokemon.held_item.is_berry():
                continue
            if self.current_pokemon.encore.active() and move is not self.current_pokemon.encore.item:
                continue
            result.append(idx)
        if not result:
            return ("struggle", [0, 1, 2, 3])
        return ("idxs", result)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, party={self.party!r})"

class MemberTrainer(Trainer):
    """
    Represents a pokemon trainer that is a discord.Member.
    """
    def __init__(self, member: discord.Member, party):
        super().__init__(member.name, party)
        self.id = member.id
        self.member = member
    
    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        return True

class NPCTrainer(Trainer):
    """
    Represents a pokemon trainer that is a NPC.
    """
    def __init__(self, party):
        super().__init__("Trainer John", party)
    
    def move(self, defender, battle):
        """Request a normal move from this trainer AI."""
        status_code, movedata = self.valid_moves(defender)
        if status_code == "forced":
            self.selected_action = movedata
        elif status_code == "struggle":
            self.selected_action = Move.struggle()
        else:
            self.selected_action = self.current_pokemon.moves[random.choice(movedata)]
        self.event.set()
        #TODO: npc ai?
    
    def swap(self, defender, battle, *, mid_turn=False):
        """Request a swap choice from this trainer AI."""
        poke_idx = random.choice(self.valid_swaps(defender, battle, check_trap=False))
        self.switch_poke(poke_idx, mid_turn=mid_turn)
        self.event.set()
        #TODO: npc ai?
    
    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        return False
