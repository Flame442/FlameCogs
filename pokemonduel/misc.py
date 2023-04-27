import random
from .enums import Ability, ElementType


class ExpiringEffect():
    """
    Some effect that has a specific amount of time it is active.
    
    turns_to_expire can be None, in which case this effect never expires.
    """
    def __init__(self, turns_to_expire: int):
        self._remaining_turns = turns_to_expire
    
    def active(self):
        """Returns True if this effect is still active, False otherwise."""
        if self._remaining_turns is None:
            return True
        return bool(self._remaining_turns)
    
    def next_turn(self):
        """
        Progresses this effect for a turn.
        
        Returns True if the effect just ended.
        """
        if self._remaining_turns is None:
            return False
        if self.active():
            self._remaining_turns -= 1
            return not self.active()
        return False
    
    def set_turns(self, turns_to_expire):
        """Set the amount of turns until this effect expires."""
        self._remaining_turns = turns_to_expire


class Weather(ExpiringEffect):
    """
    The current weather of the battlefield.
    
    Options:
    -hail
    -sandstorm
    -h-rain
    -rain
    -h-sun
    -sun
    -h-wind
    """
    def __init__(self, battle):
        super().__init__(0)
        self._weather_type = ""
        self.battle = battle

    def _expire_weather(self):
        """Clear the current weather and update Castform forms."""
        self._weather_type = ""
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            # Forecast
            if poke.ability() == Ability.FORECAST and poke._name in ("Castform-snowy", "Castform-rainy", "Castform-sunny"):
                if poke.form("Castform"):
                    poke.type_ids = [ElementType.NORMAL]
    
    def next_turn(self):
        """Progresses the weather a turn."""
        if super().next_turn():
            self._expire_weather()
            return True
        return False
    
    def recheck_ability_weather(self):
        """Checks if strong weather effects from a pokemon with a weather ability need to be removed."""
        maintain_weather = False
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if self._weather_type == "h-wind" and poke.ability() == Ability.DELTA_STREAM:
                maintain_weather = True
            if self._weather_type == "h-sun" and poke.ability() == Ability.DESOLATE_LAND:
                maintain_weather = True
            if self._weather_type == "h-rain" and poke.ability() == Ability.PRIMORDIAL_SEA:
                maintain_weather = True
        
        if self._weather_type in ("h-wind", "h-sun", "h-rain") and not maintain_weather:
            self._expire_weather()
            return True
        return False
    
    def get(self):
        """Get the current weather type."""
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() in (Ability.CLOUD_NINE, Ability.AIR_LOCK):
                return ""
        return self._weather_type
    
    def set(self, weather: str, pokemon):
        """
        Set the weather, lasting a certain number of turns.
        
        Returns a formatted message indicating any weather change.
        """
        msg = ""
        turns = None
        element = None
        castform = None
        if self._weather_type == weather:
            return ""
        if weather == "hail":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "icy-rock":
                turns = 8
            else:
                turns = 5
            msg += "It starts to hail!\n"
            element = ElementType.ICE
            castform = "Castform-snowy"
        elif weather == "sandstorm":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "smooth-rock":
                turns = 8
            else:
                turns = 5
            msg += "A sandstorm is brewing up!\n"
            element = ElementType.NORMAL
            castform = "Castform"
        elif weather == "rain":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "damp-rock":
                turns = 8
            else:
                turns = 5
            msg += "It starts to rain!\n"
            element = ElementType.WATER
            castform = "Castform-rainy"
        elif weather == "sun":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "heat-rock":
                turns = 8
            else:
                turns = 5
            msg += "The sunlight is strong!\n"
            element = ElementType.FIRE
            castform = "Castform-sunny"
        elif weather == "h-rain":
            msg += "Heavy rain begins to fall!\n"
            element = ElementType.WATER
            castform = "Castform-rainy"
        elif weather == "h-sun":
            msg += "The sunlight is extremely harsh!\n"
            element = ElementType.FIRE
            castform = "Castform-sunny"
        elif weather == "h-wind":
            msg += "The winds are extremely strong!\n"
            element = ElementType.NORMAL
            castform = "Castform"
        else:
            raise ValueError("unexpected weather")
        
        # Forecast
        t = ElementType(element).name.lower()
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.FORECAST and poke._name != castform:
                if poke.form(castform):
                    poke.type_ids = [element]
                    msg += f"{poke.name} transformed into a {t} type using its forecast!\n"
        
        self._weather_type = weather
        self._remaining_turns = turns
        return msg


