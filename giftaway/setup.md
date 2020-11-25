# GiftAway IGDB integration setup

This guide will teach you how to enable IGDB integration for GiftAway. IGDB integration will allow giftaway messages to display info about the game being given away.

## Step 1

Ensure you have the cog installed.

Add the repo: `[p]repo add flamecogs https://github.com/Flame442/FlameCogs`.

>[p] is your prefix.

Install giftaway: `[p]cog install flamecogs giftaway`.

Load giftaway: `[p]load giftaway`.

## Step 2

Create a [twitch account](https://dev.twitch.tv/login).

## Step 3

Enable [two factor authentication](https://www.twitch.tv/settings/security) for your twitch account.

## Step 4

[Create](https://dev.twitch.tv/console/apps/create) a new application on twitch. Put whatever you want for the application name (although it needs to be unique), 
enter "`http://localhost`" for the OAuth Redirect URLs field, and select "`Application integration`" for the category.

## Step 5

Click [manage](https://dev.twitch.tv/console/apps) on your newly created app.

## Step 6

Generate a new client secret by clicking "`New secret`".

## Step 7

Give the bot your API ID and secret with `[p]set api igdb id <your_id> secret <your_secret>`.
