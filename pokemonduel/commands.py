import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import aiohttp
import logging
from .battle import Battle
from .buttons import DuelAcceptView
from .pokemon import DuelPokemon
from .data import generate_team_preview, find, find_one
from .trainer import MemberTrainer, NPCTrainer


class TeambuilderReadException(Exception):
    """Generic exception raised when failing to parse a teambuilder export string."""
    pass


class PokemonDuel(commands.Cog):
    """Battle in a Pokemon Duel with another member of your server."""
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger('red.flamecogs.pokemonduel')
        self.games = {}
        self.config = Config.get_conf(self, identifier=145519400223506432)
        self.config.register_member(
			party = [],
		)
        self.config.register_guild(
            useThreads = False,
        )

    @staticmethod
    async def party_from_teambuilder(ctx, teambuilder):
        """
        Builds a party from an exported pokemon showdown teambuilder team.
        https://play.pokemonshowdown.com/teambuilder
        """
        teambuilder = teambuilder.strip()
        party = []
        for raw in teambuilder.split("\n\n"):
            raw = raw.strip()
            lines = raw.split("\n")
            
            # FIRST LINE
            nameraw = lines.pop(0)
            item = "None"
            if "@" in nameraw:
                nameraw, item = nameraw.split("@")
                item = item.strip().replace(" ", "-").lower()
            gender = "-m"
            if "(M)" in nameraw:
                nameraw = nameraw.replace("(M)", "")
                gender = "-m"
            elif "(F)" in nameraw:
                nameraw = nameraw.replace("(F)", "")
                gender = "-f"
            nick = "None"
            if "(" in nameraw:
                nick, nameraw = nameraw.split("(")
                nameraw = nameraw.strip()[:-1]
                nick = nick.strip()
            
            pokname = nameraw.strip().replace(" ", "-").capitalize()
            if pokname == "nidoran":
                name += gender
            
            forms = await find_one(ctx, "forms", {"identifier": pokname.lower()})
            if forms is None:
                raise TeambuilderReadException(f"`{pokname}` is not a valid pokemon.")
            pfile = await find_one(ctx, "pfile", {"id": forms["base_id"]})
            if pfile is None:
                raise TeambuilderReadException(f"Could not find a `pfile` entry for `{pokname}`. Please report this bug.")
            gender_rate = pfile["gender_rate"]
            if gender_rate == 0:
                gender = "-m"
            elif gender_rate == 8:
                gender = "-f"
            elif gender_rate == -1:
                gender = "-x"
            
            # REST OF THE LINES
            hpiv = 31
            atkiv = 31
            defiv = 31
            spatkiv = 31
            spdefiv = 31
            speediv = 31
            hpev = 0
            atkev = 0
            defev = 0
            spatkev = 0
            spdefev = 0
            speedev = 0
            level = 100
            happiness = 255
            ability_index = 0
            shiny = False
            nature = "Hardy"
            moves = []
            for line in lines:
                line = line.strip()
                if line.startswith("IVs:"):
                    line = line[4:].strip()
                    ivs = line.split("/")
                    for iv in ivs:
                        amount, iv = iv.strip().split(" ")
                        amount = int(amount)
                        iv = iv.lower()
                        if iv == "hp":
                            hpiv = amount
                        elif iv == "atk":
                            atkiv = amount
                        elif iv == "def":
                            defiv = amount
                        elif iv == "spa":
                            spatkiv = amount
                        elif iv == "spd":
                            spdefiv = amount
                        elif iv == "spe":
                            speediv = amount
                elif line.startswith("EVs:"):
                    line = line[4:].strip()
                    evs = line.split("/")
                    for ev in evs:
                        amount, ev = ev.strip().split(" ")
                        amount = int(amount)
                        ev = ev.lower()
                        if ev == "hp":
                            hpev = amount
                        elif ev == "atk":
                            atkev = amount
                        elif ev == "def":
                            defev = amount
                        elif ev == "spa":
                            spatkev = amount
                        elif ev == "spd":
                            spdefev = amount
                        elif ev == "spe":
                            speedev = amount
                elif line.startswith("Shiny:"):
                    if "Yes" in line:
                        shiny = True
                elif line.startswith("Level:"):
                    line = line[6:].strip()
                    level = int(line)
                elif line.startswith("Happiness:"):
                    line = line[10:].strip()
                    happiness = int(line)
                elif line.endswith("Nature"):
                    line = line[:-6].strip()
                    nature = line.capitalize()
                elif line.startswith("Ability:"):
                    ability = line[8:].strip().lower().replace(" ", "-")
                    ability_raw = await find_one(ctx, "abilities", {"identifier": ability})
                    if ability_raw is None:
                        raise TeambuilderReadException(f"`{pokname}` was given an ability `{ability}` which does not exist.")
                    ability_id = ability_raw["id"]
                    abilities = await find(ctx, "poke_abilities", {"pokemon_id": forms["pokemon_id"]})
                    abilities = [a["ability_id"] for a in abilities]
                    if ability_id not in abilities:
                        raise TeambuilderReadException(f"`{pokname}` can not have the ability `{ability}`.")
                    ability_index = abilities.index(ability_id)
                elif line.startswith("-"):
                    line = line[1:].split("/")[0].strip()
                    move = line.lower().replace(" ", "-")
                    if move.startswith("hidden-power"):
                        move = "hidden-power"
                    if await find_one(ctx, "moves", {"identifier": move}) is None:
                        raise TeambuilderReadException(f"`{pokname}` was given a move `{move}` which does not exist.")
                    moves.append(move)
                elif line.startswith("Hidden Power:"):
                    pass
                elif line.startswith("Tera Type:"):
                    pass # TODO: figure out how to handle teras
                else:
                    raise TeambuilderReadException(f"Data line `{line[:200]}` is not properly formatted.")
            if len(moves) != 4:
                raise TeambuilderReadException(f"`{pokname}` was given {len(moves)} moves. It must have exactly 4 moves.")
            evsum = sum([hpev, atkev, defev, spatkev, spdefev, speedev])
            if evsum > 510:
                raise TeambuilderReadException(f"`{pokname}` was given {evsum} EV points. It must have no more than 510 EV points.")
            for s in [hpiv, atkiv, defiv, spatkiv, spdefiv, speediv]:
                if s > 31 or s < 0:
                    raise TeambuilderReadException(f"`{pokname}` was given an IV stat of {s}. IVs must be between 0 and 31.")
            for s in [hpev, atkev, defev, spatkev, spdefev, speedev]:
                if s > 252 or s < 0:
                    raise TeambuilderReadException(f"`{pokname}` was given an EV stat of {s}. EVs must be between 0 and 252.")
            if item != "None":
                item_raw = await find_one(ctx, "items", {"identifier": item})
                if item_raw is None:
                    raise TeambuilderReadException(f"`{pokname}` was given an item `{item}` which does not exist.")
                if item in (
                    "venusaurite", "blastoisinite", "alakazite", "gengarite", "kangaskhanite", "pinsirite",
                    "gyaradosite", "aerodactylite", "ampharosite", "scizorite", "heracronite", "houndoominite",
                    "tyranitarite", "blazikenite", "gardevoirite", "mawilite", "aggronite", "medichamite",
                    "manectite", "banettite", "absolite", "latiasite", "latiosite", "garchompite", "lucarionite",
                    "abomasite", "beedrillite", "pidgeotite", "slowbronite", "steelixite", "sceptilite",
                    "swampertite", "sablenite", "sharpedonite", "cameruptite", "altarianite", "glalitite",
                    "salamencite", "metagrossite", "lopunnite", "galladite", "audinite", "diancite",
                ):
                    item = "mega-stone"
                elif item in ("charizardite-x", "mewtwonite-x"):
                    item = "mega-stone-x"
                elif item in ("charizardite-y", "mewtwonite-y"):
                    item = "mega-stone-y"
            if nature not in (
                "Hardy", "Bold", "Modest", "Calm", "Timid", "Lonely", "Docile", "Mild", "Gentle", "Hasty", "Adamant", "Impish", "Bashful",
                "Careful", "Jolly", "Naughty", "Lax", "Rash", "Quirky", "Naive", "Brave", "Relaxed", "Quiet", "Sassy", "Serious",
            ):
                raise TeambuilderReadException(f"`{pokname}` was given a nature `{nature}` which does not exist.")
            if level > 100 or level < 1:
                raise TeambuilderReadException(f"`{pokname}` was given a level of {level}. Its level must be between 1 and 100.")
            if happiness < 0:
                raise TeambuilderReadException(f"`{pokname}` was given a happiness of {happiness}. Its happiness must be at least 0.")
            pokemon = {
                'id': 0,
                'pokname': pokname,
                'hpiv': hpiv,
                'atkiv': atkiv,
                'defiv': defiv,
                'spatkiv': spatkiv,
                'spdefiv': spdefiv,
                'speediv': speediv,
                'hpev': hpev,
                'atkev': atkev,
                'defev': defev,
                'spatkev': spatkev,
                'spdefev': spdefev,
                'speedev': speedev,
                'moves': moves,
                'hitem': item,
                'nature': nature,
                'poknick': nick,
                'pokelevel': level,
                'happiness': happiness,
                'ability_index': ability_index,
                'gender': gender,
                'shiny': shiny,
                'radiant': False,
                'skin': None,
            }
            party.append(pokemon)
        if len(party) < 1 or len(party) > 6:
            raise TeambuilderReadException(f"Your party has {len(party)} pokemon. It must have 1 to 6 pokemon.")
        return party
    
    async def wrapped_run(self, battle):
        """
        Runs the provided battle, handling any errors that are raised.
        
        Returns the output of the battle, or None if the battle errored.
        """
        self.games[int(battle.ctx.message.id)] = battle
        try:
            winner = await battle.run()
        except (aiohttp.client_exceptions.ClientOSError, asyncio.TimeoutError):
            await battle.channel.send(
                "The bot encountered an unexpected network issue, "
                "and the duel could not continue. "
                "Please try again in a few moments.\n"
                "Note: Do not report this as a bug."
            )
            return None
        except Exception as exc:
            msg = 'Error in PokemonDuel.\n'
            self.log.exception(msg)
            self.bot.dispatch('flamecogs_game_error', battle, exc)
            await battle.channel.send(
                'A fatal error has occurred, shutting down.\n'
                'Please have the bot owner copy the error from console '
                'and post it in the support channel of <https://discord.gg/bYqCjvu>.'
            )
            return None
        else:
            if int(battle.ctx.message.id) in self.games:
                del self.games[int(battle.ctx.message.id)]
            return winner

    @commands.group(aliases=["pokeduel"], invoke_without_command=True)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def pokemonduel(self, ctx, opponent: discord.Member):
        """Battle in a Pokemon Duel with another member of your server."""
        await self._start_duel(ctx, opponent)
    
    @pokemonduel.command()
    async def inverse(self, ctx, opponent: discord.Member):
        """Battle in an Inverse Duel with another member of your server."""
        await self._start_duel(ctx, opponent, inverse_battle=True)
    
    async def _start_duel(self, ctx, opponent: discord.Member, *, inverse_battle=False):
        """Runs a duel."""
        if opponent.id == ctx.author.id:
            await ctx.send("You cannot duel yourself!")
            return
        if opponent.bot:
            await ctx.send("You cannot duel a bot!")
            return
        
        view = DuelAcceptView(ctx, opponent)
        battle_type = "an inverse battle" if inverse_battle else "a duel"
        initial_message = await ctx.send(
            f"{opponent.mention} You have been challenged to {battle_type} by {ctx.author.name}!\n",
            view=view
        )
        view.message = initial_message
        channel = ctx.channel
        if (
            await self.config.guild(ctx.guild).useThreads()
            and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
            and ctx.channel.type is discord.ChannelType.text
        ):
            try:
                channel = await initial_message.create_thread(
                    name='PokemonDuel',
                    reason='Automated thread for PokemonDuel.',
                )
            except discord.HTTPException:
                pass
        await view.wait()
        if not view.confirm:
            return
        trainers = []
        for player in (ctx.author, opponent):
            party = await self.config.member(player).party()
            if not party:
                await channel.send(f"{player} has not setup their party yet!\nSet one with `{ctx.prefix}pokemonduel party set`.")
                return
            party = [await DuelPokemon.create(ctx, p) for p in party]
            trainers.append(MemberTrainer(player, party))
        battle = Battle(ctx, channel, *trainers, inverse_battle=inverse_battle) # pylint: disable=E1120
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()
        winner = await self.wrapped_run(battle)
    
    @pokemonduel.group()
    async def party(self, ctx):
        """Manage your party of pokemon."""
        pass
    
    @party.command(name="set")
    async def party_set(self, ctx, *, pokemon_data):
        """
        Set your party of pokemon.
        
        In order to set your party, you will need to create a team on Pokemon Showdown Team Builder.
        1. Go to the [Team Builder site](https://play.pokemonshowdown.com/teambuilder).
        2. Click the "New Team" button.
        3. Select the format "Anything Goes".
        4. Use the "Add Pokemon" button to create a new pokemon.
        5. Pick its moves, ability, gender, level, etc.
        6. Repeat steps 4 and 5 for up to 6 total pokemon
        7. On the team view, select the "Import/Export" button at the TOP.
        8. Copy the text provided, and pass that to this command.
        """
        try:
            party = await self.party_from_teambuilder(ctx, pokemon_data)
        except TeambuilderReadException as e:
            await ctx.send(f"Couldn't validate your team.\n{e}")
            return
        except Exception:
            await ctx.send("Couldn't properly parse your team. Make sure you follow the format provided by Showdown's Team Builder. An error has been logged to console to debug this issue.")
            self.log.exception("Failed to read a teambuilder team string.")
            return
        await self.config.member(ctx.author).party.set(party)
        embed = discord.Embed(
            title="Your new party",
            color=await ctx.embed_color(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await self.gen_party_embed(ctx, party, embed)
        await ctx.send(embed=embed)
    
    @party.command(name="pokecord", hidden=True)
    async def party_pokecord(self, ctx, *ids: int):
        """Create a party of pokemon imported from Pokecord."""
        pass
    
    @party.command(name="list", aliases=["view"])
    async def party_list(self, ctx):
        """View the pokemon currently in your party."""
        party = await self.config.member(ctx.author).party()
        if len(party) == 0:
            await ctx.send(f"You haven't setup your party yet!\nSet one with `{ctx.prefix}pokemonduel party set`.")
            return
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Party",
            color=await ctx.embed_color(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await self.gen_party_embed(ctx, party, embed)
        await ctx.send(embed=embed)
 
    @staticmethod
    async def gen_party_embed(ctx, party, embed):
        """Adds fields to the provided `embed` that are rendered descriptors of the pokemon in the provided `party`."""
        for idx, pokemon in enumerate(party):
            pokname = pokemon["pokname"]
            poknick = pokemon["poknick"]
            gender = pokemon["gender"]
            if gender == "-m":
                gender = "Male"
            elif gender == "-f":
                gender = "Female"
            elif gender == "-x":
                gender = "Genderless"
            moves = pokemon["moves"]
            moves = "|".join([f"`{x}`" for x in moves])
            ability_index = pokemon["ability_index"]
            form_info = await find_one(ctx, "forms", {"identifier": pokname.lower()})
            ab_ids = []
            for record in await find(ctx, "poke_abilities", {"pokemon_id": form_info["pokemon_id"]}):
                ab_ids.append(record["ability_id"])
            try:
                ab_id = ab_ids[ability_index]
            except IndexError:
                ab_id = ab_ids[0]
            ability = await find_one(ctx, "abilities", {"id": ab_id})
            ability = ability["identifier"]
            hitem = pokemon["hitem"]
            nature = pokemon["nature"].lower()
            happiness = pokemon["happiness"]
            hpiv = pokemon["hpiv"]
            atkiv = pokemon["atkiv"]
            defiv = pokemon["defiv"]
            spatkiv = pokemon["spatkiv"]
            spdefiv = pokemon["spdefiv"]
            speediv = pokemon["speediv"]
            hpev = pokemon["hpev"]
            atkev = pokemon["atkev"]
            defev = pokemon["defev"]
            spatkev = pokemon["spatkev"]
            spdefev = pokemon["spdefev"]
            speedev = pokemon["speedev"]
            
            title = f"{gender} {pokname} "
            if poknick != "None":
                title += f"({poknick}) "
            
            desc = f"{moves}\nAbility `{ability}`"
            if hitem != "None":
                desc += f" | Holding `{hitem}`"
            desc += f"\nNature `{nature}` | Happiness `{happiness}`\n"
            desc += "`    `|` hp`|`atk`|`def`|`spa`|`spd`|`spe`\n"
            desc += f"`IVs:`|`{hpiv:3d}`|`{atkiv:3d}`|`{defiv:3d}`|`{spatkiv:3d}`|`{spdefiv:3d}`|`{speediv:3d}`\n"
            desc += f"`EVs:`|`{hpev:3d}`|`{atkev:3d}`|`{defev:3d}`|`{spatkev:3d}`|`{spdefev:3d}`|`{speedev:3d}`\n"
            
            embed.add_field(name=title, value=desc, inline=bool(idx % 2))

    @commands.guild_only()
    @commands.guildowner()
    @commands.group(invoke_without_command=True)
    async def pokemonduelset(self, ctx):
        """Config options for pokemon duels."""
        await ctx.send_help()
        cfg = await self.config.guild(ctx.guild).all()
        msg = (
            "Game contained to a thread: {useThreads}\n"
        ).format_map(cfg)
        await ctx.send(f"```py\n{msg}```")

    @pokemonduelset.command()
    async def thread(self, ctx, value: bool=None):
        """
        Set if a thread should be created per-game to contain game messages.
        
        Defaults to False.
        This value is server specific.
        """
        if value is None:
            v = await self.config.guild(ctx.guild).useThreads()
            if v:
                await ctx.send("The game is currently run in a per-game thread.")
            else:
                await ctx.send("The game is not currently run in a thread.")
        else:
            await self.config.guild(ctx.guild).useThreads.set(value)
            if value:
                await ctx.send("The game will now be run in a per-game thread.")
            else:
                await ctx.send("The game will not be run in a thread.")