class LockedMove(ExpiringEffect):
    """A multi-turn move that a pokemon is locked into."""
    def __init__(self, move, turns_to_expire: int):
        super().__init__(turns_to_expire)
        self.move = move
        self.turn = 0
    
    def next_turn(self):
        """Progresses the move a turn."""
        expired = super().next_turn()
        self.turn += 1
        return expired
    
    def is_last_turn(self):
        """Returns True if this is the last turn this move will be used."""
        return self._remaining_turns == 1


class ExpiringItem(ExpiringEffect):
    """An expiration timer with some data."""
    def __init__(self):
        super().__init__(0)
        self.item = None
    
    def next_turn(self):
        """Progresses the effect a turn."""
        expired = super().next_turn()
        if expired:
            self.item = None
        return expired
    
    def set(self, item, turns: int):
        """Set the item and turns until expiration."""
        self.item = item
        self._remaining_turns = turns
    
    def end(self):
        """Ends this expiring item."""
        self.item = None
        self._remaining_turns = 0


class Terrain(ExpiringItem):
    """The terrain of the battle"""
    def __init__(self, battle):
        super().__init__()
        self.battle = battle
    
    def next_turn(self):
        """Progresses the effect a turn."""
        expired = super().next_turn()
        if expired:
            self.end()
        return expired
    
    def set(self, item, attacker):
        """
        Set the terrain and turns until expiration.
        
        Returns a formatted string.
        """
        if item == self.item:
            return f"There's already a {item} terrain!\n"
        turns = 8 if attacker.held_item == "terrain-extender" else 5
        super().set(item, turns)
        msg = f"{attacker.name} creates a{'n' if item == 'electric' else ''} {item} terrain!\n"
        # Mimicry
        element = None
        if item == "electric":
            element = ElementType.ELECTRIC
        elif item == "grassy":
            element = ElementType.GRASS
        elif item == "misty":
            element = ElementType.FAIRY
        elif item == "psychic":
            element = ElementType.PSYCHIC
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.MIMICRY:
                poke.type_ids = [element]
                t = ElementType(element).name.lower()
                msg += f"{poke.name} became a {t} type using its mimicry!\n"
            if poke.held_item == "electric-seed" and item == "electric":
                msg += poke.append_defense(1, attacker=poke, source="its electric seed")
                poke.held_item.use()
            if poke.held_item == "psychic-seed" and item == "psychic":
                msg += poke.append_spdef(1, attacker=poke, source="its psychic seed")
                poke.held_item.use()
            if poke.held_item == "misty-seed" and item == "misty":
                msg += poke.append_spdef(1, attacker=poke, source="its misty seed")
                poke.held_item.use()
            if poke.held_item == "grassy-seed" and item == "grassy":
                msg += poke.append_defense(1, attacker=poke, source="its grassy seed")
                poke.held_item.use()
        return msg
    
    def end(self):
        """Ends the terrain."""
        super().end()
        # Mimicry
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.MIMICRY:
                poke.type_ids = poke.starting_type_ids.copy()


class ExpiringWish(ExpiringEffect):
    """Stores the HP and when to heal for the move Wish."""
    def __init__(self):
        super().__init__(0)
        self.hp = None
    
    def next_turn(self):
        """Progresses the effect a turn."""
        expired = super().next_turn()
        hp = 0
        if expired:
            hp = self.hp
            self.hp = None
        return hp
    
    def set(self, hp):
        """Set the move and turns until expiration."""
        self.hp = hp
        self._remaining_turns = 2


