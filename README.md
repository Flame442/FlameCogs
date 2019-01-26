# FlameCogs

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
[Gamevoice](../master/README.md#gamevoice) | Make voice channels require playing a specific game in order to join.
[Hangman](../master/README.md#hangman) | Play hangman with the bot.
[Monopoly](../master/README.md#monopoly) | Play monopoly with up to 7 other people in your server.

## Battleship

This cog will let you play battleship against another member of your server.

### Usage

**`[p]battleship`**  
Begin a game of battleship.

**`[p]battleshipset [value]`**  
Set if an extra shot should be given after a hit.  
Defaults to `True`.  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

## Deepfry

This cog lets you deepfry and nuke images. It has a configurable chance to deepfry any image posted automaticly and users can choose to deepfry or nuke images.  
Images have to be attatched to the command, links do NOT work!

### Usage

**`[p]deepfry`**  
Deepfries the attatched image.  
Alias: `[p]df`

**`[p]nuke`**  
Nukes the attatched image

**`[p]deepfryset [value]`**  
Change the rate images are automatically deepfried.  
Images will have a 1/`[value]` chance to be deepfried.  
Higher values cause less often fries.  
Set to `0` to disable.  
Defaults to `0` (off)  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

## Gamevoice

This cog lets you make voice channels that require a user to be playing a specific game in order to join.

### Usage

**`[p]gamevoice <argument>`**  
Alias `[p]gv <argument>`

**`[p]gamevoice set`**  
Sets the voice channel you are in to only work with the game you are playing.  
Any activity will count, including Spotify, so make sure discord thinks you are doing the correct activity.  
This command is only usable by the guild owner and bot owner.

**`[p]gamevoice reset`**  
Resets the voice channel you are in to defaults.  
Will remove ALL permissions, not just those set by the cog, making it completely open.  
This command is only usable by the guild owner and bot owner.

**`[p]gamevoice listroles`**  
Lists all the roles created for games on the server.  
This command is only usable by the guild owner and bot owner.

**`[p]gamevoice deleterole <name>`**  
Delete a role from the server.  
Also removes that game's restrictions from all channels.  
Case sensitive.  
Use `[p]gv listroles` to see all roles.  
This command is only usable by the guild owner and bot owner.  
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
This command is only usable by the guild owner and bot owner.

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
This command is only usable by the guild owner and bot owner.  
This value is server specific.

## Monopoly

This cog will let you play monopoly with up to 7 other people in your server.

### Usage

**`[p]monopoly [savename]`**  
Begin a game of monopoly.   
Use the optional paramater `savename` to load a saved game.

**`[p]monopolyset <argument>`**  
Config options for monopoly.  
This command is only usable by the guild owner and bot owner.

**`[p]monopolyset mention [value]`**  
Set if players should be mentioned when their turn begins.  
Defaults to `False`.  
This command is only usable by the guild owner and bot owner.
This value is server specific.  

**`[p]monopolyset startingcash [value]`**  
Set how much money players should start the game with.  
Defaults to `1500`.  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

**`[p]monopolyset income [value]`**  
Set how much Income Tax should cost.  
Defaults to `200`.  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

**`[p]monopolyset luxury [value]`**  
Set how much Luxury Tax should cost.  
Defaults to `100`.  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

**`[p]monopolyset auction [value]`**  
Set if properties should be auctioned when passed on.
Defaults to `False`.
This command is only usable by the guild owner and bot owner.  
This value is server specific.

**`[p]monopolyset bail [value]`**  
Set how much bail should cost.  
Defaults to `50`.  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

**`[p]monopolyset maxjailrolls [value]`**  
Set the maximum number of rolls in jail before bail has to be paid.  
Defaults to 3.  
This command is only usable by the guild owner and bot owner.  
This value is server specific.

# Planned changes

**[Monopoly]** Add config for various house rules (~~auctions~~, free parking, landing on go, etc)

**[Battleship/Hangman/Monopoly]** Add optional betting to games

**[Battleship]** Add command to end game

# Contact

Feel free to create an issue on this repository or join [my discord](https://discord.gg/bYqCjvu) if you have any issues.

# Credit

Thanks to the [creators of Redbot](https://github.com/Cog-Creators/Red-DiscordBot/graphs/contributors) for creating the base these cogs run on, the helpful support staff at the [Redbot discord](https://discord.gg/red), Aikaterna for taking the time to QA this repo, TrustyJAID for helping with deepfry, and [Desi Quintans](http://www.desiquintans.com/nounlist) for the wordlist used by Hangman.
