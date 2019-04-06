# FlameCogs

[![Discord server](https://discordapp.com/api/guilds/535921134152187919/embed.png)](https://discord.gg/bYqCjvu)
[![Red cogs](https://img.shields.io/badge/Red--DiscordBot-cogs-red.svg)](https://github.com/Cog-Creators/Red-DiscordBot/tree/V3/develop)
[![discord.py](https://img.shields.io/badge/discord-py-blue.svg)](https://github.com/Rapptz/discord.py)

Cogs for a [Red Discord Bot](https://github.com/Cog-Creators/Red-DiscordBot)  
These cogs are a collection of random stuff I make.

# Installation

These are cogs for the [Red Bot V3](https://github.com/Cog-Creators/Red-DiscordBot/tree/V3/develop) so ensure you have a working red bot.

Add this repo using

`[p]repo add flamecogs https://github.com/Flame442/FlameCogs`

>[p] is your prefix.

Then, install each cog individually with

`[p]cog install flamecogs <cog name>`

And load each cog with

`[p]load <cog name>`

# Cogs

Name | Description
--- | ---
[Battleship](../master/README.md#battleship) | Play battleship against another member of your server.
[Deepfry](../master/README.md#deepfry) | Deepfry and nuke images.
[Face](../master/README.md#face) | Find and describe the faces in an image.
[Gamevoice](../master/README.md#gamevoice) | Make voice channels require playing a specific game in order to join.
[Hangman](../master/README.md#hangman) | Play hangman with the bot.
[Monopoly](../master/README.md#monopoly) | Play monopoly with up to 7 other people in your server.
[Onlinestats](../master/README.md#onlinestats) | Information about what devices people are using to run discord.
[Partygames](../master/README.md#partygames) | Chat games focused on coming up with words from 3 letters.
[Wordstats](../master/README.md#wordstats) | Track commonly used words by server and member.

## Battleship

This cog will let you play battleship against another member of your server.

### Usage

**`[p]battleship`**  
Begin a game of battleship.

**`[p]battleshipset <argument>`**  
Config options for batteship.  
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

## Deepfry

This cog lets you deepfry and nuke images. It has a configurable chance to deepfry any image posted automatically and users can choose to deepfry or nuke images.  

### Usage

**`[p]deepfry [link]`**  
Deepfries the attatched image.  
Use the optional paramater `link` to use a **direct link** as the target.  
Alias: `[p]df`

**`[p]nuke [link]`**  
Nukes the attatched image.  
Use the optional paramater `link` to use a **direct link** as the target.

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

## Face

This cog will find faces in images and give information about them such as predicted age, hair color, and emotions.  
This cog requires an API key from Microsoft Azure Face API. Setup instructions can be found [here!](../master/face/setup.md)

### Usage

**`[p]face [link]`**  
Finds and describes faces in the attatched image.  
Use the optional paramater `link` to use a **direct link** as the target.

**`[p]faceset <argument>`**  
Config options for face.  
This command is only usable by the server owner and bot owner.

**`[p]faceset key <key>`**  
Set the API key.  
This command is only usable by the bot owner.  
This value is global.

**`[p]faceset url <key>`**  
Set the API URL.  
This command is only usable by the bot owner.  
This value is global.

**`[p]faceset menu [value]`**  
Set if results should be made into a menu.  
If in a menu, one large image with faces marked will be sent instead of cropped images of each face.  
Defaults to `True`.  
This command is only usable by the server owner.  
This value is server specific.

## Gamevoice

This cog lets you make voice channels that require a user to be playing a specific game in order to join.

### Usage

**`[p]gamevoice <argument>`**  
Alias `[p]gv <argument>`

**`[p]gamevoice set`**  
Sets the voice channel you are in to only work with the game you are playing.  
Any activity will count, including Spotify, so make sure discord thinks you are doing the correct activity.  
This command is only usable by the server owner and bot owner.

**`[p]gamevoice reset`**  
Resets the voice channel you are in to defaults.  
Will remove ALL permissions, not just those set by the cog, making it completely open.  
This command is only usable by the server owner and bot owner.

**`[p]gamevoice listroles`**  
Lists all the roles created for games on the server.  
This command is only usable by the server owner and bot owner.

**`[p]gamevoice deleterole <name>`**  
Delete a role from the server.  
Also removes that game's restrictions from all channels.  
Case sensitive.  
Use `[p]gv listroles` to see all roles.  
This command is only usable by the server owner and bot owner.  
Alias `[p]gamevoice delrole <name>`

**`[p]gamevoice recheck`**  
Force a recheck of your current game.  
Use this if you are playing the correct game and it does not let you join.

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
This command is only usable by the server owner and bot owner.  
This value is server specific.

## Monopoly

This cog will let you play monopoly with up to 7 other people in your server.

### Usage

**`[p]monopoly [savename]`**  
Begin a game of monopoly.   
Use the optional paramater `savename` to load a saved game.

**`[p]monopolyset <argument>`**  
Config options for monopoly.  
This command is only usable by the server owner and bot owner.

**`[p]monopolyset mention [value]`**  
Set if players should be mentioned when their turn begins.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.
This value is server specific.  

**`[p]monopolyset startingcash [value]`**  
Set how much money players should start the game with.  
Defaults to `1500`.  
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

**`[p]monopolyset maxjailrolls [value]`**  
Set the maximum number of rolls in jail before bail has to be paid.  
Defaults to `3`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset go [value]`**  
Set the base value of passing go.  
Defaults to `200`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

**`[p]monopolyset doublego [value]`**  
Set if landing on go should double the amount of money given.  
Defaults to `False`.  
This command is only usable by the server owner and bot owner.  
This value is server specific.

## Onlinestats

This cog gives information about what devices people are using to run discord.

### Usage

**`[p]onlinestatus`**  
Prints how many people are using each type of device.  
Alias: `[p]onlinestats`

**`[p]onlineinfo`**  
Shows what devices a user is using.

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
Use the optional paramater `hp` to set the number of lives each person starts with.

**`[p]partygames fast [maxpoints]`**  
Race to type a word the fastest.  
The first person to type a word that contains the given characters gets a point.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional paramater `maxpoints` to set the number of points required to win.

**`[p]partygames long [maxpoints]`**  
Type the longest word.  
The person to type the longest word that contains the given characters gets a point.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional paramater `maxpoints` to set the number of points required to win.

**`[p]partygames most [maxpoints]`**  
Type the most words.  
The person to type the most words that contain the given characters gets a point.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional paramater `maxpoints` to set the number of points required to win.

**`[p]partygames mix [maxpoints]`**  
Play a mixture of all 4 games.  
Words cannot be reused.  
The first person to get `maxpoints` points wins.  
Use the optional paramater `maxpoints` to set the number of points required to win.

## Wordstats

This cog will track commonly used words by server and member.

### Usage

**`[p]wordstats [member] [amount]`**  
Prints the most commonly used words.  
Use the optional paramater `member` to see the stats of a member.  
Use the optional paramater `amount` to change the number of words that are displayed, or to check the stats of a specific word (default `30`).

**`[p]topchatters [amount]`**  
Prints the members who have said the most words.  
Use the optional paramater `amount` to change the number of members that are displayed (default `10`).

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

# Planned changes

**[Monopoly]** Add config for various house rules (~~auctions~~, free parking, ~~landing on go~~, etc)

**[Battleship/Hangman/Monopoly]** Add optional betting to games

# Contact

Feel free to create an issue on this repository or join [my discord](https://discord.gg/bYqCjvu) if you have any issues.

# Credit

Thanks to:  
The [creators of Redbot](https://github.com/Cog-Creators/Red-DiscordBot/graphs/contributors) for creating the base these cogs run on,  
The helpful support staff at the [Redbot discord](https://discord.gg/red),  
[Aikaterna](https://github.com/aikaterna) for taking the time to QA this repo,  
[Hasbro](hasbro.com) for creating the games that Battleship and Monopoly are based off of,  
[TrustyJAID](https://github.com/TrustyJAID) for helping with Deepfry,  
[Desi Quintans](http://www.desiquintans.com/nounlist) for the wordlist used by Hangman,  
iComputer7#0007 for the inspiration for Face,  
[Microsoft Azure](https://azure.microsoft.com/en-us/) for the API that Face uses,  
[Sparklin Labs](http://bombparty.sparklinlabs.com/) for creating the game that Partygames is based off of,  
[/u/YoungsterGlenn](https://www.reddit.com/r/BombParty/comments/3lehxq/a_nearly_exhaustive_subset_of_the_bombparty/) for the wordlist used by Partygames,  
And [Sinbad](https://github.com/mikeshardmind) for helping with Wordstats.
