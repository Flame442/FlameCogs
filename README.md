# FlameCogs

[![Discord server](https://discordapp.com/api/guilds/535921134152187919/embed.png)](https://discord.gg/bYqCjvu)
[![Red cogs](https://img.shields.io/badge/Red--DiscordBot-cogs-red.svg)](https://github.com/Cog-Creators/Red-DiscordBot/tree/V3/develop)
[![discord.py](https://img.shields.io/badge/discord-py-blue.svg)](https://github.com/Rapptz/discord.py)

Cogs for a [Red Discord Bot](https://github.com/Cog-Creators/Red-DiscordBot)  

# Installation

>These are cogs for the [Red-DiscordBot V3](https://github.com/Cog-Creators/Red-DiscordBot/tree/V3/develop). You need to have a working V3 Redbot in order to install these cogs.

*[p] is your prefix.*

Make sure downloader is loaded:  
`[p]load downloader`

Add the repo to your bot:  
`[p]repo add flamecogs https://github.com/Flame442/FlameCogs`

Install the cogs you want:  
`[p]cog install flamecogs <cog name>`

Load installed cogs:  
`[p]load <cog name>`

# Cogs

Name | Description
--- | ---
[Battleship](../master/README.md#battleship) | Play battleship against another member of your server.
[Deepfry](../master/README.md#deepfry) | Deepfry and nuke images.
[Gameroles](../master/README.md#gameroles) | Grant roles when a user is playing a specific game.
[Giftaway](../master/README.md#giftaway) | Create grabbable key giveaways.
[Hangman](../master/README.md#hangman) | Play hangman with the bot.
[Hider](../master/README.md#hider) | Hide commands from users in help.
[Monopoly](../master/README.md#monopoly) | Play monopoly with up to 7 other people in your server.
[Onlinestats](../master/README.md#onlinestats) | Information about what devices people are using to run discord.
[Partygames](../master/README.md#partygames) | Chat games focused on coming up with words from 3 letters.
[PokemonDuel](../master/README.md#pokemonduel) | Play a pokemon battle against another member of your server.
[SimpleEmbed](../master/README.md#simpleembed) | Simply create embeds.
[Stocks](../master/README.md#stocks) | Buy and sell stocks with bot currency.
[UTTT](../master/README.md#uttt) | Play ultimate tic tac toe against another member of your server.
[Wordstats](../master/README.md#wordstats) | Track commonly used words by server and member.

## Battleship

This cog will let you play battleship against another member of your server.

### Usage

**`[p]battleship`**  
Begin a game of battleship.

**`[p]battleshipboard <channel>`**  
View your current board from an ongoing game in your DMs.  
Use `channel` to specify the channel ID of the channel the game is in.

**`[p]battleshipset <argument>`**  
Config options for battleship.  
This command is only usable by the server owner and bot owner.

**`[p]battleshipset extra [value]`**  
Set if an extra shot should be given after a hit.  
Defaults to `True`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]battleshipset mention [value]`**  
Set if players should be mentioned when their turn begins.  
Defaults to `True`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]battleshipset imgboard [value]`**  
Set if the board should be displayed using an image.  
Defaults to `True`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]battleshipset thread [value]`**  
Set if a thread should be created per-game to contain game messages.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

## Deepfry

This cog lets you deepfry and nuke images. It has a configurable chance to deepfry any image posted automatically and users can choose to deepfry or nuke images.  

### Usage

**`[p]deepfry [link]`**  
Deepfries the attached image.  
The optional parameter `link` can be either a member or a **direct link** to an image.  
Alias: `[p]df`

**`[p]nuke [link]`**  
Nukes the attached image.  
The optional parameter `link` can be either a member or a **direct link** to an image.

**`[p]deepfryset <argument>`**  
Config options for deepfry.  
This command is only usable by the server owner and bot owner.

**`[p]deepfryset frychance [value]`**  
Change the rate images are automatically deepfried.  
Images will have a 1/`[value]` chance to be deepfried.  
Higher values cause less often fries.  
Set to `0` to disable.  
Defaults to `0` (off)  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]deepfryset nukechance [value]`**  
Change the rate images are automatically nuked.  
Images will have a 1/`[value]` chance to be nuked.  
Higher values cause less often nukes.  
Set to `0` to disable.  
Defaults to `0` (off)  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]deepfryset allowalltypes [value]`**  
Allow filetypes that have not been verified to be valid.  
Can cause errors if enabled, **use at your own risk**.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

## Gameroles

This cog will grant roles when a user is playing a specific game.

### Usage

**`[p]gameroles <argument>`**  
Alias `[p]gr <argument>`

**`[p]gameroles addrole <role>`**  
Sets a role to be managed by gameroles.  
Roles with multiple word names need to be surrounded in quotes.
The bot's highest role needs to be above the role that you are adding and the bot needs permission to manage roles.  
This command is only usable by the server owner and bot owner.

**`[p]gameroles delrole <role>`**  
Stop a role from being managed by gameroles.  
Roles with multiple word names need to be surrounded in quotes.  
Accepts the ID of the role in case it was deleted.  
This command is only usable by the server owner and bot owner.

**`[p]gameroles addactivity <role> <activity>`**  
Add an activity to trigger a role.  
Roles and activities with multiple word names need to be surrounded in quotes.  
You can get the name of your current activity with `[p]gameroles currentactivity`.  
This command is only usable by the server owner and bot owner.

**`[p]gameroles delactivity <role> <activity>`**  
Remove an activity from triggering a role.  
Roles and activities with multiple word names need to be surrounded in quotes.  
You can get the name of your current activity with `[p]gameroles currentactivity`.   
This command is only usable by the server owner and bot owner.

**`[p]gameroles listroles`**  
List the roles currently managed by gameroles.  
This command is only usable by the server owner and bot owner.

**`[p]gameroles listactivities <role>`**  
List the activities that trigger a role.  
Roles with multiple word names need to be surrounded in quotes.  
This command is only usable by the server owner and bot owner.

**`[p]gameroles currentactivity`**  
Get your current activity.  
This command is only usable by the server owner and bot owner.

**`[p]gameroles recheck`**  
Force a recheck of your current activities.  

**`[p]gameroleset <argument>`**  
Config options for gameroles.  
This command is only usable by the server owner and bot owner.  
Alias: `[p]grset`

**`[p]gameroleset add [value]`**  
Set if roles should be added when someone starts playing a game.  
Defaults to `True`.  
This value is server specific.

**`[p]gameroleset remove [value]`**  
Set if roles should be removed when someone stops playing a game.  
Defaults to `True`.  
This value is server specific.

## GiftAway

This cog allows you to create giveaways for game keys. Users can claim a key by reacting to a message describing the key. It was originally requested by Mistery#3287  
This cog features optional integration with the IGDB API to display a description of the game being given away. Setup instructions can be found [here!](../master/giftaway/setup.md)

### Usage

**`[p]giftaway <guild> <game_name> <key1> [key2]...`**  
Giftaway a key to a specific server.  
Wrap any parameters that require spaces in quotes.  
This command is only usable in DMs.  
Alias: `[p]ga`

**`[p]globalgift <game_name> <key1> [key2]...`**  
Giftaway a key to all servers.  
Wrap any parameters that require spaces in quotes.  
This command is only usable in DMs.  
Alias: `[p]gg`

**`[p]giftat <channel> <game_name> <key1> [key2]...`**  
Giftaway a key to a specific channel.  
You probably should run this command from a location people can't see to protect the keys.  
Wrap any parameters that require spaces in quotes.  
This command is only usable in a server.

**`[p]giftawayset <argument>`**  
Config options for giftaway.  
This command is only usable by the server owner and bot owner.

**`[p]giftawayset channel <channel>`**  
Set the channel that giftaway messages will be sent to in the current server.  
This value is server specific.

**`[p]giftawayset channel remove`**  
Remove the giftaway channel from the current server and stop receiving giftaway messages.  
This value is server specific.

## Hangman

This cog will play hangman with you.

### Usage

**`[p]hangman`**  
Begin a game of hangman.

**`[p]hangmanset <argument>`**  
Config options for hangman.  
This command is only usable by the server owner and bot owner.

**`[p]hangmanset wordlist [value]`**  
Change the wordlist used.  
Extra wordlists can be put in the data folder of this cog.  
Wordlists are a text file with every new line being a new word.  
Use `default` to restore the default wordlist.  
Use `list` to list available wordlists.  
This value is server specific.

**`[p]hangmanset edit [value]`**  
Set if hangman messages should be one edited message or many individual messages.  
Defaults to `True`.  
This value is server specific.

## Hider

This cog will let you hide commands from showing up in help.

### Usage

**`[p]hider <argument>`**  
Hide commands from users in help.  
This command is only usable by the bot owner.

**`[p]hider hide <command>`**  
Hide a command from being displayed in help.  
This will not work if `[p]helpset showhidden` is enabled.  
This command is only usable by the bot owner.

**`[p]hider show <command>`**  
Show a command that was previously hidden by Hider.  
This command is only usable by the bot owner.

**`[p]hider list`**  
List the commands that Hider is hiding.  
This command is only usable by the bot owner.

## Monopoly

This cog will let you play monopoly with up to 7 other people in your server.

### Usage

**`[p]monopoly [savename]`**  
Begin a game of monopoly.   
Use the optional parameter `savename` to load a saved game.

**`[p]monopoly delete <savefiles>`**  
Delete one or more save files.  
This cannot be undone.  
This command is only usable by the server owner and bot owner.

**`[p]monopoly list`**  
List available save files.   

**`[p]monopolyconvert <savefile>`**  
Convert a savefile to work with the latest version of this cog.

**`[p]monopolyconvert list`**  
List save files that can be converted.

**`[p]monopolystop`**  
Stop the game of monopoly in the current channel.  
This command is only usable by the server owner and bot owner.

**`[p]monopolyset <argument>`**  
Config options for monopoly.  
This command is only usable by the server owner and bot owner.

**`[p]monopolyset auction [value]`**  
Set if properties should be auctioned when passed on.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset bail [value]`**  
Set how much bail should cost.  
Defaults to `50`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset darkmode [value]`**  
Set if the board should be a darker variant.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset doublego [value]`**  
Set if landing on go should double the amount of money given.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset freeparking [value]`**  
Set the reward for landing on free parking.  
Use an integer to set a static reward.  
Use "none" for no reward.  
Use "tax" to use the sum of taxes and fees as the reward.  
Defaults to `None`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset go [value]`**  
Set the base value of passing go.  
Defaults to `200`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset hotellimit [value]`**  
Set a limit on the number of hotels that can be bought.  
Use -1 to disable the limit.  
Defaults to `12`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset houselimit [value]`**  
Set a limit on the number of houses that can be bought.  
Use -1 to disable the limit.  
Defaults to `32`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset income [value]`**  
Set how much Income Tax should cost.  
Defaults to `200`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset luxury [value]`**  
Set how much Luxury Tax should cost.  
Defaults to `100`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset maxjailrolls [value]`**  
Set the maximum number of rolls in jail before bail has to be paid.  
Defaults to `3`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset mention [value]`**  
Set if players should be mentioned when their turn begins.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.
This value is server specific.  

**`[p]monopolyset minraise [value]`**  
Set the minimum raise in auctions.  
Defaults to `1`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset startingcash [value]`**  
Set how much money players should start the game with.  
Defaults to `1500`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset thread [value]`**  
Set if a thread should be created per-game to contain game messages.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset timeout [value]`**  
Set the amount of time before the game times out.  
Value is in seconds.  
Use -1 to disable the timeout.  
Defaults to `60`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

## Onlinestats

This cog gives information about what devices people are using to run discord.

### Usage

**`[p]onlinestatus`**  
Prints how many people are using each type of device.  
Alias: `[p]onlinestats`

**`[p]onlineinfo [member]`**  
Shows what devices a member is using.  
Defaults to the author.

## Partygames

This cog has chat games focused on coming up with words from 3 letters.

### Usage

**`[p]partygames <argument>`**  
Alias `[p]pg <argument>`

**`[p]partygames bombparty [hp]`**  
Start a game of bombparty.  
Each player will be asked to come up with a word that contains the given characters.  
If they are unable to do so, they will lose a life.  
Words cannot be reused.  
The last person to have lives left wins.  
Use the optional parameter `hp` to set the number of lives each person starts with.

**`[p]partygames fast [maxpoints]`**  
Race to type a word the fastest.  
The first person to type a word that contains the given characters gets a point.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional parameter `maxpoints` to set the number of points required to win.

**`[p]partygames long [maxpoints]`**  
Type the longest word.  
The person to type the longest word that contains the given characters gets a point.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional parameter `maxpoints` to set the number of points required to win.

**`[p]partygames most [maxpoints]`**  
Type the most words.  
The person to type the most words that contain the given characters gets a point.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional parameter `maxpoints` to set the number of points required to win.

**`[p]partygames mix [maxpoints]`**  
Play a mixture of all 4 games.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional parameter `maxpoints` to set the number of points required to win.

**`[p]partygames locale <locale>`**  
Override the bot's locale for partygames.  
Use `reset` to remove the override.  
This command is only usable by the bot owner.  
This value is global.

## PokemonDuel

This cog will let you play a Pokemon battle against another member of your server, similar to Pokemon Showdown. All pokemon, moves, and abilities are coded, but only some items are. It is based off of generation 8, or the last generation a pokemon, move, ability, or item was included.

### Usage

**`[p]pokemonduel <opponent>`**  
Battle in a Pokemon Duel with another member of your server.  
Alias `[p]pokeduel <opponent>`

**`[p]pokemonduel inverse <opponent>`**  
Battle in an Inverse Duel with another member of your server.

**`[p]pokemonduel party set <pokemon_data>`**  
Set your party of pokemon.  
In order to set your party, you will need to create a team on Pokemon Showdown Team Builder.  
1. Go to the [Team Builder site](https://play.pokemonshowdown.com/teambuilder).  
2. Click the "New Team" button.  
3. Use the "Add Pokemon" button to create a new pokemon.  
4. Pick its moves, ability, gender, level, etc.  
5. Repeat steps 3 and 4 for up to 6 total pokemon  
6. On the team view, select the "Import/Export" button at the TOP.  
7. Copy the text provided, and pass that to this command.

**`[p]pokemonduel party list`**  
View the pokemon currently in your party.

**`[p]pokemonduelset <argument>`**  
Config options for pokemon duel.  
This command is only usable by the server owner and bot owner.

**`[p]pokemonduelset thread [value]`**  
Set if a thread should be created per-game to contain game messages.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

## SimpleEmbed

This cog will let you send embedded messages quickly and easily.

### Usage

**`[p]sendembed [color] <text>`**  
Send an embed.  
Use the optional parameter `color` to change the color of the embed.  
The embed will contain the text `text`.  
All normal discord formatting will work inside the embed.

## Stocks

This cog allows you to purchase stocks using the economy credits built in to the bot.  
This cog assumes the bank is set to be a global bank, if your bank is guild-specific, users will be able to transfer credits between guilds using this cog.

### Usage

**`[p]stocks <argument>`**  
Alias `[p]stock <argument>`  
Alias `[p]stonks <argument>`  
Alias `[p]stonk <argument>`

**`[p]stocks buy <name> <shares>`**  
Buy stocks.  
Enter the ticker symbol for the stock.  
Conversion rate: $1 = 100 credits.

**`[p]stocks sell <name> <shares>`**  
Sell stocks.  
Enter the ticker symbol for the stock.  
Conversion rate: $1 = 100 credits.

**`[p]stocks price <name>`**  
View the price of a stock.  
Enter the ticker symbol for the stock.  
Conversion rate: $1 = 100 credits.

**`[p]stocks list`**  
List your stocks.

**`[p]stocks leaderboard`**  
Show a leaderboard of total stock value by user.

## UTTT

Play ultimate tic tac toe against another member of your server.

### Usage

**`[p]uttt`**  
Play a game of ultimate tic tac toe.  
You may only play in the sub board that corresponds to the last spot your opponent played.  
If you are sent to a sub board that has been finished, you can choose any sub board.  
First to win three sub boards in a row wins.

**`[p]utttstop`**  
Stop the game of ultimate tic tac toe in the current channel.  
This command is only usable by the server owner and bot owner.

## Wordstats

This cog will track commonly used words by server and member.

### Usage

**`[p]wordstats [member_or_guild] [amount_or_word]`**  
Prints the most commonly used words.  
Use the optional parameter `member_or_guild` to see the stats of a member or guild.  
Use the optional parameter `amount_or_word` to change the number of words that are displayed, or to check the stats of a specific word (default `30`).

**`[p]wordstats global [amount_or_word]`**  
Prints the most commonly used words across all guilds.  
Use the optional parameter `amount_or_word` to change the number of words that are displayed, or to check the stats of a specific word (default `30`).

**`[p]topchatters [guild] [word] [amount]`**  
Prints the members who have said the most words.  
Use the optional parameter `guild` to see the topchatters in a specific guild.
Use the optional parameter `word` to see the topchatters of a specific word.  
Use the optional parameter `amount` to change the number of members that are displayed (default `10`).

**`[p]topchatters global [word] [amount]`**  
Prints the members who have said the most words across all guilds.  
Use the optional parameter `word` to see the topchatters of a specific word.  
Use the optional parameter `amount` to change the number of members that are displayed (default `10`).

**`[p]topratio <word> [guild] [amount] [min_total]`**  
Prints the members with the highest "word to all words" ratio.  
Use the parameter `word` to set the word to compare.  
Use the optional parameter `guild` to see the ratio in a specific guild.  
Use the optional parameter `amount` to change the number of members that are displayed (default `10`).  
Use the optional parameter `min_total` to change the minimum number of words a user needs to have said to be shown.

**`[p]topratio global <word> [amount] [min_total]`**  
Prints the members with the highest "word to all words" ratio in all guilds.  
Use the parameter `word` to set the word to compare.  
Use the optional parameter `amount` to change the number of members that are displayed (default `10`).  
Use the optional parameter `min_total` to change the minimum number of words a user needs to have said to be shown.

**`[p]wordstatsset <argument>`**  
Config options for wordstats.  
This command is only usable by the server owner and bot owner.  

**`[p]wordstatsset server [value]`**  
Set if wordstats should record stats for the channel the command is used in.  
Defaults to `True`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]wordstatsset channel [value]`**  
Set if wordstats should record stats for the server the command is used in.  
Defaults to `True`.  
This command is only usable by the server owner and bot owner.  
This value is channel specific.

**`[p]wordstatsset user [value]`**  
Set if wordstats should record stats for you.  
Defaults to True.  
This value is user specific.

**`[p]wordstatsset stopwords [value]`**  
Set if stopwords should be included in outputs.  
Stopwords are common words such as "a", "it" and "the".  
Stopwords will still be included in numerical counts, they will only be hidden from list displays.  
Defaults to `True`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]wordstatsset minlength [value]`**  
Set the minimum length a word has to be in order to be displayed.  
Shorter words will still be included in numerical counts, they will only be hidden from list displays.  
Set to 0 to disable.  
Defaults to `0`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]wordstatsset convert`**  
Convert data from config to the SQLite database.  
This command is only usable by the bot owner.

**`[p]wordstatsset forgetme`**  
Make wordstats forget all data about you.  
This is equivalent to `[p]mydata forgetme`, but only for wordstats.  
This cannot be undone.

**`[p]wordstatsset deleteall`**  
Delete all wordstats data.  
This removes all existing data, creating a blank state.  
This cannot be undone.  
This command is only usable by the bot owner.

# Contact

Feel free to create an issue on this repository or join [my discord](https://discord.gg/bYqCjvu) if you have any issues.

# Credit

Thanks to:  
The [creators of Redbot](https://github.com/Cog-Creators/Red-DiscordBot/graphs/contributors) for creating the base these cogs run on,  
The helpful support staff at the [Redbot discord](https://discord.gg/red),  
[Aikaterna](https://github.com/aikaterna) for taking the time to QA this repo,  
[Hasbro](https://hasbro.com) for creating the games that Battleship and Monopoly are based off of,  
[TrustyJAID](https://github.com/TrustyJAID) for helping with Deepfry,  
[Desi Quintans](http://www.desiquintans.com/nounlist) for the wordlist used by Hangman,  
[Sparklin Labs](http://bombparty.sparklinlabs.com/) for creating the game that Partygames is based off of,  
[/u/YoungsterGlenn](https://www.reddit.com/r/BombParty/comments/3lehxq/a_nearly_exhaustive_subset_of_the_bombparty/) for the wordlist used by Partygames,  
[Sinbad](https://github.com/mikeshardmind) for helping with Wordstats,  
[Preda](https://github.com/PredaaA) for translating Partygames,  
Red for creating the sprites used in Battleship,  
Mistery#3287 for requesting and translating GiftAway,  
[Tradier](https://tradier.com/) for the API used in Stocks,  
[The Pokémon Company](https://www.pokemon.com/us/) (Nintendo, Game Freak, Creatures) for creating the games that PokemonDuel is based off of,  
And Cruithne, skylarr, ConCon, vKoIIextionz, Bloomlake, Dylee, KYPspikes, De Ultimate Gamer, Snowy Wolfie, RadioactiveRenegade, Falcon, Blotch,
Chichiri12345, ampplaca, xxmoonlotusxx, Silver5mith, and Starregi for helping to keep the data files of PokemonDuel updated and accurate.  
