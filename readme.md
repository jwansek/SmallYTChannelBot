# /u/SmallYTChannelBot Source Code

- SmallYTChannelBotSubmissions.py is where the main code is kept. It has the
main subreddit stream in it.

- SmallYTChannelDatabase.db is an SQLite file containing the database. I chose
SQLite over MySQL since it's easier to backup. Maybe one day we'll upgrade to
MySQL and do automated backups.

- database.py is a class for interfacing with the database.

- onceaday.py is a file which calls a function in the main prog every 24h
to do statistcs stuff, drawing the graphs etc.

- runprog.py calls the main program. The way it does this is kinda alkward,
because it kills the main program and restarts it every 2h. I don't even know
if this is needed anymore but it fixed problems so it stays. It works because
the main prog writes its pid in a text file every time it's called. This pid
is called after 2h and a new instance is started.

- ytapi.py gets data about user's videos in the subreddit to do the stats comment
and do the flair.

- Not included for security reasons is login.py which has the PRAW instance and
API keys for imgur. The YT api key is in ytapi.py for some reason. Hope that
isn't a massive problem.

If you're looking at this because you think I'm dead, the bot is running on an
AWS instance that expires in November 2019, you'll need to find a new host
before then. The backup is probably out of date, so you'll need to write a script
that parses the subreddit and gets everyone's lambda scores from their flair.

# TODOs

- Automatically flair when [] is in submission title

- Implement !recheck command to recheck already removed submissions

- Ignore bot commands when they're formatted as code (` or indentation)

- Write a bot for the discord

- Automate backups

# About the database's structure

`users` is where usernames and the scores are kept. `lambdas` is for every
time a lambda is given. Is linked to `users`. `stats` keeps unique users (just
the amount of users in `users`), the total lambda in circulation (everyone's
lambda scores summed), and the times help given, which is just the sum of every
unique entry in `lambdas`. `blacklist` is the reddit id of every comment / 
submission the bot has dealt with. If running on a new system you'll need to
update this. You can do this using archive_posts.py
