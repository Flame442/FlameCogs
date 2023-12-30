import random
from .enums import Ability, DamageClass, ElementType, MoveTarget
from .misc import LockedMove, BatonPass, ExpiringEffect, ExpiringItem


class Move():
    """Represents an instance of a move."""
    def __init__(self, **kwargs):
        """Accepts a dict from the mongo moves table."""
        self.id = kwargs["id"]
        self.name = kwargs["identifier"]
        self.pretty_name = self.name.capitalize().replace("-", " ")
        self.power = kwargs["power"]
        self.pp = kwargs["pp"]
        self.starting_pp = self.pp
        self.accuracy = kwargs["accuracy"]
        self.priority = kwargs["priority"]
        self.type = kwargs["type_id"]
        self.damage_class = kwargs["damage_class_id"]
        self.effect = kwargs["effect_id"]
        self.effect_chance = kwargs["effect_chance"]
        self.target = kwargs["target_id"]
        self.crit_rate = kwargs["crit_rate"]
        self.min_hits = kwargs["min_hits"]
        self.max_hits = kwargs["max_hits"]
        self.used = False
    
    def setup(self, attacker, defender, battle):
        """
        Sets up anything this move needs to do prior to normal move execution.
        
        Returns a formatted message.
        """
        msg = ""
        if self.effect == 129 and (isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.effect in (128, 154, 229, 347, 493)):
            msg += self.use(attacker, defender, battle)
        if self.effect == 171:
            msg += f"{attacker.name} is focusing on its attack!\n"
        if self.effect == 404:
            attacker.beak_blast = True
        return msg
    
    def use(self, attacker, defender, battle, *, use_pp=True, override_sleep=False, bounced=False):
        """
        Uses this move as attacker on defender.
        
        Returns a string of formatted results of the move.
        """
        #This handles an edge case for moves that cause the target to swap out
        if attacker.has_moved and use_pp:
            return ""
        self.used = True
        if use_pp:
            attacker.has_moved = True
            attacker.last_move = self
            attacker.beak_blast = False
            attacker.destiny_bond = False
            # Reset semi-invulnerable status in case this is turn 2
            attacker.dive = False
            attacker.dig = False
            attacker.fly = False
            attacker.shadow_force = False
        current_type = self.get_type(attacker, defender, battle)
        effect_chance = self.get_effect_chance(attacker, defender, battle)
        msg = ""

        if self.effect in (5, 126, 168, 254, 336, 398, 458) and attacker.nv.freeze():
            attacker.nv.reset()
            msg += f"{attacker.name} thawed out!\n"
        if attacker.nv.freeze():
            if use_pp and not random.randint(0, 4):
                attacker.nv.reset()
                msg += f"{attacker.name} is no longer frozen!\n"
            else:
                msg += f"{attacker.name} is frozen solid!\n"
                if self.effect == 28:
                    attacker.locked_move = None
                return msg
        if attacker.nv.paralysis() and not random.randint(0, 3):
            msg += f"{attacker.name} is paralyzed! It can't move!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.infatuated is defender and not random.randint(0, 1):
            msg += f"{attacker.name} is in love with {defender.name} and can't bare to hurt them!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.flinched:
            msg += f"{attacker.name} flinched! It can't move!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.nv.sleep():
            if use_pp and attacker.nv.sleep_timer.next_turn():
                attacker.nv.reset()
                msg += f"{attacker.name} woke up!\n"
            elif self.effect not in (93, 98) and attacker.ability() != Ability.COMATOSE and not override_sleep:
                msg += f"{attacker.name} is fast asleep!\n"
                if self.effect == 28:
                    attacker.locked_move = None
                return msg 
        if attacker.confusion.next_turn():
            msg += f"{attacker.name} is no longer confused!\n"
        if attacker.confusion.active() and not random.randint(0, 2):
            msg += f"{attacker.name} hurt itself in its confusion!\n"
            msgadd, numhits = self.confusion().attack(attacker, attacker, battle)
            msg += msgadd
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.ability() == Ability.TRUANT and attacker.truant_turn % 2:
            msg += f"{attacker.name} is loafing around!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        
        if not bounced:
            msg += f"{attacker.name} used {self.pretty_name}!\n"
            attacker.metronome.use(self.name)
        
        # PP
        if attacker.locked_move is None and use_pp:
            self.pp -= 1
            if defender.ability(attacker=attacker, move=self) == Ability.PRESSURE and self.pp != 0:
                if self.targets_opponent() or self.effect in (113, 193, 196, 250, 267):
                    self.pp -= 1
            if self.pp == 0:
                msg += "It ran out of PP!\n"

        #User is using a choice item and had not used a move yet, set that as their only move.
        if attacker.choice_move is None and use_pp:
            if attacker.held_item in ("choice-scarf", "choice-band", "choice-specs"):
                attacker.choice_move = self
            elif attacker.ability() == Ability.GORILLA_TACTICS:
                attacker.choice_move = self

        # Stance change
        if attacker.ability() == Ability.STANCE_CHANGE:
            if attacker._name == "Aegislash" and self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                if attacker.form("Aegislash-blade"):
                    msg += f"{attacker.name} draws its blade!\n"
            if attacker._name == "Aegislash-blade" and self.effect == 356:
                if attacker.form("Aegislash"):
                    msg += f"{attacker.name} readies its shield!\n"

        # Powder damage
        if attacker.powdered and current_type == ElementType.FIRE and battle.weather.get() != "h-rain":
            msg += attacker.damage(attacker.starting_hp // 4, battle, source="its powder exploding")
            return msg

        # Snatch steal
        if defender.snatching and self.selectable_by_snatch():
            msg += f"{defender.name} snatched the move!\n"
            msg += self.use(defender, attacker, battle, use_pp=False)
            return msg

        # Check Fail
        if not self.check_executable(attacker, defender, battle):
            msg += "But it failed!\n"
            if self.effect in (28, 118):
                attacker.locked_move = None
            attacker.last_move_failed = True
            return msg
        
        # Setup for multi-turn moves
        if attacker.locked_move is None:
            # 2 turn moves
            # During sun, this move does not need to charge
            if self.effect == 152 and battle.weather.get() not in ("sun", "h-sun"):
                attacker.locked_move = LockedMove(self, 2)
            if self.effect in (40, 76, 81, 146, 156, 256, 257, 264, 273, 332, 333, 366, 451):
                attacker.locked_move = LockedMove(self, 2)
            # 3 turn moves
            if self.effect == 27:
                attacker.locked_move = LockedMove(self, 3)
                attacker.bide = 0
            if self.effect == 160:
                attacker.locked_move = LockedMove(self, 3)
                attacker.uproar.set_turns(3)
                if attacker.nv.sleep():
                    attacker.nv.reset()
                    msg += f"{attacker.name} woke up!\n"
                if defender.nv.sleep():
                    defender.nv.reset()
                    msg += f"{defender.name} woke up!\n"
            # 5 turn moves
            if self.effect == 118:
                attacker.locked_move = LockedMove(self, 5)
            # 2-3 turn moves
            if self.effect == 28:
                attacker.locked_move = LockedMove(self, random.randint(2, 3))
            #2-5 turn moves
            if self.effect == 160:
                attacker.locked_move = LockedMove(self, random.randint(2, 5))
            # Semi-invulnerable
            if self.effect == 256:
                attacker.dive = True
            if self.effect == 257:
                attacker.dig = True
            if self.effect in (156, 264):
                attacker.fly = True
            if self.effect == 273:
                attacker.shadow_force = True
        
        # Early exits for moves that hit a certain turn when it is not that turn
        # Turn 1 hit moves
        if self.effect == 81 and attacker.locked_move:
            if attacker.locked_move.turn != 0:
                msg += "It's recharging!\n"
                return msg
        
        # Turn 2 hit moves
        elif self.effect in (40, 76, 146, 152, 156, 256, 257, 264, 273, 332, 333, 366, 451) and attacker.locked_move:
            if attacker.locked_move.turn != 1:
                if self.effect == 146:
                    msg += attacker.append_defense(1, attacker=attacker, move=self)
                elif self.effect == 451:
                    msg += attacker.append_spatk(1, attacker=attacker, move=self)
                else:
                    msg += "It's charging up!\n"
                    # Gulp Missile
                    if self.effect == 256 and attacker.ability() == Ability.GULP_MISSILE and attacker._name == "Cramorant":
                        if attacker.hp > attacker.starting_hp // 2:
                            if attacker.form("Cramorant-gulping"):
                                msg += f"{attacker.name} gulped up an arrokuda!\n"
                        else:
                            if attacker.form("Cramorant-gorging"):
                                msg += f"{attacker.name} gulped up a pikachu!\n"
                return msg
        
        # Turn 3 hit moves
        elif self.effect == 27:
            if attacker.locked_move.turn != 2:
                msg += "It's storing energy!\n"
                return msg
        
        # User Faints
        if self.effect in (8, 444):
            msg += attacker.faint(battle)

        # User takes damage
        if self.effect == 420:
            msg += attacker.damage(attacker.starting_hp // 2, battle, source="its head exploding (tragic)")
        
        # User's type changes
        if current_type != ElementType.TYPELESS:
            if attacker.ability() == Ability.PROTEAN:
                attacker.type_ids = [current_type]
                t = ElementType(current_type).name.lower()
                msg += f"{attacker.name} transformed into a {t} type using its protean!\n"
            if attacker.ability() == Ability.LIBERO:
                attacker.type_ids = [current_type]
                t = ElementType(current_type).name.lower()
                msg += f"{attacker.name} transformed into a {t} type using its libero!\n"
        
        # Status effects reflected by magic coat or magic bounce.
        if self.is_affected_by_magic_coat() and (defender.ability(attacker=attacker, move=self) == Ability.MAGIC_BOUNCE or defender.magic_coat) and not bounced:
            msg += f"It was reflected by {defender.name}'s magic bounce!\n"
            hm = defender.has_moved
            msg += self.use(defender, attacker, battle, use_pp=False, bounced=True)
            defender.has_moved = hm
            return msg
        
        # Check Effect
        if not self.check_effective(attacker, defender, battle) and not bounced:
            msg += "It had no effect...\n"
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            attacker.last_move_failed = True
            return msg
        
        # Check Semi-invulnerable - treated as a miss
        if not self.check_semi_invulnerable(attacker, defender, battle):
            msg += f"{defender.name} avoided the attack!\n"
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            return msg
        
        # Check Protection
        was_hit, msgdelta = self.check_protect(attacker, defender, battle)
        if not was_hit:
            msg += f"{defender.name} was protected against the attack!\n"
            msg += msgdelta
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            return msg
        
        # Check Hit
        if not self.check_hit(attacker, defender, battle):
            msg += "But it missed!\n"
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            return msg
        
        # Absorbs
        if self.targets_opponent() and self.effect != 459:
            # Heal
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.VOLT_ABSORB:
                msg += f"{defender.name}'s volt absorb absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) == Ability.WATER_ABSORB:
                msg += f"{defender.name}'s water absorb absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) == Ability.DRY_SKIN:
                msg += f"{defender.name}'s dry skin absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            if current_type == ElementType.GROUND and defender.ability(attacker=attacker, move=self) == Ability.EARTH_EATER:
                msg += f"{defender.name}'s earth eater absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            # Stat stage changes
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.LIGHTNING_ROD:
                msg += f"{defender.name}'s lightning rod absorbed the move!\n"
                msg += defender.append_spatk(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.MOTOR_DRIVE:
                msg += f"{defender.name}'s motor drive absorbed the move!\n"
                msg += defender.append_speed(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) == Ability.STORM_DRAIN:
                msg += f"{defender.name}'s storm drain absorbed the move!\n"
                msg += defender.append_spatk(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.GRASS and defender.ability(attacker=attacker, move=self) == Ability.SAP_SIPPER:
                msg += f"{defender.name}'s sap sipper absorbed the move!\n"
                msg += defender.append_attack(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.FIRE and defender.ability(attacker=attacker, move=self) == Ability.WELL_BAKED_BODY:
                msg += f"{defender.name}'s well baked body absorbed the move!\n"
                msg += defender.append_defense(2, attacker=defender, move=self)
                return msg
            # Other
            if current_type == ElementType.FIRE and defender.ability(attacker=attacker, move=self) == Ability.FLASH_FIRE:
                defender.flash_fire = True
                msg += f"{defender.name} used its flash fire to buff its fire type moves!\n"
                return msg
        
        # Metronome
        if self.effect == 84:
            attacker.has_moved = False
            raw = random.choice(battle.metronome_moves_raw)
            msg += Move(**raw).use(attacker, defender, battle)
            return msg
        
        # Brick break - runs before damage calculation
        if self.effect == 187:
            if defender.owner.aurora_veil.active():
                defender.owner.aurora_veil.set_turns(0)
                msg += f"{defender.name}'s aurora veil wore off!\n"
            if defender.owner.light_screen.active():
                defender.owner.light_screen.set_turns(0)
                msg += f"{defender.name}'s light screen wore off!\n"
            if defender.owner.reflect.active():
                defender.owner.reflect.set_turns(0)
                msg += f"{defender.name}'s reflect wore off!\n"
        
        # Sleep talk
        if self.effect == 98:
            move = random.choice([m for m in attacker.moves if m.selectable_by_sleep_talk()])
            msg += move.use(attacker, defender, battle, use_pp=False, override_sleep=True)
            return msg
        
        # Mirror Move/Copy Cat
        if self.effect in (10, 243):
            msg += defender.last_move.use(attacker, defender, battle, use_pp=False)
            return msg
        
        # Me First
        if self.effect == 242:
            msg += defender.owner.selected_action.use(attacker, defender, battle, use_pp=False)
            return msg
        
        # Assist
        if self.effect == 181:
            msg += attacker.get_assist_move().use(attacker, defender, battle, use_pp=False)
            return msg
        
        # Spectral Thief
        if self.effect == 410:
            if defender.attack_stage > 0:
                stage = defender.attack_stage
                defender.attack_stage = 0
                msg += f"{defender.name}'s attack stage was reset!\n"
                msg += attacker.append_attack(stage, attacker=attacker, move=self)
            if defender.defense_stage > 0:
                stage = defender.defense_stage
                defender.defense_stage = 0
                msg += f"{defender.name}'s defense stage was reset!\n"
                msg += attacker.append_defense(stage, attacker=attacker, move=self)
            if defender.spatk_stage > 0:
                stage = defender.spatk_stage
                defender.spatk_stage = 0
                msg += f"{defender.name}'s special attack stage was reset!\n"
                msg += attacker.append_spatk(stage, attacker=attacker, move=self)
            if defender.spdef_stage > 0:
                stage = defender.spdef_stage
                defender.spdef_stage = 0
                msg += f"{defender.name}'s special defense stage was reset!\n"
                msg += attacker.append_spdef(stage, attacker=attacker, move=self)
            if defender.speed_stage > 0:
                stage = defender.speed_stage
                defender.speed_stage = 0
                msg += f"{defender.name}'s speed stage was reset!\n"
                msg += attacker.append_speed(stage, attacker=attacker, move=self)
            if defender.evasion_stage > 0:
                stage = defender.evasion_stage
                defender.evasion_stage = 0
                msg += f"{defender.name}'s evasion stage was reset!\n"
                msg += attacker.append_evasion(stage, attacker=attacker, move=self)
            if defender.accuracy_stage > 0:
                stage = defender.accuracy_stage
                defender.accuracy_stage = 0
                msg += f"{defender.name}'s accuracy stage was reset!\n"
                msg += attacker.append_accuracy(stage, attacker=attacker, move=self) 
        
        # Future Sight
        if self.effect == 149:
            defender.owner.future_sight.set((attacker, self), 3)
            msg += f"{attacker.name} foresaw an attack!\n"
            return msg
        
        # Present
        if self.effect == 123:
            action = random.randint(1, 4)
            if action == 1:
                if defender.hp == defender.starting_hp:
                    msg += "It had no effect!\n"
                else:
                    msg += defender.heal(defender.starting_hp // 4, source=f"{attacker.name}'s present")
                return msg
            if action == 2:
                power = 40
            elif action == 3:
                power = 80
            else:
                power = 120
            m = self.present(power)
            msgadd, _ = m.attack(attacker, defender, battle)
            msg += msgadd
            return msg
        
        # Incinerate
        if self.effect == 315 and defender.held_item.is_berry(only_active=False):
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                defender.held_item.remove()
                msg += f"{defender.name}'s berry was incinerated!\n"
        
        # Poltergeist 
        if self.effect == 446:
            msg += f"{defender.name} is about to be attacked by its {defender.held_item.get()}!\n"
        
        numhits = 0
        # Turn 1 hit moves
        if self.effect == 81 and attacker.locked_move:
            if attacker.locked_move.turn == 0:
                msgadd, numhits = self.attack(attacker, defender, battle)
                msg += msgadd
                
        # Turn 2 hit moves
        elif self.effect in (40, 76, 146, 152, 156, 256, 257, 264, 273, 332, 333, 366, 451) and attacker.locked_move:
            if attacker.locked_move.turn == 1:
                if self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                    msgadd, numhits = self.attack(attacker, defender, battle)
                    msg += msgadd
                
        # Turn 3 hit moves
        elif self.effect == 27:
            if attacker.locked_move.turn == 2:
                msg += defender.damage(attacker.bide * 2, battle, move=self, move_type=current_type, attacker=attacker)
                attacker.bide = None
                numhits = 1
        
        # Counter attack moves
        elif self.effect == 228:
            msg += defender.damage(int(1.5 * attacker.last_move_damage[0]), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 145:
            msg += defender.damage(2 * attacker.last_move_damage[0], battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 90:
            msg += defender.damage(2 * attacker.last_move_damage[0], battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        
        # Static-damage moves
        elif self.effect == 41:
            msg += defender.damage(defender.hp // 2, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 42:
            msg += defender.damage(40, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 88:
            msg += defender.damage(attacker.level, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 89:
            # 0.5-1.5, increments of .1
            scale = (random.randint(0, 10) / 10.0) + .5
            msg += defender.damage(int(attacker.level * scale), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 131:
            msg += defender.damage(20, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 190:
            msg += defender.damage(max(0, defender.hp - attacker.hp), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 39:
            msg += defender.damage(defender.hp, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 321:
            msg += defender.damage(attacker.hp, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 413:
            msg += defender.damage(3 * (defender.hp // 4), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        
        # Beat up, a stupid move
        elif self.effect == 155:
            for poke in attacker.owner.party:
                if defender.hp == 0:
                    break
                if poke.hp == 0:
                    continue
                if poke is attacker:
                    msgadd, nh = self.attack(attacker, defender, battle)
                    msg += msgadd
                    numhits += nh
                else:
                    if poke.nv.current:
                        continue
                    fake_move = {
                        "id": 251,
                        "identifier": "beat-up",
                        "power": (poke.get_raw_attack() // 10) + 5,
                        "pp": 100,
                        "accuracy": 100,
                        "priority": 0,
                        "type_id": ElementType.DARK,
                        "damage_class_id": DamageClass.PHYSICAL,
                        "effect_id": 1,
                        "effect_chance": None,
                        "target_id": 10,
                        "crit_rate": 0,
                        "min_hits": None,
                        "max_hits": None,
                    }
                    fake_move = Move(**fake_move)
                    msgadd, nh = fake_move.attack(attacker, defender, battle)
                    msg += msgadd
                    numhits += nh
        
        # Other damaging moves
        elif self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
            msgadd, numhits = self.attack(attacker, defender, battle)
            msg += msgadd
        
        # Fusion Flare/Bolt effect tracking
        battle.last_move_effect = self.effect
        
        # Stockpile
        if self.effect == 161:
            attacker.stockpile += 1
            msg += f"{attacker.name} stores energy!\n"
        if self.effect == 162:
            msg += attacker.append_defense(-attacker.stockpile, attacker=attacker, move=self)
            msg += attacker.append_spdef(-attacker.stockpile, attacker=attacker, move=self)
            attacker.stockpile = 0

        # Healing
        if self.effect in (33, 215, 471):
            msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect in (434, 457):
            msg += attacker.heal(attacker.starting_hp // 4)
        if self.effect == 310:
            if attacker.ability() == Ability.MEGA_LAUNCHER:
                msg += defender.heal((defender.starting_hp * 3) // 4)
            else:
                msg += defender.heal(defender.starting_hp // 2)
        if self.effect == 133:
            if battle.weather.get() in ("sun", "h-sun"):
                msg += attacker.heal((attacker.starting_hp * 2) // 3)
            elif battle.weather.get() == "h-wind":
                msg += attacker.heal(attacker.starting_hp // 2)
            elif battle.weather.get():
                msg += attacker.heal(attacker.starting_hp // 4)
            else:
                msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect == 85:
            defender.leech_seed = True
            msg += f"{defender.name} was seeded!\n"
        if self.effect == 163:
            msg += attacker.heal(attacker.starting_hp // {1: 4, 2: 2, 3: 1}[attacker.stockpile], source="stockpiled energy")
            msg += attacker.append_defense(-attacker.stockpile, attacker=attacker, move=self)
            msg += attacker.append_spdef(-attacker.stockpile, attacker=attacker, move=self)
            attacker.stockpile = 0
        if self.effect == 180:
            attacker.owner.wish.set(attacker.starting_hp // 2)
            msg += f"{attacker.name} makes a wish!\n"
        if self.effect == 382:
            if battle.weather.get() == "sandstorm":
                msg += attacker.heal((attacker.starting_hp * 2) // 3)
            else:
                msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect == 387:
            if battle.terrain.item == "grassy":
                msg += attacker.heal((attacker.starting_hp * 2) // 3)
            else:
                msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect == 388:
            msg += attacker.heal(defender.get_attack(battle))
        if self.effect == 400:
            status = defender.nv.current
            defender.nv.reset()
            msg += f"{defender.name}'s {status} was healed!\n"
            msg += attacker.heal(attacker.starting_hp // 2)

        # Status effects
        if self.effect in (5, 126, 201, 254, 274, 333, 458, 465):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
        if self.effect == 168:
            msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
        if self.effect == 429 and defender.stat_incresed:
            msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
        if self.effect == 37:
            status = random.choice(["burn", "freeze", "paralysis"])
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status(status, battle, attacker=attacker, move=self)
        if self.effect == 464:
            status = random.choice(["poison", "paralysis", "sleep"])
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status(status, battle, attacker=attacker, move=self)
        if self.effect in (6, 261, 275, 380, 462):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("freeze", battle, attacker=attacker, move=self)
        if self.effect in (7, 153, 263, 264, 276, 332, 372):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
        if self.effect == 68:
            msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
        if self.effect in (3, 78, 210, 447, 461):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("poison", battle, attacker=attacker, move=self)
        if self.effect in (67, 390, 486):
            msg += defender.nv.apply_status("poison", battle, attacker=attacker, move=self)
        if self.effect == 203:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("b-poison", battle, attacker=attacker, move=self)
        if self.effect == 34:
            msg += defender.nv.apply_status("b-poison", battle, attacker=attacker, move=self)
        if self.effect == 2:
            if self.id == 464 and attacker._name != "Darkrai":
                msg += f"{attacker.name} can't use the move!\n"
            else:
                msg += defender.nv.apply_status("sleep", battle, attacker=attacker, move=self)
        if self.effect == 330:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("sleep", battle, attacker=attacker, move=self)
        if self.effect == 38:
            msg += attacker.nv.apply_status("sleep", battle, attacker=attacker, move=self, turns=3, force=True)
            if attacker.nv.sleep():
                msg += f"{attacker.name}'s slumber restores its health back to full!\n"
                attacker.hp = attacker.starting_hp
        if self.effect in (50, 119, 167, 200):
            msg += defender.confuse(attacker=attacker, move=self)
        # This checks if attacker.locked_move is not None as locked_move is cleared if the poke dies to rocky helmet or similar items
        if self.effect == 28 and attacker.locked_move is not None and attacker.locked_move.is_last_turn():
            msg += attacker.confuse()
        if self.effect in (77, 268, 334, 478):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.confuse(attacker=attacker, move=self)
        if self.effect in (194, 457, 471, 472):
            attacker.nv.reset()
            msg += f"{attacker.name}'s status was cleared!\n"
        if self.effect == 386:
            if defender.nv.burn():
                defender.nv.reset()
                msg += f"{defender.name}'s burn was healed!\n"
        if self.effect == 458 and defender.nv.freeze():
            defender.nv.reset()
            msg += f"{defender.name} thawed out!\n"
        
        # Stage changes
        # +1
        if self.effect in (11, 209, 213, 278, 313, 323, 328, 392, 414, 427, 468, 472, 487):
            msg += attacker.append_attack(1, attacker=attacker, move=self)
        if self.effect in (12, 157, 161, 207, 209, 323, 367, 414, 427, 467, 468, 472):
            msg += attacker.append_defense(1, attacker=attacker, move=self)
        if self.effect in (14, 212, 291, 328, 392, 414, 427, 472):
            msg += attacker.append_spatk(1, attacker=attacker, move=self)
        if self.effect in (161, 175, 207, 212, 291, 367, 414, 427, 472):
            msg += attacker.append_spdef(1, attacker=attacker, move=self)
        if self.effect in (130, 213, 291, 296, 414, 427, 442, 469, 487):
            msg += attacker.append_speed(1, attacker=attacker, move=self)
        if self.effect in (17, 467, 471):
            msg += attacker.append_evasion(1, attacker=attacker, move=self)
        if self.effect in (278, 323):
            msg += attacker.append_accuracy(1, attacker=attacker, move=self)
        if self.effect == 139:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_defense(1, attacker=attacker, move=self)
        if self.effect in (140, 375):
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_attack(1, attacker=attacker, move=self)
        if self.effect == 277:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_spatk(1, attacker=attacker, move=self)
        if self.effect == 433:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_speed(1, attacker=attacker, move=self)
        if self.effect == 167:
            msg += defender.append_spatk(1, attacker=attacker, move=self)
        # +2
        if self.effect in (51, 309):
            msg += attacker.append_attack(2, attacker=attacker, move=self)
        if self.effect in (52, 453):
            msg += attacker.append_defense(2, attacker=attacker, move=self)
        if self.effect in (53, 285, 309, 313, 366):
            msg += attacker.append_speed(2, attacker=attacker, move=self)
        if self.effect in (54, 309, 366):
            msg += attacker.append_spatk(2, attacker=attacker, move=self)
        if self.effect in (55, 366):
            msg += attacker.append_spdef(2, attacker=attacker, move=self)
        if self.effect == 109:
            msg += attacker.append_evasion(2, attacker=attacker, move=self)
        if self.effect in (119, 432, 483):
            msg += defender.append_attack(2, attacker=attacker, move=self)
        if self.effect == 432:
            msg += defender.append_spatk(2, attacker=attacker, move=self)
        if self.effect == 359:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_defense(2, attacker=attacker, move=self)
        # -1
        if self.effect in (19, 206, 344, 347, 357, 365, 388, 412):
            msg += defender.append_attack(-1, attacker=attacker, move=self)
        if self.effect in (20, 206):
            msg += defender.append_defense(-1, attacker=attacker, move=self)
        if self.effect in (344, 347, 358, 412):
            msg += defender.append_spatk(-1, attacker=attacker, move=self)
        if self.effect == 428:
            msg += defender.append_spdef(-1, attacker=attacker, move=self)
        if self.effect in (331, 390):
            msg += defender.append_speed(-1, attacker=attacker, move=self)
        if self.effect == 24:
            msg += defender.append_accuracy(-1, attacker=attacker, move=self)
        if self.effect in (25, 259):
            msg += defender.append_evasion(-1, attacker=attacker, move=self)
        if self.effect in (69, 396):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_attack(-1, attacker=attacker, move=self)
        if self.effect in (70, 397, 435):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_defense(-1, attacker=attacker, move=self)
        if self.effect in (21, 71, 477):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_speed(-1, attacker=attacker, move=self)
        if self.effect == 72:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_spatk(-1, attacker=attacker, move=self)
        if self.effect == 73:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_spdef(-1, attacker=attacker, move=self)
        if self.effect == 74:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_accuracy(-1, attacker=attacker, move=self)
        if self.effect == 183:
            msg += attacker.append_attack(-1, attacker=attacker, move=self)
        if self.effect in (183, 230, 309, 335, 405, 438, 442):
            msg += attacker.append_defense(-1, attacker=attacker, move=self)
        if self.effect == 480:
            msg += attacker.append_spatk(-1, attacker=attacker, move=self)
        if self.effect in (230, 309, 335):
            msg += attacker.append_spdef(-1, attacker=attacker, move=self)
        if self.effect in (219, 335, 463):
            msg += attacker.append_speed(-1, attacker=attacker, move=self)
        # -2
        if self.effect in (59, 169):
            msg += defender.append_attack(-2, attacker=attacker, move=self)
        if self.effect in (60, 483):
            msg += defender.append_defense(-2, attacker=attacker, move=self)
        if self.effect == 61:
            msg += defender.append_speed(-2, attacker=attacker, move=self)
        if self.effect in (62, 169, 266):
            msg += defender.append_spatk(-2, attacker=attacker, move=self)
        if self.effect == 63:
            msg += defender.append_spdef(-2, attacker=attacker, move=self)
        if self.effect in (272, 297):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_spdef(-2, attacker=attacker, move=self)
        if self.effect == 205:
            msg += attacker.append_spatk(-2, attacker=attacker, move=self)
        if self.effect == 479:
            msg += attacker.append_speed(-2, attacker=attacker, move=self)
        # other
        if self.effect == 26:
            attacker.attack_stage = 0
            attacker.defense_stage = 0
            attacker.spatk_stage = 0
            attacker.spdef_stage = 0
            attacker.speed_stage = 0
            attacker.accuracy_stage = 0
            attacker.evasion_stage = 0
            defender.attack_stage = 0
            defender.defense_stage = 0
            defender.spatk_stage = 0
            defender.spdef_stage = 0
            defender.speed_stage = 0
            defender.accuracy_stage = 0
            defender.evasion_stage = 0
            msg += "All pokemon had their stat stages reset!\n"
        if self.effect == 305:
            defender.attack_stage = 0
            defender.defense_stage = 0
            defender.spatk_stage = 0
            defender.spdef_stage = 0
            defender.speed_stage = 0
            defender.accuracy_stage = 0
            defender.evasion_stage = 0
            msg += f"{defender.name} had their stat stages reset!\n"
        if self.effect == 141 or (self.effect == 474 and attacker._name == "Enamorus"):
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_attack(1, attacker=attacker, move=self)
                msg += attacker.append_defense(1, attacker=attacker, move=self)
                msg += attacker.append_spatk(1, attacker=attacker, move=self)
                msg += attacker.append_spdef(1, attacker=attacker, move=self)
                msg += attacker.append_speed(1, attacker=attacker, move=self)
        if self.effect == 143:
            msg += attacker.damage(attacker.starting_hp // 2, battle)
            msg += attacker.append_attack(12, attacker=attacker, move=self)
        if self.effect == 317:
            amount = 1
            if battle.weather.get() in ("sun", "h-sun"):
                amount = 2
            msg += attacker.append_attack(amount, attacker=attacker, move=self)
            msg += attacker.append_spatk(amount, attacker=attacker, move=self)
        if self.effect == 364 and defender.nv.poison():
            msg += defender.append_attack(-1, attacker=attacker, move=self)
            msg += defender.append_spatk(-1, attacker=attacker, move=self)
            msg += defender.append_speed(-1, attacker=attacker, move=self)
        if self.effect == 329:
            msg += attacker.append_defense(3, attacker=attacker, move=self)
        if self.effect == 322:
            msg += attacker.append_spatk(3, attacker=attacker, move=self)
        if self.effect == 227:
            valid_stats = []
            if attacker.attack_stage < 6:
                valid_stats.append(attacker.append_attack)
            if attacker.defense_stage < 6:
                valid_stats.append(attacker.append_defense)
            if attacker.spatk_stage < 6:
                valid_stats.append(attacker.append_spatk)
            if attacker.spdef_stage < 6:
                valid_stats.append(attacker.append_spdef)
            if attacker.speed_stage < 6:
                valid_stats.append(attacker.append_speed)
            if attacker.evasion_stage < 6:
                valid_stats.append(attacker.append_evasion)
            if attacker.accuracy_stage < 6:
                valid_stats.append(attacker.append_accuracy)
            if valid_stats:
                stat_raise_func = random.choice(valid_stats)
                msg += stat_raise_func(2, attacker=attacker, move=self)
            else:
                msg += f"None of {attacker.name}'s stats can go any higher!\n"
        if self.effect == 473:
            raw_atk = attacker.get_raw_attack() + attacker.get_raw_spatk()
            raw_def = attacker.get_raw_defense() + attacker.get_raw_spdef()
            if raw_atk > raw_def:
                msg += attacker.append_attack(1, attacker=attacker, move=self)
                msg += attacker.append_spatk(1, attacker=attacker, move=self)
            else:
                msg += attacker.append_defense(1, attacker=attacker, move=self)
                msg += attacker.append_spdef(1, attacker=attacker, move=self)
        if self.effect == 474 and attacker._name == "Enamorus-therian":
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_defense(-1, attacker=attacker, move=self)
                msg += defender.append_spdef(-1, attacker=attacker, move=self)
        if self.effect == 475:
            msg += defender.append_defense(-1, attacker=attacker, move=self)
            msg += defender.append_spdef(-1, attacker=attacker, move=self)
        if self.effect == 485:
            msg += attacker.damage(attacker.starting_hp // 2, battle)
            msg += attacker.append_attack(2, attacker=attacker, move=self)
            msg += attacker.append_spatk(2, attacker=attacker, move=self)
            msg += attacker.append_speed(2, attacker=attacker, move=self)
        
        # Flinch
        if not defender.has_moved:
            for _ in range(numhits):
                if defender.flinched:
                    break
                if self.effect in (32, 76, 93, 147, 151, 159, 274, 275, 276, 425):
                    if random.randint(1, 100) <= effect_chance:
                        msg += defender.flinch(move=self, attacker=attacker)
                elif self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                    if attacker.ability() == Ability.STENCH:
                        if random.randint(1, 100) <= 10:
                            msg += defender.flinch(move=self, attacker=attacker, source="its stench")
                    elif attacker.held_item == "kings-rock":
                        if random.randint(1, 100) <= 10:
                            msg += defender.flinch(move=self, attacker=attacker, source="its kings rock")
                    elif attacker.held_item == "razor-fang":
                        if random.randint(1, 100) <= 10:
                            msg += defender.flinch(move=self, attacker=attacker, source="its razor fang")
        
        # Move locking
        if self.effect == 87:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects its move from being disabled!\n"
            else:
                defender.disable.set(defender.last_move, random.randint(4, 7))
                msg += f"{defender.name}'s {defender.last_move.pretty_name} was disabled!\n"
        if self.effect == 176:
            if defender.ability(attacker=attacker, move=self) == Ability.OBLIVIOUS:
                msg += f"{defender.name} is too oblivious to be taunted!\n"
            elif defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being taunted!\n"
            else:
                if defender.has_moved:
                    defender.taunt.set_turns(4)
                else:
                    defender.taunt.set_turns(3)
                msg += f"{defender.name} is being taunted!\n"
        if self.effect == 91:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being encored!\n"
            else:
                defender.encore.set(defender.last_move, 4)
                if not defender.has_moved:
                    defender.owner.selected_action = defender.last_move
                msg += f"{defender.name} is giving an encore!\n"
        if self.effect == 166:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being tormented!\n"
            else:
                defender.torment = True
                msg += f"{defender.name} is tormented!\n"
        if self.effect == 193:
            attacker.imprison = True
            msg += f"{attacker.name} imprisons!\n"
        if self.effect == 237:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being heal blocked!\n"
            else:
                defender.heal_block.set_turns(5)
                msg += f"{defender.name} is blocked from healing!\n"
        
        # Weather changing
        if self.effect == 116:
            msg += battle.weather.set("sandstorm", attacker)
        if self.effect == 137:
            msg += battle.weather.set("rain", attacker)
        if self.effect == 138:
            msg += battle.weather.set("sun", attacker)
        if self.effect == 165:
            msg += battle.weather.set("hail", attacker)
        
        # Terrain changing
        if self.effect == 352:
            msg += battle.terrain.set("grassy", attacker)
        if self.effect == 353:
            msg += battle.terrain.set("misty", attacker)
        if self.effect == 369:
            msg += battle.terrain.set("electric", attacker)
        if self.effect == 395:
            msg += battle.terrain.set("psychic", attacker)
        
        # Protection
        if self.effect in (112, 117, 279, 356, 362, 384, 454, 488):
            attacker.protection_used = True
            attacker.protection_chance *= 3
        if self.effect == 112:
            attacker.protect = True
            msg += f"{attacker.name} protected itself!\n"
        if self.effect == 117:
            attacker.endure = True
            msg += f"{attacker.name} braced itself!\n"
        if self.effect == 279:
            attacker.wide_guard = True
            msg += f"Wide guard protects {attacker.name}!\n"
        if self.effect == 350:
            attacker.crafty_shield = True
            msg += f"A crafty shield protects {attacker.name} from status moves!\n"
        if self.effect == 356:
            attacker.king_shield = True
            msg += f"{attacker.name} shields itself!\n"
        if self.effect == 362:
            attacker.spiky_shield = True
            msg += f"{attacker.name} shields itself!\n"
        if self.effect == 377:
            attacker.mat_block = True
            msg += f"{attacker.name} shields itself!\n"
        if self.effect == 384:
            attacker.baneful_bunker = True
            msg += f"{attacker.name} bunkers down!\n"
        if self.effect == 307:
            attacker.quick_guard = True
            msg += f"{attacker.name} guards itself!\n"
        if self.effect == 454:
            attacker.obstruct = True
            msg += f"{attacker.name} protected itself!\n"
        if self.effect == 488:
            attacker.silk_trap = True
            msg += f"{attacker.name} protected itself!\n"
        
        # Life orb
        if (
            attacker.held_item == "life-orb"
            and defender.owner.has_alive_pokemon()
            and self.damage_class != DamageClass.STATUS
            and (attacker.ability() != Ability.SHEER_FORCE or self.effect_chance is None)
            and self.effect != 149
        ):
            msg += attacker.damage(attacker.starting_hp // 10, battle, source="its life orb")
        
        # Swap outs
        if self.effect in (128, 154, 229, 347):
            swaps = attacker.owner.valid_swaps(defender, battle, check_trap=False)
            if swaps:
                msg += f"{attacker.name} went back!\n"
                if self.effect == 128:
                    attacker.owner.baton_pass = BatonPass(attacker)
                msg += attacker.remove(battle)
                # This NEEDS to be here to set it to *False* rather than *None*
                attacker.owner.current_pokemon = False
        if self.effect in (29, 314):
            swaps = defender.owner.valid_swaps(attacker, battle, check_trap=False)
            if not swaps:
                pass
            elif defender.ability(attacker=attacker, move=self) == Ability.SUCTION_CUPS:
                msg += f"{defender.name}'s suction cups kept it in place!\n"
            elif defender.ability(attacker=attacker, move=self) == Ability.GUARD_DOG:
                msg += f"{defender.name}'s guard dog kept it in place!\n"
            elif defender.ingrain:
                msg += f"{defender.name} is ingrained in the ground!\n"
            else:
                msg += f"{defender.name} fled in fear!\n"
                msg += defender.remove(battle)
                idx = random.choice(swaps)
                defender.owner.switch_poke(idx, mid_turn=True)
                msg += defender.owner.current_pokemon.send_out(attacker, battle)
                # Safety in case the poke dies on send out.
                if defender.owner.current_pokemon is not None:
                    defender.owner.current_pokemon.has_moved = True
        
        # Trapping
        if self.effect in (107, 374, 385, 449, 452) and not defender.trapping:
            defender.trapping = True
            msg += f"{defender.name} can't escape!\n"
        if self.effect == 449 and not attacker.trapping:
            attacker.trapping = True
            msg += f"{attacker.name} can't escape!\n"
        
        # Attacker faints
        if self.effect in (169, 221, 271, 321):
            msg += attacker.faint(battle)
        
        # Struggle
        if self.effect == 255:
            msg += attacker.damage(attacker.starting_hp // 4, battle, attacker=attacker)
        
        # Pain Split
        if self.effect == 92:
            hp = (attacker.hp + defender.hp) // 2
            attacker.hp = min(attacker.starting_hp, hp)
            defender.hp = min(defender.starting_hp, hp)
            msg += "The battlers share their pain!\n"
        
        # Spite
        if self.effect == 101:
            defender.last_move.pp = max(0, defender.last_move.pp - 4)
            msg += f"{defender.name}'s {defender.last_move.pretty_name} was reduced!\n"
        
        # Eerie Spell
        if self.effect == 439 and defender.last_move is not None:
            defender.last_move.pp = max(0, defender.last_move.pp - 3)
            msg += f"{defender.name}'s {defender.last_move.pretty_name} was reduced!\n"
        
        # Heal Bell
        if self.effect == 103:
            for poke in attacker.owner.party:
                poke.nv.reset()
            msg += f"A bell chimed, and all of {attacker.owner.name}'s pokemon had status conditions removed!\n"
        
        # Psycho Shift
        if self.effect == 235:
            transfered_status = attacker.nv.current
            msg += defender.nv.apply_status(transfered_status, battle, attacker=attacker, move=self)
            if defender.nv.current == transfered_status:
                attacker.nv.reset()
                msg += f"{attacker.name}'s {transfered_status} was transfered to {defender.name}!\n"
            else:
                msg += "But it failed!\n"
        
        # Defog
        if self.effect == 259:
            defender.owner.spikes = 0
            defender.owner.toxic_spikes = 0
            defender.owner.stealth_rock = False
            defender.owner.sticky_web = False
            defender.owner.aurora_veil = ExpiringEffect(0)
            defender.owner.light_screen = ExpiringEffect(0)
            defender.owner.reflect = ExpiringEffect(0)
            defender.owner.mist = ExpiringEffect(0)
            defender.owner.safeguard = ExpiringEffect(0)
            attacker.owner.spikes = 0
            attacker.owner.toxic_spikes = 0
            attacker.owner.stealth_rock = False
            attacker.owner.sticky_web = False
            battle.terrain.end()
            msg += f"{attacker.name} blew away the fog!\n"
        
        # Trick room
        if self.effect == 260:
            if battle.trick_room.active():
                battle.trick_room.set_turns(0)
                msg += "The Dimensions returned back to normal!\n"
            else:
                battle.trick_room.set_turns(5)
                msg += f"{attacker.name} twisted the dimensions!\n"
        
        # Magic Room
        if self.effect == 287:
            if battle.magic_room.active():
                battle.magic_room.set_turns(0)
                msg += "The room returns to normal, and held items regain their effect!\n"
            else:
                battle.magic_room.set_turns(5)
                msg += "A bizzare area was created, and pokemon's held items lost their effect!\n"
        
        # Wonder Room
        if self.effect == 282:
            if battle.wonder_room.active():
                battle.wonder_room.set_turns(0)
                msg += "The room returns to normal, and stats swap back to what they were before!\n"
            else:
                battle.wonder_room.set_turns(5)
                msg += "A bizzare area was created, and pokemon's defense and special defense were swapped!\n"
        
        # Perish Song
        if self.effect == 115:
            msg += "All pokemon hearing the song will faint after 3 turns!\n"
            if attacker.perish_song.active():
                msg += f"{attacker.name} is already under the effect of perish song!\n"
            else:
                attacker.perish_song.set_turns(4)
            if defender.perish_song.active():
                msg += f"{defender.name} is already under the effect of perish song!\n"
            elif defender.ability(attacker=attacker, move=self) == Ability.SOUNDPROOF:
                msg += f"{defender.name}'s soundproof protects it from hearing the song!\n"
            else:
                defender.perish_song.set_turns(4)
            
        # Nightmare
        if self.effect == 108:
            defender.nightmare = True
            msg += f"{defender.name} fell into a nightmare!\n"
        
        # Gravity
        if self.effect == 216:
            battle.gravity.set_turns(5)
            msg += "Gravity intensified!\n"
            defender.telekinesis.set_turns(0)
            if defender.fly:
                defender.fly = False
                defender.locked_move = None
                msg += f"{defender.name} fell from the sky!\n"
        
        # Spikes
        if self.effect == 113:
            defender.owner.spikes += 1
            msg += f"Spikes were scattered around the feet of {defender.owner.name}'s team!\n"
        
        # Toxic Spikes
        if self.effect == 250:
            defender.owner.toxic_spikes += 1
            msg += f"Toxic spikes were scattered around the feet of {defender.owner.name}'s team!\n"
        
        # Stealth Rock
        if self.effect == 267:
            defender.owner.stealth_rock = True
            msg += f"Pointed stones float in the air around {defender.owner.name}'s team!\n"
        
        # Sticky Web
        if self.effect == 341:
            defender.owner.sticky_web = True
            msg += f"A sticky web is shot around the feet of {defender.owner.name}'s team!\n"
        
        # Defense curl
        if self.effect == 157 and not attacker.defense_curl:
            attacker.defense_curl = True
        
        # Psych Up
        if self.effect == 144:
            attacker.attack_stage = defender.attack_stage
            attacker.defense_stage = defender.defense_stage
            attacker.spatk_stage = defender.spatk_stage
            attacker.spdef_stage = defender.spdef_stage
            attacker.speed_stage = defender.speed_stage
            attacker.accuracy_stage = defender.accuracy_stage
            attacker.evasion_stage = defender.evasion_stage
            attacker.focus_energy = defender.focus_energy
            msg += "It psyched itself up!\n"
        
        # Conversion
        if self.effect == 31:
            t = attacker.moves[0].type
            if t not in ElementType.__members__.values():
                t = ElementType.NORMAL
            attacker.type_ids = [t]
            t = ElementType(t).name.lower()
            msg += f"{attacker.name} transformed into a {t} type!\n"
        
        # Conversion 2
        if self.effect == 94:
            t = self.get_conversion_2(attacker, defender, battle)
            attacker.type_ids = [t]
            t = ElementType(t).name.lower()
            msg += f"{attacker.name} transformed into a {t} type!\n"
        
        # Burn up
        if self.effect == 398:
            attacker.type_ids.remove(ElementType.FIRE)
            msg += f"{attacker.name} lost its fire type!\n"

        # Double shock
        if self.effect == 481:
            attacker.type_ids.remove(ElementType.ELECTRIC)
            msg += f"{attacker.name} lost its electric type!\n"
        
        # Forest's Curse
        if self.effect == 376:
            defender.type_ids.append(ElementType.GRASS)
            msg += f"{defender.name} added grass type!\n"
        
        # Trick or Treat
        if self.effect == 343:
            defender.type_ids.append(ElementType.GHOST)
            msg += f"{defender.name} added ghost type!\n"
        
        # Soak
        if self.effect == 295:
            defender.type_ids = [ElementType.WATER]
            msg += f"{defender.name} was transformed into a water type!\n"
        
        # Magic Powder
        if self.effect == 456:
            defender.type_ids = [ElementType.PSYCHIC]
            msg += f"{defender.name} was transformed into a psychic type!\n"
        
        # Camouflage
        if self.effect == 214:
            if battle.terrain.item == "grassy":
                attacker.type_ids = [ElementType.GRASS]
                msg += f"{attacker.name} was transformed into a grass type!\n"
            elif battle.terrain.item == "misty":
                attacker.type_ids = [ElementType.FAIRY]
                msg += f"{attacker.name} was transformed into a fairy type!\n"
            elif battle.terrain.item == "electric":
                attacker.type_ids = [ElementType.ELECTRIC]
                msg += f"{attacker.name} was transformed into a electric type!\n"
            elif battle.terrain.item == "psychic":
                attacker.type_ids = [ElementType.PSYCHIC]
                msg += f"{attacker.name} was transformed into a psychic type!\n"
            else:
                attacker.type_ids = [ElementType.NORMAL]
                msg += f"{attacker.name} was transformed into a normal type!\n"
        
        # Role Play
        if self.effect == 179:
            attacker.ability_id = defender.ability_id
            ability_name = Ability(attacker.ability_id).pretty_name
            msg += f"{attacker.name} acquired {ability_name}!\n"
            msg += attacker.send_out_ability(defender, battle)
        
        # Simple Beam
        if self.effect == 299:
            defender.ability_id = Ability.SIMPLE
            msg += f"{defender.name} acquired simple!\n"
            msg += defender.send_out_ability(attacker, battle)
        
        # Entrainment
        if self.effect == 300:
            defender.ability_id = attacker.ability_id
            ability_name = Ability(defender.ability_id).pretty_name
            msg += f"{defender.name} acquired {ability_name}!\n"
            msg += defender.send_out_ability(attacker, battle)
        
        # Worry Seed
        if self.effect == 248:
            defender.ability_id = Ability.INSOMNIA
            if defender.nv.sleep():
                defender.nv.reset()
            msg += f"{defender.name} acquired insomnia!\n"
            msg += defender.send_out_ability(attacker, battle)
        
        # Skill Swap
        if self.effect == 192:
            defender.ability_id, attacker.ability_id = attacker.ability_id, defender.ability_id
            ability_name = Ability(defender.ability_id).pretty_name
            msg += f"{defender.name} acquired {ability_name}!\n"
            msg += defender.send_out_ability(attacker, battle)
            ability_name = Ability(attacker.ability_id).pretty_name
            msg += f"{attacker.name} acquired {ability_name}!\n"
            msg += attacker.send_out_ability(defender, battle)
        
        # Aurora Veil
        if self.effect == 407:
            if attacker.held_item == "light-clay":
                attacker.owner.aurora_veil.set_turns(8)
            else:
                attacker.owner.aurora_veil.set_turns(5)
            msg += f"{attacker.name} put up its aurora veil!\n"
        
        # Light Screen
        if self.effect in (36, 421):
            if attacker.held_item == "light-clay":
                attacker.owner.light_screen.set_turns(8)
            else:
                attacker.owner.light_screen.set_turns(5)
            msg += f"{attacker.name} put up its light screen!\n"
        
        # Reflect
        if self.effect in (66, 422):
            if attacker.held_item == "light-clay":
                attacker.owner.reflect.set_turns(8)
            else:
                attacker.owner.reflect.set_turns(5)
            msg += f"{attacker.name} put up its reflect!\n"
        
        # Mist
        if self.effect == 47:
            attacker.owner.mist.set_turns(5)
            msg += f"{attacker.name} gained the protection of mist!\n"
        
        # Bind
        if self.effect in (43, 262) and not defender.substitute and not defender.bind.active():
            if attacker.held_item == "grip-claw":
                defender.bind.set_turns(7)
            else:
                defender.bind.set_turns(random.randint(4, 5))
            msg += f"{defender.name} was squeezed!\n"
        
        # Splinters
        if self.effect == 470:
            defender.splinters.set_turns(4)
            msg += f"Splinters prod into {defender.name}'s body!\n"
        
        # Sketch
        if self.effect == 96:
            m = defender.last_move.copy()
            attacker.moves[attacker.moves.index(self)] = m
            msg += f"The move {m.pretty_name} was sketched!\n"
            
        # Transform
        if self.effect == 58:
            msg += f"{attacker.name} transformed into {defender._name}!\n"
            attacker.transform(defender)
        
        # Substitute
        if self.effect == 80:
            hp = attacker.starting_hp // 4
            msg += attacker.damage(hp, battle, attacker=attacker, source="building a substitute")
            attacker.substitute = hp
            attacker.bind = ExpiringEffect(0)
            msg += f"{attacker.name} made a substitute!\n"
        
        # Shed Tail
        if self.effect == 493:
            hp = attacker.starting_hp // 4
            msg += attacker.damage(attacker.starting_hp // 2, battle, attacker=attacker, source="building a substitute")
            attacker.owner.next_substitute = hp
            attacker.bind = ExpiringEffect(0)
            msg += f"{attacker.name} left behind a substitute!\n"
            msg += attacker.remove(battle)
            # This NEEDS to be here to set it to *False* rather than *None*
            attacker.owner.current_pokemon = False
        
        # Throat Chop
        if self.effect == 393 and not defender.silenced.active():
            if random.randint(1, 100) <= effect_chance:
                defender.silenced.set_turns(3)
                msg += f"{defender.name} was silenced!\n"
        
        # Speed Swap
        if self.effect == 399:
            attacker.speed, defender.speed = defender.speed, attacker.speed
            msg += "Both pokemon exchange speed!\n"
        
        # Mimic
        if self.effect == 83:
            m = defender.last_move.copy()
            m.pp = m.starting_pp
            attacker.moves[attacker.moves.index(self)] = m
            msg += f"{attacker.name} mimicked {m.pretty_name}!\n"
        
        # Rage
        if self.effect == 82:
            attacker.rage = True
            msg += f"{attacker.name}'s rage is building!\n"
            
        # Mind Reader
        if self.effect == 95:
            defender.mind_reader.set(attacker, 2)
            msg += f"{attacker.name} took aim at {defender.name}!\n"
        
        # Destiny Bond
        if self.effect == 99:
            attacker.destiny_bond = True
            attacker.destiny_bond_cooldown.set_turns(2)
            msg += f"{attacker.name} is trying to take its foe with it!\n"
        
        # Ingrain
        if self.effect == 182:
            attacker.ingrain = True
            msg += f"{attacker.name} planted its roots!\n"
        
        # Attract
        if self.effect == 121:
            msg += defender.infatuate(attacker, move=self)
        
        # Heart Swap
        if self.effect == 251:
            attacker.attack_stage, defender.attack_stage = defender.attack_stage, attacker.attack_stage
            attacker.defense_stage, defender.defense_stage = defender.defense_stage, attacker.defense_stage
            attacker.spatk_stage, defender.spatk_stage = defender.spatk_stage, attacker.spatk_stage
            attacker.spdef_stage, defender.spdef_stage = defender.spdef_stage, attacker.spdef_stage
            attacker.speed_stage, defender.speed_stage = defender.speed_stage, attacker.speed_stage
            attacker.accuracy_stage, defender.accuracy_stage = defender.accuracy_stage, attacker.accuracy_stage
            attacker.evasion_stage, defender.evasion_stage = defender.evasion_stage, attacker.evasion_stage
            msg += f"{attacker.name} switched stat changes with {defender.name}!\n"
        
        # Power Swap
        if self.effect == 244:
            attacker.attack_stage, defender.attack_stage = defender.attack_stage, attacker.attack_stage
            attacker.spatk_stage, defender.spatk_stage = defender.spatk_stage, attacker.spatk_stage
            msg += f"{attacker.name} switched attack and special attack stat changes with {defender.name}!\n"
        
        # Guard Swap
        if self.effect == 245:
            attacker.defense_stage, defender.defense_stage = defender.defense_stage, attacker.defense_stage
            attacker.spdef_stage, defender.spdef_stage = defender.spdef_stage, attacker.spdef_stage
            msg += f"{attacker.name} switched defense and special defense stat changes with {defender.name}!\n"
        
        # Aqua Ring
        if self.effect == 252:
            attacker.aqua_ring = True
            msg += f"{attacker.name} surrounded itself with a veil of water!\n"
        
        # Magnet Rise
        if self.effect == 253:
            attacker.magnet_rise.set_turns(5)
            msg += f"{attacker.name} levitated with electromagnetism!\n"
        
        # Healing Wish
        if self.effect == 221:
            attacker.owner.healing_wish = True
            msg += f"{attacker.name}'s replacement will be restored!\n"
        
        # Lunar Dance
        if self.effect == 271:
            attacker.owner.lunar_dance = True
            msg += f"{attacker.name}'s replacement will be restored!\n"

        # Gastro Acid
        if self.effect == 240:
            defender.ability_id = None
            msg += f"{defender.name}'s ability was disabled!\n"
        
        # Lucky Chant
        if self.effect == 241:
            attacker.lucky_chant.set_turns(5)
            msg += f"{attacker.name} is shielded from critical hits!\n"
        
        # Safeguard
        if self.effect == 125:
            attacker.owner.safeguard.set_turns(5)
            msg += f"{attacker.name} is protected from status effects!\n"
        
        # Guard Split
        if self.effect == 280:
            attacker.defense_split = defender.get_raw_defense()
            attacker.spdef_split = defender.get_raw_spdef()
            defender.defense_split = attacker.get_raw_defense()
            defender.spdef_split = attacker.get_raw_spdef()
            msg += f"{attacker.name} and {defender.name} shared their guard!\n"
        
        # Power Split
        if self.effect == 281:
            attacker.attack_split = defender.get_raw_attack()
            attacker.spatk_split = defender.get_raw_spatk()
            defender.attack_split = attacker.get_raw_attack()
            defender.spatk_split = attacker.get_raw_spatk()
            msg += f"{attacker.name} and {defender.name} shared their power!\n"
        
        # Smack Down/Thousand Arrows
        if self.effect in (288, 373):
            defender.telekinesis.set_turns(0)
            if defender.fly:
                defender.fly = False
                defender.locked_move = None
                defender.has_moved = True
                msg += f"{defender.name} was shot out of the air!\n"
            if not defender.grounded(battle, attacker=attacker, move=self):
                defender.grounded_by_move = True
                msg += f"{defender.name} was grounded!\n"
        
        # Reflect Type
        if self.effect == 319:
            attacker.type_ids = defender.type_ids.copy()
            msg += f"{attacker.name}'s type changed to match {defender.name}!\n"
        
        # Charge
        if self.effect == 175:
            # TODO: Gen 9 makes charge last until an electric move is used
            attacker.charge.set_turns(2)
            msg += f"{attacker.name} charges up electric type moves!\n"
        
        # Magic Coat
        if self.effect == 184:
            attacker.magic_coat = True
            msg += f"{attacker.name} shrouded itself with a magic coat!\n"
        
        # Tailwind
        if self.effect == 226:
            attacker.owner.tailwind.set_turns(4)
            msg += f"{attacker.owner.name}'s team gets a tailwind!\n"
            if attacker.ability() == Ability.WIND_RIDER:
                msg += attacker.append_attack(1, attacker=attacker, source="its wind rider")
        
        # Fling
        if self.effect == 234 and attacker.held_item.can_remove():
            item = attacker.held_item.name
            msg += f"{attacker.name}'s {item} was flung away!\n"
            if attacker.held_item.is_berry():
                msg += attacker.held_item.eat_berry(consumer=defender, attacker=attacker, move=self)
            else:
                attacker.held_item.use()
                if item == "flame-orb":
                    msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
                elif item in ("kings-rock", "razor-fang"):
                    msg += defender.flinch(attacker=attacker, move=self)
                elif item == "light-ball":
                    msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
                elif item == "mental-herb":
                    defender.infatuated = None
                    defender.taunt = ExpiringEffect(0)
                    defender.encore = ExpiringItem()
                    defender.torment = False
                    defender.disable = ExpiringItem()
                    defender.heal_block = ExpiringEffect(0)
                    msg += f"{defender.name} feels refreshed!\n"
                elif item == "poison-barb":
                    msg += defender.nv.apply_status("poison", battle, attacker=attacker, move=self)
                elif item == "toxic-orb":
                    msg += defender.nv.apply_status("b-poison", battle, attacker=attacker, move=self)
                elif item == "white-herb":
                    defender.attack_stage = max(0, defender.attack_stage)
                    defender.defense_stage = max(0, defender.defense_stage)
                    defender.spatk_stage = max(0, defender.spatk_stage)
                    defender.spdef_stage = max(0, defender.spdef_stage)
                    defender.speed_stage = max(0, defender.speed_stage)
                    defender.accuracy_stage = max(0, defender.accuracy_stage)
                    defender.evasion_stage = max(0, defender.evasion_stage)
                    msg += f"{defender.name} feels refreshed!\n"
        
        # Thief
        if self.effect == 106 and defender.held_item.has_item() and defender.held_item.can_remove() and not defender.substitute and not attacker.held_item.has_item():
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                defender.held_item.transfer(attacker.held_item)
                msg += f"{defender.name}'s {attacker.held_item.name} was stolen!\n"
        
        # Trick
        if self.effect == 178:
            attacker.held_item.swap(defender.held_item)
            msg += f"{attacker.name} and {defender.name} swapped their items!\n"
            if attacker.held_item.name is not None:
                msg += f"{attacker.name} gained {attacker.held_item.name}!\n"
            if defender.held_item.name is not None:
                msg += f"{defender.name} gained {defender.held_item.name}!\n"
        
        # Knock off
        if self.effect == 189 and defender.held_item.has_item() and defender.held_item.can_remove() and not defender.substitute and attacker.hp > 0:
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                msg += f"{defender.name} lost its {defender.held_item.name}!\n"
                defender.held_item.remove()
        
        # Teatime
        if self.effect == 476:
            msgadd = ""
            for poke in (attacker, defender):
                msgadd += poke.held_item.eat_berry(attacker=attacker, move=self)
            msg += msgadd
            if not msgadd:
                msg += "But nothing happened..."
        
        # Corrosive Gas
        if self.effect == 430:
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                msg += f"{defender.name}'s {defender.held_item.name} was corroded!\n"
                defender.corrosive_gas = True
        
        # Mud Sport
        if self.effect == 202:
            attacker.owner.mud_sport.set_turns(6)
            msg += "Electricity's power was weakened!\n"
        
        # Water Sport
        if self.effect == 211:
            attacker.owner.water_sport.set_turns(6)
            msg += "Fire's power was weakened!\n"
        
        # Power Trick
        if self.effect == 239:
            attacker.power_trick = not attacker.power_trick
            msg += f"{attacker.name} switched its Attack and Defense!\n"
        
        # Power Shift
        if self.effect == 466:
            attacker.power_shift = not attacker.power_shift
            msg += f"{attacker.name} switched its offensive and defensive stats!\n"
        
        # Yank
        if self.effect == 188:
            if battle.terrain.item == "electric" and defender.grounded(battle, attacker=attacker, move=self):
                msg += f"{defender.name} keeps alert from being shocked by the electric terrain!\n"
            else:
                defender.yawn.set_turns(2)
                msg += f"{defender.name} is drowsy!\n"
        
        # Rototiller
        if self.effect == 340:
            for p in (attacker, defender):
                if ElementType.GRASS not in p.type_ids:
                    continue
                if not p.grounded(battle):
                    continue
                if p.dive or p.dig or p.fly or p.shadow_force:
                    continue
                msg += p.append_attack(1, attacker=attacker, move=self)
                msg += p.append_spatk(1, attacker=attacker, move=self)
        
        # Flower Shield
        if self.effect == 351:
            for p in (attacker, defender):
                if ElementType.GRASS not in p.type_ids:
                    continue
                if not p.grounded(battle):
                    continue
                if p.dive or p.dig or p.fly or p.shadow_force:
                    continue
                msg += p.append_defense(1, attacker=attacker, move=self)
        
        # Ion Deluge
        if self.effect == 345:
            attacker.ion_deluge = True
            msg += f"{attacker.name} charges up the air!\n"
        
        # Topsy Turvy
        if self.effect == 348:
            defender.attack_stage = -defender.attack_stage
            defender.defense_stage = -defender.defense_stage
            defender.spatk_stage = -defender.spatk_stage
            defender.spdef_stage = -defender.spdef_stage
            defender.speed_stage = -defender.speed_stage
            defender.accuracy_stage = -defender.accuracy_stage
            defender.evasion_stage = -defender.evasion_stage
            msg += f"{defender.name}'s stat stages were inverted!\n"

        # Electrify
        if self.effect == 354:
            defender.electrify = True
            msg += f"{defender.name}'s move was charged with electricity!\n"
        
        # Instruct
        if self.effect == 403:
            hm = defender.has_moved
            defender.has_moved = False
            msg += defender.last_move.use(defender, attacker, battle)
            defender.has_moved = hm
        
        # Core Enforcer
        if self.effect == 402 and defender.has_moved and defender.ability_changeable():
            defender.ability_id = None
            msg += f"{defender.name}'s ability was nullified!\n"

        # Laser Focus
        if self.effect == 391:
            attacker.laser_focus.set_turns(2)
            msg += f"{attacker.name} focuses!\n"

        # Powder
        if self.effect == 378:
            defender.powdered = True
            msg += f"{defender.name} was coated in powder!\n"

        # Rapid/Mortal Spin
        if self.effect in (130, 486):
            attacker.bind.set_turns(0)
            attacker.splinters.set_turns(0)
            attacker.trapping = False
            attacker.leech_seed = False
            attacker.owner.spikes = 0
            attacker.owner.toxic_spikes = 0
            attacker.owner.stealth_rock = False
            attacker.owner.sticky_web = False
            msg += f"{attacker.name} was released!\n"

        # Snatch
        if self.effect == 196:
            attacker.snatching = True
            msg += f"{attacker.name} waits for a target to make a move!\n"

        # Telekinesis
        if self.effect == 286:
            defender.telekinesis.set_turns(5)
            msg += f"{defender.name} was hurled into the air!\n"

        # Embargo
        if self.effect == 233:
            defender.embargo.set_turns(6)
            msg += f"{defender.name} can't use items anymore!\n"
            
        # Echoed Voice
        if self.effect == 303:
            attacker.echoed_voice_power = min(attacker.echoed_voice_power + 40, 200)
            attacker.echoed_voice_used = True
            msg += f"{attacker.name}'s voice echos!\n"

        # Bestow
        if self.effect == 324:
            attacker.held_item.transfer(defender.held_item)
            msg += f"{attacker.name} gave its {defender.held_item.name} to {defender.name}!\n"

        # Curse
        if self.effect == 110:
            if ElementType.GHOST in attacker.type_ids:
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="inflicting the curse")
                defender.curse = True
                msg += f"{defender.name} was cursed!\n"
            else:
                msg += attacker.append_speed(-1, attacker=attacker, move=self)
                msg += attacker.append_attack(1, attacker=attacker, move=self)
                msg += attacker.append_defense(1, attacker=attacker, move=self)

        # Autotomize
        if self.effect == 285:
            attacker.autotomize += 1
            msg += f"{attacker.name} became nimble!\n"

        # Fell Stinger
        if self.effect == 342 and defender.hp == 0:
            msg += attacker.append_attack(3, attacker=attacker, move=self)
        
        # Fairy Lock
        if self.effect == 355:
            attacker.fairy_lock.set_turns(2)
            msg += f"{attacker.name} prevents escape next turn!\n"

        # Grudge
        if self.effect == 195:
            attacker.grudge = True
            msg += f"{attacker.name} has a grudge!\n"

        # Foresight
        if self.effect == 114:
            defender.foresight = True
            msg += f"{attacker.name} identified {defender.name}!\n"
        
        # Miracle Eye
        if self.effect == 217:
            defender.miracle_eye = True
            msg += f"{attacker.name} identified {defender.name}!\n"

        # Clangorous Soul
        if self.effect == 414:
            msg += attacker.damage(attacker.starting_hp // 3, battle)

        # No Retreat
        if self.effect == 427:
            attacker.no_retreat = True
            msg += f"{attacker.name} takes its last stand!\n"

        # Recycle
        if self.effect == 185:
            attacker.held_item.recover(attacker.held_item)
            msg += f"{attacker.name} recovered their {attacker.held_item.name}!\n"
            if attacker.held_item.should_eat_berry(defender):
                msg += attacker.held_item.eat_berry(attacker=defender, move=self)
        
        # Court Change
        if self.effect == 431:
            attacker.owner.spikes, defender.owner.spikes = defender.owner.spikes, attacker.owner.spikes
            attacker.owner.toxic_spikes, defender.owner.toxic_spikes = defender.owner.toxic_spikes, attacker.owner.toxic_spikes
            attacker.owner.stealth_rock, defender.owner.stealth_rock = defender.owner.stealth_rock, attacker.owner.stealth_rock
            attacker.owner.sticky_web, defender.owner.sticky_web = defender.owner.sticky_web, attacker.owner.sticky_web
            attacker.owner.aurora_veil, defender.owner.aurora_veil = defender.owner.aurora_veil, attacker.owner.aurora_veil
            attacker.owner.light_screen, defender.owner.light_screen = defender.owner.light_screen, attacker.owner.light_screen
            attacker.owner.reflect, defender.owner.reflect = defender.owner.reflect, attacker.owner.reflect
            attacker.owner.mist, defender.owner.mist = defender.owner.mist, attacker.owner.mist
            attacker.owner.safeguard, defender.owner.safeguard = defender.owner.safeguard, attacker.owner.safeguard
            attacker.owner.tailwind, defender.owner.tailwind = defender.owner.tailwind, attacker.owner.tailwind
            msg += "Active battle effects swapped sides!\n"
        
        # Roost
        if self.effect == 215:
            attacker.roost = True
            if ElementType.FLYING in attacker.type_ids:
                msg += f"{attacker.name}'s flying type is surpressed!\n"
        
        # Pluck
        if self.effect == 225 and defender.ability(attacker=attacker, move=self) != Ability.STICKY_HOLD:
            msg += defender.held_item.eat_berry(consumer=attacker)
        
        # Focus energy
        if self.effect in (48, 475):
            attacker.focus_energy = True
            msg += f"{attacker.name} focuses on its target!\n"

        # Natural Gift
        if self.effect == 223:
            msg += f"{attacker.name}'s {attacker.held_item.name} was consumed!\n"
            attacker.held_item.use()

        # Gulp Missile
        if self.effect == 258 and attacker.ability() == Ability.GULP_MISSILE and attacker._name == "Cramorant":
            if attacker.hp > attacker.starting_hp // 2:
                if attacker.form("Cramorant-gulping"):
                    msg += f"{attacker.name} gulped up an arrokuda!\n"
            else:
                if attacker.form("Cramorant-gorging"):
                    msg += f"{attacker.name} gulped up a pikachu!\n"
        
        # Steel Roller
        if self.effect in (418, 448) and battle.terrain.item is not None:
            battle.terrain.end()
            msg += "The terrain was cleared!\n"
        
        # Octolock
        if self.effect == 452:
            defender.octolock = True
            msg += f"{defender.name} is octolocked!\n"
        
        # Stuff Cheeks
        if self.effect == 453:
            msg += attacker.held_item.eat_berry()
        
        # Plasma Fists
        if self.effect == 455:
            if not battle.plasma_fists:
                battle.plasma_fists = True
                msg += f"{attacker.name} electrifies the battlefield, energizing normal type moves!\n"
        
        # Secret Power
        if self.effect == 198:
            if random.randint(1, 100) <= effect_chance:
                if battle.terrain.item == "grassy":
                    msg += defender.nv.apply_status("sleep", battle, attacker=attacker, move=self)
                elif battle.terrain.item == "misty":
                    msg += defender.append_spatk(-1, attacker=attacker, move=self)
                elif battle.terrain.item == "psychic":
                    msg += defender.append_speed(-1, attacker=attacker, move=self)
                else:
                    msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
        
        if self.is_sound_based() and attacker.held_item == "throat-spray":
            msg += attacker.append_spatk(1, attacker=attacker, source="it's throat spray")
            attacker.held_item.use()
        
        # Victory Dance
        if self.effect == 468:
            attacker.victory_dance = True
            msg += f"{attacker.name} ushers in victory!\n"
        
        # Tar Shot
        if self.effect == 477 and not defender.tar_shot:
            defender.tar_shot = True
            msg += f"{defender.name} is covered in sticky tar!\n"
        
        # Tidy Up
        if self.effect == 487:
            defender.owner.spikes = 0
            defender.owner.toxic_spikes = 0
            defender.owner.stealth_rock = False
            defender.owner.sticky_web = False
            defender.substitute = 0
            attacker.owner.spikes = 0
            attacker.owner.toxic_spikes = 0
            attacker.owner.stealth_rock = False
            attacker.owner.sticky_web = False
            attacker.substitute = 0
            msg += f"{attacker.name} tidied up!\n"
        
        # Dancer Ability - Runs at the end of move usage
        if defender.ability(attacker=attacker, move=self) == Ability.DANCER and self.is_dance() and use_pp:
            hm = defender.has_moved
            msg += self.use(defender, attacker, battle, use_pp=False)
            defender.has_moved = hm
        
        return msg
    
    def attack(self, attacker, defender, battle):
        """
        Attacks the defender using this move.
        
        Returns a string of formatted results of this attack and the number of hits this move did.
        """
        #https://bulbapedia.bulbagarden.net/wiki/Damage
        msg = ""
        current_type = self.get_type(attacker, defender, battle)
        
        # Move effectiveness
        effectiveness = defender.effectiveness(current_type, battle, attacker=attacker, move=self)
        if self.effect == 338:
            effectiveness *= defender.effectiveness(ElementType.FLYING, battle, attacker=attacker, move=self)
        if effectiveness <= 0:
            return ("The attack had no effect!\n", 0) 
        if effectiveness <= .5:
            msg += "It's not very effective...\n"
        elif effectiveness >= 2: 
            msg += "It's super effective!\n"
        
        # Calculate the number of hits for this move.
        parental_bond = False
        min_hits = self.min_hits
        max_hits = self.max_hits
        if self.effect == 361 and attacker._name == "Greninja-ash":
            hits = 3
        elif min_hits is not None and max_hits is not None:
            # Handle hit range overrides
            if attacker.ability() == Ability.SKILL_LINK:
                min_hits = max_hits
            elif attacker.held_item == "loaded-dice" and max_hits >= 4 and (min_hits < 4 or self.effect == 484):
                min_hits = 4
            # Randomly select number of hits
            if min_hits == 2 and max_hits == 5:
                hits = random.choice([
                    2, 2, 2, 2, 2, 2, 2,
                    3, 3, 3, 3, 3, 3, 3,
                    4, 4, 4,
                    5, 5, 5
                ])
            else:
                hits = random.randint(min_hits, max_hits)
        else:
            if attacker.ability() == Ability.PARENTAL_BOND:
                hits = 2
                parental_bond = True
            else:
                hits = 1
        
        for hit in range(hits):
            if defender.hp == 0:
                break
            # Explosion faints the user first, but should still do damage after death.
            # Future sight still needs to hit after the attacker dies.
            # Mind blown still needs to hit after the attacker dies.
            if attacker.hp == 0 and self.effect not in (8, 149, 420, 444):
                break
            
            # Critical hit chance
            critical_stage = self.crit_rate
            if attacker.held_item in ("scope-lens", "razor-claw"):
                critical_stage += 1
            if attacker.ability() == Ability.SUPER_LUCK:
                critical_stage += 1
            if attacker.focus_energy:
                critical_stage += 2
            if attacker.lansat_berry_ate:
                critical_stage += 2
            critical_stage = min(critical_stage, 3)
            crit_map = {
                0: 24,
                1: 8,
                2: 2,
                3: 1,
            }
            critical = not random.randrange(crit_map[critical_stage])
            if attacker.ability() == Ability.MERCILESS and defender.nv.poison():
                critical = True
            # Always scores a critical hit.
            if self.effect == 289:
                critical = True
            if attacker.laser_focus.active():
                critical = True
            if defender.ability(attacker=attacker, move=self) in (Ability.SHELL_ARMOR, Ability.BATTLE_ARMOR):
                critical = False
            if defender.lucky_chant.active():
                critical = False
            # Confusion never crits
            if self.id == 0xCFCF:
                critical = False
        
            # Stats
            if self.damage_class == DamageClass.PHYSICAL:
                damage_class = DamageClass.PHYSICAL
                a = attacker.get_attack(
                    battle,
                    critical=critical,
                    ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                )
                if self.effect == 304:
                    d = defender.get_raw_defense()
                else:
                    d = defender.get_defense(
                        battle,
                        critical=critical,
                        ignore_stages=attacker.ability() == Ability.UNAWARE,
                        attacker=attacker,
                        move=self
                    )
            else:
                damage_class = DamageClass.SPECIAL
                a = attacker.get_spatk(
                    battle,
                    critical=critical,
                    ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                )
                if self.effect == 304:
                    d = defender.get_raw_spdef()
                else:
                    d = defender.get_spdef(
                        battle,
                        critical=critical,
                        ignore_stages=attacker.ability() == Ability.UNAWARE,
                        attacker=attacker,
                        move=self
                    )
        
            # Always uses defender's defense
            if self.effect == 283:
                d = defender.get_defense(
                    battle,
                    critical=critical,
                    ignore_stages=attacker.ability() == Ability.UNAWARE,
                    attacker=attacker,
                    move=self
                )
            
            # Use the user's defense instead of attack for the attack stat
            if self.effect == 426:
                # This does not pass critical, otherwise it would crop the wrong direction.
                a = attacker.get_defense(
                    battle,
                    ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                )
                
            # Use the defender's attacking stat
            if self.effect == 298:
                if self.damage_class == DamageClass.PHYSICAL:
                    a = defender.get_attack(
                        battle,
                        critical=critical,
                        ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                    )
                else:
                    a = defender.get_spatk(
                        battle,
                        critical=critical,
                        ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                    )
            
            # Use the higher of attack or special attack
            if self.effect == 416:
                ignore_stages = defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                a = max(attacker.get_attack(battle, critical=critical, ignore_stages=ignore_stages), attacker.get_spatk(battle, critical=critical, ignore_stages=ignore_stages))
            
            if attacker.flash_fire and current_type == ElementType.FIRE:
                a *= 1.5
            if defender.ability(attacker=attacker, move=self) == Ability.THICK_FAT and current_type in (ElementType.FIRE, ElementType.ICE):
                a *= .5
        
            power = self.get_power(attacker, defender, battle)
            if power is None:
                raise ValueError(f"{self.name} has no power and no override.")
            
            # Check accuracy on each hit
            # WARNING: If there is something BEFORE this in the loop which adds to msg (like "A critical hit")
            # it MUST be after this block, or it will appear even after "misses" from this move.
            if hit > 0 and not attacker.ability() == Ability.SKILL_LINK:
                # Increasing damage each hit
                if self.effect == 105:
                    if not self.check_hit(attacker, defender, battle):
                        # Reset the number of hits to the number of ACTUAL hits
                        hits = hit
                        break
                    # x2 then x3
                    power *= 1 + hit
                # Only checks if loaded dice did not activate
                if self.effect == 484 and attacker.held_item != "loaded-dice":
                    if not self.check_hit(attacker, defender, battle):
                        hits = hit
                        break
            
            damage = 2 * attacker.level
            damage /= 5
            damage += 2
            damage = damage * power * (a / d)
            damage /= 50
            damage += 2
            
            # Critical hit damage
            if critical:
                msg += "A critical hit!\n"
                damage *= 1.5
            
            # Type buffing weather
            if current_type == ElementType.WATER and battle.weather.get() in ("rain", "h-rain"):
                damage *= 1.5
            elif current_type == ElementType.FIRE and battle.weather.get() in ("rain", "h-rain"):
                damage *= 0.5
            elif current_type == ElementType.FIRE and battle.weather.get() == "sun":
                damage *= 1.5
            elif current_type == ElementType.WATER and battle.weather.get() == "sun":
                damage *= 0.5
        
            # Same type attack bonus - extra damage for using a move that is the same type as your poke's type.
            if current_type in attacker.type_ids:
                if attacker.ability() == Ability.ADAPTABILITY:
                    damage *= 2
                else:
                    damage *= 1.5
        
            # Move effectiveness
            damage *= effectiveness
        
            # Burn
            if (
                attacker.nv.burn()
                and damage_class == DamageClass.PHYSICAL
                and attacker.ability() != Ability.GUTS
                and self.effect != 170
            ):
                damage *= .5
        
            # Aurora Veil, Light Screen, Reflect do not stack but all reduce incoming damage in some way
            if not critical and attacker.ability() != Ability.INFILTRATOR:
                if defender.owner.aurora_veil.active():
                    damage *= .5
                elif defender.owner.light_screen.active() and damage_class == DamageClass.SPECIAL:
                    damage *= .5
                elif defender.owner.reflect.active() and damage_class == DamageClass.PHYSICAL:
                    damage *= .5
        
            # Moves that do extra damage to minimized pokes
            if defender.minimized and self.effect == 338:
                damage *= 2
            
            # Fluffy
            if defender.ability(attacker=attacker, move=self) == Ability.FLUFFY:
                if self.makes_contact(attacker):
                    damage *= .5
                if current_type == ElementType.FIRE:
                    damage *= 2
        
            # Abilities that change damage
            if defender.ability(attacker=attacker, move=self) in (Ability.FILTER, Ability.PRISM_ARMOR, Ability.SOLID_ROCK) and effectiveness > 1:
                damage *= .75
            if attacker.ability() == Ability.NEUROFORCE and effectiveness > 1:
                damage *= 1.25
            if defender.ability(attacker=attacker, move=self) == Ability.ICE_SCALES and damage_class == DamageClass.SPECIAL:
                damage *= .5
            if attacker.ability() == Ability.SNIPER and critical:
                damage *= 1.5
            if attacker.ability() == Ability.TINTED_LENS and effectiveness < 1:
                damage *= 2
            if attacker.ability() == Ability.PUNK_ROCK and self.is_sound_based():
                damage *= 1.3
            if defender.ability(attacker=attacker, move=self) == Ability.PUNK_ROCK and self.is_sound_based():
                damage *= .5
            if defender.ability(attacker=attacker, move=self) == Ability.HEATPROOF and current_type == ElementType.FIRE:
                damage *= .5
            if defender.ability(attacker=attacker, move=self) == Ability.PURIFYING_SALT and current_type == ElementType.GHOST:
                damage *= .5
            if Ability.DARK_AURA in (attacker.ability(), defender.ability(attacker=attacker, move=self)) and current_type == ElementType.DARK:
                if Ability.AURA_BREAK in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
                    damage *= .75
                else:
                    damage *= 4/3
            if Ability.FAIRY_AURA in (attacker.ability(), defender.ability(attacker=attacker, move=self)) and current_type == ElementType.FAIRY:
                if Ability.AURA_BREAK in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
                    damage *= .75
                else:
                    damage *= 4/3
            if defender.ability(attacker=attacker, move=self) == Ability.DRY_SKIN and current_type == ElementType.FIRE:
                damage *= 1.25
        
            # Items that change damage
            if defender.held_item == "chilan-berry" and current_type == ElementType.NORMAL:
                damage *= .5
            if attacker.held_item == "expert-belt" and effectiveness > 1:
                damage *= 1.2
            if (
                attacker.held_item == "life-orb"
                and self.damage_class != DamageClass.STATUS
                and self.effect != 149
            ):
                damage *= 1.3
            if attacker.held_item == "metronome":
                damage *= attacker.metronome.get_buff(self.name)
            
            # Parental bond - adds an extra low power hit
            if parental_bond and hit > 0:
                damage *= .25
            
            # Reduced damage while at full hp
            if defender.ability(attacker=attacker, move=self) in (Ability.MULTISCALE, Ability.SHADOW_SHIELD) and defender.hp == defender.starting_hp:
                damage *= .5

            # Random damage scaling
            damage *= random.uniform(0.85, 1)
            damage = max(1, int(damage))
            
            # Cannot lower the target's HP below 1.
            if self.effect == 102:
                damage = min(damage, defender.hp - 1)
            
            # Drain ratios
            drain_heal_ratio = None
            if self.effect in (4, 9, 346):
                drain_heal_ratio = 1/2
            elif self.effect == 349:
                drain_heal_ratio = 3/4

            # Do the damage
            msgadd, damage = defender._damage(damage, battle, move=self, move_type=current_type, attacker=attacker, critical=critical, drain_heal_ratio=drain_heal_ratio)
            msg += msgadd
            
            # Recoil
            if attacker.ability() != Ability.ROCK_HEAD and defender.owner.has_alive_pokemon():
                if self.effect == 49:
                    msg += attacker.damage(damage // 4, battle, source="recoil")
                if self.effect in (199, 254, 263, 469):
                    msg += attacker.damage(damage // 3, battle, source="recoil")
                if self.effect in (270, 463):
                    msg += attacker.damage(damage // 2, battle, source="recoil")
        
        # Weakness Policy
        if effectiveness > 1 and defender.held_item == "weakness-policy" and not defender.substitute:
            msg += defender.append_attack(2, attacker=defender, move=self, source="its weakness policy")
            msg += defender.append_spatk(2, attacker=defender, move=self, source="its weakness policy")
            defender.held_item.use()
        
        return (msg, hits)
    
    def get_power(self, attacker, defender, battle):
        """Get the power of this move."""
        current_type = self.get_type(attacker, defender, battle)
        # Inflicts damage equal to the user's level.
        if self.effect == 88:
            power = attacker.level
        # Inflicts damage between 50% and 150% of the user's level.
        elif self.effect == 89:
            power = random.randint(int(attacker.level * 0.5), int(attacker.level * 1.5))
        # Inflicts more damage to heavier targets, with a maximum of 120 power.
        elif self.effect == 197:
            def_weight = defender.weight(attacker=attacker, move=self)
            if def_weight <= 100:
                power = 20
            elif def_weight <= 250:
                power = 40
            elif def_weight <= 500:
                power = 60
            elif def_weight <= 1000:
                power = 80
            elif def_weight <= 2000:
                power = 100
            else:
                power = 120
        # Power is higher when the user weighs more than the target, up to a maximum of 120.
        elif self.effect == 292:
            weight_delta = attacker.weight() / defender.weight(attacker=attacker, move=self)
            if weight_delta <= 2:
                power = 40
            elif weight_delta <= 3:
                power = 60
            elif weight_delta <= 4:
                power = 80
            elif weight_delta <= 5:
                power = 100
            else:
                power = 120
        # Power increases with happiness, up to a maximum of 102.
        elif self.effect == 122:
            power = int(attacker.happiness / 2.5)
            if power > 102:
                power = 102
            elif power < 1:
                power = 1
        # Power increases as happiness **decreases**, up to a maximum of 102.
        elif self.effect == 124:
            power = int((255 - attacker.happiness) / 2.5)
            if power > 102:
                power = 102
            elif power < 1:
                power = 1
        # Power raises when the user has lower Speed, up to a maximum of 150.
        elif self.effect == 220:
            power = min(150, int(1 + 25 * defender.get_speed(battle) / attacker.get_speed(battle)))
        # Inflicts more damage when the user has more HP remaining, with a maximum of 150 power.
        elif self.effect == 191:
            power = int(150 * (attacker.hp / attacker.starting_hp))
        # Power is 100 times the amount of energy Stockpiled.
        elif self.effect == 162:
            power = 100 * attacker.stockpile
        # Inflicts more damage when the user has less HP remaining, with a maximum of 200 power.
        elif self.effect == 100:
            hp_percent = 64 * (attacker.hp / attacker.starting_hp)
            if hp_percent <= 1:
                power = 200
            elif hp_percent <= 5:
                power = 150
            elif hp_percent <= 12:
                power = 100
            elif hp_percent <= 21:
                power = 80
            elif hp_percent <= 42:
                power = 40
            else:
                power = 20
        # Power increases when this move has less PP, up to a maximum of 200.
        elif self.effect == 236:
            if self.pp == 0:
                power = 200
            elif self.pp == 1:
                power = 80
            elif self.pp == 2:
                power = 60
            elif self.pp == 3:
                power = 50
            else:
                power = 40
        # Power increases against targets with more HP remaining, up to a maximum of 121 power.
        elif self.effect == 238:
            power = int(1 + (120 * (defender.hp / defender.starting_hp)))
        # Power increases against targets with more raised stats, up to a maximum of 200.
        elif self.effect == 246:
            delta = 0
            delta += max(0, defender.attack_stage)
            delta += max(0, defender.defense_stage)
            delta += max(0, defender.spatk_stage)
            delta += max(0, defender.spdef_stage)
            delta += max(0, defender.speed_stage)
            power = min(200, 60 + (delta * 20))
        # Power is higher when the user has greater Speed than the target, up to a maximum of 150.
        elif self.effect == 294:
            delta = attacker.get_speed(battle) // defender.get_speed(battle)
            if delta <= 0:
                power = 40
            elif delta <= 1:
                power = 60
            elif delta <= 2:
                power = 80
            elif delta <= 3:
                power = 120
            else:
                power = 150
        # Power is higher the more the user's stats have been raised.
        elif self.effect == 306:
            delta = 1
            delta += max(0, attacker.attack_stage)
            delta += max(0, attacker.defense_stage)
            delta += max(0, attacker.spatk_stage)
            delta += max(0, attacker.spdef_stage)
            delta += max(0, attacker.speed_stage)
            delta += max(0, attacker.accuracy_stage)
            delta += max(0, attacker.evasion_stage)
            power = 20 * delta
        # Power doubles every turn this move is used in succession after the first, maxing out after five turns.
        elif self.effect == 120:
            power = (2 ** attacker.fury_cutter) * 10
            attacker.fury_cutter = min(4, attacker.fury_cutter + 1)
        # Power doubles every turn this move is used in succession after the first, resetting after five turns.
        elif self.effect == 118:
            power = (2 ** attacker.locked_move.turn) * self.power
        # Power varies randomly from 10 to 150.
        elif self.effect == 127:
            percentile = random.randint(0, 100)
            if percentile <= 5:
                power = 10
            elif percentile <= 15:
                power = 30
            elif percentile <= 35:
                power = 50
            elif percentile <= 65:
                power = 70
            elif percentile <= 85:
                power = 90
            elif percentile <= 95:
                power = 110
            else:
                power = 150
        # Power is based on the user's held item
        elif self.effect == 234:
            power = attacker.held_item.power
        # Power increases by 100% for each consecutive use by any friendly Pokémon, to a maximum of 200.
        elif self.effect == 303:
            power = attacker.echoed_voice_power
        # Power is dependent on the user's held berry.
        elif self.effect == 223:
            if attacker.held_item.get() in (
                "enigma berry", "rowap berry", "maranga berry", "jaboca berry", "belue berry", "kee berry",
                "salac berry", "watmel berry", "lansat berry", "custap berry", "liechi berry", "apicot berry",
                "ganlon berry", "petaya berry", "starf berry", "micle berry", "durin berry"
            ):
                power = 100
            elif attacker.held_item.get() in (
                "cornn berry", "spelon berry", "nomel berry", "wepear berry", "kelpsy berry", "bluk berry",
                "grepa berry", "rabuta berry", "pinap berry", "hondew berry", "pomeg berry", "qualot berry",
                "tamato berry", "magost berry", "pamtre berry", "nanab berry"
            ):
                power = 90
            else:
                power = 80
        elif self.effect == 361 and attacker._name == "Greninja-ash":
            power = 20
        # Power is based on the user's base attack. Only applies when not explicitly overridden.
        elif self.effect == 155 and self.power is None:
            power = (attacker.get_raw_attack() // 10) + 5
        # No special changes to power, return its raw value.
        else:
            power = self.power
        
        if power is None:
            return None
        
        #NOTE: this needs to be first as it only applies to raw power
        if attacker.ability() == Ability.TECHNICIAN and power <= 60:
            power *= 1.5
        if attacker.ability() == Ability.TOUGH_CLAWS and self.makes_contact(attacker):
            power *= 1.3
        if attacker.ability() == Ability.RIVALRY and "-x" not in (attacker.gender, defender.gender):
            if attacker.gender == defender.gender:
                power *= 1.25
            else:
                power *= .75
        if attacker.ability() == Ability.IRON_FIST and self.is_punching():
            power *= 1.2
        if attacker.ability() == Ability.STRONG_JAW and self.is_biting():
            power *= 1.5
        if attacker.ability() == Ability.MEGA_LAUNCHER and self.is_aura_or_pulse():
            power *= 1.5
        if attacker.ability() == Ability.SHARPNESS and self.is_slicing():
            power *= 1.5
        if attacker.ability() == Ability.RECKLESS and self.effect in (46, 49, 199, 254, 263, 270):
            power *= 1.2
        if attacker.ability() == Ability.TOXIC_BOOST and self.damage_class == DamageClass.PHYSICAL and attacker.nv.poison():
            power *= 1.5
        if attacker.ability() == Ability.FLARE_BOOST and self.damage_class == DamageClass.SPECIAL and attacker.nv.burn():
            power *= 1.5
        if attacker.ability() == Ability.ANALYTIC and defender.has_moved:
            power *= 1.3
        if attacker.ability() == Ability.BATTERY and self.damage_class == DamageClass.SPECIAL:
            power *= 1.3
        if attacker.ability() == Ability.SHEER_FORCE and self.effect_chance is not None: # Not *perfect* but good enough
            power *= 1.3
        if attacker.ability() == Ability.STAKEOUT and defender.swapped_in:
            power *= 2
        if attacker.ability() == Ability.SUPREME_OVERLORD:
            fainted = sum(poke.hp == 0 for poke in attacker.owner.party)
            if fainted:
                power *= (10 + fainted) / 10
        
        # Type buffing abilities - Some use naive type because the type is changed.
        if attacker.ability() == Ability.AERILATE and self.type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.PIXILATE and self.type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.GALVANIZE and self.type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.REFRIGERATE and self.type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.DRAGONS_MAW and current_type == ElementType.DRAGON:
            power *= 1.5
        if attacker.ability() == Ability.TRANSISTOR and current_type == ElementType.ELECTRIC:
            power *= 1.5
        if attacker.ability() == Ability.WATER_BUBBLE and current_type == ElementType.WATER:
            power *= 2
        if defender.ability(attacker=attacker, move=self) == Ability.WATER_BUBBLE and current_type == ElementType.FIRE:
            power *= .5
        if attacker.ability() == Ability.OVERGROW and current_type == ElementType.GRASS and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.BLAZE and current_type == ElementType.FIRE and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.TORRENT and current_type == ElementType.WATER and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.SWARM and current_type == ElementType.BUG and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.NORMALIZE and current_type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.SAND_FORCE and current_type in (ElementType.ROCK, ElementType.GROUND, ElementType.STEEL) and battle.weather.get() == "sandstorm":
            power *= 1.3
        if attacker.ability() in (Ability.STEELWORKER, Ability.STEELY_SPIRIT) and current_type == ElementType.STEEL:
            power *= 1.5
        if attacker.ability() == Ability.ROCKY_PAYLOAD and current_type == ElementType.ROCK:
            power *= 1.5
        
        # Type buffing items
        if attacker.held_item == "black-glasses" and current_type == ElementType.DARK:
            power *= 1.2
        if attacker.held_item == "black-belt" and current_type == ElementType.FIGHTING:
            power *= 1.2
        if attacker.held_item == "hard-stone" and current_type == ElementType.ROCK:
            power *= 1.2
        if attacker.held_item == "magnet" and current_type == ElementType.ELECTRIC:
            power *= 1.2
        if attacker.held_item == "mystic-water" and current_type == ElementType.WATER:
            power *= 1.2
        if attacker.held_item == "never-melt-ice" and current_type == ElementType.ICE:
            power *= 1.2
        if attacker.held_item == "dragon-fang" and current_type == ElementType.DRAGON:
            power *= 1.2
        if attacker.held_item == "poison-barb" and current_type == ElementType.POISON:
            power *= 1.2
        if attacker.held_item == "charcoal" and current_type == ElementType.FIRE:
            power *= 1.2
        if attacker.held_item == "silk-scarf" and current_type == ElementType.NORMAL:
            power *= 1.2
        if attacker.held_item == "metal-coat" and current_type == ElementType.STEEL:
            power *= 1.2
        if attacker.held_item == "draco-plate" and current_type == ElementType.DRAGON:
            power *= 1.2
        if attacker.held_item == "dread-plate" and current_type == ElementType.DARK:
            power *= 1.2
        if attacker.held_item == "earth-plate" and current_type == ElementType.GROUND:
            power *= 1.2
        if attacker.held_item == "fist-plate" and current_type == ElementType.FIGHTING:
            power *= 1.2
        if attacker.held_item == "flame-plate" and current_type == ElementType.FIRE:
            power *= 1.2
        if attacker.held_item == "icicle-plate" and current_type == ElementType.ICE:
            power *= 1.2
        if attacker.held_item == "insect-plate" and current_type == ElementType.BUG:
            power *= 1.2
        if attacker.held_item == "iron-plate" and current_type == ElementType.STEEL:
            power *= 1.2
        if attacker.held_item == "meadow-plate" and current_type == ElementType.GRASS:
            power *= 1.2
        if attacker.held_item == "mind-plate" and current_type == ElementType.PSYCHIC:
            power *= 1.2
        if attacker.held_item == "pixie-plate" and current_type == ElementType.FAIRY:
            power *= 1.2
        if attacker.held_item == "sky-plate" and current_type == ElementType.FLYING:
            power *= 1.2
        if attacker.held_item == "splash-plate" and current_type == ElementType.WATER:
            power *= 1.2
        if attacker.held_item == "spooky-plate" and current_type == ElementType.GHOST:
            power *= 1.2
        if attacker.held_item == "stone-plate" and current_type == ElementType.ROCK:
            power *= 1.2
        if attacker.held_item == "toxic-plate" and current_type == ElementType.POISON:
            power *= 1.2
        if attacker.held_item == "zap-plate" and current_type == ElementType.ELECTRIC:
            power *= 1.2
        if attacker.held_item == "adamant-orb" and current_type in (ElementType.DRAGON, ElementType.STEEL) and attacker._name == "Dialga":
            power *= 1.2
        if attacker.held_item == "griseous-orb" and current_type in (ElementType.DRAGON, ElementType.GHOST) and attacker._name == "Giratina":
            power *= 1.2
        if attacker.held_item == "soul-dew" and current_type in (ElementType.DRAGON, ElementType.PSYCHIC) and attacker._name in ("Latios", "Latias"):
            power *= 1.2
        if attacker.held_item == "lustrous-orb" and current_type in (ElementType.DRAGON, ElementType.WATER) and attacker._name == "Palkia":
            power *= 1.2
        
        # Damage class buffing items
        if attacker.held_item == "wise-glasses" and self.damage_class == DamageClass.SPECIAL:
            power *= 1.1
        if attacker.held_item == "muscle-band" and self.damage_class == DamageClass.PHYSICAL:
            power *= 1.1

        # If there be weather, this move has doubled power and the weather's type.
        if self.effect == 204 and battle.weather.get() in ("hail", "sandstorm", "rain", "h-rain", "sun", "h-sun"):
            power *= 2
        # During hail, rain-dance, or sandstorm, power is halved.
        if self.effect == 152 and battle.weather.get() in ("rain", "hail"):
            power *= 0.5
        # Power doubles if user is burned, paralyzed, or poisoned.
        if self.effect == 170 and (attacker.nv.burn() or attacker.nv.poison() or attacker.nv.paralysis()):
            power *= 2
        # If the target is paralyzed, power is doubled and cures the paralysis.
        if self.effect == 172 and defender.nv.paralysis():
            power *= 2
            defender.nv.reset()
        # If the target is poisoned, this move has double power.
        if self.effect == 284 and defender.nv.poison():
            power *= 2
        # If the target is sleeping, this move has double power, and the target wakes up.
        if self.effect == 218 and defender.nv.sleep():
            power *= 2
            defender.nv.reset()
        # Has double power against Pokémon that have less than half their max HP remaining.
        if self.effect == 222 and defender.hp < defender.starting_hp // 2:
            power *= 2
        # Power is doubled if the target has already moved this turn.
        if self.effect == 231 and defender.has_moved:
            power *= 2
        # Has double power if the target has a major status ailment.
        if self.effect == 311 and defender.nv.current:
            power *= 2
        # If the user has used defense-curl since entering the field, this move has double power.
        if self.effect == 118 and attacker.defense_curl:
            power *= 2
        # Has double power if the user's last move failed.
        if self.effect == 409 and attacker.last_move_failed:
            power *= 2
        # Has double power if the target is in the first turn of dive.
        if self.effect in (258, 262) and defender.dive:
            power *= 2
        # Has double power if the target is in the first turn of dig.
        if self.effect in (127, 148) and defender.dig:
            power *= 2
        # Has double power if the target is in the first turn of bounce or fly.
        if self.effect in (147, 150) and defender.fly:
            power *= 2
        # Has double power if the user takes damage before attacking this turn.
        if self.effect == 186 and attacker.last_move_damage is not None:
            power *= 2
        # Has double power if the user has no held item.
        if self.effect == 318 and not attacker.held_item.has_item():
            power *= 2
        # Has double power if a friendly Pokémon fainted last turn.
        if self.effect == 320 and attacker.owner.retaliate.active():
            power *= 2
        # Has double power against, and can hit, Pokémon attempting to switch out.
        if self.effect == 129 and (isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.effect in (128, 154, 229, 347, 493)):
            power *= 2
        # Power is doubled if the target has already received damage this turn.
        if self.effect == 232 and defender.dmg_this_turn:
            power *= 2
        # Power is doubled if the target is minimized.
        if self.effect == 151 and defender.minimized:
            power *= 2
        # With Fusion Bolt, power is doubled.
        if self.effect == 336 and battle.last_move_effect == 337:
            power *= 2
        # With Fusion Flare, power is doubled.
        if self.effect == 337 and battle.last_move_effect == 336:
            power *= 2
        # Me first increases the power of the used move by 50%.
        if attacker.owner.selected_action is not None and not isinstance(attacker.owner.selected_action, int) and attacker.owner.selected_action.effect == 242:
            power *= 1.5
        # Has 1.5x power during gravity.
        if self.effect == 435 and battle.gravity.active():
            power *= 1.5
        # If the user attacks before the target, or if the target switched in this turn, its base power doubles.
        if self.effect == 436 and (not defender.has_moved or defender.swapped_in):
            power *= 2
        # If the terrain is psychic and the user is grounded, this move gets 1.5x power.
        if self.effect == 440 and battle.terrain.item == "psychic" and attacker.grounded(battle):
            power *= 1.5
        # Power is doubled if terrain is present.
        if self.effect == 441 and battle.terrain.item and attacker.grounded(battle):
            power *= 2
        # Power is boosted by 50% if used on a Pokémon that is holding an item that can be knocked off.
        if self.effect == 189 and defender.held_item.has_item() and defender.held_item.can_remove():
            power *= 1.5
        # If the target is under the effect of electric terrain, this move has double power.
        if self.effect == 443 and battle.terrain.item == "electric" and defender.grounded(battle, attacker=attacker, move=self):
            power *= 2
        # Deals 1.5x damage if the user is under the effect of misty terrain.
        if self.effect == 444 and battle.terrain.item == "misty" and attacker.grounded(battle):
            power *= 1.5
        # Power is doubled if any of the user's stats were lowered this turn.
        if self.effect == 450 and attacker.stat_decreased:
            power *= 2
        # Power is doubled if the defender has a non volatile status effect.
        if self.effect in (461, 462, 465) and defender.nv.current:
            power *= 2
        # Deals 4/3x damage if supereffective.
        if self.effect == 482 and defender.effectiveness(current_type, battle, attacker=attacker, move=self) > 1:
            power *= 4/3
        # Power is multiplied by (1 + number of fainted party members)x, capping at 101x (100 faints).
        if self.effect == 490:
            power *= 1 + min(attacker.owner.num_fainted, 100)
        # Power is multiplied by (1 + number of times hit)x, capping at 7x (6 hits).
        if self.effect == 491:
            power *= 1 + min(attacker.num_hits, 6)

        # Terrains
        if battle.terrain.item == "psychic" and attacker.grounded(battle) and current_type == ElementType.PSYCHIC:
            power *= 1.3
        if battle.terrain.item == "grassy" and attacker.grounded(battle) and current_type == ElementType.GRASS:
            power *= 1.3
        if battle.terrain.item == "grassy" and defender.grounded(battle, attacker=attacker, move=self) and self.id in (89, 222, 523):
            power *= 0.5
        if battle.terrain.item == "electric" and attacker.grounded(battle) and current_type == ElementType.ELECTRIC:
            power *= 1.3
        if battle.terrain.item == "misty" and defender.grounded(battle, attacker=attacker, move=self) and current_type == ElementType.DRAGON:
            power *= 0.5
            
        # Power buffing statuses
        if attacker.charge.active() and current_type == ElementType.ELECTRIC:
            power *= 2
        if (attacker.owner.mud_sport.active() or defender.owner.mud_sport.active()) and current_type == ElementType.ELECTRIC:
            power //= 3
        if (attacker.owner.water_sport.active() or defender.owner.water_sport.active()) and current_type == ElementType.FIRE:
            power //= 3
        if attacker.victory_dance:
            # This is a DELIBERATE CHOICE to make this move more reasonable given that it comes from a game where
            # stage changes are only applied once and go away after a few turns.
            power *= 1.25

        return int(power)
    
    def get_type(self, attacker, defender, battle):
        """
        Calculates the element type this move will be.
        """
        # Abilities are first because those are intrinsic to the poke and would "apply" to the move first
        if attacker.ability() == Ability.REFRIGERATE and self.type == ElementType.NORMAL:
            return ElementType.ICE
        if attacker.ability() == Ability.PIXILATE and self.type == ElementType.NORMAL:
            return ElementType.FAIRY
        if attacker.ability() == Ability.AERILATE and self.type == ElementType.NORMAL:
            return ElementType.FLYING
        if attacker.ability() == Ability.GALVANIZE and self.type == ElementType.NORMAL:
            return ElementType.ELECTRIC
        if attacker.ability() == Ability.NORMALIZE:
            return ElementType.NORMAL
        if attacker.ability() == Ability.LIQUID_VOICE and self.is_sound_based():
            return ElementType.WATER
        if self.type == ElementType.NORMAL and (attacker.ion_deluge or defender.ion_deluge or battle.plasma_fists):
            return ElementType.ELECTRIC
        if attacker.electrify:
            return ElementType.ELECTRIC
        if self.effect == 204:
            if battle.weather.get() == "hail":
                return ElementType.ICE
            if battle.weather.get() == "sandstorm":
                return ElementType.ROCK
            if battle.weather.get() in ("h-sun", "sun"):
                return ElementType.FIRE
            if battle.weather.get() in ("h-rain", "rain"):
                return ElementType.WATER
        if self.effect == 136:
            # Uses starting IVs as its own IVs should be used even if transformed
            type_idx = attacker.starting_hpiv % 2
            type_idx += 2 * (attacker.starting_atkiv % 2)
            type_idx += 4 * (attacker.starting_defiv % 2)
            type_idx += 8 * (attacker.starting_speediv % 2)
            type_idx += 16 * (attacker.starting_spatkiv % 2)
            type_idx += 32 * (attacker.starting_spdefiv % 2)
            type_idx = (type_idx * 15) // 63
            type_options = {
                0:  ElementType.FIGHTING,
                1:  ElementType.FLYING,
                2:  ElementType.POISON,
                3:  ElementType.GROUND,
                4:  ElementType.ROCK,
                5:  ElementType.BUG,
                6:  ElementType.GHOST,
                7:  ElementType.STEEL,
                8:  ElementType.FIRE,
                9:  ElementType.WATER,
                10: ElementType.GRASS,
                11: ElementType.ELECTRIC,
                12: ElementType.PSYCHIC,
                13: ElementType.ICE,
                14: ElementType.DRAGON,
                15: ElementType.DARK,
            }
            return type_options[type_idx]
        if self.effect == 401:
            if len(attacker.type_ids) == 0:
                return ElementType.TYPELESS
            return attacker.type_ids[0]
        if self.effect == 269:
            if attacker.held_item in ("draco-plate", "dragon-memory"):
                return ElementType.DRAGON
            if attacker.held_item in ("dread-plate", "dark-memory"):
                return ElementType.DARK
            if attacker.held_item in ("earth-plate", "ground-memory"):
                return ElementType.GROUND
            if attacker.held_item in ("fist-plate", "fighting-memory"):
                return ElementType.FIGHTING
            if attacker.held_item in ("flame-plate", "burn-drive", "fire-memory"):
                return ElementType.FIRE
            if attacker.held_item in ("icicle-plate", "chill-drive", "ice-memory"):
                return ElementType.ICE
            if attacker.held_item in ("insect-plate", "bug-memory"):
                return ElementType.BUG
            if attacker.held_item in ("iron-plate", "steel-memory"):
                return ElementType.STEEL
            if attacker.held_item in ("meadow-plate", "grass-memory"):
                return ElementType.GRASS
            if attacker.held_item in ("mind-plate", "psychic-memory"):
                return ElementType.PSYCHIC
            if attacker.held_item in ("pixie-plate", "fairy-memory"):
                return ElementType.FAIRY
            if attacker.held_item in ("sky-plate", "flying-memory"):
                return ElementType.FLYING
            if attacker.held_item in ("splash-plate", "douse-drive", "water-memory"):
                return ElementType.WATER
            if attacker.held_item in ("spooky-plate", "ghost-memory"):
                return ElementType.GHOST
            if attacker.held_item in ("stone-plate", "rock-memory"):
                return ElementType.ROCK
            if attacker.held_item in ("toxic-plate", "poison-memory"):
                return ElementType.POISON
            if attacker.held_item in ("zap-plate", "shock-drive", "electric-memory"):
                return ElementType.ELECTRIC
        if self.effect == 223:
            hi = attacker.held_item.get()
            if hi in ("figy-berry", "tanga-berry", "cornn-berry", "enigma-berry"):
                return ElementType.BUG
            if hi in ("iapapa-berry", "colbur-berry", "spelon-berry", "rowap-berry", "maranga-berry"):
                return ElementType.DARK
            if hi in ("aguav-berry", "haban-berry", "nomel-berry", "jaboca-berry"):
                return ElementType.DRAGON
            if hi in ("pecha-berry", "wacan-berry", "wepear-berry", "belue-berry"):
                return ElementType.ELECTRIC
            if hi in ("roseli-berry", "kee-berry"):
                return ElementType.FAIRY
            if hi in ("leppa-berry", "chople-berry", "kelpsy-berry", "salac-berry"):
                return ElementType.FIGHTING
            if hi in ("cheri-berry", "occa-berry", "bluk-berry", "watmel-berry"):
                return ElementType.FIRE
            if hi in ("lum-berry", "coba-berry", "grepa-berry", "lansat-berry"):
                return ElementType.FLYING
            if hi in ("mago-berry", "kasib-berry", "rabuta-berry", "custap-berry"):
                return ElementType.GHOST
            if hi in ("rawst-berry", "rindo-berry", "pinap-berry", "liechi-berry"):
                return ElementType.GRASS
            if hi in ("persim-berry", "shuca-berry", "hondew-berry", "apicot-berry"):
                return ElementType.GROUND
            if hi in ("aspear-berry", "yache-berry", "pomeg-berry", "ganlon-berry"):
                return ElementType.ICE
            if hi in ("oran-berry", "kebia-berry", "qualot-berry", "petaya-berry"):
                return ElementType.POISON
            if hi in ("sitrus-berry", "payapa-berry", "tamato-berry", "starf-berry"):
                return ElementType.PSYCHIC
            if hi in ("wiki-berry", "charti-berry", "magost-berry", "micle-berry"):
                return ElementType.ROCK
            if hi in ("razz-berry", "babiri-berry", "pamtre-berry"):
                return ElementType.STEEL
            if hi in ("chesto-berry", "passho-berry", "nanab-berry", "durin-berry"):
                return ElementType.WATER
            if hi == "chilan-berry":
                return ElementType.NORMAL
        if self.effect == 433 and attacker._name == "Morpeko-hangry":
            return ElementType.DARK
        if self.effect == 441 and attacker.grounded(battle):
            if battle.terrain.item == "electric":
                return ElementType.ELECTRIC
            if battle.terrain.item == "grass":
                return ElementType.GRASS
            if battle.terrain.item == "misty":
                return ElementType.FAIRY
            if battle.terrain.item == "psychic":
                return ElementType.PSYCHIC
        if self.id == 873:
            if attacker._name == "Tauros-paldea":
                return ElementType.FIGHTING
            if attacker._name == "Tauros-aqua-paldea":
                return ElementType.WATER
            if attacker._name == "Tauros-blaze-paldea":
                return ElementType.FIRE
        
        return self.type
           
    def get_priority(self, attacker, defender, battle):
        """
        Calculates the priority value for this move.
        
        Returns an int priority from -7 to 5.
        """
        priority = self.priority
        current_type = self.get_type(attacker, defender, battle)
        if self.effect == 437 and attacker.grounded(battle) and battle.terrain.item == "grassy":
            priority += 1
        if attacker.ability() == Ability.GALE_WINGS and current_type == ElementType.FLYING and attacker.hp == attacker.starting_hp:
            priority += 1
        if attacker.ability() == Ability.PRANKSTER and self.damage_class == DamageClass.STATUS:
            priority += 1
        if attacker.ability() == Ability.TRIAGE and self.is_affected_by_heal_block():
            priority += 3
        return priority
    
    def get_effect_chance(self, attacker, defender, battle):
        """
        Gets the chance for secondary effects to occur.
        
        Returns an int from 0-100.
        """
        if self.effect_chance is None:
            return 100
        if defender.ability(attacker=attacker, move=self) == Ability.SHIELD_DUST:
            return 0
        if attacker.ability() == Ability.SHEER_FORCE:
            return 0
        if attacker.ability() == Ability.SERENE_GRACE:
            return min(100, self.effect_chance * 2)
        return self.effect_chance
    
    def check_executable(self, attacker, defender, battle):
        """
        Returns True if the move can be executed, False otherwise
        
        Checks different requirements for moves that can make them fail.
        """
        if attacker.taunt.active() and self.damage_class == DamageClass.STATUS:
            return False
        if attacker.silenced.active() and self.is_sound_based():
            return False
        if self.is_affected_by_heal_block() and attacker.heal_block.active():
            return False
        if self.is_powder_or_spore() and (ElementType.GRASS in defender.type_ids or defender.ability(attacker=attacker, move=self) == Ability.OVERCOAT or defender.held_item == "safety-goggles"):
            return False
        if battle.weather.get() == "h-sun" and self.get_type(attacker, defender, battle) == ElementType.WATER and self.damage_class != DamageClass.STATUS:
            return False
        if battle.weather.get() == "h-rain" and self.get_type(attacker, defender, battle) == ElementType.FIRE and self.damage_class != DamageClass.STATUS:
            return False
        if attacker.disable.active() and attacker.disable.item is self:
            return False
        if attacker is not defender and defender.imprison and self.id in [x.id for x in defender.moves]:
            return False
        #Since we only have single battles, these moves always fail
        if self.effect in (173, 301, 308, 316, 363, 445):
            return False
        if self.effect in (93, 98) and not attacker.nv.sleep():
            return False
        if self.effect in (9, 108) and not defender.nv.sleep():
            return False
        if self.effect == 364 and not defender.nv.poison():
            return False
        if self.effect in (162, 163) and attacker.stockpile == 0:
            return False
        if self.effect == 85 and (ElementType.GRASS in defender.type_ids or defender.leech_seed):
            return False
        if self.effect == 193 and attacker.imprison:
            return False
        if self.effect == 166 and defender.torment:
            return False
        if self.effect == 91 and (defender.encore.active() or defender.last_move is None or defender.last_move.pp == 0):
            return False
        if self.effect == 87 and (defender.disable.active() or defender.last_move is None or defender.last_move.pp == 0):
            return False
        if self.effect in (96, 101) and (defender.last_move is None or defender.last_move.pp == 0):
            return False
        if self.effect == 176 and defender.taunt.active():
            return False
        if self.effect == 29 and not defender.owner.valid_swaps(attacker, battle, check_trap=False):
            return False
        if self.effect in (128, 154, 493) and not attacker.owner.valid_swaps(defender, battle, check_trap=False):
            return False
        if self.effect == 161 and attacker.stockpile >= 3:
            return False
        if self.effect in (90, 145, 228, 408) and attacker.last_move_damage is None:
            return False
        if self.effect == 145 and attacker.last_move_damage[1] != DamageClass.SPECIAL:
            return False
        if self.effect in (90, 408) and attacker.last_move_damage[1] != DamageClass.PHYSICAL:
            return False
        if self.effect in (10, 243) and (defender.last_move is None or not defender.last_move.selectable_by_mirror_move()):
            return False
        if self.effect == 83 and (defender.last_move is None or not defender.last_move.selectable_by_mimic()):
            return False
        if self.effect == 180 and attacker.owner.wish.active():
            return False
        if self.effect == 388 and defender.attack_stage == -6:
            return False
        if self.effect in (143, 485, 493) and attacker.hp <= attacker.starting_hp // 2:
            return False
        if self.effect == 414 and attacker.hp < attacker.starting_hp // 3:
            return False
        if self.effect == 80 and attacker.hp <= attacker.starting_hp // 4:
            return False
        if self.effect == 48 and attacker.focus_energy:
            return False
        if self.effect == 190 and attacker.hp >= defender.hp:
            return False
        if self.effect == 194 and not (attacker.nv.burn() or attacker.nv.paralysis() or attacker.nv.poison()):
            return False
        if self.effect == 235 and (not attacker.nv.current or defender.nv.current):
            return False
        if self.effect in (121, 266) and ("-x" in (attacker.gender, defender.gender) or attacker.gender == defender.gender or defender.ability(attacker=attacker, move=self) == Ability.OBLIVIOUS):
            return False
        if self.effect in (367, 392) and attacker.ability() not in (Ability.PLUS, Ability.MINUS):
            return False
        if self.effect == 39 and attacker.level < defender.level:
            return False
        if self.effect in (46, 86, 156, 264, 286) and battle.gravity.active():
            return False
        if self.effect == 113 and defender.owner.spikes == 3:
            return False
        if self.effect == 250 and defender.owner.toxic_spikes == 2:
            return False
        if self.effect in (159, 377, 383) and attacker.active_turns != 0:
            return False
        if self.effect == 98 and not any(m.selectable_by_sleep_talk() for m in attacker.moves):
            return False
        if self.effect == 407 and not battle.weather.get() == "hail":
            return False
        if self.effect == 407 and attacker.owner.aurora_veil.active():
            return False
        if self.effect == 47 and attacker.owner.mist.active():
            return False
        if self.effect in (80, 493) and attacker.substitute:
            return False
        if self.effect == 398 and ElementType.FIRE not in attacker.type_ids:
            return False
        if self.effect == 481 and ElementType.ELECTRIC not in attacker.type_ids:
            return False
        if self.effect == 376 and ElementType.GRASS in defender.type_ids:
            return False
        if self.effect == 343 and ElementType.GHOST in defender.type_ids:
            return False
        if self.effect == 107 and defender.trapping:
            return False
        if self.effect == 182 and attacker.ingrain:
            return False
        if self.effect == 94 and self.get_conversion_2(attacker, defender, battle) is None:
            return False
        if self.effect == 121 and defender.infatuated is attacker:
            return False
        if self.effect == 248 and defender.ability(attacker=attacker, move=self) == Ability.INSOMNIA:
            return False
        if self.effect in (242, 249) and (defender.has_moved or isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.damage_class == DamageClass.STATUS):
            return False
        if self.effect == 252 and attacker.aqua_ring:
            return False
        if self.effect == 253 and attacker.magnet_rise.active():
            return False
        if self.effect == 221 and attacker.owner.healing_wish:
            return False
        if self.effect == 271 and attacker.owner.lunar_dance:
            return False
        if self.effect in (240, 248, 299, 300) and not defender.ability_changeable():
            return False
        if self.effect == 300 and not attacker.ability_giveable():
            return False
        if self.effect == 241 and attacker.lucky_chant.active():
            return False
        if self.effect == 125 and attacker.owner.safeguard.active():
            return False
        if self.effect == 293 and not set(attacker.type_ids) & set(defender.type_ids):
            return False
        if self.effect == 295 and defender.ability(attacker=attacker, move=self) == Ability.MULTITYPE:
            return False
        if self.effect == 319 and not defender.type_ids:
            return False
        if self.effect == 171 and attacker.last_move_damage is not None:
            return False
        if self.effect == 179 and not (attacker.ability_changeable() and defender.ability_giveable()):
            return False
        if self.effect == 181 and attacker.get_assist_move() is None:
            return False
        if self.effect in (112, 117, 184, 195, 196, 279, 307, 345, 350, 354, 356, 362, 378, 384, 454, 488) and defender.has_moved:
            return False
        if self.effect == 192 and not (attacker.ability_changeable() and attacker.ability_giveable() and defender.ability_changeable() and defender.ability_giveable()):
            return False
        if self.effect == 226 and attacker.owner.tailwind.active():
            return False
        if self.effect in (90, 92, 145) and attacker.substitute:
            return False
        if self.effect in (85, 92, 169, 178, 188, 206, 388) and defender.substitute:
            return False
        if self.effect == 234 and (not attacker.held_item.power or attacker.ability() == Ability.STICKY_HOLD):
            return False
        if self.effect == 178 and (Ability.STICKY_HOLD in (attacker.ability(), defender.ability(attacker=attacker, move=self)) or not attacker.held_item.can_remove() or not defender.held_item.can_remove()):
            return False
        if self.effect == 202 and attacker.owner.mud_sport.active():
            return False
        if self.effect == 211 and attacker.owner.water_sport.active():
            return False
        if self.effect == 149 and defender.owner.future_sight.active():
            return False
        if self.effect == 188 and (defender.nv.current or defender.ability(attacker=attacker, move=self) in (Ability.INSOMNIA, Ability.VITAL_SPIRIT, Ability.SWEET_VEIL) or defender.yawn.active()):
            return False
        if self.effect == 188 and battle.terrain.item == "electric" and attacker.grounded(battle):
            return False
        if self.effect in (340, 351) and not any(ElementType.GRASS in p.type_ids and p.grounded(battle) and not p.dive and not p.dig and not p.fly and not p.shadow_force for p in (attacker, defender)):
            return False
        if self.effect == 341 and defender.owner.sticky_web:
            return False
        if self.effect in (112, 117, 356, 362, 384, 454, 488) and random.randint(1, attacker.protection_chance) != 1:
            return False
        if self.effect == 403 and (defender.last_move is None or defender.last_move.pp == 0 or not defender.last_move.selectable_by_instruct() or defender.locked_move is not None):
            return False
        if self.effect == 378 and (ElementType.GRASS in defender.type_ids or defender.ability(attacker=attacker, move=self) == Ability.OVERCOAT or defender.held_item == "safety-goggles"):
            return False
        if self.effect == 233 and defender.embargo.active():
            return False
        if self.effect == 324 and (not attacker.held_item.has_item() or defender.held_item.has_item() or not attacker.held_item.can_remove()):
            return False
        if self.effect == 185 and (attacker.held_item.has_item() or attacker.held_item.last_used is None):
            return False
        if self.effect == 430 and (not defender.held_item.has_item() or not defender.held_item.can_remove() or defender.corrosive_gas):
            return False
        if self.effect == 114 and defender.foresight:
            return False
        if self.effect == 217 and defender.miracle_eye:
            return False
        if self.effect == 38 and (attacker.nv.sleep() or attacker.hp == attacker.starting_hp or attacker._name == "Minior"):
            return False
        if self.effect == 427 and attacker.no_retreat:
            return False
        if self.effect == 99 and attacker.destiny_bond_cooldown.active():
            return False
        if self.effect in (116, 137, 138, 165) and battle.weather.get() in ("h-rain", "h-sun", "h-wind"):
            return False
        if self.effect in (8, 420, 444) and Ability.DAMP in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
            return False
        if self.effect in (223, 453) and not attacker.held_item.is_berry():
            return False
        if self.effect == 369 and battle.terrain.item == "electric":
            return False
        if self.effect == 352 and battle.terrain.item == "grassy":
            return False
        if self.effect == 353 and battle.terrain.item == "misty":
            return False
        if self.effect == 395 and battle.terrain.item == "psychic":
            return False
        if self.effect == 66 and attacker.owner.reflect.active():
            return False
        if self.effect == 36 and attacker.owner.light_screen.active():
            return False
        if self.effect == 110 and ElementType.GHOST in attacker.type_ids and defender.cursed:
            return False
        if self.effect == 58 and (defender.substitute or defender.illusion_name is not None):
            return False
        if self.effect == 446 and defender.held_item.get() is None:
            return False
        if self.effect == 448 and not battle.terrain.item:
            return False
        if self.effect == 452 and defender.octolock:
            return False
        if self.effect == 280 and any([defender.defense_split, defender.spdef_split, attacker.defense_split, attacker.spdef_split]):
            return False
        if self.effect == 281 and any([defender.attack_split, defender.spatk_split, attacker.attack_split, attacker.spatk_split]):
            return False
        if self.effect == 456 and (defender.type_ids == [ElementType.PSYCHIC] or defender.ability(attacker=attacker, move=self) == Ability.RKS_SYSTEM):
            return False
        if self.effect == 83 and self not in attacker.moves:
            return False
        if self.effect == 468 and attacker.victory_dance:
            return False
        if defender.ability(attacker=attacker, move=self) in (Ability.QUEENLY_MAJESTY, Ability.DAZZLING, Ability.ARMOR_TAIL) and self.get_priority(attacker, defender, battle) > 0:
            return False
        return True
    
    def check_semi_invulnerable(self, attacker, defender, battle):
        """
        Returns True if this move hits, False otherwise.
        
        Checks if a pokemon is in the semi-invulnerable turn of dive or dig.
        """
        if not self.targets_opponent():
            return True
        if Ability.NO_GUARD in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
            return True
        if defender.mind_reader.active() and defender.mind_reader.item is attacker:
            return True
        if defender.dive and self.effect not in (258, 262):
            return False
        if defender.dig and self.effect not in (127, 148):
            return False
        if defender.fly and self.effect not in (147, 150, 153, 208, 288, 334, 373):
            return False
        if defender.shadow_force:
            return False
        return True
    
    def check_protect(self, attacker, defender, battle):
        """
        Returns True if this move hits, False otherwise.
        
        Checks if this pokemon is protected by a move like protect or wide guard.
        Also returns a formatted message.
        """
        msg = ""
        # Moves that don't target the opponent can't be protected by the target.
        if not self.targets_opponent():
            return True, msg
        # Moves which bypass all protection.
        if self.effect in (149, 224, 273, 360, 438, 489):
            return True, msg
        if attacker.ability() == Ability.UNSEEN_FIST and self.makes_contact(attacker):
            return True, msg
        if defender.crafty_shield and self.damage_class == DamageClass.STATUS:
            return False, msg
        # Moves which bypass all protection except for crafty shield.
        if self.effect in (29, 107, 179, 412):
            return True, msg
        if defender.protect:
            return False, msg
        if defender.spiky_shield:
            if self.makes_contact(attacker):
                msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{defender.name}'s spiky shield")
            return False, msg
        if defender.baneful_bunker:
            if self.makes_contact(attacker):
                msg += attacker.nv.apply_status("poison", battle, attacker=defender, source=f"{defender.name}'s baneful bunker")
            return False, msg
        if defender.wide_guard and self.targets_multiple():
            return False, msg
        if self.get_priority(attacker, defender, battle) > 0 and battle.terrain.item == "psychic" and defender.grounded(battle, attacker=attacker, move=self):
            return False, msg
        if defender.mat_block and self.damage_class != DamageClass.STATUS:
            return False, msg
        if defender.king_shield and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker):
                msg += attacker.append_attack(-1, attacker=defender, move=self)
            return False, msg
        if defender.obstruct and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker):
                msg += attacker.append_defense(-2, attacker=defender, move=self)
            return False, msg
        if defender.silk_trap and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker):
                msg += attacker.append_speed(-1, attacker=defender, move=self)
            return False, msg
        if defender.quick_guard and self.get_priority(attacker, defender, battle) > 0:
            return False, msg
        return True, msg
    
    def check_hit(self, attacker, defender, battle):
        """
        Returns True if this move hits, False otherwise.
        
        Calculates the chance to hit & does an RNG check using that chance.
        """
        micle_used = attacker.micle_berry_ate
        attacker.micle_berry_ate = False
        #Moves that have a None accuracy always hit.
        if self.accuracy is None:
            return True
        
        # During hail, this bypasses accuracy checks
        if self.effect == 261 and battle.weather.get() == "hail":
            return True
        # During rain, this bypasses accuracy checks
        if self.effect in (153, 334) and battle.weather.get() in ("rain", "h-rain"):
            return True
        # If used by a poison type, this bypasses accuracy checks
        if self.effect == 34 and ElementType.POISON in attacker.type_ids:
            return True
        # If used against a minimized poke, this bypasses accuracy checks
        if self.effect == 338 and defender.minimized:
            return True
        
        # These DO allow OHKO moves to bypass accuracy checks
        if self.targets_opponent():
            if defender.mind_reader.active() and defender.mind_reader.item is attacker:
                return True
            if attacker.ability() == Ability.NO_GUARD:
                return True
            if defender.ability(attacker=attacker, move=self) == Ability.NO_GUARD:
                return True
        
        # OHKO moves
        if self.effect == 39:
            accuracy = 30 + (attacker.level - defender.level)
            return random.uniform(0, 100) <= accuracy
        
        # This does NOT allow OHKO moves to bypass accuracy checks
        if attacker.telekinesis.active():
            return True
            
        
        accuracy = self.accuracy
        # When used during harsh sunlight, this has an accuracy of 50%
        if self.effect in (153, 334) and battle.weather.get() in ("sun", "h-sun"):
            accuracy = 50
        if self.targets_opponent():
            if defender.ability(attacker=attacker, move=self) == Ability.WONDER_SKIN and self.damage_class == DamageClass.STATUS:
                accuracy = 50
        
        if defender.ability(attacker=attacker, move=self) == Ability.UNAWARE:
            stage = 0
        else:
            stage = attacker.get_accuracy(battle)
        if not (self.effect == 304 or defender.foresight or defender.miracle_eye or attacker.ability() == Ability.UNAWARE):
            stage -= defender.get_evasion(battle)
        stage = min(6, max(-6, stage))
        stage_multiplier = {
            -6: 3/9,
            -5: 3/8,
            -4: 3/7,
            -3: 3/6,
            -2: 3/5,
            -1: 3/4,
            0: 1,
            1: 4/3,
            2: 5/3,
            3: 2,
            4: 7/3,
            5: 8/3,
            6: 3,
        }
        accuracy *= stage_multiplier[stage]
        if self.targets_opponent():
            if defender.ability(attacker=attacker, move=self) == Ability.TANGLED_FEET and defender.confusion.active():
                accuracy *= .5
            if defender.ability(attacker=attacker, move=self) == Ability.SAND_VEIL and battle.weather.get() == "sandstorm":
                accuracy *= .8
            if defender.ability(attacker=attacker, move=self) == Ability.SNOW_CLOAK and battle.weather.get() == "hail":
                accuracy *= .8
        if attacker.ability() == Ability.COMPOUND_EYES:
            accuracy *= 1.3
        if attacker.ability() == Ability.HUSTLE and self.damage_class == DamageClass.PHYSICAL:
            accuracy *= .8
        if attacker.ability() == Ability.VICTORY_STAR:
            accuracy *= 1.1
        if battle.gravity.active():
            accuracy *= (5 / 3)
        if attacker.held_item == "wide-lens":
            accuracy *= 1.1
        if attacker.held_item == "zoom-lens" and defender.has_moved:
            accuracy *= 1.2
        if defender.held_item == "bright-powder":
            accuracy *= .9
        if micle_used:
            accuracy *= 1.2

        return random.uniform(0, 100) <= accuracy
    
    def check_effective(self, attacker, defender, battle):
        """
        Returns True if a move has an effect on a poke.
        
        Moves can have no effect based on things like type effectiveness and groundedness.
        """
        # What if I :flushed: used Hold Hands :flushed: in a double battle :flushed: with you? :flushed:
        # (and you weren't protected by Crafty Shield or in the semi-invulnerable turn of a move like Fly or Dig)
        if self.effect in (86, 174, 368, 370, 371, 389):
            return False
        
        if not self.targets_opponent():
            return True
        
        if self.effect == 266 and defender.ability(attacker=attacker, move=self) == Ability.OBLIVIOUS:
            return False
        if self.effect == 39 and defender.ability(attacker=attacker, move=self) == Ability.STURDY:
            return False
        if self.effect == 39 and self.id == 329 and ElementType.ICE in defender.type_ids:
            return False
        if self.effect == 400 and not defender.nv.current:
            return False
        if self.is_sound_based() and defender.ability(attacker=attacker, move=self) == Ability.SOUNDPROOF:
            return False
        if self.is_ball_or_bomb() and defender.ability(attacker=attacker, move=self) == Ability.BULLETPROOF:
            return False
        if attacker.ability() == Ability.PRANKSTER and ElementType.DARK in defender.type_ids:
            if self.damage_class == DamageClass.STATUS:
                return False
            # If the attacker used a status move that called this move, even if this move is not a status move then it should still be considered affected by prankster.
            if not isinstance(attacker.owner.selected_action, int) and attacker.owner.selected_action.damage_class == DamageClass.STATUS:
                return False
        if defender.ability(attacker=attacker, move=self) == Ability.GOOD_AS_GOLD and self.damage_class == DamageClass.STATUS:
            return False
        
        # Status moves do not care about type effectiveness - except for thunder wave FOR SOME REASON...
        if self.damage_class == DamageClass.STATUS and self.id != 86:
            return True
        
        current_type = self.get_type(attacker, defender, battle)
        if current_type == ElementType.TYPELESS:
            return True
        effectiveness = defender.effectiveness(current_type, battle, attacker=attacker, move=self)
        if self.effect == 338:
            effectiveness *= defender.effectiveness(ElementType.FLYING, battle, attacker=attacker, move=self)
        if effectiveness == 0:
            return False
        
        if current_type == ElementType.GROUND and not defender.grounded(battle, attacker=attacker, move=self) and self.effect != 373 and not battle.inverse_battle:
            return False
        if self.effect != 459:
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.VOLT_ABSORB and defender.hp == defender.starting_hp:
                return False
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) in (Ability.WATER_ABSORB, Ability.DRY_SKIN) and defender.hp == defender.starting_hp:
                return False
        if current_type == ElementType.FIRE and defender.ability(attacker=attacker, move=self) == Ability.FLASH_FIRE and defender.flash_fire:
            return False
        if effectiveness <= 1 and defender.ability(attacker=attacker, move=self) == Ability.WONDER_GUARD:
            return False
        
        return True

    def is_sound_based(self):
        """Whether or not this move is sound based."""
        return self.id in [
            45, 46, 47, 48, 103, 173, 195, 215, 253, 304, 319, 320, 336, 405, 448, 496, 497, 547,
            555, 568, 574, 575, 586, 590, 664, 691, 728, 744, 753, 826, 871
        ]
    
    def is_punching(self):
        """Whether or not this move is a punching move."""
        return self.id in [
            4, 5, 7, 8, 9, 146, 183, 223, 264, 309, 325, 327, 359, 409, 418, 612, 665, 721, 729,
            764, 765, 834, 857, 889
        ]
    
    def is_biting(self):
        """Whether or not this move is a biting move."""
        return self.id in [44, 158, 242, 305, 422, 423, 424, 706, 733, 742]
    
    def is_ball_or_bomb(self):
        """Whether or not this move is a ball or bomb move."""
        return self.id in [
            121, 140, 188, 190, 192, 247, 296, 301, 311, 331, 350, 360, 396, 402, 411, 412, 426,
            439, 443, 486, 491, 545, 676, 690, 748
        ]
    
    def is_aura_or_pulse(self):
        """Whether or not this move is an aura or pulse move."""
        return self.id in [352, 396, 399, 406, 505, 618, 805]
    
    def is_powder_or_spore(self):
        """Whether or not this move is a powder or spore move."""
        return self.id in [77, 78, 79, 147, 178, 476, 600, 737]
    
    def is_dance(self):
        """Whether or not this move is a dance move."""
        return self.id in [14, 80, 297, 298, 349, 461, 483, 552, 686, 744, 846, 872]
    
    def is_slicing(self):
        """Whether or not this move is a slicing move."""
        return self.id in [
            15, 75, 163, 210, 314, 332, 348, 400, 403, 404, 427, 440, 533, 534, 669, 749, 830, 845,
            860, 869, 891, 895
        ]
    
    def is_wind(self):
        """Whether or not this move is a wind move."""
        return self.id in [16, 18, 59, 196, 201, 239, 257, 314, 366, 542, 572, 584, 829, 842, 844, 849]
    
    def is_affected_by_magic_coat(self):
        """Whether or not this move can be reflected by magic coat and magic bounce."""
        return self.id in [
            18, 28, 39, 43, 45, 46, 47, 48, 50, 73, 77, 78, 79, 81, 86, 92, 95, 103, 108, 109, 134,
            137, 139, 142, 147, 148, 169, 178, 180, 184, 186, 191, 193, 204, 207, 212, 213, 227, 230,
            259, 260, 261, 269, 281, 297, 313, 316, 319, 320, 321, 335, 357, 373, 377, 380, 388, 390,
            432, 445, 446, 464, 477, 487, 493, 494, 505, 564, 567, 568, 571, 575, 576, 589, 590, 598,
            599, 600, 608, 666, 668, 671, 672, 685, 715, 736, 737, 810
        ]
    
    def is_affected_by_heal_block(self):
        """Whether or not this move cannot be selected during heal block."""
        return self.id in [
            71, 72, 105, 135, 138, 141, 156, 202, 208, 234, 235, 236, 256, 273, 303, 355, 361, 409,
            456, 461, 505, 532, 570, 577, 613, 659, 666, 668, 685
        ]
    
    def is_affected_by_substitute(self):
        """Whether or not this move is able to bypass a substitute."""
        return self.id not in [
            18, 45, 46, 47, 48, 50, 102, 103, 114, 166, 173, 174, 176, 180, 193, 195, 213, 215, 227,
            244, 253, 259, 269, 270, 272, 285, 286, 304, 312, 316, 319, 320, 357, 367, 382, 384, 385,
            391, 405, 448, 495, 496, 497, 513, 516, 547, 555, 568, 574, 575, 586, 587, 589, 590, 593,
            597, 600, 602, 607, 621, 664, 674, 683, 689, 691, 712, 728, 753, 826
        ]
    
    def targets_opponent(self):
        """Whether or not this move targets the opponent."""
        #Moves which don't follow normal targeting protocals, ignore them unless they are damaging.
        if self.target == MoveTarget.SPECIFIC_MOVE and self.damage_class == DamageClass.STATUS:
            return False
        #Moves which do not target the opponent pokemon.
        return self.target not in (
            MoveTarget.SELECTED_POKEMON_ME_FIRST,
            MoveTarget.ALLY,
            MoveTarget.USERS_FIELD,
            MoveTarget.USER_OR_ALLY,
            MoveTarget.OPPONENTS_FIELD,
            MoveTarget.USER,
            MoveTarget.ENTIRE_FIELD,
            MoveTarget.USER_AND_ALLIES,
            MoveTarget.ALL_ALLIES,
        )
    
    def targets_multiple(self):
        """Whether or not this move targets multiple pokemon."""
        return self.target in (
            MoveTarget.ALL_OTHER_POKEMON,
            MoveTarget.ALL_OPPONENTS,
            MoveTarget.USER_AND_ALLIES,
            MoveTarget.ALL_POKEMON,
            MoveTarget.ALL_ALLIES,
        )
    
    def makes_contact(self, attacker):
        """Whether or not this move makes contact."""
        return self.id in [
            1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 15, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29,
            30, 31, 32, 33, 34, 35, 36, 37, 38, 44, 64, 65, 66, 67, 68, 69, 70, 80, 91, 98, 99,
            117, 122, 127, 128, 130, 132, 136, 141, 146, 152, 154, 158, 162, 163, 165, 167, 168,
            172, 175, 179, 183, 185, 200, 205, 206, 209, 210, 211, 216, 218, 223, 224, 228, 229,
            231, 232, 233, 238, 242, 245, 249, 252, 263, 264, 265, 276, 279, 280, 282, 283, 291,
            292, 299, 301, 302, 305, 306, 309, 310, 325, 327, 332, 337, 340, 342, 343, 344, 348,
            358, 359, 360, 365, 369, 370, 371, 372, 376, 378, 386, 387, 389, 394, 395, 398, 400,
            401, 404, 407, 409, 413, 416, 418, 419, 421, 422, 423, 424, 425, 428, 431, 438, 440,
            442, 447, 450, 452, 453, 457, 458, 462, 467, 480, 484, 488, 490, 492, 498, 507, 509,
            512, 514, 525, 528, 529, 530, 531, 532, 533, 534, 535, 537, 541, 543, 544, 550, 557,
            560, 565, 566, 577, 583, 609, 610, 611, 612, 620, 658, 660, 663, 665, 667, 669, 675,
            677, 679, 680, 681, 684, 688, 692, 693, 696, 699, 701, 706, 707, 709, 710, 712, 713,
            716, 718, 721, 724, 729, 730, 733, 741, 742, 745, 747, 749, 750, 752, 756, 760, 764,
            765, 766, 779, 799, 803, 806, 812, 813, 821, 830, 832, 834, 840, 845, 848, 853, 857,
            859, 860, 861, 862, 866, 869, 872, 873, 878, 879, 884, 885, 887, 889, 891, 892, 894
        ] and not attacker.ability() == Ability.LONG_REACH
    
    def selectable_by_mirror_move(self):
        """Whether or not this move can be selected by mirror move."""
        return self.id not in [
            10, 14, 54, 68, 74, 96, 97, 100, 102, 104, 105, 106, 107, 110, 111, 112, 113, 114, 115,
            116, 117, 118, 119, 133, 135, 144, 150, 151, 156, 159, 160, 164, 165, 166, 174, 176,
            182, 187, 191, 194, 195, 197, 201, 203, 208, 214, 215, 219, 226, 234, 235, 236, 240,
            241, 243, 244, 248, 254, 255, 256, 258, 264, 266, 267, 268, 270, 272, 273, 274, 275,
            277, 278, 286, 287, 288, 289, 293, 294, 300, 303, 312, 322, 334, 336, 339, 346, 347,
            349, 353, 355, 356, 361, 366, 367, 379, 381, 382, 383, 390, 392, 393, 397, 417, 446,
            455, 456, 461, 468, 469, 470, 471, 475, 476, 483, 489, 495, 501, 502, 504, 505, 508,
            513, 515, 526, 538, 561, 562, 563, 564, 569, 578, 579, 580, 581, 596, 597, 601, 602,
            603, 604, 606, 607
        ]
    
    def selectable_by_sleep_talk(self):
        """Whether or not this move can be selected by sleep talk."""
        return self.id not in [
            13, 19, 76, 91, 102, 117, 118, 119, 130, 143, 166, 253, 264, 274, 291, 340, 382, 383,
            467, 507, 553, 554, 562, 566, 601, 669, 690, 704, 731
        ]
    
    def selectable_by_assist(self):
        """Whether or not this move can be selected by assist."""
        return self.id not in [
            18, 19, 46, 68, 91, 102, 118, 119, 144, 165, 166, 168, 182, 194, 197, 203, 214, 243,
            264, 266, 267, 270, 271, 289, 291, 340, 343, 364, 382, 383, 415, 448, 467, 476, 507,
            509, 516, 525, 561, 562, 566, 588, 596, 606, 607, 661, 671, 690, 704
        ]
    
    def selectable_by_mimic(self):
        """Whether or not this move can be selected by mimic."""
        return self.id not in [102, 118, 165, 166, 448, 896]
    
    def selectable_by_instruct(self):
        """Whether or not this move can be selected by instruct."""
        return self.id not in [
            13, 19, 63, 76, 91, 102, 117, 118, 119, 130, 143, 144, 165, 166, 214, 264, 267, 274,
            289, 291, 307, 308, 338, 340, 382, 383, 408, 416, 439, 459, 467, 507, 553, 554, 566,
            588, 601, 669, 689, 690, 704, 711, 761, 762, 896
        ]
    
    def selectable_by_snatch(self):
        """Whether or not this move can be selected by snatch."""
        return self.id in [
            14, 54, 74, 96, 97, 104, 105, 106, 107, 110, 111, 112, 113, 115, 116, 133, 135, 151,
            156, 159, 160, 164, 187, 208, 215, 219, 234, 235, 236, 254, 256, 268, 273, 275, 278,
            286, 287, 293, 294, 303, 312, 322, 334, 336, 339, 347, 349, 355, 361, 366, 379, 381,
            392, 393, 397, 417, 455, 456, 461, 468, 469, 475, 483, 489, 501, 504, 508, 526, 538,
            561, 602, 659, 673, 674, 694, 0xCFCF
        ]
    
    @staticmethod
    def get_conversion_2(attacker, defender, battle):
        """
        Gets a random new type for attacker that is resistant to defender's last move type.
        
        Returns a random possible type id, or None if there is no valid type.
        """
        if defender.last_move is None:
            return None
        movetype = defender.last_move.get_type(attacker, defender, battle)
        newtypes = set()
        for e in ElementType:
            if e == ElementType.TYPELESS:
                continue
            if battle.inverse_battle:
                if battle.type_effectiveness[(movetype, e)] > 100:
                    newtypes.add(e)
            else:
                if battle.type_effectiveness[(movetype, e)] < 100:
                    newtypes.add(e)
        newtypes -= set(attacker.type_ids)
        newtypes = list(newtypes)
        if not newtypes:
            return None
        return random.choice(newtypes)
    
    def copy(self):
        """Generate a copy of this move."""
        return Move(
            id=self.id,
            identifier=self.name,
            power=self.power,
            pp=self.pp,
            accuracy=self.accuracy,
            priority=self.priority,
            type_id=self.type,
            damage_class_id=self.damage_class,
            effect_id=self.effect,
            effect_chance=self.effect_chance,
            target_id=self.target,
            crit_rate=self.crit_rate,
            min_hits=self.min_hits,
            max_hits=self.max_hits,
        )
    
    @classmethod
    def struggle(cls):
        """Generate an instance of the move struggle."""
        return cls(
            id=165,
            identifier="struggle",
            power=50,
            pp=999999999999,
            accuracy=None,
            priority=0,
            type_id=ElementType.TYPELESS,
            damage_class_id=2,
            effect_id=255,
            effect_chance=None,
            target_id=10,
            crit_rate=0,
            min_hits=None,
            max_hits=None,
        )
    
    @classmethod
    def confusion(cls):
        """Generate an instance of the move confusion."""
        return cls(
            id=0xCFCF,
            identifier="confusion",
            power=40,
            pp=999999999999,
            accuracy=None,
            priority=0,
            type_id=ElementType.TYPELESS,
            damage_class_id=DamageClass.PHYSICAL,
            effect_id=1,
            effect_chance=None,
            target_id=7,
            crit_rate=0,
            min_hits=None,
            max_hits=None,
        )
    
    @classmethod
    def present(cls, power):
        """Generate an instance of the move present."""
        return cls(
            id=217,
            identifier="present",
            power=power,
            pp=999999999999,
            accuracy=90,
            priority=0,
            type_id=ElementType.NORMAL,
            damage_class_id=DamageClass.PHYSICAL,
            effect_id=123,
            effect_chance=None,
            target_id=10,
            crit_rate=0,
            min_hits=None,
            max_hits=None,
        )
    
    def __repr__(self):
        return f"Move(name={self.name!r}, power={self.power!r}, effect_id={self.effect!r})"
