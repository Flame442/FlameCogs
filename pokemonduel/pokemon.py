import random
from .data import find, find_one
from .enums import Ability, DamageClass, ElementType
from .misc import NonVolatileEffect, Metronome, ExpiringEffect, ExpiringItem, HeldItem
from .move import Move


class DuelPokemon():
    """
    An instance of a pokemon in a duel.
    
    Contains extra duel-specific information.
    """
    
    def __init__(self, **kwargs):
        #ID from pfile
        self.pokemon_id = kwargs['pokemon_id']
        self._name = kwargs['name']
        self._nickname = kwargs['nickname']
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        self.illusion__name = None
        self.illusion_name = None
        
        # Dict {pokname: List[int]}
        self.base_stats = kwargs['base_stats']
        self.hp = kwargs['hp']
        self.attack = self.base_stats[self._name][1]
        self.defense = self.base_stats[self._name][2]
        self.spatk = self.base_stats[self._name][3]
        self.spdef = self.base_stats[self._name][4]
        self.speed = self.base_stats[self._name][5]
        self.hpiv = min(31, kwargs['hpiv'])
        self.atkiv = min(31, kwargs['atkiv'])
        self.defiv = min(31, kwargs['defiv'])
        self.spatkiv = min(31, kwargs['spatkiv'])
        self.spdefiv = min(31, kwargs['spdefiv'])
        self.speediv = min(31, kwargs['speediv'])
        self.hpev = kwargs['hpev']
        self.atkev = kwargs['atkev']
        self.defev = kwargs['defev']
        self.spatkev = kwargs['spatkev']
        self.spdefev = kwargs['spdefev']
        self.speedev = kwargs['speedev']
        self.nature_stat_deltas = kwargs['nature_stat_deltas']
        self.moves = kwargs['moves']
        self.ability_id = kwargs['ability_id']
        self.mega_ability_id = kwargs['mega_ability_id']
        self.type_ids = kwargs['type_ids']
        self.mega_type_ids = kwargs['mega_type_ids']
        self._starting_name = self._name
        self.starting_hp = self.hp
        self.starting_hpiv = self.hpiv
        self.starting_atkiv = self.atkiv
        self.starting_defiv = self.defiv
        self.starting_spatkiv = self.spatkiv
        self.starting_spdefiv = self.spdefiv
        self.starting_speediv = self.speediv
        self.starting_hpev = self.hpev
        self.starting_atkev = self.atkev
        self.starting_defev = self.defev
        self.starting_spatkev = self.spatkev
        self.starting_spdefev = self.spdefev
        self.starting_speedev = self.speedev
        self.starting_moves = self.moves.copy() #shallow copy to keep the objects but not the list itself
        self.starting_ability_id = self.ability_id
        self.starting_type_ids = self.type_ids.copy()
        #10 "weight" = 1 kg
        self.starting_weight = max(1, kwargs['weight'])
        self.attack_stage = 0
        self.defense_stage = 0
        self.spatk_stage = 0
        self.spdef_stage = 0
        self.speed_stage = 0
        self.accuracy_stage = 0
        self.evasion_stage = 0
        self.level = kwargs['level']
        self.shiny = kwargs['shiny']
        self.radiant = kwargs['radiant']
        self.skin = kwargs['skin']
        self.id = kwargs['id']
        self.held_item = HeldItem(kwargs['held_item'], self)
        self.happiness = kwargs['happiness']
        self.gender = kwargs['gender']
        self.can_still_evolve = kwargs['can_still_evolve']
        self.disliked_flavor = kwargs['disliked_flavor']

        self.owner = None
        self.active_turns = 0
        
        self.cursed = False
        self.switched = False
        self.minimized = False
        self.nv = NonVolatileEffect(self)
        self.metronome = Metronome()
        self.leech_seed = False
        self.stockpile = 0
        self.flinched = False
        self.confusion = ExpiringEffect(0)
        
        self.can_move = True
        self.has_moved = False
        #Boolean - stores whether this poke swapped in this turn, and should not have the next_turn function be called.
        self.swapped_in = False
        #Boolean - stores whether this poke has ever been sent in.
        self.ever_sent_out = False
        #Boolean - stores whether this poke should attempt to mega evolve this turn.
        self.should_mega_evolve = False
        
        # Moves
        #Optional[Move] - stores the last move used by this poke
        self.last_move = None
        #Optional[Tuple[int, DamageClass]] - stores the damage taken and the class of that damage.
        #Resets at the end of a turn.
        self.last_move_damage = None
        #Boolean - stores whether or not the last move used by this poke failed.
        self.last_move_failed = False
        #Optional[LockedMove] - stores the move this poke is currently locked into using due to it being a multi turn move.
        self.locked_move = None
        #Optional[Move] - stores the move this poke is currently locked into using due to a choice item.
        self.choice_move = None
        #ExpiringItem - stores the number of turns a specific move is disabled.
        self.disable = ExpiringItem()
        #ExpiringEffect - stores the number of turns this poke is taunted.
        self.taunt = ExpiringEffect(0)
        #ExpiringItem - stores the number of turns this poke is giving an encore of a specific move.
        self.encore = ExpiringItem()
        #Boolean - stores whether or not this pokemon is affected by torment.
        self.torment = False
        #Boolean - stores whether or not this pokemon has imprison active.
        self.imprison = False
        #ExpiringEffect - stores the number of turns this poke is blocked from using healing moves.
        self.heal_block = ExpiringEffect(0)
        #Optional[int] - stores the damage takes since bide was started.
        self.bide = None
        #Boolean - stores whether or not this pokemon has used focus energy.
        self.focus_energy = False
        #ExpiringEffect - stores the number of turns until this pokemon faints.
        self.perish_song = ExpiringEffect(0)
        #Boolean - stores whether or not this pokemon is inflicted by nightmare.
        self.nightmare = False
        #Boolean - stores whether or not this pokemon has used defense curl since entering the field.
        self.defense_curl = False
        #Int - stores the number of times fury cutter has been used since entering the field.
        self.fury_cutter = 0
        #ExpiringEffect - stores the number of turns bind is active on this poke.
        self.bind = ExpiringEffect(0)
        #Int - stores the remaining HP of this pokemon's substitute, or 0 if there is no substitute.
        self.substitute = 0
        #ExpiringEffect - stores the number of turns this pokemon is silenced for (can't use sound based moves).
        self.silenced = ExpiringEffect(0)
        #Boolean - stores whether or not this poke is in rage, and gains attack stages after being hit.
        self.rage = False
        #ExpiringItem - stores whether or not mind reader is active ON this poke, and the poke which is reading its mind.
        self.mind_reader = ExpiringItem()
        #Boolean - stores whether any attacker that causes this poke to faint will also faint this turn.
        self.destiny_bond = False
        #ExpiringEffect - stores whether destiny bond is on cooldown and cannot be executed.
        self.destiny_bond_cooldown = ExpiringEffect(0)
        #Boolean - stores whether or not this poke is prevented from switching out. This does not prevent moves that swap the target or user.
        self.trapping = False
        #Boolean - stores whether or not this poke is under the effect of ingrain. This does not prevent moves that swap the user, but does prevent target swaps.
        self.ingrain = False
        #Optional[DuelPokemon] - stores the pokemon that this pokemon is infatuated with.
        self.infatuated = None
        #Boolean - stores whether or not this poke is under the effect of aqua ring.
        self.aqua_ring = False
        #ExpiringEffect - stores the number of turns this pokemon is ungrounded due to magnet rise.
        self.magnet_rise = ExpiringEffect(0)
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from dive.
        self.dive = False
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from dig.
        self.dig = False
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from bounce or fly.
        self.fly = False
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from shadow force or phantom force.
        self.shadow_force = False
        #ExpiringEffect - stores how long this poke cannot be hit by critical hits due to lucky chant.
        self.lucky_chant = ExpiringEffect(0)
        #Boolean - stores whether or not this poke has been hit by smack down or thousand arrows, and is grounded.
        self.grounded_by_move = False
        #ExpiringEffect - stores the number of turns electric type moves have double power from this poke.
        self.charge = ExpiringEffect(0)
        #ExpiringEffect - stores the number of turns pokes cannot fall asleep.
        self.uproar = ExpiringEffect(0)
        #Boolean - stores whether or not this poke reflects status moves due to magic coat.
        self.magic_coat = False
        #Boolean - stores whether or not this poke has used power trick.
        self.power_trick = False
        #Boolean - stores whether or not this poke has used power shift.
        self.power_shift = False
        #ExpiringEffect - stores the number of turns until this poke falls asleep due to drowsiness.
        self.yawn = ExpiringEffect(0)
        #Boolean - stores whether this poke is turning normal moves to electric this turn.
        self.ion_deluge = False
        #Boolean - stores whether this poke's move is changed to electric type due to electrify.
        self.electrify = False
        #Boolean - stores whether this poke used a protection move this turn.
        self.protection_used = False
        #Int - stores the current chance (1/x) that a poke can use a protection move.
        self.protection_chance = 1
        #Boolean - stores whether this poke is protected by protect this turn.
        self.protect = False
        #Boolean - stores whether this poke is protected by endure this turn.
        self.endure = False
        #Boolean - stores whether this poke is protected by wide guard this turn.
        self.wide_guard = False
        #Boolean - stores whether this poke is protected by crafty shield this turn.
        self.crafty_shield = False
        #Boolean - stores whether this poke is protected by king shield this turn.
        self.king_shield = False
        #Boolean - stores whether this poke is protected by spiky shield this turn.
        self.spiky_shield = False
        #Boolean - stores whether this poke is protected by mat block this turn.
        self.mat_block = False
        #Boolean - stores whether this poke is protected by baneful bunker this turn.
        self.baneful_bunker = False
        #Boolean - stores whether this poke is protected by quick guard this turn.
        self.quick_guard = False
        #Boolean - stores whether this poke is protected by obstruct this turn.
        self.obstruct = False
        #Boolean - stores whether this poke is protected by silk trap this turn.
        self.silk_trap = False
        #ExpiringEffect - stores whether this poke will always crit due to laser focus.
        self.laser_focus = ExpiringEffect(0)
        #Boolean - stores whether this poke is coated with powder and will explode if it uses a fire type move.
        self.powdered = False
        #Boolean - stores whether this poke will steal the effect of certain self targeted moves this turn using snatch.
        self.snatching = False
        #ExpiringEffect - stores the number of turns this poke is ungrounded and hits to it never miss due to telekinesis.
        self.telekinesis = ExpiringEffect(0)
        #ExpiringEffect - stores the number of turns this poke is blocked from using held items due to embargo.
        self.embargo = ExpiringEffect(0)
        #Int - stores the current power of echoed voice.
        self.echoed_voice_power = 40
        #Boolean - stores whether echoed voice was used this turn.
        self.echoed_voice_used = False
        #Boolean - stores whether this poke is inflicted with a curse.
        self.curse = False
        #ExpiringEffect - stores whether this poke is preventing swap outs this turn.
        self.fairy_lock = ExpiringEffect(0)
        #Boolean - stores whether this poke remove all PP from a move that kills it this turn.
        self.grudge = False
        #Boolean - stores whether this poke is affected by foresight.
        self.foresight = False
        #Boolean - stores whether this poke is affected by miracle_eye.
        self.miracle_eye = False
        #Boolean - stores whether this poke is currently charging beak blast.
        self.beak_blast = False
        #Boolean - stores whether this poke is unable to switch out from no retreat.
        self.no_retreat = False
        #Boolean - stores whether this poke has taken ANY damage this turn.
        self.dmg_this_turn = False
        #Boolean - stores whether this poke has eaten a berry this battle.
        self.ate_berry = False
        #Boolean - stores whether this poke is unable to use its held item for the rest of the battle due to corrosive gas.
        self.corrosive_gas = False
        #Boolean - stores whether this poke has had a stat increase this turn.
        self.stat_incresed = False
        #Boolean - stores whether this poke has had a stat decrease this turn.
        self.stat_decreased = False
        #Boolean - stores whether this poke has had its flying type surpressed this turn.
        self.roost = False
        #Boolean - stores whether this poke is affected by octolock, and has its def/spdef lowered each turn.
        self.octolock = False
        #Optional[Int] - stores the raw attack value this poke's attack is split with.
        self.attack_split = None
        #Optional[Int] - stores the raw special attack value this poke's special attack is split with.
        self.spatk_split = None
        #Optional[Int] - stores the raw defense value this poke's defense is split with.
        self.defense_split = None
        #Optional[Int] - stores the raw special defense value this poke's special defense is split with.
        self.spdef_split = None
        #ExpiringEffect - stores the number of turns splinters are active on this pokemon.
        self.splinters = ExpiringEffect(0)
        #Boolean - stores whether this poke has used victory dance since entering the field.
        self.victory_dance = False
        #Int - stores the number of times autotomize has been used since switching out.
        self.autotomize = 0
        #Boolean - stores whether or not this pokemon's critical hit ratio is increased from eating a lansat berry.
        self.lansat_berry_ate = False
        #Boolean - stores whether or not this pokemon's next move has increased accuracy from eating a micle berry.
        self.micle_berry_ate = False
        #Boolean - stores whether or not fire type moves are 2x effective on this pokemon from tar shot.
        self.tar_shot = False
        #Int - stores the number of times this pokemon has been hit this battle, and does NOT reset when switching out.
        self.num_hits = 0

        # Abilities
        #Boolean - stores whether this poke's fire moves are boosted by flash fire.
        self.flash_fire = False
        #Int - stores the turn number relative to getting truant, % 2 == 1 -> loaf around.
        self.truant_turn = 0
        #Boolean - stores whether the ice face of this pokemon has been repaired.
        self.ice_repaired = False
        #Optional[Item] - stores the last berry ate by this pokemon.
        self.last_berry = None
        #ExpiringEffect - stores the number of turns until this pokemon attempts to recover & eat their last eaten berry.
        self.cud_chew = ExpiringEffect(0)

    def send_out(self, otherpoke, battle):
        """
        Initalize a poke upon first sending it out.
        
        otherpoke may be None, if two pokes are sent out at the same time and the first is killed in the send out process.
        Returns a formatted message.
        """
        self.ever_sent_out = True
        
        # Emergency exit `remove`s the pokemon *in the middle of the turn* in a somewhat unsafe way.
        # `remove` may need to be called here, but that seems like it may have side effects.
        self.flinched = False
        
        # This has to go BEFORE the send out message, and not in send_out_ability as it only
        # applies on send out, not when abilities are changed, and it changes the send out msg.
        illusion_options = [x for x in self.owner.party if x is not self and x.hp > 0]
        if self.ability() == Ability.ILLUSION and illusion_options:
            self.illusion__name = self._name
            self.illusion_name = self.name
            self._name = illusion_options[-1]._name
            self.name = illusion_options[-1].name
        
        if self._name == "Pikachu":
            msg = f"{self.name}, I choose you!\n"
        else:
            msg = f"{self.owner.name} sent out {self.name}!\n"
        
        # Any time a poke switches out, certain effects it had put on its opponent end
        if otherpoke is not None:
            otherpoke.trapping = False
            otherpoke.octolock = False
            otherpoke.bind.set_turns(0)
            otherpoke.splinters.set_turns(0)
        
        #Baton Pass
        if self.owner.baton_pass is not None:
            msg += f"{self.name} carries on the baton!\n"
            self.owner.baton_pass.apply(self)
            self.owner.baton_pass = None
        
        #Shed Tail
        if self.owner.next_substitute:
            self.substitute = self.owner.next_substitute
            self.owner.next_substitute = 0
        
        #Entry hazards
        #Special case for clearing toxic spikes, still happens even with heavy duty boots
        if self.owner.toxic_spikes and self.grounded(battle) and ElementType.POISON in self.type_ids:
            self.owner.toxic_spikes = 0
            msg += f"{self.name} absorbed the toxic spikes!\n"
        if self.held_item != "heavy-duty-boots":
            #Grounded entry hazards
            if self.grounded(battle):
                #Spikes
                if self.owner.spikes:
                    #1/8 -> 1/4
                    damage = self.starting_hp // (10 - (2 * self.owner.spikes))
                    msg += self.damage(damage, battle, source="spikes")
                #Toxic spikes
                if self.owner.toxic_spikes == 1:
                    msg += self.nv.apply_status("poison", battle, source="toxic spikes")
                elif self.owner.toxic_spikes == 2:
                    msg += self.nv.apply_status("b-poison", battle, source="toxic spikes")
                #Sticky web
                if self.owner.sticky_web:
                    msg += self.append_speed(-1, source="the sticky web")
            #Non-grounded entry hazards
            if self.owner.stealth_rock:
                effective = self.effectiveness(ElementType.ROCK, battle)
                if effective:
                    # damage = 1/8 max hp * effectiveness
                    damage = self.starting_hp // (32 // (4 * effective))
                    msg += self.damage(int(damage), battle, source="stealth rock")
        
        if self.hp > 0:
            msg += self.send_out_ability(otherpoke, battle)
        
        #Restoration
        if self.owner.healing_wish:
            used = False
            if self.hp != self.starting_hp:
                used = True
                self.hp = self.starting_hp
            if self.nv.current:
                used = True
                self.nv.reset()
            if used:
                self.owner.healing_wish = False
                msg += f"{self.name} was restored by healing wish!\n"
        if self.owner.lunar_dance:
            used = False
            if self.hp != self.starting_hp:
                used = True
                self.hp = self.starting_hp
            if self.nv.current:
                used = True
                self.nv.reset()
            not_at_full_pp = [move for move in self.moves if move.pp != move.starting_pp]
            if not_at_full_pp:
                used = True
                for move in not_at_full_pp:
                    move.pp = move.starting_pp
            if used:
                self.owner.lunar_dance = False
                msg += f"{self.name} was restored by lunar dance\n"
        
        # Items
        if self.held_item == "air-balloon" and not self.grounded(battle):
            msg += f"{self.name} floats in the air with its air balloon!\n"
        if self.held_item == "electric-seed" and battle.terrain.item == "electric":
            msg += self.append_defense(1, attacker=self, source="its electric seed")
            self.held_item.use()
        if self.held_item == "psychic-seed" and battle.terrain.item == "psychic":
            msg += self.append_spdef(1, attacker=self, source="its psychic seed")
            self.held_item.use()
        if self.held_item == "misty-seed" and battle.terrain.item == "misty":
            msg += self.append_spdef(1, attacker=self, source="its misty seed")
            self.held_item.use()
        if self.held_item == "grassy-seed" and battle.terrain.item == "grassy":
            msg += self.append_defense(1, attacker=self, source="its grassy seed")
            self.held_item.use()
        
        return msg
    
    def send_out_ability(self, otherpoke, battle):
        """
        Initalize this poke's ability.
        
        otherpoke may be None.
        Returns a formatted message.
        """
        msg = ""
        
        #Imposter (sus)
        if self.ability() == Ability.IMPOSTER and otherpoke is not None and not otherpoke.substitute and otherpoke.illusion_name is None:
            msg += f"{self.name} transformed into {otherpoke._name}!\n"
            self.transform(otherpoke)
        
        #Weather
        if self.ability() == Ability.DRIZZLE:
            msg += battle.weather.set("rain", self)
        if self.ability() == Ability.PRIMORDIAL_SEA:
            msg += battle.weather.set("h-rain", self)
        if self.ability() == Ability.SAND_STREAM:
            msg += battle.weather.set("sandstorm", self)
        if self.ability() == Ability.SNOW_WARNING:
            msg += battle.weather.set("hail", self)
        if self.ability() in (Ability.DROUGHT, Ability.ORICHALCUM_PULSE):
            msg += battle.weather.set("sun", self)
        if self.ability() == Ability.DESOLATE_LAND:
            msg += battle.weather.set("h-sun", self)
        if self.ability() == Ability.DELTA_STREAM:
            msg += battle.weather.set("h-wind", self)
        
        #Terrain
        if self.ability() == Ability.GRASSY_SURGE:
            msg += battle.terrain.set("grassy", self)
        if self.ability() == Ability.MISTY_SURGE:
            msg += battle.terrain.set("misty", self)
        if self.ability() in (Ability.ELECTRIC_SURGE, Ability.HADRON_ENGINE):
            msg += battle.terrain.set("electric", self)
        if self.ability() == Ability.PSYCHIC_SURGE:
            msg += battle.terrain.set("psychic", self)
        
        # Message only
        if self.ability() == Ability.MOLD_BREAKER:
            msg += f"{self.name} breaks the mold!\n"
        if self.ability() == Ability.TURBOBLAZE:
            msg += f"{self.name} is radiating a blazing aura!\n"
        if self.ability() == Ability.TERAVOLT:
            msg += f"{self.name} is radiating a bursting aura!\n"
        
        if self.ability() == Ability.INTIMIDATE and otherpoke is not None:
            if otherpoke.ability() == Ability.OBLIVIOUS:
                msg += f"{otherpoke.name} is too oblivious to be intimidated!\n"
            elif otherpoke.ability() == Ability.OWN_TEMPO:
                msg += f"{otherpoke.name} keeps walking on its own tempo, and is not intimidated!\n"
            elif otherpoke.ability() == Ability.INNER_FOCUS:
                msg += f"{otherpoke.name} is too focused to be intimidated!\n"
            elif otherpoke.ability() == Ability.SCRAPPY:
                msg += f"{otherpoke.name} is too scrappy to be intimidated!\n"
            elif otherpoke.ability() == Ability.GUARD_DOG:
                msg += f"{otherpoke.name}'s guard dog keeps it from being intimidated!\n"
                msg += otherpoke.append_attack(1, attacker=otherpoke, source="its guard dog")
            else:
                msg += otherpoke.append_attack(-1, attacker=self, source=f"{self.name}'s Intimidate")
                if otherpoke.held_item == "adrenaline-orb":
                    msg += otherpoke.append_speed(1, attacker=otherpoke, source="its adrenaline orb")
                if otherpoke.ability() == Ability.RATTLED:
                    msg += otherpoke.append_speed(1, attacker=otherpoke, source="its rattled")
        if self.ability() == Ability.SCREEN_CLEANER:
            battle.trainer1.aurora_veil.set_turns(0)
            battle.trainer1.light_screen.set_turns(0)
            battle.trainer1.reflect.set_turns(0)
            battle.trainer2.aurora_veil.set_turns(0)
            battle.trainer2.light_screen.set_turns(0)
            battle.trainer2.reflect.set_turns(0)
            msg += f"{self.name}'s screen cleaner removed barriers from both sides of the field!\n"
        if self.ability() == Ability.INTREPID_SWORD:
            msg += self.append_attack(1, attacker=self, source="its intrepid sword")
        if self.ability() == Ability.DAUNTLESS_SHIELD:
            msg += self.append_defense(1, attacker=self, source="its dauntless shield")
        if self.ability() == Ability.TRACE and otherpoke is not None and otherpoke.ability_giveable():
            self.ability_id = otherpoke.ability_id
            msg += f"{self.name} traced {otherpoke.name}'s ability!\n"
            msg += self.send_out_ability(otherpoke, battle)
            return msg
        if self.ability() == Ability.DOWNLOAD and otherpoke is not None:
            if otherpoke.get_spdef(battle) > otherpoke.get_defense(battle):
                msg += self.append_attack(1, attacker=self, source="its download")
            else:
                msg += self.append_spatk(1, attacker=self, source="its download")
        if self.ability() == Ability.ANTICIPATION and otherpoke is not None:
            for move in otherpoke.moves:
                if move.effect == 39:
                    msg += f"{self.name} shuddered in anticipation!\n"
                    break
                if self.effectiveness(move.type, battle) > 1:
                    msg += f"{self.name} shuddered in anticipation!\n"
                    break
        if self.ability() == Ability.FOREWARN and otherpoke is not None:
            bestmoves = []
            bestpower = 0
            for move in otherpoke.moves:
                if move.damage_class == DamageClass.STATUS:
                    power = 0
                if move.effect == 39:
                    power = 150
                elif move.power is None: # Good enough
                    power = 80
                else:
                    power = move.power
                if power > bestpower:
                    bestpower = power
                    bestmoves = [move]
                elif power == bestpower:
                    bestmoves.append(move)
            if bestmoves:
                move = random.choice(bestmoves)
                msg += f"{self.name} is forewarned about {otherpoke.name}'s {move.pretty_name}!\n"
        if self.ability() == Ability.FRISK and otherpoke is not None and otherpoke.held_item.has_item():
            msg += f"{self.name} senses that {otherpoke.name} is holding a {otherpoke.held_item.name} using its frisk!\n"
        if self.ability() == Ability.MULTITYPE:
            e = None
            if self.held_item == "draco-plate":
                e = ElementType.DRAGON
                f = "Arceus-dragon"
            elif self.held_item == "dread-plate":
                e = ElementType.DARK
                f = "Arceus-dark"
            elif self.held_item == "earth-plate":
                e = ElementType.GROUND
                f = "Arceus-ground"
            elif self.held_item == "fist-plate":
                e = ElementType.FIGHTING
                f = "Arceus-fighting"
            elif self.held_item == "flame-plate":
                e = ElementType.FIRE
                f = "Arceus-fire"
            elif self.held_item == "icicle-plate":
                e = ElementType.ICE
                f = "Arceus-ice"
            elif self.held_item == "insect-plate":
                e = ElementType.BUG
                f = "Arceus-bug"
            elif self.held_item == "iron-plate":
                e = ElementType.STEEL
                f = "Arceus-steel"
            elif self.held_item == "meadow-plate":
                e = ElementType.GRASS
                f = "Arceus-grass"
            elif self.held_item == "mind-plate":
                e = ElementType.PSYCHIC
                f = "Arceus-psychic"
            elif self.held_item == "pixie-plate":
                e = ElementType.FAIRY
                f = "Arceus-fairy"
            elif self.held_item == "sky-plate":
                e = ElementType.FLYING
                f = "Arceus-flying"
            elif self.held_item == "splash-plate":
                e = ElementType.WATER
                f = "Arceus-water"
            elif self.held_item == "spooky-plate":
                e = ElementType.GHOST
                f = "Arceus-ghost"
            elif self.held_item == "stone-plate":
                e = ElementType.ROCK
                f = "Arceus-rock"
            elif self.held_item == "toxic-plate":
                e = ElementType.POISON
                f = "Arceus-poison"
            elif self.held_item == "zap-plate":
                e = ElementType.ELECTRIC
                f = "Arceus-electric"
            if e is not None and self.form(f):
                self.type_ids = [e]
                t = ElementType(e).name.lower()
                msg += f"{self.name} transformed into a {t} type using its multitype!\n"
        if self.ability() == Ability.RKS_SYSTEM and self._name == "Silvally":
            e = None
            if self.held_item == "dragon-memory":
                if self.form("Silvally-dragon"):
                    e = ElementType.DRAGON
            elif self.held_item == "dark-memory":
                if self.form("Silvally-dark"):
                    e = ElementType.DARK
            elif self.held_item == "ground-memory":
                if self.form("Silvally-ground"):
                    e = ElementType.GROUND
            elif self.held_item == "fighting-memory":
                if self.form("Silvally-fighting"):
                    e = ElementType.FIGHTING
            elif self.held_item == "fire-memory":
                if self.form("Silvally-fire"):
                    e = ElementType.FIRE
            elif self.held_item == "ice-memory":
                if self.form("Silvally-ice"):
                    e = ElementType.ICE
            elif self.held_item == "bug-memory":
                if self.form("Silvally-bug"):
                    e = ElementType.BUG
            elif self.held_item == "steel-memory":
                if self.form("Silvally-steel"):
                    e = ElementType.STEEL
            elif self.held_item == "grass-memory":
                if self.form("Silvally-grass"):
                    e = ElementType.GRASS
            elif self.held_item == "psychic-memory":
                if self.form("Silvally-psychic"):
                    e = ElementType.PSYCHIC
            elif self.held_item == "fairy-memory":
                if self.form("Silvally-fairy"):
                    e = ElementType.FAIRY
            elif self.held_item == "flying-memory":
                if self.form("Silvally-flying"):
                    e = ElementType.FLYING
            elif self.held_item == "water-memory":
                if self.form("Silvally-water"):
                    e = ElementType.WATER
            elif self.held_item == "ghost-memory":
                if self.form("Silvally-ghost"):
                    e = ElementType.GHOST
            elif self.held_item == "rock-memory":
                if self.form("Silvally-rock"):
                    e = ElementType.ROCK
            elif self.held_item == "poison-memory":
                if self.form("Silvally-poison"):
                    e = ElementType.POISON
            elif self.held_item == "electric-memory":
                if self.form("Silvally-electric"):
                    e = ElementType.ELECTRIC
            if e is not None:
                self.type_ids = [e]
                t = ElementType(e).name.lower()
                msg += f"{self.name} transformed into a {t} type using its rks system!\n"
        if self.ability() == Ability.TRUANT:
            self.truant_turn = 0
        if self.ability() == Ability.FORECAST and self._name in ("Castform", "Castform-snowy", "Castform-rainy", "Castform-sunny"):
            weather = battle.weather.get()
            element = None
            if weather == "hail" and self._name != "Castform-snowy":
                if self.form("Castform-snowy"):
                    element = ElementType.ICE
            elif weather in ("sandstorm", "h-wind", None) and self._name != "Castform":
                if self.form("Castform"):
                    element = ElementType.NORMAL
            elif weather in ("rain", "h-rain") and self._name != "Castform-rainy":
                if self.form("Castform-rainy"):
                    element = ElementType.WATER
            elif weather in ("sun", "h-sun") and self._name != "Castform-sunny":
                if self.form("Castform-sunny"):
                    element = ElementType.FIRE
            if element is not None:
                self.type_ids = [element]
                t = ElementType(element).name.lower()
                msg += f"{self.name} transformed into a {t} type using its forecast!\n"
        if self.ability() == Ability.MIMICRY and battle.terrain.item:
            terrain = battle.terrain.item
            if terrain == "electric":
                element = ElementType.ELECTRIC
            elif terrain == "grassy":
                element = ElementType.GRASS
            elif terrain == "misty":
                element = ElementType.FAIRY
            elif terrain == "psychic":
                element = ElementType.PSYCHIC
            self.type_ids = [element]
            t = ElementType(element).name.lower()
            msg += f"{self.name} transformed into a {t} type using its mimicry!\n"
        if self.ability() == Ability.WIND_RIDER and self.owner.tailwind.active():
            msg += self.append_attack(1, attacker=self, source="its wind rider")
        
        return msg
    
    def remove(self, battle, *, fainted=False):
        """
        Clean up a poke when it is removed from battle.
        
        Returns a formatted message of anything that happened while switching out.
        """
        msg = ""
        if not fainted:
            if self.ability() == Ability.NATURAL_CURE and self.nv.current:
                msg += f"{self.name}'s {self.nv.current} was cured by its natural cure!\n"
                self.nv.reset()
            if self.ability() == Ability.REGENERATOR:
                msg += self.heal(self.starting_hp // 3, source="its regenerator")
            if self.ability() == Ability.ZERO_TO_HERO:
                if self.form("Palafin-hero"):
                    msg += f"{self.name} is ready to be a hero!\n"
        self.nv.badly_poisoned_turn = 0
        self.minimized = False
        self.has_moved = False
        self.choice_move = None
        self.last_move = None
        self.should_mega_evolve = False
        self.swapped_in = False
        self.active_turns = 0
        if self.illusion__name is not None:
            self._name = self.illusion__name
            self.name = self.illusion_name
        self.illusion__name = None
        self.illusion_name = None
        if self._starting_name in ("Ditto", "Smeargle", "Mew", "Aegislash"):
            self._name = self._starting_name
            if self._nickname != "None":
                self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
            else:
                self.name = self._name.replace("-", " ")
        if self.owner.current_pokemon is self:
            self.owner.current_pokemon = None
        if battle.weather.recheck_ability_weather():
            msg += "The weather cleared!\n"
        self.attack = self.base_stats[self._name][1]
        self.defense = self.base_stats[self._name][2]
        self.spatk = self.base_stats[self._name][3]
        self.spdef = self.base_stats[self._name][4]
        self.speed = self.base_stats[self._name][5]
        self.hpiv = self.starting_hpiv
        self.atkiv = self.starting_atkiv
        self.defiv = self.starting_defiv
        self.spatkiv = self.starting_spatkiv
        self.spdefiv = self.starting_spdefiv
        self.speediv = self.starting_speediv
        self.hpev = self.starting_hpev
        self.atkev = self.starting_atkev
        self.defev = self.starting_defev
        self.spatkev = self.starting_spatkev
        self.spdefev = self.starting_spdefev
        self.speedev = self.starting_speedev
        self.moves = self.starting_moves.copy()
        self.ability_id = self.starting_ability_id
        self.type_ids = self.starting_type_ids.copy()
        self.attack_stage = 0
        self.defense_stage = 0
        self.spatk_stage = 0
        self.spdef_stage = 0
        self.speed_stage = 0
        self.accuracy_stage = 0
        self.evasion_stage = 0
        self.metronome = Metronome()
        self.leech_seed = False
        self.stockpile = 0
        self.flinched = False
        self.confusion = ExpiringEffect(0)
        self.last_move_damage = None
        self.locked_move = None
        self.bide = None
        self.torment = False
        self.imprison = False
        self.disable = ExpiringItem()
        self.taunt = ExpiringEffect(0)
        self.encore = ExpiringItem()
        self.heal_block = ExpiringEffect(0)
        self.focus_energy = False
        self.perish_song = ExpiringEffect(0)
        self.nightmare = False
        self.defense_curl = False
        self.fury_cutter = 0
        self.bind = ExpiringEffect(0)
        self.substitute = 0
        self.silenced = ExpiringEffect(0)
        self.last_move_failed = False
        self.rage = False
        self.mind_reader = ExpiringItem()
        self.destiny_bond = False
        self.destiny_bond_cooldown = ExpiringEffect(0)
        self.trapping = False
        self.ingrain = False
        self.infatuated = None
        self.aqua_ring = False
        self.magnet_rise = ExpiringEffect(0)
        self.dive = False
        self.dig = False
        self.fly = False
        self.shadow_force = False
        self.lucky_chant = ExpiringEffect(0)
        self.grounded_by_move = False
        self.charge = ExpiringEffect(0)
        self.uproar = ExpiringEffect(0)
        self.magic_coat = False
        self.power_trick = False
        self.power_shift = False
        self.yawn = ExpiringEffect(0)
        self.ion_deluge = False
        self.electrify = False
        self.protection_used = False
        self.protection_chance = 1
        self.protect = False
        self.endure = False
        self.wide_guard = False
        self.crafty_shield = False
        self.king_shield = False
        self.spiky_shield = False
        self.mat_block = False
        self.baneful_bunker = False
        self.quick_guard = False
        self.obstruct = False
        self.silk_trap = False
        self.laser_focus = ExpiringEffect(0)
        self.powdered = False
        self.snatching = False
        self.telekinesis = ExpiringEffect(0)
        self.embargo = ExpiringEffect(0)
        self.echoed_voice_power = 40
        self.echoed_voice_used = False
        self.curse = False
        self.fairy_lock = ExpiringEffect(0)
        self.grudge = False
        self.foresight = False
        self.miracle_eye = False
        self.beak_blast = False
        self.no_retreat = False
        self.dmg_this_turn = False
        self.autotomize = 0
        self.lansat_berry_ate = False
        self.micle_berry_ate = False
        self.flash_fire = False
        self.truant_turn = 0
        self.cud_chew = ExpiringEffect(0)
        self.stat_incresed = False
        self.stat_decreased = False
        self.roost = False
        self.octolock = False
        self.attack_split = None
        self.spatk_split = None
        self.defense_split = None
        self.spdef_split = None
        self.splinters = ExpiringEffect(0)
        self.victory_dance = False
        self.tar_shot = False
        self.held_item.ever_had_item = self.held_item.item is not None

        return msg

    def next_turn(self, otherpoke, battle):
        """
        Updates this pokemon for a new turn.
        
        `otherpoke` may be None if the opponent fainted the previous turn.
        Returns a formatted message.
        """
        msg = ""
        # This needs to be here, as swapping sets this value explicitly
        self.has_moved = False
        if not self.swapped_in:
            self.active_turns += 1
        self.last_move_damage = None
        self.last_move_failed = False
        self.should_mega_evolve = False
        self.rage = False
        self.mind_reader.next_turn()
        self.charge.next_turn()
        self.destiny_bond_cooldown.next_turn()
        self.magic_coat = False
        self.ion_deluge = False
        self.electrify = False
        if not self.protection_used:
            self.protection_chance = 1
        self.protection_used = False
        self.protect = False
        self.endure = False
        self.wide_guard = False
        self.crafty_shield = False
        self.king_shield = False
        self.spiky_shield = False
        self.mat_block = False
        self.baneful_bunker = False
        self.quick_guard = False
        self.obstruct = False
        self.silk_trap = False
        self.laser_focus.next_turn()
        self.powdered = False
        self.snatching = False
        if not self.echoed_voice_used:
            self.echoed_voice_power = 40
        self.grudge = False
        self.beak_blast = False
        self.dmg_this_turn = False
        if self.locked_move:
            if self.locked_move.next_turn():
                self.locked_move = None
                # Just in case they never actually used the move to remove it
                self.dive = False
                self.dig = False
                self.fly = False
                self.shadow_force = False
        self.fairy_lock.next_turn()
        self.flinched = False
        self.truant_turn += 1
        self.stat_incresed = False
        self.stat_decreased = False
        self.roost = False
        
        msg += self.nv.next_turn(battle)
        
        # Volatile status turn progression
        prev_disab_move = self.disable.item
        if self.disable.next_turn():
            msg += f"{self.name}'s {prev_disab_move.pretty_name} is no longer disabled!\n"
        if self.taunt.next_turn():
            msg += f"{self.name}'s taunt has ended!\n"
        if self.heal_block.next_turn():
            msg += f"{self.name}'s heal block has ended!\n"
        if self.silenced.next_turn():
            msg += f"{self.name}'s voice returned!\n"
        if self.magnet_rise.next_turn():
            msg += f"{self.name}'s magnet rise has ended!\n"
        if self.lucky_chant.next_turn():
            msg += f"{self.name} is no longer shielded by lucky chant!\n"
        if self.uproar.next_turn():
            msg += f"{self.name} calms down!\n"
        if self.telekinesis.next_turn():
            msg += f"{self.name} was released from telekinesis!\n"
        if self.embargo.next_turn():
            msg += f"{self.name}'s embargo was lifted!\n"
        if self.yawn.next_turn():
            msg += self.nv.apply_status("sleep", battle, source="drowsiness")
        if self.encore.next_turn():
            msg += f"{self.name}'s encore is over!\n"
        if self.perish_song.next_turn():
            msg += self.faint(battle, source="perish song")
        if self.encore.active() and self.encore.item.pp == 0:
            self.encore.end()
            msg += f"{self.name}'s encore is over!\n"
        if self.cud_chew.next_turn() and self.held_item.last_used is not None and self.held_item.last_used.name.endswith("-berry"):
            self.held_item.recover(self.held_item)
            msg += self.held_item.eat_berry()
            self.held_item.last_used = None
        
        # Held Items
        if self.held_item == "white-herb":
            changed = False
            if self.attack_stage < 0:
                self.attack_stage = 0
                changed = True
            if self.defense_stage < 0:
                self.defense_stage = 0
                changed = True
            if self.spatk_stage < 0:
                self.spatk_stage = 0
                changed = True
            if self.spdef_stage < 0:
                self.spdef_stage = 0
                changed = True
            if self.speed_stage < 0:
                self.speed_stage = 0
                changed = True
            if self.accuracy_stage < 0:
                self.accuracy_stage = 0
                changed = True
            if self.evasion_stage < 0:
                self.evasion_stage = 0
                changed = True
            if changed:
                msg += f"{self.name}'s white herb reset all negative stat stage changes.\n"
                self.held_item.use()
        if self.held_item == "toxic-orb":
            msg += self.nv.apply_status("b-poison", battle, attacker=self, source="its toxic orb")
        if self.held_item == "flame-orb":
            msg += self.nv.apply_status("burn", battle, attacker=self, source="its flame orb")
        if self.held_item == "leftovers":
            msg += self.heal(self.starting_hp // 16, source="its leftovers")
        if self.held_item == "black-sludge":
            if ElementType.POISON in self.type_ids:
                msg += self.heal(self.starting_hp // 16, source="its black sludge")
            else:
                msg += self.damage(self.starting_hp // 8, battle, source="its black sludge")
        
        # Abilities
        if self.ability() == Ability.SPEED_BOOST and not self.swapped_in:
            msg += self.append_speed(1, attacker=self, source="its Speed boost")
        if self.ability() == Ability.LIMBER and self.nv.paralysis():
            self.nv.reset()
            msg += f"{self.name}'s limber cured it of its paralysis!\n"
        if self.ability() == Ability.INSOMNIA and self.nv.sleep():
            self.nv.reset()
            msg += f"{self.name}'s insomnia woke it up!\n"
        if self.ability() == Ability.VITAL_SPIRIT and self.nv.sleep():
            self.nv.reset()
            msg += f"{self.name}'s vital spirit woke it up!\n"
        if self.ability() == Ability.IMMUNITY and self.nv.poison():
            self.nv.reset()
            msg += f"{self.name}'s immunity cured it of its poison!\n"
        if self.ability() == Ability.MAGMA_ARMOR and self.nv.freeze():
            self.nv.reset()
            msg += f"{self.name}'s magma armor cured it of thawed it!\n"
        if self.ability() in (Ability.WATER_VEIL, Ability.WATER_BUBBLE) and self.nv.burn():
            self.nv.reset()
            ability_name = Ability(self.ability_id).pretty_name
            msg += f"{self.name}'s {ability_name} cured it of its burn!\n"
        if self.ability() == Ability.OWN_TEMPO and self.confusion.active():
            self.confusion.set_turns(0)
            msg += f"{self.name}'s tempo cured it of its confusion!\n"
        if self.ability() == Ability.OBLIVIOUS:
            if self.infatuated:
                self.infatuated = None
                msg += f"{self.name} fell out of love because of its obliviousness!\n"
            if self.taunt.active():
                self.taunt.set_turns(0)
                msg += f"{self.name} stopped caring about being taunted because of its obliviousness!\n"
        if self.ability() == Ability.RAIN_DISH and battle.weather.get() in ("rain", "h-rain"):
            msg += self.heal(self.starting_hp // 16, source="its rain dish")
        if self.ability() == Ability.ICE_BODY and battle.weather.get() == "hail":
            msg += self.heal(self.starting_hp // 16, source="its ice body")
        if self.ability() == Ability.DRY_SKIN:
            if battle.weather.get() in ("rain", "h-rain"):
                msg += self.heal(self.starting_hp // 8, source="its dry skin")
            elif battle.weather.get() in ("sun", "h-sun"):
                msg += self.damage(self.starting_hp // 8, battle, source="its dry skin")
        if self.ability() == Ability.SOLAR_POWER and battle.weather.get() in ("sun", "h-sun"):
            msg += self.damage(self.starting_hp // 8, battle, source="its solar power")
        if self.ability() == Ability.MOODY:
            stats = [
                (self.attack_stage, "attack"),
                (self.defense_stage, "defense"),
                (self.spatk_stage, "special attack"),
                (self.spdef_stage, "special defense"),
                (self.speed_stage, "speed")
            ]
            add_stats = stats.copy()
            remove_stats = stats.copy()
            for stat in stats:
                if stat[0] == 6:
                    add_stats.remove(stat)
            add_stat = None
            if add_stats:
                add_stat = random.choice(add_stats)
                msg += self.append_stat(2, self, None, add_stat[1], "its moodiness")
            for stat in stats:
                if stat == add_stat:
                    remove_stats.remove(stat)
                if stat[0] == -6:
                    remove_stats.remove(stat)
            if remove_stats:
                remove_stat = random.choice(remove_stats)
                msg += self.append_stat(-1, self, None, remove_stat[1], "its moodiness")
        if (
            self.ability() == Ability.PICKUP
            and not self.held_item.has_item()
            and otherpoke is not None
            and otherpoke.held_item.last_used is not None
        ):
            self.held_item.recover(otherpoke.held_item)
            msg += f"{self.name} picked up a {self.held_item.name}!\n"
        if self.ability() == Ability.ICE_FACE and not self.ice_repaired and self._name == "Eiscue-noice" and battle.weather.get() == "hail":
            if self.form("Eiscue"):
                self.ice_repaired = True
                msg += f"{self.name}'s ice face was restored by the hail!\n"
        if self.ability() == Ability.HARVEST and self.last_berry is not None and not self.held_item.has_item():
            if random.randint(0, 1):
                self.held_item.item = self.last_berry
                self.last_berry = None
                msg += f"{self.name} harvested a {self.held_item.name}!\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan" and self.hp < self.starting_hp / 2:
            if self.form("Darmanitan-zen"):
                if ElementType.PSYCHIC not in self.type_ids:
                    self.type_ids.append(ElementType.PSYCHIC)
                msg += f"{self.name} enters a zen state.\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-galar" and self.hp < self.starting_hp / 2:
            if self.form("Darmanitan-zen-galar"):
                if ElementType.FIRE not in self.type_ids:
                    self.type_ids.append(ElementType.FIRE)
                msg += f"{self.name} enters a zen state.\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-zen" and self.hp >= self.starting_hp / 2:
            if self.form("Darmanitan"):
                if ElementType.PSYCHIC in self.type_ids:
                    self.type_ids.remove(ElementType.PSYCHIC)
                msg += f"{self.name}'s zen state ends!\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-zen-galar" and self.hp >= self.starting_hp / 2:
            if self.form("Darmanitan-galar"):
                if ElementType.FIRE in self.type_ids:
                    self.type_ids.remove(ElementType.FIRE)
                msg += f"{self.name}'s zen state ends!\n"
        if self.ability() == Ability.SHIELDS_DOWN and self._name == "Minior" and self.hp < self.starting_hp / 2:
            if self.id % 7 == 0:
                new_form = "Minior-red"
            elif self.id % 7 == 1:
                new_form = "Minior-orange"
            elif self.id % 7 == 2:
                new_form = "Minior-yellow"
            elif self.id % 7 == 3:
                new_form = "Minior-green"
            elif self.id % 7 == 4:
                new_form = "Minior-blue"
            elif self.id % 7 == 5:
                new_form = "Minior-indigo"
            else:
                new_form = "Minior-violet"
            if self.form(new_form):
                msg += f"{self.name}'s core was exposed!\n"
        if (
            self.ability() == Ability.SHIELDS_DOWN
            and self._name in ("Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet")
            and self.hp >= self.starting_hp / 2
        ):
            if self.form("Minior"):
                msg += f"{self.name}'s shell returned!\n"
        if self.ability() == Ability.SCHOOLING and self._name == "Wishiwashi-school" and self.hp < self.starting_hp / 4:
            if self.form("Wishiwashi"):
                msg += f"{self.name}'s school is gone!\n"
        if self.ability() == Ability.SCHOOLING and self._name == "Wishiwashi" and self.hp >= self.starting_hp / 4 and self.level >= 20:
            if self.form("Wishiwashi-school"):
                msg += f"{self.name} schools together!\n"
        if self.ability() == Ability.POWER_CONSTRUCT and self._name in ("Zygarde", "Zygarde-10") and self.hp < self.starting_hp / 2 and self.hp > 0:
            if self.form("Zygarde-complete"):
                msg += f"{self.name} is at full power!\n"
                # Janky way to raise the current HP of this poke, as it's new form has a higher HP stat. Note, this is NOT healing.
                new_hp = round((((2 * self.base_stats["Zygarde-complete"][0] + self.hpiv + (self.hpev / 4)) * self.level) / 100) + self.level + 10)
                self.hp = new_hp - (self.starting_hp - self.hp)
                self.starting_hp = new_hp
        if self.ability() == Ability.HUNGER_SWITCH:
            if self._name == "Morpeko":
                self.form("Morpeko-hangry")
            elif self._name == "Morpeko-hangry":
                self.form("Morpeko")
        if self.ability() == Ability.FLOWER_GIFT and self._name == "Cherrim" and battle.weather.get() in ("sun", "h-sun"):
            self.form("Cherrim-sunshine")
        if self.ability() == Ability.FLOWER_GIFT and self._name == "Cherrim-sunshine" and battle.weather.get() not in ("sun", "h-sun"):
            self.form("Cherrim")
        
        #Bad Dreams
        if otherpoke is not None and otherpoke.ability() == Ability.BAD_DREAMS and self.nv.sleep():
            msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s bad dreams")
        #Leech seed
        if self.leech_seed and otherpoke is not None:
            damage = self.starting_hp // 8
            msg += self.damage(damage, battle, attacker=otherpoke, drain_heal_ratio=1, source="leech seed")
        #Curse
        if self.curse:
            msg += self.damage(self.starting_hp // 4, battle, source="its curse")
        
        #Weather damages
        if self.ability() == Ability.OVERCOAT:
            pass
        elif self.held_item == "safety-goggles":
            pass
        elif battle.weather.get() == "sandstorm":
            if (
                ElementType.ROCK not in self.type_ids
                and ElementType.GROUND not in self.type_ids
                and ElementType.STEEL not in self.type_ids
                and self.ability() not in (Ability.SAND_RUSH, Ability.SAND_VEIL, Ability.SAND_FORCE)
            ):
                msg += self.damage(self.starting_hp // 16, battle, source="the sandstorm")
        elif battle.weather.get() == "hail":
            if (
                ElementType.ICE not in self.type_ids
                and self.ability() not in (Ability.SNOW_CLOAK, Ability.ICE_BODY)
            ):
                msg += self.damage(self.starting_hp // 16, battle, source="the hail")
        
        #Bind
        if self.bind.next_turn():
            msg += f"{self.name} is no longer bound!\n"
        elif self.bind.active() and otherpoke is not None:
            if otherpoke.held_item == "binding-band":
                msg += self.damage(self.starting_hp // 6, battle, source=f"{otherpoke.name}'s bind")
            else:
                msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s bind")
        #Ingrain
        if self.ingrain:
            heal = self.starting_hp // 16
            if self.held_item == "big_root":
                heal = int(heal * 1.3)
            msg += self.heal(heal, source="ingrain")
        #Aqua Ring
        if self.aqua_ring:
            heal = self.starting_hp // 16
            if self.held_item == "big_root":
                heal = int(heal * 1.3)
            msg += self.heal(heal, source="aqua ring")
        #Octolock
        if self.octolock and otherpoke is not None:
            msg += self.append_defense(-1, attacker=self, source=f"{otherpoke.name}'s octolock")
            msg += self.append_spdef(-1, attacker=self, source=f"{otherpoke.name}'s octolock")
        #Grassy Terrain
        if battle.terrain.item == "grassy" and self.grounded(battle) and not self.heal_block.active():
            msg += self.heal(self.starting_hp // 16, source="grassy terrain")
        #Splinters
        if self.splinters.next_turn():
            msg += f"{self.name}'s splinters wore off!\n"
        elif self.splinters.active() and otherpoke is not None:
            msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s splinters")
        
        #Goes at the end so everything in this func that checks it handles it correctly
        self.swapped_in = False
        
        return msg
    
    def faint(self, battle, *, move=None, attacker=None, source: str=""):
        """
        Sets a pokemon's HP to zero and cleans it up.
        
        If a pokemon takes damage equal to its HP, use damage instead.
        This method ignores focus sash and sturdy, forcing the pokemon to faint.
        Returns a formatted message.
        """
        msg = ""
        self.hp = 0
        if source:
            source = f" from {source}"
        msg += f"{self.name} fainted{source}!\n"
        if move is not None and attacker is not None and self.destiny_bond and self.owner.has_alive_pokemon():
            msg += attacker.faint(battle, source=f"{self.name}'s destiny bond")
        if move is not None and attacker is not None and attacker._name == "Greninja" and attacker.ability() == Ability.BATTLE_BOND:
            if attacker.form("Greninja-ash"):
                msg += f"{attacker.name}'s bond with its trainer has strengthened it!\n"
        if move is not None and self.grudge:
            move.pp = 0
            msg += f"{move.pretty_name}'s pp was depleted!\n"
        if attacker is not None and attacker.ability() in (Ability.CHILLING_NEIGH, Ability.AS_ONE_ICE):
            msg += attacker.append_attack(1, attacker=attacker, source="its chilling neigh")
        if attacker is not None and attacker.ability() in (Ability.GRIM_NEIGH, Ability.AS_ONE_SHADOW):
            msg += attacker.append_spatk(1, attacker=attacker, source="its grim neigh")
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.SOUL_HEART:
                msg += poke.append_spatk(
                    1,
                    attacker=poke,
                    source="its soul heart"
                )
        self.owner.retaliate.set_turns(2)
        self.owner.num_fainted += 1
        msg += self.remove(battle, fainted=True)
        return msg
    
    def damage(self, damage, battle, *, move=None, move_type=None, attacker=None, critical=False, drain_heal_ratio=None, source: str=""):
        """
        Applies a certain amount of damage to this pokemon.
        
        Returns a formatted message.
        """
        msgadd, _ = self._damage(damage, battle, move=move, move_type=move_type, attacker=attacker, critical=critical, drain_heal_ratio=drain_heal_ratio, source=source)
        return msgadd
    
    def _damage(self, damage, battle, *, move=None, move_type=None, attacker=None, critical=False, drain_heal_ratio=None, source: str=""):
        """
        Applies a certain amount of damage to this pokemon.
        
        Returns a formatted message and the amount of damage actually dealt.
        """
        msg = ""
        # Don't go through with an attack if the poke is already dead.
        # If this is a bad idea for *some* reason, make sure to add an `attacker is self` check to INNARDS_OUT.
        if self.hp <= 0:
            return "", 0
        previous_hp = self.hp
        damage = max(1, damage)
        
        # Magic guard
        if self.ability(attacker=attacker, move=move) == Ability.MAGIC_GUARD and move is None and attacker is not self:
            return f"{self.name}'s magic guard protected it from damage!\n", 0
        
        # Substitute
        if (
            self.substitute
            and move is not None and move.is_affected_by_substitute() and not move.is_sound_based()
            and (attacker is None or attacker.ability() != Ability.INFILTRATOR)
        ):
            msg += f"{self.name}'s substitute took {damage} damage{source}!\n"
            new_hp = max(0, self.substitute - damage)
            true_damage = self.substitute - new_hp
            self.substitute = new_hp
            if self.substitute == 0:
                msg += f"{self.name}'s substitute broke!\n"
            return msg, true_damage
        
        # Damage blocking forms / abilities
        if move is not None:
            if self.ability(attacker=attacker, move=move) == Ability.DISGUISE and self._name == "Mimikyu":
                if self.form("Mimikyu-busted"):
                    msg += f"{self.name}'s disguise was busted!\n"
                    msg += self.damage(self.starting_hp // 8, battle, source="losing its disguise")
                    return msg, 0
            if self.ability(attacker=attacker, move=move) == Ability.ICE_FACE and self._name == "Eiscue" and move.damage_class == DamageClass.PHYSICAL:
                if self.form("Eiscue-noice"):
                    msg += f"{self.name}'s ice face was busted!\n"
                    return msg, 0
        
        # OHKO protection
        self.dmg_this_turn = True
        if damage >= self.hp and move is not None:
            if self.endure:
                msg += f"{self.name} endured the hit!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.ability(attacker=attacker, move=move) == Ability.STURDY:
                msg += f"{self.name} endured the hit with its Sturdy!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.held_item == "focus-sash":
                msg += f"{self.name} held on using its focus sash!\n"
                damage = self.hp - 1
                self.held_item.use()
            elif self.held_item == "focus-band" and not random.randrange(10):
                msg += f"{self.name} held on using its focus band!\n"
                damage = self.hp - 1
        
        # Apply the damage
        dropped_below_half = self.hp > self.starting_hp / 2
        dropped_below_quarter = self.hp > self.starting_hp / 4
        
        new_hp = max(0, self.hp - damage)
        true_damage = self.hp - new_hp
        self.hp = new_hp
        
        dropped_below_half = dropped_below_half and self.hp <= self.starting_hp / 2
        dropped_below_quarter = dropped_below_quarter and self.hp <= self.starting_hp / 4
        if source:
            source = f" from {source}"
        msg += f"{self.name} took {damage} damage{source}!\n"
        self.num_hits += 1
        
        # Drain
        if drain_heal_ratio is not None and attacker is not None:
            heal = true_damage * drain_heal_ratio
            if attacker.held_item == "big-root":
                heal = heal * 1.3
            heal = int(heal)
            if self.ability() == Ability.LIQUID_OOZE:
                msg += attacker.damage(heal, battle, source=f"{self.name}'s liquid ooze")
            else:
                if not attacker.heal_block.active():
                    msg += attacker.heal(heal, source=source)
        
        if self.hp == 0:
            msg += self.faint(battle, move=move, attacker=attacker)
            if (
                self.ability() == Ability.AFTERMATH
                and attacker is not None
                and attacker is not self
                and attacker.ability() != Ability.DAMP
                and move is not None
                and move.makes_contact(attacker)
            ):
                msg += attacker.damage(attacker.starting_hp // 4, battle, source=f"{self.name}'s aftermath")
            if attacker is not None and attacker.ability() == Ability.MOXIE:
                msg += attacker.append_attack(1, attacker=attacker, source="its moxie")
            if attacker is not None and attacker.ability() == Ability.BEAST_BOOST:
                stats = (
                    (attacker.get_raw_attack(), attacker.append_attack),
                    (attacker.get_raw_defense(), attacker.append_defense),
                    (attacker.get_raw_spatk(), attacker.append_spatk),
                    (attacker.get_raw_spdef(), attacker.append_spdef),
                    (attacker.get_raw_speed(), attacker.append_speed),
                )
                append_func = sorted(stats, reverse=True, key=lambda s: s[0])[0][1]
                msg += append_func(1, attacker=attacker, source="its beast boost")
            if attacker is not None and self.ability() == Ability.INNARDS_OUT:
                msg += attacker.damage(previous_hp, battle, attacker=self, source=f"{self.name}'s innards out")
        elif move is not None and move_type is not None:
            if move_type == ElementType.FIRE and self.nv.freeze():
                self.nv.reset()
                msg += f"{self.name} thawed out!\n"
            if self.ability() == Ability.COLOR_CHANGE and move_type not in self.type_ids:
                self.type_ids = [move_type]
                t = ElementType(move_type).name.lower()
                msg += f"{self.name} changed its color, transforming into a {t} type!\n"
            if self.ability() == Ability.ANGER_POINT and critical:
                msg += self.append_attack(6, attacker=self, source="its anger point")
            if self.ability() == Ability.WEAK_ARMOR and move.damage_class == DamageClass.PHYSICAL and attacker is not self:
                msg += self.append_defense(-1, attacker=self, source="its weak armor")
                msg += self.append_speed(2, attacker=self, source="its weak armor")
            if self.ability() == Ability.JUSTIFIED and move_type == ElementType.DARK:
                msg += self.append_attack(1, attacker=self, source="justified")
            if self.ability() == Ability.RATTLED and move_type in (ElementType.BUG, ElementType.DARK, ElementType.GHOST):
                msg += self.append_speed(1, attacker=self, source="its rattled")
            if self.ability() == Ability.STAMINA:
                msg += self.append_defense(1, attacker=self, source="its stamina")
            if self.ability() == Ability.WATER_COMPACTION and move_type == ElementType.WATER:
                msg += self.append_defense(2, attacker=self, source="its water compaction")
            if self.ability() == Ability.BERSERK and dropped_below_half:
                msg += self.append_spatk(1, attacker=self, source="its berserk")
            if self.ability() == Ability.ANGER_SHELL and dropped_below_half:
                msg += self.append_attack(1, attacker=self, source="its anger shell")
                msg += self.append_spatk(1, attacker=self, source="its anger shell")
                msg += self.append_speed(1, attacker=self, source="its anger shell")
                msg += self.append_defense(-1, attacker=self, source="its anger shell")
                msg += self.append_spdef(-1, attacker=self, source="its anger shell")
            if self.ability() == Ability.STEAM_ENGINE and move_type in (ElementType.FIRE, ElementType.WATER):
                msg += self.append_speed(6, attacker=self, source="its steam engine")
            if self.ability() == Ability.THERMAL_EXCHANGE and move_type == ElementType.FIRE:
                msg += self.append_attack(1, attacker=self, source="its thermal exchange")
            if self.ability() == Ability.WIND_RIDER and move.is_wind():
                msg += self.append_attack(1, attacker=self, source="its wind rider")
            if self.ability() == Ability.COTTON_DOWN and attacker is not None:
                msg += attacker.append_speed(-1, attacker=self, source=f"{self.name}'s cotton down")
            if self.ability() == Ability.SAND_SPIT:
                msg += battle.weather.set("sandstorm", self)
            if self.ability() == Ability.SEED_SOWER and battle.terrain.item is None:
                msg += battle.terrain.set("grassy", self)
            if self.ability() == Ability.ELECTROMORPHOSIS:
                self.charge.set_turns(2)
                msg += f"{self.name} became charged by its electromorphosis!\n"
            if self.ability() == Ability.WIND_POWER and move.is_wind():
                self.charge.set_turns(2)
                msg += f"{self.name} became charged by its wind power!\n"
            if self.ability() == Ability.TOXIC_DEBRIS and move.damage_class == DamageClass.PHYSICAL:
                if attacker is not None and attacker is not self and attacker.owner.toxic_spikes < 2:
                    attacker.owner.toxic_spikes += 1
                    msg += f"Toxic spikes were scattered around the feet of {attacker.owner.name}'s team because of {self.name}'s toxic debris!\n"
            if self.illusion_name is not None:
                self._name = self.illusion__name
                self.name = self.illusion_name
                self.illusion__name = None
                self.illusion_name = None
                msg += f"{self.name}'s illusion broke!\n"
            if self.held_item == "air-balloon":
                self.held_item.remove()
                msg += f"{self.name}'s air balloon popped!\n"
        
        if move is not None:
            self.last_move_damage = (max(1, damage), move.damage_class)
            if self.bide is not None:
                self.bide += damage
            if self.rage:
                msg += self.append_attack(1, attacker=self, source="its rage")
            if attacker is not None:
                if (
                    self.ability() == Ability.CURSED_BODY
                    and not attacker.disable.active()
                    and move in attacker.moves
                    and random.randint(1, 100) <= 30
                ):
                    if attacker.ability() == Ability.AROMA_VEIL:
                        msg += f"{attacker.name}'s aroma veil protects its move from being disabled!\n"
                    else:
                        attacker.disable.set(move, 4)
                        msg += f"{attacker.name}'s {move.pretty_name} was disabled by {self.name}'s cursed body!\n"
                if attacker.ability() == Ability.MAGICIAN and not attacker.held_item.has_item() and self.held_item.can_remove():
                    self.held_item.transfer(attacker.held_item)
                    msg += f"{attacker.name} stole {attacker.held_item.name} using its magician!\n"
                if attacker.held_item == "shell-bell":
                    # Shell bell does not trigger when a move is buffed by sheer force.
                    if attacker.ability() != Ability.SHEER_FORCE or move.effect_chance is None:
                        msg += attacker.heal(damage // 8, source="its shell bell")
        
        # Retreat
        if dropped_below_half and sum(x.hp > 0 for x in self.owner.party) > 1:
            if self.ability() == Ability.WIMP_OUT:
                msg += f"{self.name} wimped out and retreated!\n"
                msg += self.remove(battle)
            elif self.ability() == Ability.EMERGENCY_EXIT:
                msg += f"{self.name} used the emergency exit and retreated!\n"
                msg += self.remove(battle)
        
        # Gulp Missile
        if attacker is not None and self._name in ("Cramorant-gulping", "Cramorant-gorging") and self.owner.has_alive_pokemon():
            prey = "pikachu" if self._name == "Cramorant-gorging" else "arrokuda"
            if self.form("Cramorant"):
                msg += attacker.damage(attacker.starting_hp // 4, battle, source=f"{self.name} spitting out its {prey}")
                if prey == "arrokuda":
                    msg += attacker.append_defense(-1, attacker=self, source=f"{self.name} spitting out its {prey}")
                elif prey == "pikachu":
                    msg += attacker.nv.apply_status("paralysis", battle, attacker=self, source=f"{self.name} spitting out its {prey}")
        
        # Berries
        if self.held_item.should_eat_berry_damage(attacker):
            msg += self.held_item.eat_berry(attacker=attacker, move=move)
        
        # Contact
        if move is not None and attacker is not None and move.makes_contact(attacker):
            # Affects ATTACKER
            if attacker.held_item != "protective-pads":
                if self.beak_blast:
                    msg += attacker.nv.apply_status("burn", battle, attacker=self, source=f"{self.name}'s charging beak blast")
                if self.ability() == Ability.STATIC:
                    if random.randint(1, 100) <= 30:
                        msg += attacker.nv.apply_status("paralysis", battle, attacker=self, source=f"{self.name}'s static")
                if self.ability() == Ability.POISON_POINT:
                    if random.randint(1, 100) <= 30:
                        msg += attacker.nv.apply_status("poison", battle, attacker=self, source=f"{self.name}'s poison point")
                if self.ability() == Ability.FLAME_BODY:
                    if random.randint(1, 100) <= 30:
                        msg += attacker.nv.apply_status("burn", battle, attacker=self, source=f"{self.name}'s flame body")
                if self.ability() == Ability.ROUGH_SKIN and self.owner.has_alive_pokemon():
                    msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{self.name}'s rough skin")
                if self.ability() == Ability.IRON_BARBS and self.owner.has_alive_pokemon():
                    msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{self.name}'s iron barbs")
                if self.ability() == Ability.EFFECT_SPORE:
                    if (
                        attacker.ability() != Ability.OVERCOAT
                        and ElementType.GRASS not in attacker.type_ids
                        and attacker.held_item != "safety-glasses"
                        and random.randint(1, 100) <= 30
                    ):
                        status = random.choice(["paralysis", "poison", "sleep"])
                        msg += attacker.nv.apply_status(status, battle, attacker=self)
                if self.ability() == Ability.CUTE_CHARM and random.randint(1, 100) <= 30:
                    msg += attacker.infatuate(self, source=f"{self.name}'s cute charm")
                if self.ability() == Ability.MUMMY and attacker.ability() != Ability.MUMMY and attacker.ability_changeable():
                    attacker.ability_id = Ability.MUMMY
                    msg += f"{attacker.name} gained mummy from {self.name}!\n"
                    msg += attacker.send_out_ability(self, battle)
                if self.ability() == Ability.LINGERING_AROMA and attacker.ability() != Ability.LINGERING_AROMA and attacker.ability_changeable():
                    attacker.ability_id = Ability.LINGERING_AROMA
                    msg += f"{attacker.name} gained lingering aroma from {self.name}!\n"
                    msg += attacker.send_out_ability(self, battle)
                if self.ability() == Ability.GOOEY:
                    msg += attacker.append_speed(-1, attacker=self, source=f"touching {self.name}'s gooey body")
                if self.ability() == Ability.TANGLING_HAIR:
                    msg += attacker.append_speed(-1, attacker=self, source=f"touching {self.name}'s tangled hair")
                if self.held_item == "rocky-helmet" and self.owner.has_alive_pokemon():
                    msg += attacker.damage(attacker.starting_hp // 6, battle, source=f"{self.name}'s rocky helmet")
            # Pickpocket is not included in the protective pads protection
            if (
                self.ability() == Ability.PICKPOCKET
                and not self.held_item.has_item()
                and attacker.held_item.has_item()
                and attacker.held_item.can_remove()
            ):
                if attacker.ability() == Ability.STICKY_HOLD:
                    msg += f"{attacker.name}'s sticky hand kept hold of its item!\n"
                else:
                    attacker.held_item.transfer(self.held_item)
                    msg += f"{attacker.name}'s {self.held_item.name} was stolen!\n"
            # Affects DEFENDER
            if attacker.ability() == Ability.POISON_TOUCH:
                if random.randint(1, 100) <= 30:
                    msg += self.nv.apply_status("poison", battle, attacker=attacker, move=move, source=f"{attacker.name}'s poison touch")
            # Affects BOTH
            if attacker.held_item != "protective-pads":
                if self.ability() == Ability.PERISH_BODY and not attacker.perish_song.active():
                    attacker.perish_song.set_turns(4)
                    self.perish_song.set_turns(4)
                    msg += f"All pokemon will faint after 3 turns from {self.name}'s perish body!\n"
            if self.ability() == Ability.WANDERING_SPIRIT and attacker.ability_changeable() and attacker.ability_giveable():
                msg += f"{attacker.name} swapped abilities with {self.name} because of {self.name}'s wandering spirit!\n"
                self.ability_id, attacker.ability_id = attacker.ability_id, self.ability_id
                ability_name = Ability(self.ability_id).pretty_name
                msg += f"{self.name} acquired {ability_name}!\n"
                msg += self.send_out_ability(attacker, battle)
                ability_name = Ability(attacker.ability_id).pretty_name
                msg += f"{attacker.name} acquired {ability_name}!\n"
                msg += attacker.send_out_ability(self, battle)
        
        return msg, true_damage
    
    def heal(self, health, *, source: str=""):
        """
        Heals a pokemon by a certain amount.
        
        Handles heal-affecting items and abilities, and keeping health within bounds.
        Returns a formatted message.
        """
        msg = ""
        health = max(1, int(health))
        #greater than is used to prevent zygarde's hp incresing form from losing its extra health
        if self.hp >= self.starting_hp:
            return msg
        #safety to prevent errors from ""reviving"" pokes
        if self.hp == 0:
            return msg
        if self.heal_block.active():
            return msg
        health = min(self.starting_hp - self.hp, health)
        self.hp += health
        if source:
            source = f" from {source}"
        msg += f"{self.name} healed {health} hp{source}!\n"
        return msg
    
    def confuse(self, *, attacker=None, move=None, source=""):
        """
        Attempts to confuse this poke.
        
        Returns a formatted message.
        """ 
        if self.substitute:
            return ""
        if self.confusion.active():
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.OWN_TEMPO:
            return ""
        self.confusion.set_turns(random.randint(2, 5))
        if source:
            source = f" from {source}"
        msg = f"{self.name} is confused{source}!\n"
        if self.held_item.should_eat_berry_status(attacker):
            msg += self.held_item.eat_berry(attacker=attacker, move=move)
        return msg
    
    def flinch(self, *, attacker=None, move=None, source=""):
        """
        Attepts to flinch this poke.
        
        Returns a formatted message.
        """
        msg = ""
        if self.substitute:
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.INNER_FOCUS:
            return f"{self.name} resisted the urge to flinch with its inner focus!\n"
        self.flinched = True
        if source:
            source = f" from {source}"
        msg += f"{self.name} flinched{source}!\n"
        if self.ability() == Ability.STEADFAST:
            msg += self.append_speed(1, attacker=self, source="its steadfast")
        return msg
        
    def infatuate(self, attacker, *, move=None, source=""):
        """
        Attepts to cause attacker to infatuate this poke.
        
        Returns a formatted message.
        """
        msg = ""
        if source:
            source = f" from {source}"
        if "-x" in (self.gender, attacker.gender):
            return ""
        if self.gender == attacker.gender:
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.OBLIVIOUS:
            return f"{self.name} is too oblivious to fall in love!\n"
        if self.ability(move=move, attacker=attacker) == Ability.AROMA_VEIL:
            return f"{self.name}'s aroma veil protects it from being infatuated!\n"
        self.infatuated = attacker
        msg += f"{self.name} fell in love{source}!\n"
        if self.held_item == "destiny-knot":
            msg += attacker.infatuate(self, source=f"{self.name}'s destiny knot")
        return msg
    
    def calculate_raw_stat(self, base, iv, ev, nature):
        """
        Helper function to calculate a raw stat using the base, IV, EV, level, and nature.
        
        https://bulbapedia.bulbagarden.net/wiki/Stat#Determination_of_stats "In Generation III onward"
        """
        return round((((2 * base + iv + (ev / 4)) * self.level) / 100) + 5) * nature
    
    @staticmethod
    def calculate_stat(stat, stat_stage, *, crop=False):
        """Calculates a stat based on that stat's stage changes."""
        if crop == "bottom":
            stat_stage = max(stat_stage, 0)
        elif crop == "top":
            stat_stage = min(stat_stage, 0)
        stage_multiplier = {
            -6: 2/8,
            -5: 2/7,
            -4: 2/6,
            -3: 2/5,
            -2: 2/4,
            -1: 2/3,
            0: 1,
            1: 3/2,
            2: 2,
            3: 5/2,
            4: 3,
            5: 7/2,
            6: 4,
        }
        return stage_multiplier[stat_stage] * stat
    
    def get_raw_attack(self, *, check_power_trick=True, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_trick and check_power_trick:
            return self.get_raw_defense(check_power_trick=False, check_power_shift=check_power_shift)
        if self.power_shift and check_power_shift:
            return self.get_raw_defense(check_power_trick=check_power_trick, check_power_shift=False)
        stat = self.calculate_raw_stat(self.attack, self.atkiv, self.atkev, self.nature_stat_deltas["Attack"])
        if self.attack_split is not None:
            stat = (stat + self.attack_split) // 2
        return stat
    
    def get_raw_defense(self, *, check_power_trick=True, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_trick and check_power_trick:
            return self.get_raw_attack(check_power_trick=False, check_power_shift=check_power_shift)
        if self.power_shift and check_power_shift:
            return self.get_raw_attack(check_power_trick=check_power_trick, check_power_shift=False)
        stat = self.calculate_raw_stat(self.defense, self.defiv, self.defev, self.nature_stat_deltas["Defense"])
        if self.defense_split is not None:
            stat = (stat + self.defense_split) // 2
        return stat
    
    def get_raw_spatk(self, *, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_shift and check_power_shift:
            return self.get_raw_spdef(check_power_shift=False)
        stat = self.calculate_raw_stat(self.spatk, self.spatkiv, self.spatkev, self.nature_stat_deltas["Special attack"])
        if self.spatk_split is not None:
            stat = (stat + self.spatk_split) // 2
        return stat
    
    def get_raw_spdef(self, *, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_shift and check_power_shift:
            return self.get_raw_spatk(check_power_shift=False)
        stat = self.calculate_raw_stat(self.spdef, self.spdefiv, self.spdefev, self.nature_stat_deltas["Special defense"])
        if self.spdef_split is not None:
            stat = (stat + self.spdef_split) // 2
        return stat
    
    def get_raw_speed(self):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        return self.calculate_raw_stat(self.speed, self.speediv, self.speedev, self.nature_stat_deltas["Speed"])
    
    def get_attack(self, battle, *, critical=False, ignore_stages=False):
        """Helper method to call calculate_stat for attack."""
        attack = self.get_raw_attack()
        if not ignore_stages:
            attack = self.calculate_stat(attack, self.attack_stage, crop="bottom" if critical else False)
        if self.ability() == Ability.GUTS and self.nv.current:
            attack *= 1.5
        if self.ability() == Ability.SLOW_START and self.active_turns < 5:
            attack *= .5
        if self.ability() in (Ability.HUGE_POWER, Ability.PURE_POWER):
            attack *= 2
        if self.ability() == Ability.HUSTLE:
            attack *= 1.5
        if self.ability() == Ability.DEFEATIST and self.hp <= self.starting_hp / 2:
            attack *= .5
        if self.ability() == Ability.GORILLA_TACTICS:
            attack *= 1.5
        if self.ability() == Ability.FLOWER_GIFT and battle.weather.get() in ("sun", "h-sun"):
            attack *= 1.5
        if self.ability() == Ability.ORICHALCUM_PULSE and battle.weather.get() in ("sun", "h-sun"):
            attack *= 4/3
        if self.held_item == "choice-band":
            attack *= 1.5
        if self.held_item == "light-ball" and self._name == "Pikachu":
            attack *= 2
        if self.held_item == "thick-club" and self._name in ("Cubone", "Marowak", "Marowak-alola"):
            attack *= 2
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.TABLETS_OF_RUIN:
                attack *= .75
        if (
            (self.ability() == Ability.PROTOSYNTHESIS and (battle.weather.get() in ("sun", "h-sun") or self.held_item == "booster-energy"))
            or (self.ability() == Ability.QUARK_DRIVE and (battle.terrain.item == "electric" or self.held_item == "booster-energy"))
        ):
            if all(self.get_raw_attack() >= x for x in (self.get_raw_defense(), self.get_raw_spatk(), self.get_raw_spdef(), self.get_raw_speed())):
                attack *= 1.3
        return attack
    
    def get_defense(self, battle, *, critical=False, ignore_stages=False, attacker=None, move=None):
        """Helper method to call calculate_stat for defense."""
        if battle.wonder_room.active():
            defense = self.get_raw_spdef()
        else:
            defense = self.get_raw_defense()
        if not ignore_stages:
            defense = self.calculate_stat(defense, self.defense_stage, crop="top" if critical else False)
        if self.ability(attacker=attacker, move=move) == Ability.MARVEL_SCALE and self.nv.current:
            defense *= 1.5
        if self.ability(attacker=attacker, move=move) == Ability.FUR_COAT:
            defense *= 2
        if self.ability(attacker=attacker, move=move) == Ability.GRASS_PELT and battle.terrain.item == "grassy":
            defense *= 1.5
        if self.held_item == "eviolite" and self.can_still_evolve:
            defense *= 1.5
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.SWORD_OF_RUIN:
                defense *= .75
        if (
            (self.ability() == Ability.PROTOSYNTHESIS and (battle.weather.get() in ("sun", "h-sun") or self.held_item == "booster-energy"))
            or (self.ability() == Ability.QUARK_DRIVE and (battle.terrain.item == "electric" or self.held_item == "booster-energy"))
        ):
            if (
                self.get_raw_defense() > self.get_raw_attack()
                and all(self.get_raw_defense() >= x for x in (self.get_raw_spatk(), self.get_raw_spdef(), self.get_raw_speed()))
            ):
                defense *= 1.3
        return defense
    
    def get_spatk(self, battle, *, critical=False, ignore_stages=False):
        """Helper method to call calculate_stat for spatk."""
        spatk = self.get_raw_spatk()
        if not ignore_stages:
            spatk = self.calculate_stat(spatk, self.spatk_stage, crop="bottom" if critical else False)
        if self.ability() == Ability.DEFEATIST and self.hp <= self.starting_hp / 2:
            spatk *= .5
        if self.ability() == Ability.SOLAR_POWER and battle.weather.get() in ("sun", "h-sun"):
            spatk *= 1.5
        if self.ability() == Ability.HADRON_ENGINE and battle.terrain.item == "grassy":
            spatk *= 4/3
        if self.held_item == "choice-specs":
            spatk *= 1.5
        if self.held_item == "deep-sea-tooth" and self._name == "Clamperl":
            spatk *= 2
        if self.held_item == "light-ball" and self._name == "Pikachu":
            spatk *= 2
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.VESSEL_OF_RUIN:
                spatk *= .75
        if (
            (self.ability() == Ability.PROTOSYNTHESIS and (battle.weather.get() in ("sun", "h-sun") or self.held_item == "booster-energy"))
            or (self.ability() == Ability.QUARK_DRIVE and (battle.terrain.item == "electric" or self.held_item == "booster-energy"))
        ):
            if (
                all(self.get_raw_spatk() >= x for x in (self.get_raw_spdef(), self.get_raw_speed()))
                and all(self.get_raw_spatk() > x for x in (self.get_raw_attack(), self.get_raw_defense()))
            ):
                spatk *= 1.3
        return spatk
    
    def get_spdef(self, battle, *, critical=False, ignore_stages=False, attacker=None, move=None):
        """Helper method to call calculate_stat for spdef."""
        if battle.wonder_room.active():
            spdef = self.get_raw_defense()
        else:
            spdef = self.get_raw_spdef()
        if not ignore_stages:
            spdef = self.calculate_stat(spdef, self.spdef_stage, crop="top" if critical else False)
        if battle.weather.get() == "sandstorm" and ElementType.ROCK in self.type_ids:
            spdef *= 1.5
        if self.ability(attacker=attacker, move=move) == Ability.FLOWER_GIFT and battle.weather.get() in ("sun", "h-sun"):
            spdef *= 1.5
        if self.held_item == "deep-sea-scale" and self._name == "Clamperl":
            spdef *= 2
        if self.held_item == "assault-vest":
            spdef *= 1.5
        if self.held_item == "eviolite" and self.can_still_evolve:
            spdef *= 1.5
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.BEADS_OF_RUIN:
                spdef *= .75
        if (
            (self.ability() == Ability.PROTOSYNTHESIS and (battle.weather.get() in ("sun", "h-sun") or self.held_item == "booster-energy"))
            or (self.ability() == Ability.QUARK_DRIVE and (battle.terrain.item == "electric" or self.held_item == "booster-energy"))
        ):
            if (
                self.get_raw_spdef() >= self.get_raw_speed()
                and all(self.get_raw_spdef() > x for x in (self.get_raw_attack(), self.get_raw_defense(), self.get_raw_spatk()))
            ):
                spdef *= 1.3
        return spdef
    
    def get_speed(self, battle):
        """Helper method to call calculate_stat for speed."""
        #Always active stage changes
        speed = self.calculate_stat(self.get_raw_speed(), self.speed_stage)
        if self.nv.paralysis() and not self.ability() == Ability.QUICK_FEET:
            speed //= 2
        if self.held_item == "iron-ball":
            speed //= 2
        if self.owner.tailwind.active():
            speed *= 2
        if self.ability() == Ability.SLUSH_RUSH and battle.weather.get() == "hail":
            speed *= 2
        if self.ability() == Ability.SAND_RUSH and battle.weather.get() == "sandstorm":
            speed *= 2
        if self.ability() == Ability.SWIFT_SWIM and battle.weather.get() in ("rain", "h-rain"):
            speed *= 2
        if self.ability() == Ability.CHLOROPHYLL and battle.weather.get() in ("sun", "h-sun"):
            speed *= 2
        if self.ability() == Ability.SLOW_START and self.active_turns < 5:
            speed *= .5
        if self.ability() == Ability.UNBURDEN and not self.held_item.has_item() and self.held_item.ever_had_item:
            speed *= 2
        if self.ability() == Ability.QUICK_FEET and self.nv.current:
            speed *= 1.5
        if self.ability() == Ability.SURGE_SURFER and battle.terrain.item == "electric":
            speed *= 2
        if self.held_item == "choice-scarf":
            speed *= 1.5
        if (
            (self.ability() == Ability.PROTOSYNTHESIS and (battle.weather.get() in ("sun", "h-sun") or self.held_item == "booster-energy"))
            or (self.ability() == Ability.QUARK_DRIVE and (battle.terrain.item == "electric" or self.held_item == "booster-energy"))
        ):
            if all(self.get_raw_speed() > x for x in (self.get_raw_attack(), self.get_raw_defense(), self.get_raw_spatk(), self.get_raw_spdef())):
                speed *= 1.5
        return speed
    
    def get_accuracy(self, battle):
        """Helper method to calculate accuracy stage."""
        return self.accuracy_stage
        
    def get_evasion(self, battle):
        """Helper method to calculate evasion stage."""
        return self.evasion_stage
    
    def append_attack(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for attack."""
        return self.append_stat(stage_change, attacker, move, "attack", source, check_looping)
    
    def append_defense(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for defense."""
        return self.append_stat(stage_change, attacker, move, "defense", source, check_looping)
    
    def append_spatk(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for special attack."""
        return self.append_stat(stage_change, attacker, move, "special attack", source, check_looping)
    
    def append_spdef(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for special defense."""
        return self.append_stat(stage_change, attacker, move, "special defense", source, check_looping)
    
    def append_speed(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for speed."""
        return self.append_stat(stage_change, attacker, move, "speed", source, check_looping)
    
    def append_accuracy(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for accuracy."""
        return self.append_stat(stage_change, attacker, move, "accuracy", source, check_looping)
    
    def append_evasion(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for evasion."""
        return self.append_stat(stage_change, attacker, move, "evasion", source, check_looping)
        
    def append_stat(self, stage_change: int, attacker, move, stat: str, source: str, check_looping: bool=True):
        """
        Adds a stat stage change to this pokemon.
        
        Returns a formatted string describing the stat change.
        """
        msg = ""
        if self.substitute and attacker is not self and attacker is not None:
            return ""
        if source:
            source = f" from {source}"
        delta_msgs = {
            -3: f"{self.name}'s {stat} severely fell{source}!\n",
            -2: f"{self.name}'s {stat} harshly fell{source}!\n",
            -1: f"{self.name}'s {stat} fell{source}!\n",
            1: f"{self.name}'s {stat} rose{source}!\n",
            2: f"{self.name}'s {stat} rose sharply{source}!\n",
            3: f"{self.name}'s {stat} rose drastically{source}!\n",
        }
        delta = stage_change
        if self.ability(attacker=attacker, move=move) == Ability.SIMPLE:
            delta *= 2
        if self.ability(attacker=attacker, move=move) == Ability.CONTRARY:
            delta *= -1
        
        if stat == "attack":
            current_stage = self.attack_stage
        elif stat == "defense":
            current_stage = self.defense_stage
        elif stat == "special attack":
            current_stage = self.spatk_stage
        elif stat == "special defense":
            current_stage = self.spdef_stage
        elif stat == "speed":
            current_stage = self.speed_stage
        elif stat == "accuracy":
            current_stage = self.accuracy_stage
        elif stat == "evasion":
            current_stage = self.evasion_stage
        else:
            raise ValueError(f"invalid stat {stat}")
        
        if delta < 0:
            #-6 -5 -4 ..  2
            # 0 -1 -2 .. -8
            cap = (current_stage * -1) - 6
            delta = max(delta, cap)
            if delta == 0:
                return f"{self.name}'s {stat} won't go any lower!\n"
        else:
            # 6  5  4 .. -2
            # 0  1  2 ..  8
            cap = (current_stage * -1) + 6
            delta = min(delta, cap)
            if delta == 0:
                return f"{self.name}'s {stat} won't go any higher!\n"
        if delta < 0 and attacker is not self:
            if self.ability(attacker=attacker, move=move) in (Ability.CLEAR_BODY, Ability.WHITE_SMOKE, Ability.FULL_METAL_BODY):
                ability_name = Ability(self.ability_id).pretty_name
                return f"{self.name}'s {ability_name} prevented its {stat} from being lowered!\n"
            if self.ability(attacker=attacker, move=move) == Ability.HYPER_CUTTER and stat == "attack":
                return f"{self.name}'s claws stayed sharp because of its hyper cutter!\n"
            if self.ability(attacker=attacker, move=move) == Ability.KEEN_EYE and stat == "accuracy":
                return f"{self.name}'s aim stayed true because of its keen eye!\n"
            if self.ability(attacker=attacker, move=move) == Ability.BIG_PECKS and stat == "defense":
                return f"{self.name}'s defense stayed strong because of its big pecks!\n"
            if self.owner.mist.active() and (attacker is None or attacker.ability() != Ability.INFILTRATOR):
                return f"The mist around {self.name}'s feet prevented its {stat} from being lowered!\n"
            if self.ability(attacker=attacker, move=move) == Ability.DEFIANT:
                msg += self.append_attack(2, attacker=self, source="its defiance")
            if self.ability(attacker=attacker, move=move) == Ability.COMPETITIVE:
                msg += self.append_spatk(2, attacker=self, source="its competitiveness")
            if self.ability(attacker=attacker, move=move) == Ability.FLOWER_VEIL and ElementType.GRASS in self.type_ids:
                return ""
            if self.ability(attacker=attacker, move=move) == Ability.MIRROR_ARMOR and attacker is not None and check_looping:
                msg += f"{self.name} reflected the stat change with its mirror armor!\n"
                msg += attacker.append_stat(delta, self, None, stat, "", check_looping=False)
                return msg
        if delta > 0:
            self.stat_incresed = True
            # TODO: fix this hacky way of doing this, but probably not until multi battles...
            battle = self.held_item.battle
            for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
                if poke is not None and poke is not self and poke.ability() == Ability.OPPORTUNIST and check_looping:
                    msg += f"{poke.name} seizes the opportunity to boost its stat with its opportunist!\n"
                    msg += poke.append_stat(delta, poke, None, stat, "", check_looping=False)
        elif delta < 0:
            self.stat_decreased = True
        
        if stat == "attack":
            self.attack_stage += delta
        elif stat == "defense":
            self.defense_stage += delta
        elif stat == "special attack":
            self.spatk_stage += delta
        elif stat == "special defense":
            self.spdef_stage += delta
        elif stat == "speed":
            self.speed_stage += delta
        elif stat == "accuracy":
            self.accuracy_stage += delta
        elif stat == "evasion":
            self.evasion_stage += delta
        else:
            raise ValueError(f"invalid stat {stat}")
        
        formatted_delta = min(max(delta, -3), 3)
        msg += delta_msgs[formatted_delta]
        return msg
    
    def grounded(self, battle, *, attacker=None, move=None):
        """
        Returns True if this pokemon is considered "grounded".
        
        Explicit grounding applies first, then explicit ungrounding, then implicit grounding.
        """
        if battle.gravity.active():
            return True
        if self.held_item == "iron-ball":
            return True
        if self.grounded_by_move:
            return True
        if ElementType.FLYING in self.type_ids and not self.roost:
            return False
        if self.ability(attacker=attacker, move=move) == Ability.LEVITATE:
            return False
        if self.held_item == "air-balloon":
            return False
        if self.magnet_rise.active():
            return False
        if self.telekinesis.active():
            return False
        return True
    
    def transform(self, otherpoke):
        """Transforms this poke into otherpoke."""
        self.choice_move = None
        self._name = otherpoke._name
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        self.attack = otherpoke.attack
        self.defense = otherpoke.defense
        self.spatk = otherpoke.spatk
        self.spdef = otherpoke.spdef
        self.speed = otherpoke.speed
        self.hpiv = otherpoke.hpiv
        self.atkiv = otherpoke.atkiv
        self.defiv = otherpoke.defiv
        self.spatkiv = otherpoke.spatkiv
        self.spdefiv = otherpoke.spdefiv
        self.speediv = otherpoke.speediv
        self.hpev = otherpoke.hpev
        self.atkev = otherpoke.atkev
        self.defev = otherpoke.defev
        self.spatkev = otherpoke.spatkev
        self.spdefev = otherpoke.spdefev
        self.speedev = otherpoke.speedev
        self.moves = [move.copy() for move in otherpoke.moves]
        for m in self.moves:
            m.pp = 5
        self.ability_id = otherpoke.ability_id
        self.type_ids = otherpoke.type_ids.copy()
        self.attack_stage = otherpoke.attack_stage
        self.defense_stage = otherpoke.defense_stage
        self.spatk_stage = otherpoke.spatk_stage
        self.spdef_stage = otherpoke.spdef_stage
        self.speed_stage = otherpoke.speed_stage
        self.accuracy_stage = otherpoke.accuracy_stage
        self.evasion_stage = otherpoke.evasion_stage
    
    def form(self, form: str):
        """
        Changes this poke's form to the provided form.
        
        This changes its name and base stats, and may affect moves, abilities, and items.
        Returns True if the poke successfully reformed.
        """
        if form not in self.base_stats:
            return False
        self._name = form
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        self.attack = self.base_stats[self._name][1]
        self.defense = self.base_stats[self._name][2]
        self.spatk = self.base_stats[self._name][3]
        self.spdef = self.base_stats[self._name][4]
        self.speed = self.base_stats[self._name][5]
        self.attack_split = None
        self.spatk_split = None
        self.defense_split = None
        self.spdef_split = None
        self.autotomize = 0
        return True
    
    def effectiveness(self, attacker_type: ElementType, battle, *, attacker=None, move=None):
        """Calculates a float representing the effectiveness of `attacker_type` damage on this poke."""
        if attacker_type == ElementType.TYPELESS:
            return 1
        effectiveness = 1
        for defender_type in self.type_ids:
            if defender_type == ElementType.TYPELESS:
                continue
            if move is not None and move.effect == 380 and defender_type == ElementType.WATER:
                effectiveness *= 2
                continue
            if move is not None and move.effect == 373 and defender_type == ElementType.FLYING and not self.grounded(battle, attacker=attacker, move=move):
                return 1 # Ignores secondary types if defender is flying type and not grounded
            if self.roost and defender_type == ElementType.FLYING:
                continue
            if self.foresight and attacker_type in (ElementType.FIGHTING, ElementType.NORMAL) and defender_type == ElementType.GHOST:
                continue
            if self.miracle_eye and attacker_type == ElementType.PSYCHIC and defender_type == ElementType.DARK:
                continue
            if attacker_type in (ElementType.FIGHTING, ElementType.NORMAL) and defender_type == ElementType.GHOST and attacker is not None and attacker.ability() == Ability.SCRAPPY:
                continue
            if attacker_type == ElementType.GROUND and defender_type == ElementType.FLYING and self.grounded(battle, attacker=attacker, move=move):
                continue
            e = battle.type_effectiveness[(attacker_type, defender_type)] / 100
            if defender_type == ElementType.FLYING and e > 1 and move is not None and battle.weather.get() == "h-wind":
                e = 1
            if battle.inverse_battle:
                if e < 1:
                    e = 2
                elif e > 1:
                    e = 0.5
            effectiveness *= e
        if attacker_type == ElementType.FIRE and self.tar_shot:
            effectiveness *= 2
        return effectiveness
    
    def weight(self, *, attacker=None, move=None):
        """
        Returns this pokemon's current weight.
        
        Dynamically modifies the weight based on the ability of this pokemon.
        """
        cur_ability = self.ability(attacker=attacker, move=move)
        cur_weight = self.starting_weight
        if cur_ability == Ability.HEAVY_METAL:
            cur_weight *= 2
        if cur_ability == Ability.LIGHT_METAL:
            cur_weight //= 2
            cur_weight = max(1, cur_weight)
        cur_weight -= self.autotomize * 1000
        cur_weight = max(1, cur_weight)
        return cur_weight
        
    
    def ability(self, *, attacker=None, move=None):
        """
        Returns this pokemon's current ability.
        
        Returns None in cases where the ability is blocked or nullified.
        """
        # Currently there are two categories of ability ignores, and both only apply when a move is used.
        # Since this could change, the method signature is flexable. However, without both present, it
        # should not consider the existing options.
        if move is None or attacker is None or attacker is self:
            return self.ability_id
        if not self.ability_ignorable():
            return self.ability_id
        if move.effect in (411, 460):
            return None
        if attacker.ability_id in (Ability.MOLD_BREAKER, Ability.TURBOBLAZE, Ability.TERAVOLT, Ability.NEUTRALIZING_GAS):
            return None
        if attacker.ability_id == Ability.MYCELIUM_MIGHT and move.damage_class == DamageClass.STATUS:
            return None
        return self.ability_id
    
    def ability_changeable(self):
        """Returns True if this pokemon's current ability can be changed."""
        return self.ability_id not in (
            Ability.MULTITYPE, Ability.STANCE_CHANGE, Ability.SCHOOLING, Ability.COMATOSE,
            Ability.SHIELDS_DOWN, Ability.DISGUISE, Ability.RKS_SYSTEM, Ability.BATTLE_BOND,
            Ability.POWER_CONSTRUCT, Ability.ICE_FACE, Ability.GULP_MISSILE, Ability.ZERO_TO_HERO
        )
    
    def ability_giveable(self):
        """Returns True if this pokemon's current ability can be given to another pokemon."""
        return self.ability_id not in (
            Ability.TRACE, Ability.FORECAST, Ability.FLOWER_GIFT, Ability.ZEN_MODE, Ability.ILLUSION,
            Ability.IMPOSTER, Ability.POWER_OF_ALCHEMY, Ability.RECEIVER, Ability.DISGUISE, Ability.STANCE_CHANGE,
            Ability.POWER_CONSTRUCT, Ability.ICE_FACE, Ability.HUNGER_SWITCH, Ability.GULP_MISSILE, Ability.ZERO_TO_HERO
        )
    
    def ability_ignorable(self):
        """Returns True if this pokemon's current ability can be ignored."""
        return self.ability_id in (
            Ability.AROMA_VEIL, Ability.BATTLE_ARMOR, Ability.BIG_PECKS, Ability.BULLETPROOF, Ability.CLEAR_BODY,
            Ability.CONTRARY, Ability.DAMP, Ability.DAZZLING, Ability.DISGUISE, Ability.DRY_SKIN, Ability.FILTER,
            Ability.FLASH_FIRE, Ability.FLOWER_GIFT, Ability.FLOWER_VEIL, Ability.FLUFFY, Ability.FRIEND_GUARD,
            Ability.FUR_COAT, Ability.HEATPROOF, Ability.HEAVY_METAL, Ability.HYPER_CUTTER, Ability.ICE_FACE,
            Ability.ICE_SCALES, Ability.IMMUNITY, Ability.INNER_FOCUS, Ability.INSOMNIA, Ability.KEEN_EYE,
            Ability.LEAF_GUARD, Ability.LEVITATE, Ability.LIGHT_METAL, Ability.LIGHTNING_ROD, Ability.LIMBER,
            Ability.MAGIC_BOUNCE, Ability.MAGMA_ARMOR, Ability.MARVEL_SCALE, Ability.MIRROR_ARMOR, Ability.MOTOR_DRIVE,
            Ability.MULTISCALE, Ability.OBLIVIOUS, Ability.OVERCOAT, Ability.OWN_TEMPO, Ability.PASTEL_VEIL,
            Ability.PUNK_ROCK, Ability.QUEENLY_MAJESTY, Ability.SAND_VEIL, Ability.SAP_SIPPER, Ability.SHELL_ARMOR,
            Ability.SHIELD_DUST, Ability.SIMPLE, Ability.SNOW_CLOAK, Ability.SOLID_ROCK, Ability.SOUNDPROOF,
            Ability.STICKY_HOLD, Ability.STORM_DRAIN, Ability.STURDY, Ability.SUCTION_CUPS, Ability.SWEET_VEIL,
            Ability.TANGLED_FEET, Ability.TELEPATHY, Ability.THICK_FAT, Ability.UNAWARE, Ability.VITAL_SPIRIT,
            Ability.VOLT_ABSORB, Ability.WATER_ABSORB, Ability.WATER_BUBBLE, Ability.WATER_VEIL, Ability.WHITE_SMOKE,
            Ability.WONDER_GUARD, Ability.WONDER_SKIN, Ability.ARMOR_TAIL, Ability.EARTH_EATER, Ability.GOOD_AS_GOLD,
            Ability.PURIFYING_SALT, Ability.WELL_BAKED_BODY
        )
    
    def get_assist_move(self):
        """
        Returns a Move that can be used with assist, or None if none exists.
        
        This selects a random move from the pool of moves from pokes in the user's party that are eligable.
        """
        moves = []
        for idx, poke in enumerate(self.owner.party):
            if idx == self.owner.last_idx:
                continue
            for move in poke.moves:
                if move.selectable_by_assist():
                    moves.append(move)
        if not moves:
            return None
        return random.choice(moves)
    
    @classmethod
    async def create(cls, ctx, raw_data: dict):
        """Creates a new DuelPokemon object using the raw data provided."""
        pn = raw_data["pokname"]
        nick = raw_data["poknick"]
        hpiv = min(31, raw_data["hpiv"])
        atkiv = min(31, raw_data["atkiv"])
        defiv = min(31, raw_data["defiv"])
        spatkiv = min(31, raw_data["spatkiv"])
        spdefiv = min(31, raw_data["spdefiv"])
        speediv = min(31, raw_data["speediv"])
        hpev = raw_data["hpev"]
        atkev = raw_data["atkev"]
        defev = raw_data["defev"]
        spaev = raw_data["spatkev"]
        spdev = raw_data["spdefev"]
        speedev = raw_data["speedev"]
        plevel = raw_data["pokelevel"]
        shiny = raw_data["shiny"]
        radiant = raw_data["radiant"]
        skin = raw_data["skin"]
        id = raw_data["id"]
        hitem = raw_data["hitem"]
        happiness = raw_data["happiness"]
        moves = raw_data["moves"]
        ab_index = raw_data["ability_index"]
        nature = raw_data["nature"]
        gender = raw_data["gender"]

        nature = await find_one(ctx, "natures", {"identifier": nature.lower()})
        dec_stat_id = nature["decreased_stat_id"]
        inc_stat_id = nature["increased_stat_id"]
        dec_stat = await find_one(ctx, "stat_types", {"id": dec_stat_id})
        inc_stat = await find_one(ctx, "stat_types", {"id": inc_stat_id})
        dec_stat = dec_stat["identifier"].capitalize().replace("-", " ")
        inc_stat = inc_stat["identifier"].capitalize().replace("-", " ")
        nature_stat_deltas = {"Attack": 1, "Defense": 1, "Special attack": 1, "Special defense": 1, "Speed": 1}
        flavor_map = {
            "Attack": "spicy",
            "Defense": "sour",
            "Speed": "sweet",
            "Special attack": "dry",
            "Special defense": "bitter",
        }
        disliked_flavor = ""
        if dec_stat != inc_stat:
            nature_stat_deltas[dec_stat] = 0.9
            nature_stat_deltas[inc_stat] = 1.1
            disliked_flavor = flavor_map[dec_stat]

        #Deform pokes that are formed into battle forms that they should not start off in
        if pn == "Mimikyu-busted":
            pn = "Mimikyu"
        if pn in ("Cramorant-gorging", "Cramorant-gulping"):
            pn = "Cramorant"
        if pn == "Eiscue-noice":
            pn = "Eiscue"
        if pn == "Darmanitan-zen":
            pn = "Darmanitan"
        if pn == "Darmanitan-zen-galar":
            pn = "Darmanitan-galar"
        if pn == "Aegislash-blade":
            pn = "Aegislash"
        if pn in ("Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet"):
            pn = "Minior"
        if pn == "Wishiwashi" and plevel >= 20:
            pn = "Wishiwashi-school"
        if pn == "Wishiwashi-school" and plevel < 20:
            pn = "Wishiwashi"
        if pn == "Greninja-ash":
            pn = "Greninja"
        if pn == "Zygarde-complete":
            pn = "Zygarde"
        if pn == "Morpeko-hangry":
            pn = "Morpeko"
        if pn == "Cherrim-sunshine":
            pn = "Cherrim"
        if pn in ("Castform-snowy", "Castform-rainy", "Castform-sunny"):
            pn = "Castform"
        if pn in (
            "Arceus-dragon",
            "Arceus-dark",
            "Arceus-ground",
            "Arceus-fighting",
            "Arceus-fire",
            "Arceus-ice",
            "Arceus-bug",
            "Arceus-steel",
            "Arceus-grass",
            "Arceus-psychic",
            "Arceus-fairy",
            "Arceus-flying",
            "Arceus-water",
            "Arceus-ghost",
            "Arceus-rock",
            "Arceus-poison",
            "Arceus-electric",
        ):
            pn = "Arceus"
        if pn in (
            "Silvally-psychic",
            "Silvally-fairy",
            "Silvally-flying",
            "Silvally-water",
            "Silvally-ghost",
            "Silvally-rock",
            "Silvally-poison",
            "Silvally-electric",
            "Silvally-dragon",
            "Silvally-dark",
            "Silvally-ground",
            "Silvally-fighting",
            "Silvally-fire",
            "Silvally-ice",
            "Silvally-bug",
            "Silvally-steel",
            "Silvally-grass",
        ):
            pn = "Silvally"
        if pn == "Palafin-hero":
            pn = "Palafin"
        if pn.endswith("-mega-x") or pn.endswith("-mega-y"):
            pn = pn[:-7]
        if pn.endswith("-mega"):
            pn = pn[:-5]
        #TODO: Meloetta, Shaymin

        form_info = await find_one(ctx, "forms", {"identifier": pn.lower()})
        #List of type ids
        type_ids = (await find_one(ctx, "ptypes", {"id": form_info["pokemon_id"]}))["types"]
        
        #6 element list of stat values (int)
        stats = (await find_one(ctx, "pokemon_stats", {"pokemon_id": form_info["pokemon_id"]}))["stats"]
        pokemonHp = stats[0]
        
        #Store the base stats for all forms of this poke
        base_stats = {}
        base_stats[pn] = stats
        extra_forms = []
        if pn == "Mimikyu":
            extra_forms = ["Mimikyu-busted"]
        if pn == "Cramorant":
            extra_forms = ["Cramorant-gorging", "Cramorant-gulping"]
        if pn == "Eiscue":
            extra_forms = ["Eiscue-noice"]
        if pn == "Darmanitan":
            extra_forms = ["Darmanitan-zen"]
        if pn == "Darmanitan-galar":
            extra_forms = ["Darmanitan-zen-galar"]
        if pn == "Aegislash":
            extra_forms = ["Aegislash-blade"]
        if pn == "Minior":
            extra_forms = ["Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet"]
        if pn == "Wishiwashi":
            extra_forms = ["Wishiwashi-school"]
        if pn == "Wishiwashi-school":
            extra_forms = ["Wishiwashi"]
        if pn == "Greninja":
            extra_forms = ["Greninja-ash"]
        if pn == "Zygarde":
            extra_forms = ["Zygarde-complete"]
        if pn == "Zygarde-10":
            extra_forms = ["Zygarde-complete"]
        if pn == "Morpeko":
            extra_forms = ["Morpeko-hangry"]
        if pn == "Cherrim":
            extra_forms = ["Cherrim-sunshine"]
        if pn == "Castform":
            extra_forms = ["Castform-snowy", "Castform-rainy", "Castform-sunny"]
        if pn == "Arceus":
            extra_forms = [
                "Arceus-dragon",
                "Arceus-dark",
                "Arceus-ground",
                "Arceus-fighting",
                "Arceus-fire",
                "Arceus-ice",
                "Arceus-bug",
                "Arceus-steel",
                "Arceus-grass",
                "Arceus-psychic",
                "Arceus-fairy",
                "Arceus-flying",
                "Arceus-water",
                "Arceus-ghost",
                "Arceus-rock",
                "Arceus-poison",
                "Arceus-electric",
            ]
        if pn == "Silvally":
            extra_forms = [
                "Silvally-psychic",
                "Silvally-fairy",
                "Silvally-flying",
                "Silvally-water",
                "Silvally-ghost",
                "Silvally-rock",
                "Silvally-poison",
                "Silvally-electric",
                "Silvally-dragon",
                "Silvally-dark",
                "Silvally-ground",
                "Silvally-fighting",
                "Silvally-fire",
                "Silvally-ice",
                "Silvally-bug",
                "Silvally-steel",
                "Silvally-grass",
            ]
        if pn == "Palafin":
            extra_forms = ["Palafin-hero"]
        mega_form = None
        mega_ability_id = None
        mega_type_ids = None
        if pn != "Rayquaza":
            if hitem == "mega-stone":
                mega_form = pn + "-mega"
            elif hitem == "mega-stone-x":
                mega_form = pn + "-mega-x"
            elif hitem == "mega-stone-y":
                mega_form = pn + "-mega-y"
        else:
            if "dragon-ascent" in moves:
                mega_form = pn + "-mega"
        if mega_form is not None:
            mega_form_info = await find_one(ctx, "forms", {"identifier": mega_form.lower()})
            if mega_form_info is not None:
                mega_ability = await find_one(ctx, "poke_abilities", {"pokemon_id": mega_form_info["pokemon_id"]})
                if mega_ability is None:
                    raise ValueError("mega form missing ability in `poke_abilities`")
                mega_ability_id = mega_ability["ability_id"]
                mega_types = (await find_one(ctx, "ptypes", {"id": mega_form_info["pokemon_id"]}))
                if mega_types is None:
                    raise ValueError("mega form missing types in `ptypes`")
                mega_type_ids = mega_types["types"]
                extra_forms.append(mega_form)
        
        for f_name in extra_forms:
            f_info = await find_one(ctx, "forms", {"identifier": f_name.lower()})
            f_stats = (await find_one(ctx, "pokemon_stats", {"pokemon_id": f_info["pokemon_id"]}))["stats"]
            base_stats[f_name] = f_stats

        #Builds a list of the possible ability ids for this poke, `ab_index` is the currently selected ability from this list
        ab_ids = []
        for record in await find(ctx, "poke_abilities", {"pokemon_id": form_info["pokemon_id"]}):
            ab_ids.append(record["ability_id"])

        try:
            ab_id = ab_ids[ab_index]
        #Should never happen, but better safe than sorry
        except IndexError:
            ab_id = ab_ids[0]

        if any(
            pn.endswith(suffix)
            for suffix in [
                "-bug","-summer","-marine","-elegant","-poison","-average","-altered","-winter","-trash","-incarnate",
                "-baile","-rainy","-steel","-star","-ash","-diamond","-pop-star","-fan","-school","-therian","-pau",
                "-river","-poke-ball","-kabuki","-electric","-heat","-unbound","-chill","-archipelago","-zen","-normal",
                "-mega-y","-resolute","-blade","-speed","-indigo","-dusk","-sky","-west","-sun","-dandy","-solo","-high-plains",
                "-la-reine","-50","-unova-cap","-burn","-mega-x","-monsoon","-primal","-red-striped","-blue-striped",
                "-white-striped","-ground","-super","-yellow","-polar","-cosplay","-ultra","-heart","-snowy","-sensu",
                "-eternal","-douse","-defense","-sunshine","-psychic","-modern","-natural","-tundra","-flying","-pharaoh",
                "-libre","-sunny","-autumn","-10","-orange","-standard","-land","-partner","-dragon","-plant","-pirouette",
                "-male","-hoenn-cap","-violet","-spring","-fighting","-sandstorm","-original-cap","-neutral","-fire",
                "-fairy","-attack","-black","-shock","-shield","-shadow","-grass","-continental","-overcast","-disguised",
                "-exclamation","-origin","-garden","-blue","-matron","-red-meteor","-small","-rock-star","-belle",
                "-alola-cap","-green","-active","-red","-mow","-icy-snow","-debutante","-east","-midday","-jungle","-frost",
                "-midnight","-rock","-fancy","-busted","-ordinary","-water","-phd","-ice","-spiky-eared","-savanna","-original",
                "-ghost","-meadow","-dawn","-question","-pom-pom","-female","-kalos-cap","-confined","-sinnoh-cap","-aria",
                "-dark","-ocean","-wash","-white","-mega","-sandy","-complete","-large","-crowned","-ice-rider","-shadow-rider",
                "-zen-galar","-rapid-strike","-noice","-hangry",
            ]
        ):
            name = pn.lower().split("-")[0]
            pid = (await find_one(ctx, "forms", {"identifier": name}))["pokemon_id"]
        else:
            pid = form_info["pokemon_id"]

        #True if any possible future evo exists
        can_still_evolve = bool(await find_one(ctx, "pfile", {"evolves_from_species_id": pid}))
        #Unreleased pokemon that is treated like a form in the bot, monkeypatch fix.
        if pn == "Floette-eternal":
            can_still_evolve = False

        #This stat can (/has to) be calculated ahead of time, as it does not change between forms.
        #If transform copied HP, I would probably take up drinking...
        pokemonHp = round((((2 * pokemonHp + hpiv + (hpev / 4)) * plevel) / 100) + plevel + 10)
        
        hitem = await find_one(ctx, "items", {"identifier": hitem})

        if pn == "Shedinja":
            pokemonHp = 1
        
        weight = (await find_one(ctx, "forms", {"identifier": pn.lower()}))["weight"]
        if weight is None:
            weight = 20
        
        object_moves = []
        for move in moves:
            type_override = None
            if move.startswith("hidden-power-"):
                element = move.split("-")[2]
                move = "hidden-power"
                type_override = ElementType[element.upper()]
            move = await find_one(ctx, "moves", {"identifier": move})
            if move is None:
                move = await find_one(ctx, "moves", {"identifier": "tackle"})
            else:
                if type_override is not None:
                    move["type_id"] = type_override
            object_moves.append(Move(**move))
        p = cls(
            pokemon_id=pid,
            name=pn,
            nickname=nick,
            base_stats=base_stats,
            hp=pokemonHp,
            hpiv=hpiv,
            atkiv=atkiv,
            defiv=defiv,
            spatkiv=spatkiv,
            spdefiv=spdefiv,
            speediv=speediv,
            hpev=hpev,
            atkev=atkev,
            defev=defev,
            spatkev=spaev,
            spdefev=spdev,
            speedev=speedev,
            level=plevel,
            nature_stat_deltas=nature_stat_deltas,
            shiny=shiny,
            radiant=radiant,
            skin=skin,
            type_ids=type_ids,
            mega_type_ids=mega_type_ids,
            id=id,
            held_item=hitem,
            happiness=happiness,
            moves=object_moves,
            ability_id=ab_id,
            mega_ability_id=mega_ability_id,
            weight=weight,
            gender=gender,
            can_still_evolve=can_still_evolve,
            disliked_flavor=disliked_flavor,
        )

        return p

    def __repr__(self):
        return f"DuelPokemon(name={self._name!r}, hp={self.hp!r})"
