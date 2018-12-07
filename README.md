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

## Battleship
This cog will let you play battleship against another member of your server.
### Usage
`[p]battleship`

Begin a game of battleship.

`[p]battleshipset [value]`

Set if an extra shot should be given after a hit.

Defaults to `True`.

This value is server specific.
## Deepfry
This cog lets you deepfry and nuke images. It has a configurable chance to deepfry any image posted automaticly and users can choose to deepfry or nuke images. 

Images have to be attatched to the command, links do NOT work!
### Usage
`[p]deepfry [amount]`

Deepfries the attatched image by the `amount` provided.

Alias: `[p]df [amount]`

`[p]nuke`

Nukes the attatched image

`[p]deepfryset [value]`

Change the rate images are automatically deepfried.

Images will have a 1/`[value]` chance to be deepfried.

Higher values cause less often fries.

Set to `0` to disable.

This command is only usable by the guild owner and bot owner.

This value is server specific.

Defaults to `0` (off)
## Gamevoice
This cog lets you make voice channels that require a user to be playing a specific game in order to join.
### Usage
`[p]gamevoice <argument>`

Alias `[p]gv <argument`

`[p]gamevoice set`

Sets the voice channel you are in to only work with the game you are playing.

If you are not playing a game, the channel will be reset.

Any activity will count, including Spotify, so make sure discord thinks you are doing the correct activity.

This command is only usable by the guild owner and bot owner.

`[p]gamevoice recheck`

Force a recheck of your current game.

Use this if you are playing the correct game and it does not let you join.
## Hangman
This cog will play hangman with you.
### Usage
`[p]hangman`

Begin a game of hangman.

`[p]hangmanset <argument>`

Settings for hangman.

This command is only usable by the guild owner and bot owner.

`[p]hangmanset wordlist [value]`

Change the wordlist used.

Extra wordlists can be put in the data folder of this cog.

Wordlists are a text file with every new line being a new word.

Use `default` to restore the default wordlist.

Use `list` to list available wordlists.

This value is server specific.

`[p]hangmanset edit [value]`

<In development>
## Monopoly
This cog will let you play monopoly with up to 7 other people in your server.
### Usage
`[p]monopoly [savename]`

Begin a game of monopoly. 

Use the optional paramater `savename` to load a saved game.
# Planned changes

**[Battleship]** Make placing ships eaisier to understand

**[Monopoly]** Add config for various house rules (auctions, free parking, landing on go, etc)
# Contact
Feel free to create an issue on this repository for any bugs you find.
# Credit
Thanks to the creators of Redbot for creating the base these cogs run on and the helpful support staff at the Redbot [discord](https://discord.gg/red).
