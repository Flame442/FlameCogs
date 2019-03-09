# Face cog setup

This guide will teach you how to properly set up this cog.

## Step 1

Install and load the cog on to your redbot.

Add the repo: `[p]repo add flamecogs https://github.com/Flame442/FlameCogs`.

>[p] is your prefix.

Install face: `[p]cog install flamecogs face`.

Load face: `[p]load face`.

## Step 2

Go to the [Azure website](https://portal.azure.com/).  
You will be asked to sign in with your Microsoft account. Create one if you do not already have one.  
If asked to follow a tutorial, select "Maybe later".

## Step 3

Click on "Create a resource" at the top left.
![Step3](https://docs.microsoft.com/en-us/azure/cognitive-services/media/cognitive-services-apis-create-account/azureportalscreen.png)

## Step 4

Under "Azure Marketplace", select "AI + Machine Learning".  
Then under "Featured" select "Face".
![Step4](https://i.imgur.com/JKoaEU1.png)

## Step 5

You may be asked to create a free account.  

Select "Start free" at the bottom of the page.  
Click the green "Start Free" button in the middle of the tab that will open.  
Fill out the form with the required information to create your account.  

## Step 6

Fill out the fields:  
Under "Name" put any name you want.  
Under "Subscription" select "Free Trial".  
Under "Location" select the region closest to your bot's location.  
Under "Pricing tier" select "F0".  
Click "Create new" under "Pricing group" and create a group,then select that group.

![Step5](https://docs.microsoft.com/en-us/azure/cognitive-services/media/cognitive-services-apis-create-account/resource_create_screen.png)

Click "Create" at the bottom.

# Step 7

On the left side of the page, click "Resource Groups" then select the group you just made.  
Select the resource you just made.  
![Step7a](https://i.imgur.com/SNtAItE.png)

Select "Overview" from the list on the left.  
![Step7b](https://i.imgur.com/mvlOuVU.png)

# Step 8

Copy the link under "Endpoint". Give that link to the bot using `[p]faceset url <link>`.  
Copy one of your keys under "Manage keys". Give that key to the bot using `[p]faceset key <key>`.
![Step8](https://i.imgur.com/37kdPGZ.png)