class NonVolatileEffect():
    """The current non volatile effect status."""
    def __init__(self, pokemon):
        self.current = ""
        self.pokemon = pokemon
        self.sleep_timer = ExpiringEffect(0)
        self.badly_poisoned_turn = 0
    
    def next_turn(self, battle):
        """
        Progresses this status by a turn.
        
        Returns a formatted string if a status wore off.
        """
        if not self.current:
            return ""
        if self.current == "b-poison":
            self.badly_poisoned_turn += 1
        if self.pokemon.ability() == Ability.HYDRATION and battle.weather.get() in ("rain", "h-rain"):
            removed = self.current
            self.reset()
            return f"{self.pokemon.name}'s hydration cured its {removed}!\n"
        if self.pokemon.ability() == Ability.SHED_SKIN and not random.randint(0, 2):
            removed = self.current
            self.reset()
            return f"{self.pokemon.name}'s shed skin cured its {removed}!\n"
        # The poke still has a status effect, apply damage
        if self.current == "burn":
            damage = max(1, self.pokemon.starting_hp // 16)
            if self.pokemon.ability() == Ability.HEATPROOF:
                damage //= 2
            return self.pokemon.damage(damage, battle, source="its burn")
        if self.current == "b-poison":
            if self.pokemon.ability() == Ability.POISON_HEAL:
                return self.pokemon.heal(self.pokemon.starting_hp // 8, source="its poison heal")
            damage = max(1, (self.pokemon.starting_hp // 16) * min(15, self.badly_poisoned_turn))
            return self.pokemon.damage(damage, battle, source="its bad poison")
        if self.current == "poison":
            if self.pokemon.ability() == Ability.POISON_HEAL:
                return self.pokemon.heal(self.pokemon.starting_hp // 8, source="its poison heal")
            damage = max(1, self.pokemon.starting_hp // 8)
            return self.pokemon.damage(damage, battle, source="its poison")
        if self.current == "sleep" and self.pokemon.nightmare:
            return self.pokemon.damage(self.pokemon.starting_hp // 4, battle, source="its nightmare")
        return ""

    def burn(self):
        """Returns True if the pokemon is burned."""
        return self.current == "burn"
        
    def sleep(self):
        """Returns True if the pokemon is asleep."""
        if self.pokemon.ability() == Ability.COMATOSE:
            return True
        return self.current == "sleep"
        
    def poison(self):
        """Returns True if the pokemon is poisoned."""
        return self.current in ("poison", "b-poison")
    
    def paralysis(self):
        """Returns True if the pokemon is paralyzed."""
        return self.current == "paralysis"
        
    def freeze(self):
        """Returns True if the pokemon is frozen."""
        return self.current == "freeze"
    
    def apply_status(self, status, battle, *, attacker=None, move=None, turns=None, force=False, source: str=""):
        """
        Apply a non volatile status to a pokemon.
        
        Returns a formatted message.
        """
        msg = ""
        if source:
            source = f" from {source}"
        if self.current and not force:
            return f"{self.pokemon.name} already has a status, it can't get {status} too!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.COMATOSE:
            return f"{self.pokemon.name} already has a status, it can't get {status} too!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.PURIFYING_SALT:
            return f"{self.pokemon.name}'s purifying salt protects it from being inflicted with {status}!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.LEAF_GUARD and battle.weather.get() in ("sun", "h-sun"):
            return f"{self.pokemon.name}'s leaf guard protects it from being inflicted with {status}!\n"
        if self.pokemon.substitute and attacker is not self.pokemon:
            return f"{self.pokemon.name}'s substitute protects it from being inflicted with {status}!\n"
        if self.pokemon.owner.safeguard.active() and attacker is not self.pokemon and (attacker is None or attacker.ability() != Ability.INFILTRATOR):
            return f"{self.pokemon.name}'s safeguard protects it from being inflicted with {status}!\n"
        if self.pokemon.grounded(battle, attacker=attacker, move=move) and battle.terrain.item == "misty":
            return f"The misty terrain protects {self.pokemon.name} from being inflicted with {status}!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.FLOWER_VEIL and ElementType.GRASS in self.pokemon.type_ids:
            return f"{self.pokemon.name}'s flower veil protects it from being inflicted with {status}!\n"
        if self.pokemon._name == "Minior":
            return "Minior's hard shell protects it from status effects!\n"
        if status == "burn":
            if ElementType.FIRE in self.pokemon.type_ids:
                return f"{self.pokemon.name} is a fire type and can't be burned!\n"
            if self.pokemon.ability(attacker=attacker, move=move) in (Ability.WATER_VEIL, Ability.WATER_BUBBLE):
                ability_name = Ability(self.pokemon.ability_id).pretty_name
                return f"{self.pokemon.name}'s {ability_name} prevents it from getting burned!\n"
            self.current = status
            msg += f"{self.pokemon.name} was burned{source}!\n"
        if status == "sleep":
            if self.pokemon.ability(attacker=attacker, move=move) in (Ability.INSOMNIA, Ability.VITAL_SPIRIT, Ability.SWEET_VEIL):
                ability_name = Ability(self.pokemon.ability_id).pretty_name
                return f"{self.pokemon.name}'s {ability_name} keeps it awake!\n"
            if self.pokemon.grounded(battle, attacker=attacker, move=move) and battle.terrain.item == "electric":
                return f"The terrain is too electric for {self.pokemon.name} to fall asleep!\n"
            if battle.trainer1.current_pokemon and battle.trainer1.current_pokemon.uproar.active():
                return f"An uproar keeps {self.pokemon.name} from falling asleep!\n"
            if battle.trainer2.current_pokemon and battle.trainer2.current_pokemon.uproar.active():
                return f"An uproar keeps {self.pokemon.name} from falling asleep!\n"
            if turns is None:
                turns = random.randint(2, 4)
            if self.pokemon.ability(attacker=attacker, move=move) == Ability.EARLY_BIRD:
                turns //= 2
            self.current = status
            self.sleep_timer.set_turns(turns)
            msg += f"{self.pokemon.name} fell asleep{source}!\n"
        if status in ("poison", "b-poison"):
            if attacker is None or attacker.ability() != Ability.CORROSION:
                if ElementType.STEEL in self.pokemon.type_ids:
                    return f"{self.pokemon.name} is a steel type and can't be poisoned!\n"
                if ElementType.POISON in self.pokemon.type_ids:
                    return f"{self.pokemon.name} is a poison type and can't be poisoned!\n"
            if self.pokemon.ability(attacker=attacker, move=move) in (Ability.IMMUNITY, Ability.PASTEL_VEIL):
                ability_name = Ability(self.pokemon.ability_id).pretty_name
                return f"{self.pokemon.name}'s {ability_name} keeps it from being poisoned!\n"
            self.current = status
            bad = " badly" if status == "b-poison" else ""
            msg += f"{self.pokemon.name} was{bad} poisoned{source}!\n"
        if status == "paralysis":
            if ElementType.ELECTRIC in self.pokemon.type_ids:
                return f"{self.pokemon.name} is an electric type and can't be paralyzed!\n"
            if self.pokemon.ability(attacker=attacker, move=move) == Ability.LIMBER:
                return f"{self.pokemon.name}'s limber keeps it from being paralyzed!\n"
            self.current = status
            msg += f"{self.pokemon.name} was paralyzed{source}!\n"
        if status == "freeze":
            if ElementType.ICE in self.pokemon.type_ids:
                return f"{self.pokemon.name} is an ice type and can't be frozen!\n"
            if self.pokemon.ability(attacker=attacker, move=move) == Ability.MAGMA_ARMOR:
                return f"{self.pokemon.name}'s magma armor keeps it from being frozen!\n"
            if battle.weather.get() in ("sun", "h-sun"):
                return f"It's too sunny to freeze {self.pokemon.name}!\n"
            self.current = status
            msg += f"{self.pokemon.name} was frozen solid{source}!\n"
        
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.SYNCHRONIZE and attacker is not None:
            msg += attacker.nv.apply_status(status, battle, attacker=self.pokemon, source=f"{self.pokemon.name}'s synchronize")
        
        if self.pokemon.held_item.should_eat_berry_status(attacker):
            msg += self.pokemon.held_item.eat_berry(attacker=attacker, move=move)
        
        return msg
    
    def reset(self):
        """Remove a non volatile status from a pokemon."""
        self.current = ""
        self.badly_poisoned_turn = 0
        self.sleep_timer.set_turns(0)
        self.pokemon.nightmare = False


class Metronome():
    """Holds recent move status for the held item metronome."""
    def __init__(self):
        self.move = ""
        self.count = 0
    
    def reset(self):
        """A move failed or a non-move action was done."""
        self.move = ""
        self.count = 0
    
    def use(self, movename):
        """Updates the metronome based on a used move."""
        if self.move == movename:
            self.count += 1
        else:
            self.move = movename
            self.count = 1
    
    def get_buff(self, movename):
        """Get the buff multiplier for this metronome."""
        if self.move != movename:
            return 1
        return min(2, 1 + (.2 * self.count))


class Item():
    """Stores information about an item."""
    def __init__(self, item_data):
        self.name = item_data["identifier"]
        self.id = item_data["id"]
        self.power = item_data["fling_power"]
        self.effect = item_data["fling_effect_id"]

class HeldItem():
    """Stores information about the current held item for a particualar poke."""
    def __init__(self, item_data, owner):
        if item_data is None:
            self.item = None
        else:
            self.item = Item(item_data)
        self.owner = owner
        self.battle = None
        self.last_used = None
        self.ever_had_item = self.item is not None
    
    def get(self):
        """Get the current held item identifier."""
        if self.item is None:
            return None
        if not self.can_remove():
            return self.item.name
        if self.owner.embargo.active():
            return None
        if self.battle and self.battle.magic_room.active():
            return None
        if self.owner.ability() == Ability.KLUTZ:
            return None
        if self.owner.corrosive_gas:
            return None
        return self.item.name
    
    def has_item(self):
        """Helper method to prevent attempting to acquire a new item if the poke already has one."""
        return self.item is not None
    
    def can_remove(self):
        """Returns a boolean indicating whether this held item can be removed."""
        return self.name not in (
            # Plates
            "draco-plate", "dread-plate", "earth-plate", "fist-plate", "flame-plate", "icicle-plate",
            "insect-plate", "iron-plate", "meadow-plate", "mind-plate", "pixie-plate", "sky-plate",
            "splash-plate", "spooky-plate", "stone-plate", "toxic-plate", "zap-plate",
            # Memories
            "dragon-memory", "dark-memory", "ground-memory", "fighting-memory", "fire-memory",
            "ice-memory", "bug-memory", "steel-memory", "grass-memory", "psychic-memory",
            "fairy-memory", "flying-memory", "water-memory", "ghost-memory", "rock-memory",
            "poison-memory", "electric-memory",
            # Misc
            "primal-orb", "griseous-orb", "blue-orb", "red-orb", "rusty-sword", "rusty-shield",
            # Mega Stones
            "mega-stone", "mega-stone-x", "mega-stone-y",
        )
    
    def is_berry(self, *, only_active=True):
        """
        Returns a boolean indicating whether this held item is a berry.
        
        The optional param only_active determines if this method should only return True if the berry is active and usable.
        """
        if only_active:
            return self.get() is not None and self.get().endswith("-berry")
        return self.name is not None and self.name.endswith("-berry")
    
    def remove(self):
        """Remove this held item, setting it to None."""
        if not self.can_remove():
            raise ValueError(f"{self.name} cannot be removed.")
        self.item = None
    
    def use(self):
        """Uses this item, setting it to None but also recording that it was used."""
        if not self.can_remove():
            raise ValueError(f"{self.name} cannot be removed.")
        self.last_used = self.item
        self.owner.choice_move = None
        self.remove()
    
    def transfer(self, other):
        """Transfer the data of this held item to other, and clear this item."""
        if not self.can_remove():
            raise ValueError(f"{self.name} cannot be removed.")
        if not other.can_remove():
            raise ValueError(f"{other.name} cannot be removed.")
        other.item = self.item
        self.remove()
    
    def swap(self, other):
        """Swap the date between this held item and other."""
        if not self.can_remove():
            raise ValueError(f"{self.name} cannot be removed.")
        if not other.can_remove():
            raise ValueError(f"{other.name} cannot be removed.")
        self.item, other.item = other.item, self.item
        self.owner.choice_move = None
        other.owner.choice_move = None
        self.ever_had_item = self.ever_had_item or self.item is not None
    
    def recover(self, other):
        """Recover & claim the last_used item from other."""
        self.item = other.last_used
        other.last_used = None
        self.ever_had_item = self.ever_had_item or self.item is not None
    
    def _should_eat_berry_util(self, otherpoke=None):
        """Util for all the things that are shared between the different kinds of berry."""
        if self.owner.hp == 0:
            return False
        if otherpoke is not None and otherpoke.ability() in (Ability.UNNERVE, Ability.AS_ONE_SHADOW, Ability.AS_ONE_ICE): #TODO: idk make this check better...
            return False
        if not self.is_berry():
            return False
        return True
    
    def should_eat_berry_damage(self, otherpoke=None):
        """Returns True if the pokemon meets the criteria to eat its held berry after being damaged."""
        if not self._should_eat_berry_util(otherpoke):
            return False
        if self.owner.hp <= self.owner.starting_hp / 4:
            if self in (
                # HP berries
                "figy-berry", "wiki-berry", "mago-berry", "aguav-berry", "iapapa-berry",
                # Stat berries
                "apicot-berry", "ganlon-berry", "lansat-berry", "liechi-berry", "micle-berry", "petaya-berry", "salac-berry", "starf-berry",
            ):
                return True
        if self.owner.hp <= self.owner.starting_hp / 2:
            if self.owner.ability() == Ability.GLUTTONY:
                return True
            if self == "sitrus-berry":
                return True
        return False
    
    def should_eat_berry_status(self, otherpoke=None):
        """Returns True if the pokemon meets the criteria to eat its held berry after getting a status."""
        if not self._should_eat_berry_util(otherpoke):
            return False
        if self in ("aspear-berry", "lum-berry") and self.owner.nv.freeze():
            return True
        if self in ("cheri-berry", "lum-berry") and self.owner.nv.paralysis():
            return True
        if self in ("chesto-berry", "lum-berry") and self.owner.nv.sleep():
            return True
        if self in ("pecha-berry", "lum-berry") and self.owner.nv.poison():
            return True
        if self in ("rawst-berry", "lum-berry") and self.owner.nv.burn():
            return True
        if self in ("persim-berry", "lum-berry") and self.owner.confusion.active():
            return True
        return False
    
    def should_eat_berry(self, otherpoke=None):
        """Returns True if the pokemon meets the criteria to eat its held berry."""
        return self.should_eat_berry_damage(otherpoke) or self.should_eat_berry_status(otherpoke)
    
    def eat_berry(self, *, consumer=None, attacker=None, move=None):
        """
        Eat this held item berry.
        
        Returns a formatted message.
        """
        msg = ""
        if not self.is_berry():
            return ""
        if consumer is None:
            consumer = self.owner
        else:
            msg += f"{consumer.name} eats {self.owner.name}'s berry!\n"
        
        # 2x or 1x
        ripe = int(consumer.ability(attacker=attacker, move=move) == Ability.RIPEN) + 1
        flavor = None
        
        if self == "sitrus-berry":
            msg += consumer.heal((ripe * consumer.starting_hp) // 4, source="eating its berry")
        elif self == "figy-berry":
            msg += consumer.heal((ripe * consumer.starting_hp) // 3, source="eating its berry")
            flavor = "spicy"
        elif self == "wiki-berry":
            msg += consumer.heal((ripe * consumer.starting_hp) // 3, source="eating its berry")
            flavor = "dry"
        elif self == "mago-berry":
            msg += consumer.heal((ripe * consumer.starting_hp) // 3, source="eating its berry")
            flavor = "sweet"
        elif self == "aguav-berry":
            msg += consumer.heal((ripe * consumer.starting_hp) // 3, source="eating its berry")
            flavor = "bitter"
        elif self == "iapapa-berry":
            msg += consumer.heal((ripe * consumer.starting_hp) // 3, source="eating its berry")
            flavor = "sour"
        elif self == "apicot-berry":
            msg += consumer.append_spdef(ripe * 1, attacker=attacker, move=move, source="eating its berry")
        elif self == "ganlon-berry":
            msg += consumer.append_defense(ripe * 1, attacker=attacker, move=move, source="eating its berry")
        elif self == "lansat-berry":
            consumer.lansat_berry_ate = True
            msg += f"{consumer.name} is powered up by eating its berry.\n"
        elif self == "liechi-berry":
            msg += consumer.append_attack(ripe * 1, attacker=attacker, move=move, source="eating its berry")
        elif self == "micle-berry":
            consumer.micle_berry_ate = True
            msg += f"{consumer.name} is powered up by eating its berry.\n"
        elif self == "petaya-berry":
            msg += consumer.append_spatk(ripe * 1, attacker=attacker, move=move, source="eating its berry")
        elif self == "salac-berry":
            msg += consumer.append_speed(ripe * 1, attacker=attacker, move=move, source="eating its berry")
        elif self == "starf-berry":
            funcs = [
                consumer.append_attack,
                consumer.append_defense,
                consumer.append_spatk,
                consumer.append_spdef,
                consumer.append_speed,
            ]
            func = random.choice(funcs)
            msg += func(ripe * 2, attacker=attacker, move=move, source="eating its berry")
        elif self == "aspear-berry":
            if consumer.nv.freeze():
                consumer.nv.reset()
                msg += f"{consumer.name} is no longer frozen after eating its berry!\n"
            else:
                msg += f"{consumer.name}'s berry had no effect!\n"
        elif self == "cheri-berry":
            if consumer.nv.paralysis():
                consumer.nv.reset()
                msg += f"{consumer.name} is no longer paralyzed after eating its berry!\n"
            else:
                msg += f"{consumer.name}'s berry had no effect!\n"
        elif self == "chesto-berry":
            if consumer.nv.sleep():
                consumer.nv.reset()
                msg += f"{consumer.name} woke up after eating its berry!\n"
            else:
                msg += f"{consumer.name}'s berry had no effect!\n"
        elif self == "pecha-berry":
            if consumer.nv.poison():
                consumer.nv.reset()
                msg += f"{consumer.name} is no longer poisoned after eating its berry!\n"
            else:
                msg += f"{consumer.name}'s berry had no effect!\n"
        elif self == "rawst-berry":
            if consumer.nv.burn():
                consumer.nv.reset()
                msg += f"{consumer.name} is no longer burned after eating its berry!\n"
            else:
                msg += f"{consumer.name}'s berry had no effect!\n"
        elif self == "persim-berry":
            if consumer.confusion.active():
                consumer.confusion.set_turns(0)
                msg += f"{consumer.name} is no longer confused after eating its berry!\n"
            else:
                msg += f"{consumer.name}'s berry had no effect!\n"
        elif self == "lum-berry":
            consumer.nv.reset()
            consumer.confusion.set_turns(0)
            msg += f"{consumer.name}'s statuses were cleared from eating its berry!\n"
        
        if flavor is not None and consumer.disliked_flavor == flavor:
            msg += consumer.confuse(attacker=attacker, move=move, source="disliking its berry's flavor")
        if consumer.ability(attacker=attacker, move=move) == Ability.CHEEK_POUCH:
            msg += consumer.heal(consumer.starting_hp // 3, source="its cheek pouch")
        
        consumer.last_berry = self.item
        consumer.ate_berry = True
        # TODO: right now HeldItem does not support `recover`ing/setting from anything other than another HeldItem object.
        #       this should probably be modified to be an `ExpiringItem` w/ that item for cases where `last_item` gets reset.
        if consumer.ability(attacker=attacker, move=move) == Ability.CUD_CHEW:
            consumer.cud_chew.set_turns(2)
        if consumer is self.owner:
            self.use()
        else:
            self.remove()
        
        return msg
    
    def __eq__(self, other):
        return self.get() == other
    
    def __getattr__(self, attr):
        if attr not in ("name", "power", "id", "effect"):
            raise AttributeError(f"{attr} is not an attribute of {self.__class__.__name__}.")
        if self.item is None:
            return None
        if attr == "name":
            return self.item.name
        if attr == "power":
            return self.item.power
        if attr == "id":
            return self.item.id
        if attr == "effect":
            return self.item.effect
        raise AttributeError(f"{attr} is not an attribute of {self.__class__.__name__}.")

class BatonPass():
    """Stores the necessary data from a pokemon to baton pass to another pokemon."""
    def __init__(self, poke):
        self.attack_stage = poke.attack_stage
        self.defense_stage = poke.defense_stage
        self.spatk_stage = poke.spatk_stage
        self.spdef_stage = poke.spdef_stage
        self.speed_stage = poke.speed_stage
        self.evasion_stage = poke.evasion_stage
        self.accuracy_stage = poke.accuracy_stage
        self.confusion = poke.confusion
        self.focus_energy = poke.focus_energy
        self.mind_reader = poke.mind_reader
        self.leech_seed = poke.leech_seed
        self.curse = poke.curse
        self.substitute = poke.substitute
        self.ingrain = poke.ingrain
        self.power_trick = poke.power_trick
        self.power_shift = poke.power_shift
        self.heal_block = poke.heal_block
        self.embargo = poke.embargo
        self.perish_song = poke.perish_song
        self.magnet_rise = poke.magnet_rise
        self.aqua_ring = poke.aqua_ring
        self.telekinesis = poke.telekinesis
    
    def apply(self, poke):
        """Push this objects data to a poke."""
        if poke.ability() != Ability.CURIOUS_MEDICINE:
            poke.attack_stage = self.attack_stage
            poke.defense_stage = self.defense_stage
            poke.spatk_stage = self.spatk_stage
            poke.spdef_stage = self.spdef_stage
            poke.speed_stage = self.speed_stage
            poke.evasion_stage = self.evasion_stage
            poke.accuracy_stage = self.accuracy_stage
        poke.confusion = self.confusion
        poke.focus_energy = self.focus_energy
        poke.mind_reader = self.mind_reader
        poke.leech_seed = self.leech_seed
        poke.curse = self.curse
        poke.substitute = self.substitute
        poke.ingrain = self.ingrain
        poke.power_trick = self.power_trick
        poke.power_shift = self.power_shift
        poke.heal_block = self.heal_block
        poke.embargo = self.embargo
        poke.perish_song = self.perish_song
        poke.magnet_rise = self.magnet_rise
        poke.aqua_ring = self.aqua_ring
        poke.telekinesis = self.telekinesis
