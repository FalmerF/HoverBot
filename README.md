# HoverBot
Univirsal Bot for Discord.
The full functionality is described in the bot itself:  
`!help`  
`!helpmoder`  
`!helpadmin`  
`!helpsettings`  
`!helpembed`  
`!totalhelp`

# Member profile
Each member has their own profile with balance, level, voice activity and reputation.

The balance can be increased by picking up daily rewards with `!everyday` or by being in the voice channels.

You can gain experience and level up by sending messages to text channels (the channel list is configurable) or being in the voice channel (the channel list is also configurable).

Reputation is increased by other members with the `!pr <member>`.

![](https://github.com/FalmerF/HoverBot/blob/main/Screenshots/screenshot_1.png)

# Role Store 
In the role store, you can get the roles specified by the server administrators for the currency in the profile. Each role and its cost in the store is configured by administrators using the commands:  
`!shopadd <@role> <cost>`  
`!shopdel <number>`

![](https://github.com/FalmerF/HoverBot/blob/main/Screenshots/screenshot_2.png)

# Auto-Moderation
The bot has auto-moderation elements, specifically:  
`-Spam filter`  
`-Link filter`

The channels in which the filters operate are configured by administrators with the command `!setspam <channelsID>`

![](https://github.com/FalmerF/HoverBot/blob/main/Screenshots/screenshot_3.png)

# Moderation
The bot has elements of manual moderation. You can issue warns to participants and block chat. For a certain number of warns, the bot will automatically block the chat to the participant. You can still remove warnings and blocking chat using commands. More: `!helpmoder`

![](https://github.com/FalmerF/HoverBot/blob/main/Screenshots/screenshot_4.png)
