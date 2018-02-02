# TrackTimeBot

A Telegram bot to help you track your time.

## Installation:

The bot depends on a telegram wrapper of mine which is currently pre-alpha. Install the wrapper and the bot
like so:

```commandline
python3 -m pip install git+https://github.com/jarhill0/pawt.git
git clone https://github.com/jarhill0/TrackTimeBot.git
```

## Configuration:

```commandline
cd TrackTimeBot
touch secrets.py
```

Use an editor of your choice to add the following line to `secrets.py`, with your token substituted for the
placeholder:

```python
TOKEN = '123456789:QwErTyUiOpAsDfGhJkLzXcVbNm'
```

Configure the bot with `crontab` (or Task Scheduler if you're on Windows, but then you're on your own). The
following will work if the bot is in `/home/user/TrackTimeBot`. Modify it appropriately if the bot is in a 
different directory. An absolute path is recommended. 

```text
00 * * * * python3 /home/user/TrackTimeBot/main.py hourly
55 0 * * * python3 /home/user/TrackTimeBot/main.py daily
```

## Bot Usage

[Try it out!](https://t.me/TrackTimeBot)

To interact with the bot:

- /subscribe will subscribe you to bot messages
- /unsubscribe will unsubscribe you.
- /help and /start will bring up appropriate messages

Every hour, on the hour, the bot will message you to ask what you did the previous hour. Reply to its hour 
message (e.g. "3 pm") at any point during the day, and it will log that activity. Activities can be 
anything you can put in a plain text message (not an image caption, or a caption of anything else), such as
"3" or "programming" or "going to the beach."

Every day at 12:55 am (00:55), the bot will send a tab-separated list of your past 24 hours, assuming you
responded with at least one activity in that period. I chose tab-separated over alternatives because 
Numbers for Mac (which I am using to track my time) supports pasting tab-separated values but not 
comma-separated values. 

The bot currently only supports running on one time zone, since it's largely a project for myself. My 
instance runs on Pacific Time, but if you set up your own instance, it will run on whatever time zone your 
system is configured for.

## Privacy

None to speak of. As you can see from reading the source code, data is stored as plain JSON on disk. Anyone
with access to the server can read your activities. Don't share anything you wouldn't want the server admin
(me, for my instance) reading.
