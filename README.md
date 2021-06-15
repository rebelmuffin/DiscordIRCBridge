#IRC-Discord Bridge

Connects to a discord user account and an IRC server with credentials and connects text channels.

###Disclaimer
This project uses Discord self-bots and is against their TOS which means using this is not advised as it will probably lead your account to a permanent ban.

This project was created solely as a proof-of-concept and has no real world use.

##Configuration
The bot is configured with JSON files (yeah, bad practice whatever whatever). You need 2 configuration files for operation: `config.json` and `channels.json`

###Examples
`config.json`
```json
{
  "TOKEN": "MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs",
  "IRC_HOST": "0.0.0.0",
  "IRC_PASS": "my_irc_password",
  "IRC_NICK": "RebelMuffin",
  "IRC_REAL": "RealMuffin"
}
```

`channels.json`
```json
{
  "#channel": 103735883630395392,
  "#dms": 80351110224678912
}
```
